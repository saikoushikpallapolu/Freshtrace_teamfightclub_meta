"""Real file/database/API boundaries on disposable storage, without AWS or Meta."""

from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import inspect, text

from backend.api.product import create_app
from backend.persistence.models import Base
from backend.persistence.runtime import initialize_schema, make_engine
from backend.storage.media import LocalMediaStore


def image_bytes():
    output = BytesIO()
    image = Image.new("RGB", (30, 20), "red")
    exif = image.getexif()
    exif[274] = 6
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def batch(client):
    response = client.post(
        "/api/batches", json={"label": "Tray A", "quantity": 12, "quantity_unit": "items"}
    )
    assert response.status_code == 201, response.text
    return response.json()["batch_id"]


@pytest.fixture
def settings(tmp_path):
    return {
        "database_url": f"sqlite:///{(tmp_path / 'product.db').as_posix()}",
        "media_root": tmp_path / "media",
    }


def test_saved_evidence_survives_restart_and_original_is_unchanged(settings):
    original = image_bytes()
    with TestClient(create_app(**settings)) as client:
        bid = batch(client)
        response = client.post(
            f"/api/batches/{bid}/media", content=original, headers={"Content-Type": "image/jpeg"}
        )
        assert response.status_code == 201, response.text
        media = response.json()
        assert (media["width"], media["height"]) == (20, 30)
        assert "original_key" not in media
        mid = media["media_id"]
        response = client.post(
            f"/api/batches/{bid}/observations",
            json={"media_id": mid, "captured_at": "2026-11-02T10:00:00+05:30", "source": "fixture"},
        )
        assert response.status_code == 201, response.text
        observation = response.json()
        assert observation["status"] == "captured"  # Never pretends model inference ran.
    with TestClient(create_app(**settings)) as client:
        assert client.get(f"/api/batches/{bid}").json()["quantity"] == 12
        assert client.get(f"/api/batches/{bid}/observations").json() == [observation]
        assert (
            client.get(f"/api/batches/{bid}/media/{mid}/content?variant=original").content
            == original
        )
        normalized = client.get(f"/api/batches/{bid}/media/{mid}/content")
        assert normalized.headers["x-content-type-options"] == "nosniff"
        with Image.open(BytesIO(normalized.content)) as image:
            assert image.size == (20, 30)
            assert not image.getexif()


def test_legacy_rows_survive_repeated_migration(settings):
    engine = make_engine(settings["database_url"])
    # Simulate a pre-product installation, not a database made by the new initializer.
    Base.metadata.tables["sessions"].create(engine)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO sessions (session_id, device_id) VALUES ('legacy', 'device')")
        )
    initialize_schema(engine)
    initialize_schema(engine)
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT device_id FROM sessions WHERE session_id='legacy'"))
            == "device"
        )
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0002_request_receipts"
        )
    assert "product_model_calls" in inspect(engine).get_table_names()
    engine.dispose()


def test_invalid_inputs_and_cross_batch_media_are_rejected(settings):
    with TestClient(create_app(**settings)) as client:
        first, second = batch(client), batch(client)
        assert client.get("/api/batches/not-a-uuid").status_code == 422
        assert client.get(f"/api/batches/{uuid4()}").status_code == 404
        for quantity in [0, -1, 1.5]:
            assert (
                client.post(
                    "/api/batches",
                    json={"label": "x", "quantity": quantity, "quantity_unit": "items"},
                ).status_code
                == 422
            )
        assert (
            client.post(
                "/api/batches", json={"label": " ", "quantity": 1, "quantity_unit": "kg"}
            ).status_code
            == 422
        )
        media = client.post(
            f"/api/batches/{first}/media",
            content=image_bytes(),
            headers={"Content-Type": "image/jpeg"},
        ).json()
        mid = media["media_id"]
        assert client.get(f"/api/batches/{second}/media/{mid}").status_code == 404
        assert client.get(f"/api/batches/{second}/media/{mid}/content").status_code == 404
        payload = {"media_id": mid, "captured_at": "2026-11-02T10:00:00Z"}
        assert client.post(f"/api/batches/{second}/observations", json=payload).status_code == 404
        payload["captured_at"] = "2026-11-02T10:00:00"
        assert client.post(f"/api/batches/{first}/observations", json=payload).status_code == 422
        assert client.get(f"/api/batches/{first}/observations").json() == []


