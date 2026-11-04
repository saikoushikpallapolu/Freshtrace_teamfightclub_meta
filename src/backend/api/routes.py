import asyncio
import json
import os
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.product import configure_product
from backend.inference_service import InferenceEngineService
from backend.persistence.db import engine, get_db
from backend.persistence.models import (
    EventModel,
    RawTelemetryModel,
    SessionModel,
    StateSnapshotModel,
)

app = FastAPI(title="Application Biochemical Spoilage Intelligence API", version="0.2.0")

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "APP_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global inference engine instance
inference_engine = InferenceEngineService()

# Global list of connected stream subscribers for live push
subscribers: List[asyncio.Queue] = []


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/devices")
def get_devices(db: Session = Depends(get_db)):
    sessions = db.query(SessionModel).all()
    devices = list(set([s.device_id for s in sessions]))
    return {"devices": devices}


def check_device_online(ts_val) -> tuple[bool, float]:
    """Calculates whether the hardware node is actively streaming or powered off."""
    if not ts_val:
        return False, 999999.0
    try:
        if isinstance(ts_val, str):
            clean_ts = ts_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
        elif isinstance(ts_val, datetime):
            dt = ts_val
        else:
            return False, 999999.0

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
        elapsed = (now - dt).total_seconds()
        # ESP32 publishes every 1-2 seconds. If no packet in >15s, sensor is considered OFFLINE / DISCONNECTED
        is_online = 0 <= elapsed <= 15.0
        return is_online, max(0.0, elapsed)
    except Exception:
        return False, 999999.0


@app.get("/devices/{device_id}/status")
def get_device_status(device_id: str, db: Session = Depends(get_db)):
    """Returns the primary real-time state object for the dashboard with online/offline detection."""
    session_record = (
        db.query(SessionModel)
        .filter_by(device_id=device_id)
        .order_by(SessionModel.started_at.desc())
        .first()
    )
    snapshot = None
    telemetry = None
    if session_record:
        snapshot = (
            db.query(StateSnapshotModel)
            .filter_by(session_id=session_record.session_id)
            .order_by(StateSnapshotModel.id.desc())
            .first()
        )
        telemetry = (
            db.query(RawTelemetryModel)
            .filter_by(session_id=session_record.session_id)
            .order_by(RawTelemetryModel.id.desc())
            .first()
        )
    state = (snapshot.payload or {}) if snapshot else {}
    ts = snapshot.timestamp if snapshot else (telemetry.received_at if telemetry else None)
    is_online, elapsed = check_device_online(ts)
    return {
        "device_id": device_id,
        "has_data": telemetry is not None,
        "is_online": is_online,
        "connection_state": "ONLINE_STREAMING" if is_online else "OFFLINE_STANDBY",
        "seconds_since_last_packet": round(elapsed, 1) if ts else None,
        "food_type": session_record.food_type if session_record else None,
        "state": snapshot.spoilage_state if snapshot else "AWAITING_TELEMETRY",
        "spoilage_risk": snapshot.overall_risk if snapshot else None,
        "dominant_risk": state.get("dominant_risk"),
        "risk": {
            "biochemical": state.get("biochemical_risk"),
            "thermal": state.get("thermal_risk"),
            "overall": snapshot.overall_risk if snapshot else None,
            "dominant": state.get("dominant_risk"),
        },
        "remaining_useful_life": {
            "hours": snapshot.rul_hours if snapshot else None,
            "lower": state.get("rul_lower"),
            "upper": state.get("rul_upper"),
        },
        "sensor": None
        if telemetry is None
        else {
            "temperature_c": telemetry.temperature_c,
            "humidity_pct": telemetry.humidity_pct,
            "voc_raw": telemetry.voc_raw,
            "nox_raw": telemetry.nox_raw,
        },
        "voc_velocity": state.get("voc_velocity"),
        "baseline_established": state.get("baseline_established", False),
        "last_updated": ts,
    }


class SubscriptionPayload(BaseModel):
    protocol: Literal["email", "sms"] = "email"
    endpoint: str  # Email address or phone number in E.164 format


@app.post("/notifications/subscribe")
def subscribe_sns_alerts(payload: SubscriptionPayload):
    """Subscribes an email or phone number to the AWS SNS ApplicationSpoilageAlerts topic."""
    import os

    import boto3

    topic_arn = os.getenv("AWS_SNS_TOPIC_ARN")
    if not topic_arn:
        raise HTTPException(status_code=500, detail="AWS SNS Topic not configured.")
    try:
        sns = boto3.client(
            "sns",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
        )
        res = sns.subscribe(
            TopicArn=topic_arn, Protocol=payload.protocol.lower(), Endpoint=payload.endpoint.strip()
        )
        sub_arn = res.get("SubscriptionArn", "pending confirmation")
        return {
            "status": "success",
            "subscription_arn": sub_arn,
            "message": f"Successfully registered {payload.endpoint} with AWS SNS Spoilage Alerts. A confirmation message has been dispatched via AWS.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AWS SNS Subscription error: {str(e)}")


