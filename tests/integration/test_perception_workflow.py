"""Durable job/review boundaries with an explicitly injected offline pipeline."""

from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from backend.api.product import create_app
from backend.persistence.product_models import PerceptionJobModel
from backend.workflows.perception import PerceptionWorker


@pytest.fixture
def configured(tmp_path):
    return dict(
        database_url=f"sqlite:///{(tmp_path / 'jobs.db').as_posix()}", media_root=tmp_path / "media"
    )


def setup_observation(client):
    bid = client.post(
        "/api/batches",
        json={"label": "Offline workflow test", "quantity": 2, "quantity_unit": "items"},
    ).json()["batch_id"]
    content = BytesIO()
    Image.new("RGB", (40, 20), "red").save(content, format="JPEG")
    mid = client.post(
        f"/api/batches/{bid}/media",
        content=content.getvalue(),
        headers={"Content-Type": "image/jpeg"},
    ).json()["media_id"]
    oid = client.post(
        f"/api/batches/{bid}/observations",
        json={"media_id": mid, "captured_at": "2026-11-02T12:00:00Z", "source": "fixture"},
    ).json()["observation_id"]
    return bid, oid, f"/api/batches/{bid}/observations/{oid}"


def offline_pipeline(client, source, directory, receipt):
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGB")
    for filename in ["analysis.jpg", "inspection_overlay.jpg", "crop_000.jpg"]:
        image.save(directory / filename)
    Image.new("L", image.size, 255).save(directory / "mask_000.png")
    receipt(SimpleNamespace(model="sam-3.1", status="completed", id="offline-sam", usage=None), 1)
    return {
        "mode": "test_fixture",
        "width": 40,
        "height": 20,
        "prompt_version": "test-only",
        "scene_limits": ["offline test"],
        "sensor": None,
        "objects": [
            {
                "object_id": "T01",
                "bounds": [0, 0, 20, 20],
                "category": "inspect",
                "observations": ["offline test"],
                "visibility_limits": ["hidden side"],
                "crop_file": "crop_000.jpg",
                "mask_file": "mask_000.png",
            }
        ],
    }


