"""Saved job state, evidence artifacts and append-only item reviews."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, update

from backend.api.endpoints.batches import repository
from backend.contracts.inspection import ReviewCreate
from backend.persistence.product_models import (
    ItemReviewModel,
    ModelCallModel,
    ObservationModel,
    PerceptionJobModel,
)
from backend.persistence.repositories import NotFound, now
from backend.workflows.perception import enqueue, job_directory

router = APIRouter(prefix="/api", tags=["inspection"])


def observation(repo, batch_id, observation_id):
    repo.get(batch_id)
    obj = repo.db.get(ObservationModel, str(observation_id))
    if obj is None or obj.batch_id != str(batch_id):
        raise NotFound("Observation not found in this batch")
    return obj


def get_job(repo, observation_id):
    return repo.db.scalar(
        select(PerceptionJobModel).where(PerceptionJobModel.observation_id == str(observation_id))
    )


def serialize(job):
    if job is None:
        return None
    return {
        "job_id": job.job_id,
        "observation_id": job.observation_id,
        "status": job.status,
        "attempt": job.attempt,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "result": job.result,
        "error_code": job.error_code,
    }


@router.get("/capabilities")
def capabilities(request: Request):
    return {
        "live_analysis": request.app.state.analysis_enabled,
        "models": ["sam-3.1", "muse-spark-1.3"],
        "sensor_sessions": False,
    }


@router.post("/batches/{batch_id}/observations/{observation_id}/analysis", status_code=202)
def start_analysis(
    batch_id: UUID, observation_id: UUID, request: Request, repo=Depends(repository)
):
    obj = observation(repo, batch_id, observation_id)
    existing = get_job(repo, observation_id)
    if existing:
        return serialize(existing)
    if not request.app.state.analysis_enabled:
        raise HTTPException(
            503, "Live analysis needs a server-side MODEL_API_KEY and a restarted API"
        )
    return serialize(enqueue(repo.db, obj))


@router.post("/batches/{batch_id}/observations/{observation_id}/analysis/retry", status_code=202)
def retry_analysis(
    batch_id: UUID, observation_id: UUID, request: Request, repo=Depends(repository)
):
    observation(repo, batch_id, observation_id)
    if not request.app.state.analysis_enabled:
        raise HTTPException(503, "Live analysis is not configured")
    job = get_job(repo, observation_id)
    if job is None or job.status != "failed":
        raise HTTPException(409, "Only a failed analysis can be retried")
    previous_attempt = job.attempt
    result = repo.db.execute(
        update(PerceptionJobModel)
        .where(
            PerceptionJobModel.job_id == job.job_id,
            PerceptionJobModel.status == "failed",
            PerceptionJobModel.attempt == previous_attempt,
        )
        .values(
            status="queued",
            error_code=None,
            result=None,
            lease_until=None,
            attempt=previous_attempt + 1,
            updated_at=now(),
        )
    )
    if not result.rowcount:
        repo.db.rollback()
        raise HTTPException(409, "Analysis state changed; refresh before retrying")
    repo.db.get(ObservationModel, str(observation_id)).status = "queued"
    repo.db.commit()
    repo.db.refresh(job)
    return serialize(job)


@router.get("/batches/{batch_id}/observations/{observation_id}/analysis")
def analysis(batch_id: UUID, observation_id: UUID, repo=Depends(repository)):
    observation(repo, batch_id, observation_id)
    job = get_job(repo, observation_id)
    reviews = (
        []
        if job is None
        else repo.db.scalars(
            select(ItemReviewModel)
            .where(ItemReviewModel.job_id == job.job_id)
            .order_by(ItemReviewModel.created_at)
        ).all()
    )
    calls = repo.db.scalars(
        select(ModelCallModel).where(ModelCallModel.observation_id == str(observation_id))
    ).all()
    return {
        "job": serialize(job),
        "reviews": [
            {
                "object_id": r.object_id,
                "category": r.category,
                "note": r.note,
                "created_at": r.created_at,
                "review_id": r.review_id,
            }
            for r in reviews
        ],
        "calls": [
            {
                "model": c.model,
                "prompt_version": c.prompt_version,
                "response_id": c.response_id,
                "status": c.status,
                "input_tokens": c.input_tokens,
                "output_tokens": c.output_tokens,
                "latency_ms": c.latency_ms,
            }
            for c in calls
        ],
    }


@router.get("/batches/{batch_id}/observations/{observation_id}/artifacts/{filename}")
def artifact(
    batch_id: UUID, observation_id: UUID, filename: str, request: Request, repo=Depends(repository)
):
    observation(repo, batch_id, observation_id)
    job = get_job(repo, observation_id)
    if job is None or job.status != "complete":
        raise HTTPException(404, "Completed analysis not available")
    allowed = {"analysis.jpg", "inspection_overlay.jpg", "hit_map.png"}
    for obj in job.result["objects"]:
        allowed.update([obj["crop_file"], obj["mask_file"]])
    if filename not in allowed:
        raise HTTPException(404, "Artifact not found")
    path = job_directory(request.app.state.product_media, job) / filename
    if not path.is_file():
        raise HTTPException(404, "Artifact file unavailable")
    return FileResponse(
        path, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
    )


@router.post("/batches/{batch_id}/observations/{observation_id}/reviews", status_code=201)
def review(batch_id: UUID, observation_id: UUID, payload: ReviewCreate, repo=Depends(repository)):
    observation(repo, batch_id, observation_id)
    job = get_job(repo, observation_id)
    if (
        job is None
        or job.status != "complete"
        or payload.object_id not in {o["object_id"] for o in job.result["objects"]}
    ):
        raise HTTPException(409, "Review must reference an object in a completed analysis")
    record = ItemReviewModel(
        review_id=str(uuid4()), job_id=job.job_id, created_at=now(), **payload.model_dump()
    )
    repo.db.add(record)
    repo.db.commit()
    return {
        "review_id": record.review_id,
        "category": record.category,
        "object_id": record.object_id,
        "note": record.note,
        "created_at": record.created_at,
    }