class AlertPublishPayload(BaseModel):
    device_id: str = "Device-01"
    risk_score: float = Field(ge=0, le=1)
    reason: Optional[str] = "Critical Spoilage Alert"


@app.post("/notifications/publish-alert")
def trigger_alert_publish(payload: AlertPublishPayload):
    """Manually or programmatically triggers an immediate AWS SNS Spoilage Alert."""
    import json
    import os

    import boto3

    topic_arn = os.getenv("AWS_SNS_TOPIC_ARN")
    if not topic_arn:
        raise HTTPException(status_code=500, detail="AWS SNS Topic not configured.")
    try:
        sns = boto3.client(
            "sns",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
        )
        risk_pct = round(payload.risk_score * 100, 1)
        msg_body = {
            "alert": "CRITICAL_SPOILAGE_RISK_THRESHOLD_EXCEEDED",
            "device_id": payload.device_id,
            "risk_percentage": f"{risk_pct}%",
            "status": "SPOILAGE_ONSET",
            "message": f"🚨 EMERGENCY: Spoilage risk reached {risk_pct}%! Inspect the stored food and refrigeration conditions.",
            "action_required": "Inspect refrigeration unit and isolate spoiled inventory immediately.",
        }
        res = sns.publish(
            TopicArn=topic_arn,
            Subject=f"🚨 ALERT: project Critical Spoilage Risk ({risk_pct}%) on {payload.device_id}",
            Message=json.dumps(msg_body, indent=2),
        )
        return {"status": "success", "message_id": res.get("MessageId")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to publish SNS alert: {str(e)}")


@app.get("/devices/{device_id}/events")
def get_device_events(device_id: str, db: Session = Depends(get_db)):
    """Returns the immutable evidence ledger of baseline & state transitions."""
    session_record = (
        db.query(SessionModel)
        .filter_by(device_id=device_id)
        .order_by(SessionModel.started_at.desc())
        .first()
    )
    if not session_record:
        return []

    events = (
        db.query(EventModel)
        .filter_by(session_id=session_record.session_id)
        .order_by(EventModel.id.asc())
        .all()
    )
    return [
        {
            "id": e.id,
            "event": e.event,
            "timestamp": e.timestamp,
            "severity": e.severity,
            "evidence": e.evidence,
        }
        for e in events
    ]


@app.get("/devices/{device_id}/telemetry/history")
def get_device_telemetry_history(
    device_id: str, limit: int = Query(60, ge=1, le=1000), db: Session = Depends(get_db)
):
    """Returns the recent sensor curves for time-series charts."""
    session_record = (
        db.query(SessionModel)
        .filter_by(device_id=device_id)
        .order_by(SessionModel.started_at.desc())
        .first()
    )
    if not session_record:
        return []

    readings = (
        db.query(RawTelemetryModel)
        .filter_by(session_id=session_record.session_id)
        .order_by(RawTelemetryModel.id.desc())
        .limit(limit)
        .all()
    )
    readings.reverse()

    return [
        {
            "received_at": r.received_at,
            "temperature_c": r.temperature_c,
            "humidity_pct": r.humidity_pct,
            "voc_raw": r.voc_raw,
            "nox_raw": r.nox_raw,
        }
        for r in readings
    ]


class IngestPayload(BaseModel):
    device_id: str
    food_type: str = "paneer"
    temperature_c: float
    humidity_pct: float
    voc_raw: int
    nox_raw: int = 0
    voc_index: Optional[int] = 0
    nox_index: Optional[int] = 0
    pressure_hpa: Optional[float] = 1013.25
    wifi_rssi: Optional[int] = -40
    sequence_number: Optional[int] = None


@app.post("/telemetry")
async def ingest_telemetry(payload: IngestPayload):
    """Direct ingestion endpoint to run inference and broadcast to live subscribers."""
    result = inference_engine.process_telemetry_payload(payload.model_dump())
    if not result:
        raise HTTPException(status_code=400, detail="Payload validation failed")

    # Broadcast to all live SSE subscribers
    dead_subscribers = []
    for queue in list(subscribers):
        try:
            queue.put_nowait(result)
        except asyncio.QueueFull:
            dead_subscribers.append(queue)
    for q in dead_subscribers:
        subscribers.remove(q)

    return {"status": "processed", "result": result}


@app.get("/stream/devices/{device_id}")
async def stream_device_updates(device_id: str):
    """Server-Sent Events (SSE) stream for instant sub-second frontend updates."""
    queue = asyncio.Queue(maxsize=64)
    subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if data.get("device_id") == device_id:
                    yield f"data: {json.dumps(data)}\n\n"
        finally:
            if queue in subscribers:
                subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Mount frontend build if present
configure_product(app, engine, os.getenv("PRODUCT_MEDIA_ROOT", "data/media/uploads"))

candidates = [
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ),
        "frontend",
        "dist",
    ),
    os.path.join(os.getcwd(), "frontend", "dist"),
    "/opt/backend/frontend/dist",
]
for c in candidates:
    if os.path.exists(c) and os.path.exists(os.path.join(c, "index.html")):
        app.mount("/", StaticFiles(directory=c, html=True), name="frontend")
        break

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8081)