def test_no_key_never_queues_or_fakes_results(configured, monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with TestClient(create_app(**configured)) as client:
        _, _, path = setup_observation(client)
        assert client.get("/api/capabilities").json()["live_analysis"] is False
        assert client.post(path + "/analysis").status_code == 503
        assert client.get(path + "/analysis").json() == {"job": None, "reviews": [], "calls": []}


def test_queue_restart_process_once_and_persist_review(configured):
    app = create_app(**configured)
    with TestClient(app) as client:
        bid, oid, path = setup_observation(client)
        app.state.analysis_enabled = True  # Queue without starting any provider or thread.
        queued = client.post(path + "/analysis").json()
        assert queued["status"] == "queued"
        assert client.post(path + "/analysis").json()["job_id"] == queued["job_id"]
    app = create_app(**configured)
    with TestClient(app) as client:
        worker = PerceptionWorker(
            app.state.product_sessions,
            app.state.product_media,
            lambda: nullcontext(None),
            pipeline=offline_pipeline,
        )
        assert worker.run_once()
        assert worker.run_once() is False
        state = client.get(path + "/analysis").json()
        assert state["job"]["status"] == "complete"
        assert state["job"]["result"]["mode"] == "test_fixture"
        assert len(state["calls"]) == 1
        assert client.get(path + "/artifacts/inspection_overlay.jpg").status_code == 200
        assert client.get(path + "/artifacts/not-allowed.txt").status_code == 404
        assert (
            client.post(
                path + "/reviews",
                json={"object_id": "other", "category": "inspect", "note": "test"},
            ).status_code
            == 409
        )
        review = {"object_id": "T01", "category": "unclear", "note": "Need another view"}
        assert client.post(path + "/reviews", json=review).status_code == 201
        state = client.get(path + "/analysis").json()
        assert state["reviews"][0]["category"] == "unclear"
        assert state["job"]["result"]["objects"][0]["category"] == "inspect"
        other = client.post(
            "/api/batches", json={"label": "Other", "quantity": 1, "quantity_unit": "items"}
        ).json()["batch_id"]
        assert client.get(f"/api/batches/{other}/observations/{oid}/analysis").status_code == 404
        assert (
            client.get(
                f"/api/batches/{other}/observations/{oid}/artifacts/analysis.jpg"
            ).status_code
            == 404
        )
    with TestClient(create_app(**configured)) as client:
        assert client.get(path + "/analysis").json()["reviews"][0]["note"] == "Need another view"


def test_failure_is_sanitized_and_retry_is_explicit(configured):
    app = create_app(**configured)
    with TestClient(app) as client:
        _, _, path = setup_observation(client)
        app.state.analysis_enabled = True
        client.post(path + "/analysis")

        def broken(*args):
            raise RuntimeError("secret-request-headers-must-not-be-saved")

        worker = PerceptionWorker(
            app.state.product_sessions,
            app.state.product_media,
            lambda: nullcontext(None),
            pipeline=broken,
        )
        worker.run_once()
        state = client.get(path + "/analysis")
        assert state.json()["job"]["error_code"] == "analysis_failed"
        assert "secret-request" not in state.text
        assert worker.run_once() is False
        assert client.get(path + "/artifacts/analysis.jpg").status_code == 404
        assert client.post(path + "/analysis").json()["status"] == "failed"
        retried = client.post(path + "/analysis/retry")
        assert retried.json()["attempt"] == 2
        assert client.post(path + "/analysis/retry").status_code == 409
        worker.pipeline = offline_pipeline
        assert worker.run_once()
        assert client.get(path + "/analysis").json()["job"]["status"] == "complete"


def test_expired_worker_is_not_silently_rebilled(configured):
    app = create_app(**configured)
    with TestClient(app) as client:
        _, _, path = setup_observation(client)
        app.state.analysis_enabled = True
        client.post(path + "/analysis")
        with app.state.product_sessions() as db:
            job = db.scalar(select(PerceptionJobModel))
            job.status = "running"
            job.lease_until = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            db.commit()
        worker = PerceptionWorker(
            app.state.product_sessions,
            app.state.product_media,
            lambda: nullcontext(None),
            pipeline=offline_pipeline,
        )
        assert worker.run_once() is False
        assert client.get(path + "/analysis").json()["job"]["error_code"] == "worker_interrupted"


def test_samples_have_provenance_and_import_is_idempotent(configured):
    with TestClient(create_app(**configured)) as client:
        bid, _, _ = setup_observation(client)
        samples = client.get("/api/samples").json()
        assert len(samples) == 4
        assert all(s["license_url"].startswith("https://creativecommons.org/") for s in samples)
        first = client.post("/api/samples/mixed_mold/import", json={"batch_id": bid})
        assert first.status_code == 201, first.text
        assert first.json()["source"] == "fixture"
        assert first.json()["sample_id"] == "mixed_mold"
        assert (
            client.post("/api/samples/mixed_mold/import", json={"batch_id": bid}).json()
            == first.json()
        )
        assert (
            client.post("/api/samples/not-allowlisted/import", json={"batch_id": bid}).status_code
            == 404
        )
        assert (
            client.post(
                "/api/samples/mixed_mold/import", json={"batch_id": str(uuid4())}
            ).status_code
            == 404
        )


def test_two_workers_cannot_process_the_same_job(configured):
    from concurrent.futures import ThreadPoolExecutor

    app = create_app(**configured)
    calls = []

    def pipeline(*args):
        calls.append("one paid attempt")
        return offline_pipeline(*args)

    with TestClient(app) as client:
        _, _, path = setup_observation(client)
        app.state.analysis_enabled = True
        client.post(path + "/analysis")
        workers = [
            PerceptionWorker(
                app.state.product_sessions,
                app.state.product_media,
                lambda: nullcontext(None),
                pipeline=pipeline,
            )
            for _ in range(2)
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda worker: worker.run_once(), workers))
        assert sum(results) == 1
        assert len(calls) == 1
        assert client.get(path + "/analysis").json()["job"]["status"] == "complete"