def test_upload_boundaries(settings):
    with TestClient(create_app(**settings)) as client:
        bid = batch(client)
        path = f"/api/batches/{bid}/media"
        assert (
            client.post(
                path, content=b"not an image", headers={"Content-Type": "image/jpeg"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                path, content=image_bytes(), headers={"Content-Type": "image/png"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                path, content=b"<svg/>", headers={"Content-Type": "image/svg+xml"}
            ).status_code
            == 415
        )
        assert (
            client.post(
                path, content=b"x" * (10 * 1024 * 1024 + 1), headers={"Content-Type": "image/jpeg"}
            ).status_code
            == 413
        )
        assert not settings["media_root"].exists()


def test_pixels_and_storage_traversal_rejected(settings, monkeypatch):
    import backend.storage.media as media

    monkeypatch.setattr(media, "MAX_PIXELS", 10)
    with TestClient(create_app(**settings)) as client:
        bid = batch(client)
        assert (
            client.post(
                f"/api/batches/{bid}/media",
                content=image_bytes(),
                headers={"Content-Type": "image/jpeg"},
            ).status_code
            == 422
        )
    with pytest.raises(ValueError):
        LocalMediaStore(settings["media_root"]).resolve("../escape")


def test_sqlite_foreign_keys_are_enforced(settings):
    from sqlalchemy.exc import IntegrityError

    engine = make_engine(settings["database_url"])
    initialize_schema(engine)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO product_sensor_links "
                "(session_id,batch_id,device_id,protocol_version,status) "
                "VALUES ('x','missing','d','v1','requested')"
            )
        )
    engine.dispose()


def test_retried_mutations_replay_after_restart_and_conflicts_reject(settings):
    key, media_key, observation_key = str(uuid4()), str(uuid4()), str(uuid4())
    payload = {"label": "Idempotent tray", "quantity": 5, "quantity_unit": "items"}
    with TestClient(create_app(**settings)) as client:
        first = client.post("/api/batches", json=payload, headers={"Idempotency-Key": key})
        bid = first.json()["batch_id"]
        media = client.post(
            f"/api/batches/{bid}/media",
            content=image_bytes(),
            headers={"Content-Type": "image/jpeg", "Idempotency-Key": media_key},
        )
        mid = media.json()["media_id"]
        observation_payload = {"media_id": mid, "captured_at": "2026-11-02T10:00:00Z"}
        observation = client.post(
            f"/api/batches/{bid}/observations",
            json=observation_payload,
            headers={"Idempotency-Key": observation_key},
        )
    with TestClient(create_app(**settings)) as client:
        assert (
            client.post("/api/batches", json=payload, headers={"Idempotency-Key": key}).json()
            == first.json()
        )
        assert len(client.get("/api/batches").json()) == 1
        changed = {**payload, "quantity": 6}
        assert (
            client.post("/api/batches", json=changed, headers={"Idempotency-Key": key}).status_code
            == 409
        )
        assert (
            client.post(
                f"/api/batches/{bid}/media",
                content=image_bytes(),
                headers={"Content-Type": "image/jpeg", "Idempotency-Key": media_key},
            ).json()
            == media.json()
        )
        assert (
            client.post(
                f"/api/batches/{bid}/observations",
                json=observation_payload,
                headers={"Idempotency-Key": observation_key},
            ).json()
            == observation.json()
        )
        assert len(client.get(f"/api/batches/{bid}/observations").json()) == 1


def test_database_rejects_cross_batch_observation(settings):
    from sqlalchemy.exc import IntegrityError

    with TestClient(create_app(**settings)) as client:
        first, second = batch(client), batch(client)
        media = client.post(
            f"/api/batches/{first}/media",
            content=image_bytes(),
            headers={"Content-Type": "image/jpeg"},
        ).json()
    engine = make_engine(settings["database_url"])
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO product_observations "
                "(observation_id,batch_id,media_id,captured_at,created_at,source,status) "
                "VALUES (:oid,:bid,:mid,'2026-11-02','2026-11-02','fixture','captured')"
            ),
            {"oid": str(uuid4()), "bid": second, "mid": media["media_id"]},
        )
    engine.dispose()


def test_migrations_match_models(settings):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    engine = make_engine(settings["database_url"])
    initialize_schema(engine)
    with engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    engine.dispose()
