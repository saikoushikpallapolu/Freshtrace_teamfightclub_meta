"""Batch/evidence routes shared by the standalone and legacy API entry points."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse

from backend.contracts.batch import (
    BatchCreate,
    BatchRead,
    MediaRead,
    ObservationCreate,
    ObservationRead,
)
from backend.persistence.repositories import BatchRepository, NotFound, RequestConflict
from backend.storage.media import MAX_BYTES, InvalidImage

router = APIRouter(prefix="/api/batches", tags=["batches"])


def repository(request: Request):
    with request.app.state.product_sessions() as db:
        try:
            yield BatchRepository(db)
        except NotFound as exc:
            raise HTTPException(404, str(exc)) from exc
        except RequestConflict as exc:
            raise HTTPException(409, str(exc)) from exc


@router.post("", response_model=BatchRead, status_code=201)
def create_batch(
    payload: BatchCreate,
    idempotency_key: UUID | None = Header(default=None),
    repo=Depends(repository),
):
    return repo.create(payload, idempotency_key)


@router.get("", response_model=list[BatchRead])
def list_batches(
    limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), repo=Depends(repository)
):
    return repo.list(limit, offset)


@router.get("/{batch_id}", response_model=BatchRead)
def get_batch(batch_id: UUID, repo=Depends(repository)):
    return repo.get(batch_id)


@router.post("/{batch_id}/media", response_model=MediaRead, status_code=201)
async def upload_media(
    batch_id: UUID,
    request: Request,
    idempotency_key: UUID | None = Header(default=None),
    repo=Depends(repository),
):
    repo.get(batch_id)
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(415, "Send raw JPEG or PNG bytes with the matching Content-Type")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "Image exceeds 10 MiB")
        data.extend(chunk)
    try:
        stored = request.app.state.product_media.store(bytes(data), content_type)
    except InvalidImage as exc:
        raise HTTPException(422, str(exc)) from exc
    return repo.add_media(batch_id, stored, idempotency_key)


@router.get("/{batch_id}/media/{media_id}", response_model=MediaRead)
def get_media(batch_id: UUID, media_id: UUID, repo=Depends(repository)):
    return repo.media(batch_id, media_id)


@router.get("/{batch_id}/media/{media_id}/content")
def media_content(
    batch_id: UUID,
    media_id: UUID,
    request: Request,
    variant: str = Query("normalized", pattern="^(original|normalized)$"),
    repo=Depends(repository),
):
    media = repo.media(batch_id, media_id)
    key = media.original_key if variant == "original" else media.normalized_key
    path = request.app.state.product_media.resolve(key)
    if not path.is_file():
        raise HTTPException(404, "Media file unavailable")
    content_type = media.content_type if variant == "original" else "image/jpeg"
    return FileResponse(
        path,
        media_type=content_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/{batch_id}/observations", response_model=ObservationRead, status_code=201)
def create_observation(
    batch_id: UUID,
    payload: ObservationCreate,
    idempotency_key: UUID | None = Header(default=None),
    repo=Depends(repository),
):
    return repo.observe(batch_id, payload, idempotency_key)


@router.get("/{batch_id}/observations", response_model=list[ObservationRead])
def observations(
    batch_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo=Depends(repository),
):
    return repo.history(batch_id, limit, offset)
