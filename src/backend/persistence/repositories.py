"""Transactional product operations. Media is scoped to its owning batch."""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.persistence.product_models import (
    BatchModel,
    MediaAssetModel,
    ObservationModel,
    RequestReceiptModel,
)


class NotFound(LookupError):
    pass


class RequestConflict(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


class BatchRepository:
    def __init__(self, db):
        self.db = db

    def get(self, batch_id):
        batch = self.db.get(BatchModel, str(batch_id))
        if batch is None:
            raise NotFound("Batch not found")
        return batch

    def list(self, limit=50, offset=0):
        return self.db.scalars(
            select(BatchModel)
            .order_by(BatchModel.created_at.desc(), BatchModel.batch_id)
            .limit(limit)
            .offset(offset)
        ).all()

    def _save(self, record, operation, key, payload, resource_id):
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        request_key = f"{operation}:{key}" if key else None

        def replay():
            receipt = self.db.get(RequestReceiptModel, request_key)
            if receipt is None:
                return None
            if receipt.fingerprint != fingerprint:
                raise RequestConflict("Idempotency key already used with different input")
            return self.db.get(type(record), receipt.resource_id)

        if request_key:
            previous = replay()
            if previous is not None:
                return previous
            self.db.add(
                RequestReceiptModel(
                    request_key=request_key, fingerprint=fingerprint, resource_id=resource_id
                )
            )
        self.db.add(record)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if request_key:
                previous = replay()
                if previous is not None:
                    return previous
            raise
        self.db.refresh(record)
        return record

    def create(self, payload, key=None):
        batch = BatchModel(
            batch_id=str(uuid4()), created_at=now(), status="active", **payload.model_dump()
        )
        return self._save(batch, "batch", key, payload.model_dump(mode="json"), batch.batch_id)

    def add_media(self, batch_id, stored, key=None):
        self.get(batch_id)
        media = MediaAssetModel(
            media_id=str(uuid4()), batch_id=str(batch_id), created_at=now(), **asdict(stored)
        )
        return self._save(
            media,
            "media",
            key,
            {"batch_id": str(batch_id), "sha256": stored.sha256},
            media.media_id,
        )

    def media(self, batch_id, media_id):
        self.get(batch_id)
        media = self.db.get(MediaAssetModel, str(media_id))
        if media is None or media.batch_id != str(batch_id):
            raise NotFound("Media not found in this batch")
        return media

    def observe(self, batch_id, payload, key=None):
        self.media(batch_id, payload.media_id)
        observation = ObservationModel(
            observation_id=str(uuid4()),
            batch_id=str(batch_id),
            media_id=str(payload.media_id),
            captured_at=payload.captured_at.isoformat(),
            source=payload.source,
            status="captured",
            created_at=now(),
        )
        return self._save(
            observation,
            "observation",
            key,
            {"batch_id": str(batch_id), **payload.model_dump(mode="json")},
            observation.observation_id,
        )

    def history(self, batch_id, limit=50, offset=0):
        self.get(batch_id)
        return self.db.scalars(
            select(ObservationModel)
            .where(ObservationModel.batch_id == str(batch_id))
            .order_by(ObservationModel.created_at.desc(), ObservationModel.observation_id)
            .limit(limit)
            .offset(offset)
        ).all()
