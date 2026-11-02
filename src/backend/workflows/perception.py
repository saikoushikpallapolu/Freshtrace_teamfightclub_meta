"""Durable, bounded local prototype analysis jobs. No automatic paid retries."""

import threading
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from backend.contracts.inspection import PROMPT_VERSION
from backend.persistence.product_models import (
    MediaAssetModel,
    ModelCallModel,
    ObservationModel,
    PerceptionJobModel,
)
from backend.persistence.repositories import now


def job_directory(store, job):
    return store.resolve(f"jobs/{job.job_id}/attempt-{job.attempt}")


def enqueue(db, observation):
    existing = db.scalar(
        select(PerceptionJobModel).where(
            PerceptionJobModel.observation_id == observation.observation_id
        )
    )
    if existing:
        return existing
    job = PerceptionJobModel(
        job_id=str(uuid4()),
        observation_id=observation.observation_id,
        status="queued",
        attempt=1,
        created_at=now(),
        updated_at=now(),
    )
    db.add(job)
    observation.status = "queued"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.scalar(
            select(PerceptionJobModel).where(
                PerceptionJobModel.observation_id == observation.observation_id
            )
        )
    db.refresh(job)
    return job


class PerceptionWorker:
    def __init__(self, sessions, store, provider_factory, pipeline=None):
        self.sessions, self.store = sessions, store
        self.provider_factory, self.pipeline = provider_factory, pipeline
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, name="perception-worker", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

    def run(self):
        while not self.stop_event.is_set():
            try:
                if self.run_once():
                    continue
            except Exception:
                # Do not log SDK exception text/headers; durable state is the UI boundary.
                pass
            self.stop_event.wait(1)

    def run_once(self):
        with self.sessions() as db:
            expired = db.scalars(
                select(PerceptionJobModel).where(
                    PerceptionJobModel.status == "running", PerceptionJobModel.lease_until < now()
                )
            ).all()
            for job in expired:
                job.status, job.error_code, job.updated_at = "failed", "worker_interrupted", now()
                db.get(ObservationModel, job.observation_id).status = "failed"
            db.commit()
            candidate = db.scalar(
                select(PerceptionJobModel)
                .where(PerceptionJobModel.status == "queued")
                .order_by(PerceptionJobModel.created_at)
                .limit(1)
            )
            if candidate is None:
                return False
            job_id, attempt = candidate.job_id, candidate.attempt
            lease = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
            claimed = db.execute(
                update(PerceptionJobModel)
                .where(
                    PerceptionJobModel.job_id == job_id,
                    PerceptionJobModel.status == "queued",
                    PerceptionJobModel.attempt == attempt,
                )
                .values(status="running", updated_at=now(), lease_until=lease)
            )
            if not claimed.rowcount:
                db.rollback()
                return False
            observation = db.get(ObservationModel, candidate.observation_id)
            observation.status = "running"
            media = db.get(MediaAssetModel, observation.media_id)
            source = self.store.resolve(media.normalized_key)
            observation_id = observation.observation_id
            directory = job_directory(self.store, candidate)
            db.commit()

        def receipt(response, latency_ms):
            usage = getattr(response, "usage", None)
            with self.sessions() as db:
                db.add(
                    ModelCallModel(
                        call_id=str(uuid4()),
                        observation_id=observation_id,
                        model=response.model,
                        prompt_version=PROMPT_VERSION,
                        response_id=response.id,
                        status="succeeded" if response.status == "completed" else "failed",
                        input_tokens=getattr(usage, "input_tokens", None),
                        output_tokens=getattr(usage, "output_tokens", None),
                        latency_ms=latency_ms,
                        error_code=None
                        if response.status == "completed"
                        else "incomplete_response",
                    )
                )
                db.commit()

        result = None
        code = None
        try:
            from backend.meta.inspection import inspect_photo

            with self.provider_factory() as client:
                result = (self.pipeline or inspect_photo)(client, source, directory, receipt)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            allowed_codes = {
                "no_tomatoes_detected",
                "too_many_objects_use_smaller_tray",
                "incomplete_visual_response",
                "visual_object_ids_mismatch",
            }
            code = getattr(exc, "code", None)
            if code not in allowed_codes:
                code = {
                    401: "provider_authentication_failed",
                    403: "provider_access_denied",
                    429: "provider_rate_limited",
                }.get(status, "analysis_failed")
        with self.sessions() as db:
            updated = db.execute(
                update(PerceptionJobModel)
                .where(
                    PerceptionJobModel.job_id == job_id,
                    PerceptionJobModel.status == "running",
                    PerceptionJobModel.attempt == attempt,
                )
                .values(
                    status="failed" if code else "complete",
                    result=result,
                    error_code=code,
                    lease_until=None,
                    updated_at=now(),
                )
            )
            if updated.rowcount:
                db.get(ObservationModel, observation_id).status = "failed" if code else "complete"
            db.commit()
        return True
