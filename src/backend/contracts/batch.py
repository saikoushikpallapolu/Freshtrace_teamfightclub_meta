"""Phase-one product boundaries. No model output implies food safety."""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class BatchCreate(Contract):
    label: Label
    produce_type: Label = "tomato"
    quantity: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    quantity_unit: Literal["items", "kg"]

    def model_post_init(self, context):
        if self.quantity_unit == "items" and not self.quantity.is_integer():
            raise ValueError("Item quantities must be whole numbers")


class BatchRead(BatchCreate):
    batch_id: UUID
    created_at: datetime
    status: Literal["active", "archived"]


class ObservationStatus(str, Enum):
    CAPTURED = "captured"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class ObservationCreate(Contract):
    media_id: UUID
    captured_at: datetime
    source: Literal["user_capture", "fixture"] = "user_capture"

    @field_validator("captured_at")
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("captured_at must include a timezone")
        return value.astimezone(timezone.utc)


class ObservationRead(ObservationCreate):
    observation_id: UUID
    batch_id: UUID
    status: ObservationStatus
    created_at: datetime


class MediaRead(Contract):
    media_id: UUID
    batch_id: UUID
    sha256: str
    content_type: Literal["image/jpeg", "image/png"]
    byte_size: int
    width: int
    height: int
    created_at: datetime


class SensorSessionLink(Contract):
    """Reserved contract; device reservation and phase execution ship in phase four."""

    session_id: UUID
    batch_id: UUID
    device_id: Label
    protocol_version: Label
    status: Literal["requested", "active", "valid", "invalid", "aborted"]


class ModelCallReceipt(Contract):
    call_id: UUID
    observation_id: UUID
    model: Label
    prompt_version: Label
    response_id: str | None = Field(default=None, max_length=200)
    status: Literal["succeeded", "failed"]
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    latency_ms: int = Field(ge=0)
    error_code: str | None = Field(default=None, max_length=100)
