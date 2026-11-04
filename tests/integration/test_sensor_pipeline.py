"""Sensor ingestion and cross-process status use disposable storage, never AWS."""

import importlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine


@pytest.fixture
def sensor_api(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'sensor.db').as_posix()}")
    monkeypatch.setenv("AWS_SQS_QUEUE_URL", "")
    monkeypatch.setenv("AWS_SNS_TOPIC_ARN", "")
    # The sensor API loads .env for the legacy launcher; explicit test values win.
    import backend.persistence.db as database

    importlib.reload(database)
    import backend.inference_service as service

    importlib.reload(service)
    import backend.api.routes as routes

    importlib.reload(routes)
    from backend.ingestion.processor import IngestionProcessor

    routes.inference_engine.ingestor = IngestionProcessor(tmp_path / "raw")
    with TestClient(routes.app) as client:
        yield client, routes
    database.engine.dispose()


def packet(device="Sensor-A"):
    return dict(
        device_id=device,
        food_type="tomato",
        temperature_c=25,
        humidity_pct=60,
        voc_raw=31800,
        nox_raw=16800,
    )


def test_empty_device_has_no_invented_readings(sensor_api):
    client, _ = sensor_api
    assert client.get("/devices").json() == {"devices": []}
    state = client.get("/devices/unknown/status").json()
    assert state["sensor"] is None
    assert state["spoilage_risk"] is None
    assert state["last_updated"] is None
    assert state["has_data"] is False


def test_multiple_devices_and_full_snapshot_survive_api_cache_loss(sensor_api):
    client, routes = sensor_api
    results = []
    for device in ("Sensor-A", "Sensor-B"):
        response = client.post("/telemetry", json=packet(device))
        assert response.status_code == 200, response.text
        results.append(response.json()["result"])
    assert results[0]["session_id"] != results[1]["session_id"]
    routes.inference_engine.last_known_state.clear()
    assert set(client.get("/devices").json()["devices"]) == {"Sensor-A", "Sensor-B"}
    state = client.get("/devices/Sensor-A/status").json()
    assert state["risk"]["biochemical"] == results[0]["biochemical_risk"]
    assert state["risk"]["thermal"] == results[0]["thermal_risk"]
    assert state["voc_velocity"] == results[0]["voc_velocity"]
    assert state["sensor"]["voc_raw"] == 31800
    assert len(client.get("/devices/Sensor-A/telemetry/history").json()) == 1
    assert client.get("/devices/Sensor-A/telemetry/history?limit=-1").status_code == 422


def test_old_snapshot_timestamp_and_missing_components(sensor_api):
    client, routes = sensor_api
    client.post("/telemetry", json=packet())
    from backend.persistence.db import SessionLocal

    with SessionLocal() as db:
        row = db.query(routes.StateSnapshotModel).first()
        row.payload = None
        row.timestamp = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        db.commit()
    state = client.get("/devices/Sensor-A/status").json()
    assert not state["is_online"]
    assert state["risk"]["thermal"] is None
    assert state["risk"]["biochemical"] is None
    assert state["seconds_since_last_packet"] >= 60


def test_unsafe_device_names_rejected_before_writing(sensor_api):
    client, _ = sensor_api
    assert client.post("/telemetry", json=packet("../escape")).status_code == 400
    assert client.get("/devices").json()["devices"] == []


def test_raw_history_is_available_without_a_snapshot(sensor_api):
    client, routes = sensor_api
    result = client.post("/telemetry", json=packet()).json()["result"]
    from backend.persistence.db import SessionLocal

    with SessionLocal() as db:
        db.query(routes.StateSnapshotModel).delete()
        db.commit()
    state = client.get("/devices/Sensor-A/status").json()
    assert state["last_updated"] == result["timestamp"]
    assert state["sensor"]["voc_raw"] == 31800
    assert state["spoilage_risk"] is None
    assert state["is_online"]


def test_failed_write_can_retry_without_advancing_calibration(sensor_api, monkeypatch):
    client, routes = sensor_api
    service = routes.inference_engine
    persist = service._persist_to_db

    def failed_write(*args):
        raise RuntimeError("Database unavailable")

    monkeypatch.setattr(service, "_persist_to_db", failed_write)
    payload = {**packet(), "sequence_number": 1}
    with pytest.raises(RuntimeError, match="Database unavailable"):
        service.process_telemetry_payload(payload)
    assert service.signal_engine.sessions == {}
    assert service.ingestor.sequence_trackers == {}
    monkeypatch.setattr(service, "_persist_to_db", persist)
    assert client.post("/telemetry", json=payload).status_code == 200
    session = next(iter(service.signal_engine.sessions.values()))
    assert len(session.raw_history) == 1
    assert len(client.get("/devices/Sensor-A/telemetry/history").json()) == 1


def test_migration_preserves_existing_sensor_rows(tmp_path):
    from backend.persistence.runtime import initialize_schema

    engine = create_engine(f"sqlite:///{(tmp_path / 'old.db').as_posix()}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE state_snapshots (id INTEGER PRIMARY KEY, session_id VARCHAR, "
            "timestamp VARCHAR, spoilage_state VARCHAR, overall_risk FLOAT, rul_hours FLOAT)"
        )
        connection.exec_driver_sql("INSERT INTO state_snapshots (id,overall_risk) VALUES (1,0.3)")
    initialize_schema(engine)
    with engine.connect() as connection:
        row = connection.exec_driver_sql("SELECT overall_risk,payload FROM state_snapshots").one()
        assert row == (0.3, None)
    engine.dispose()
