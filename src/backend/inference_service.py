import json
import os
import time
from copy import deepcopy

import boto3
from dotenv import load_dotenv

from backend.biochemical.engine import BiochemicalEngine
from backend.detection.onset import OnsetDetector
from backend.evidence.events import EvidenceEngine
from backend.fusion.risk import RiskFusion
from backend.ingestion.processor import IngestionProcessor
from backend.persistence.db import SessionLocal, init_db
from backend.persistence.models import (
    EventModel,
    RawTelemetryModel,
    SessionModel,
    StateSnapshotModel,
)
from backend.processing.signal_processor import SignalProcessor
from backend.rul.estimator import RULEstimator
from backend.thermal.engine import ThermalEngine

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")
QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL")
SNS_TOPIC_ARN = os.getenv("AWS_SNS_TOPIC_ARN")


class InferenceEngineService:
    def __init__(self):
        init_db()
        self.ingestor = IngestionProcessor(raw_storage_dir="data/raw")
        self.signal_engine = SignalProcessor(baseline_window=5)
        self.bio_engine = BiochemicalEngine()
        self.thermal_engine = ThermalEngine()
        self.onset_detector = OnsetDetector()
        self.rul_estimator = RULEstimator()
        self.risk_fusion = RiskFusion()
        self.evidence_engine = EvidenceEngine()

        self.sqs = (
            boto3.client(
                "sqs",
                region_name=REGION,
            )
            if QUEUE_URL
            else None
        )
        self.sns = (
            boto3.client(
                "sns",
                region_name=REGION,
            )
            if SNS_TOPIC_ARN
            else None
        )

        self.last_known_state = {}
        self.last_alert_timestamps = {}
        print(
            f"[InferenceService] Ready. SQS configured: {bool(self.sqs)}; SNS configured: {bool(self.sns)}"
        )

    def process_telemetry_payload(self, payload: dict) -> dict:
        """Runs the entire 7-phase Application pipeline on a raw sensor payload."""
        device = str(payload.get("device_id", ""))
        previous_sequence = self.ingestor.sequence_trackers.get(device)
        try:
            raw = self.ingestor.process(payload)
        except Exception:
            self._restore_sequence(device, previous_sequence)
            raise
        if not raw:
            return None

        session = raw.session_id
        stores = (
            self.signal_engine.sessions,
            self.thermal_engine.sessions,
            self.onset_detector.sessions,
            self.evidence_engine.last_onset_states,
        )
        checkpoints = [deepcopy(store.get(session)) for store in stores]
        had_baseline = session in self.evidence_engine.baseline_tracked
        try:
            return self._process_reading(raw)
        except Exception:
            # Failed persistence must not consume a sequence or advance the baseline/trends.
            self._restore_sequence(device, previous_sequence)
            for store, checkpoint in zip(stores, checkpoints):
                if checkpoint is None:
                    store.pop(session, None)
                else:
                    store[session] = checkpoint
            if not had_baseline:
                self.evidence_engine.baseline_tracked.discard(session)
            raise

    def _restore_sequence(self, device, previous):
        if previous is None:
            self.ingestor.sequence_trackers.pop(device, None)
        else:
            self.ingestor.sequence_trackers[device] = previous

    def _process_reading(self, raw):
        # 1. Signal Processing
        processed = self.signal_engine.process(raw)

        # 2. Risk Engines
        bio = self.bio_engine.calculate_risk(processed)
        thermal = self.thermal_engine.calculate_risk(processed)
        fusion = self.risk_fusion.fuse(bio["biochemical_risk"], thermal["thermal_risk"])

        # 3. State Machine & RUL
        onset = self.onset_detector.detect(processed, bio["biochemical_risk"])
        rul = self.rul_estimator.estimate(bio["biochemical_risk"], bio["degradation_velocity"])

        # 4. Evidence Events
        events = self.evidence_engine.evaluate(
            raw.session_id, raw.received_at, processed, bio, onset
        )

        result = {
            "device_id": raw.device_id,
            "session_id": raw.session_id,
            "timestamp": raw.received_at,
            "food_type": raw.food_type,
            "state": onset["current_state"],
            "overall_risk": fusion["overall_risk"],
            "dominant_risk": fusion["dominant_risk"],
            "biochemical_risk": bio["biochemical_risk"],
            "thermal_risk": thermal["thermal_risk"],
            "rul_hours": rul["remaining_useful_life_hours"],
            "rul_lower": rul["lower_bound_hours"],
            "rul_upper": rul["upper_bound_hours"],
            "temperature_c": raw.temperature_c,
            "humidity_pct": raw.humidity_pct,
            "voc_raw": raw.voc_raw,
            "nox_raw": raw.nox_raw,
            "voc_velocity": processed.voc_velocity,
            "baseline_established": processed.baseline_established,
            "events": events,
        }

        # 5. Persist to RDS Database (Hot State & Evidence Ledger)
        self._persist_to_db(raw, result, events)

        # 6. Publish threshold alerts to SNS if Risk >= 80% or SPOILAGE_ONSET detected
        if fusion["overall_risk"] >= 0.80 or onset["current_state"] == "SPOILAGE_ONSET":
            self._publish_sns_alert(result)

        self.last_known_state[raw.device_id] = result
        return result

    def _persist_to_db(self, raw, state, events):
        db = SessionLocal()
        try:
            # Session check
            existing_session = db.query(SessionModel).filter_by(session_id=raw.session_id).first()
            if not existing_session:
                new_session = SessionModel(
                    session_id=raw.session_id,
                    device_id=raw.device_id,
                    food_type=raw.food_type,
                    status="ACTIVE",
                    started_at=raw.received_at,
                )
                db.add(new_session)

            # Raw Telemetry
            telemetry_row = RawTelemetryModel(
                session_id=raw.session_id,
                received_at=raw.received_at,
                temperature_c=raw.temperature_c,
                humidity_pct=raw.humidity_pct,
                voc_raw=raw.voc_raw,
                nox_raw=raw.nox_raw,
            )
            db.add(telemetry_row)

            # State Snapshot
            snapshot_row = StateSnapshotModel(
                session_id=raw.session_id,
                timestamp=raw.received_at,
                spoilage_state=state["state"],
                overall_risk=state["overall_risk"],
                rul_hours=state["rul_hours"],
                payload=state,
            )
            db.add(snapshot_row)

            # Evidence Ledger
            for ev in events:
                event_row = EventModel(
                    session_id=ev["session_id"],
                    event=ev["event"],
                    timestamp=ev["timestamp"],
                    severity=ev["severity"],
                    evidence=ev["evidence"],
                )
                db.add(event_row)

            db.commit()
        except Exception as e:
            db.rollback()
            raise RuntimeError("Failed to persist sensor evidence") from e
        finally:
            db.close()

    def _publish_sns_alert(self, state):
        if not self.sns or not SNS_TOPIC_ARN:
            return
        device_id = state.get("device_id", "default")
        now_ts = time.time()
        last_alert = self.last_alert_timestamps.get(device_id, 0)
        # Cooldown: 120 seconds between alerts per device to prevent flooding
        if now_ts - last_alert < 120:
            return
        try:
            risk_pct = round(state["overall_risk"] * 100, 1)
            message = {
                "alert": "AWS_SPOILAGE_RISK_THRESHOLD_EXCEEDED",
                "device_id": state["device_id"],
                "food_type": state["food_type"],
                "timestamp": state["timestamp"],
                "overall_risk_percent": f"{risk_pct}%",
                "dominant_risk": state.get("dominant_risk", "BIOCHEMICAL_DOMINANT"),
                "state": state.get("state", "SPOILAGE_ONSET"),
                "remaining_useful_life_hours": f"{state.get('rul_hours', 0.0)}h",
                "sensor_telemetry": {
                    "voc_raw_ticks": state.get("voc_raw"),
                    "temperature_c": state.get("temperature_c"),
                    "humidity_pct": state.get("humidity_pct"),
                },
                "recommended_action": "Inspect the stored food and refrigeration conditions.",
            }
            self.sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"🚨 ALERT: project High Spoilage Risk ({risk_pct}%) on {state['device_id']}",
                Message=json.dumps(message, indent=2),
            )
            self.last_alert_timestamps[device_id] = now_ts
            print(
                f"[SNS ALERT SENT] Spoilage risk ({risk_pct}%) published to AWS SNS: {SNS_TOPIC_ARN}"
            )
        except Exception as e:
            print(f"[SNS ERROR] Failed to publish alert: {e}")

    def run_stream_listener(self, poll_interval_seconds: int = 1):
        """Continuously polls AWS SQS for sensor messages delivered by IoT Core."""
        if not self.sqs or not QUEUE_URL:
            print("[ERROR] SQS Queue URL not configured.")
            return

        print(f"[*] Application Stream Consumer listening on: {QUEUE_URL}")
        while True:
            try:
                response = self.sqs.receive_message(
                    QueueUrl=QUEUE_URL,
                    MaxNumberOfMessages=5,
                    WaitTimeSeconds=10,
                    VisibilityTimeout=30,
                )
                messages = response.get("Messages", [])
                for msg in messages:
                    body = json.loads(msg["Body"])
                    receipt_handle = msg["ReceiptHandle"]

                    # Process the telemetry payload
                    result = self.process_telemetry_payload(body)
                    if result:
                        print(
                            f"[{result['device_id']}] Processed: State={result['state']} | Risk={result['overall_risk']:.3f} ({result['dominant_risk']}) | RUL={result['rul_hours']}h"
                        )

                    # Delete message from SQS upon successful processing
                    self.sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)

                if not messages:
                    time.sleep(poll_interval_seconds)

            except Exception as e:
                print(f"[STREAM ERROR] {e}")
                time.sleep(2)


if __name__ == "__main__":
    service = InferenceEngineService()
    service.run_stream_listener()
