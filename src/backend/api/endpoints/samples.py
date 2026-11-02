"""Allowlisted local public samples. No arbitrary URL fetching or paid inference."""

import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from backend.api.endpoints.batches import repository
from backend.contracts.batch import ObservationRead
from backend.persistence.product_models import ObservationModel
from backend.persistence.repositories import now

router = APIRouter(prefix="/api/samples", tags=["public test samples"])
DIRECTORY = Path(__file__).resolve().parents[4] / "data/fixtures/tomato_images"


def samples():
    path = DIRECTORY / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []


def sample(sample_id):
    record = next((item for item in samples() if item["sample_id"] == sample_id), None)
    if record is None:
        raise HTTPException(404, "Sample not found")
    return record


@router.get("")
def list_samples():
    return [
        {k: v for k, v in item.items() if k not in {"filename", "download_url"}}
        for item in samples()
    ]


@router.get("/{sample_id}/image")
def sample_image(sample_id: str):
    record = sample(sample_id)
    return FileResponse(DIRECTORY / record["filename"], media_type="image/jpeg")


class ImportSample(BaseModel):
    model_config = ConfigDict(extra="forbid")
    batch_id: UUID


@router.post("/{sample_id}/import", response_model=ObservationRead, status_code=201)
def import_sample(
    sample_id: str, payload: ImportSample, request: Request, repo=Depends(repository)
):
    record = sample(sample_id)
    batch = repo.get(payload.batch_id)
    # One reusable sample observation per batch; retrying import never duplicates it.
    key = str(uuid5(NAMESPACE_URL, f"{batch.batch_id}:{sample_id}:observation"))
    previous = repo.db.get(ObservationModel, key)
    if previous:
        return previous
    data = (DIRECTORY / record["filename"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise HTTPException(409, "Sample checksum does not match provenance manifest")
    stored = request.app.state.product_media.store(data, "image/jpeg")
    media_key = uuid5(NAMESPACE_URL, f"{batch.batch_id}:{sample_id}:media")
    media = repo.add_media(batch.batch_id, stored, media_key)
    timestamp = now()
    obj = ObservationModel(
        observation_id=key,
        batch_id=batch.batch_id,
        media_id=media.media_id,
        captured_at=timestamp,
        created_at=timestamp,
        source="fixture",
        sample_id=sample_id,
        status="captured",
    )
    # Timestamp here is import time, not the date the photographer captured it.
    return repo._save(obj, "sample", key, {"sample_id": sample_id, "batch_id": batch.batch_id}, key)
