"""Additive product tables; legacy telemetry models remain untouched."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
)

from backend.persistence.models import Base


class BatchModel(Base):
    __tablename__ = "product_batches"
    batch_id = Column(String(36), primary_key=True)
    label = Column(String(120), nullable=False)
    produce_type = Column(String(120), nullable=False)
    quantity = Column(Float, nullable=False)
    quantity_unit = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(String(40), nullable=False)
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_batch_positive_quantity"),
        CheckConstraint("quantity_unit IN ('items','kg')", name="ck_batch_unit"),
        CheckConstraint("status IN ('active','archived')", name="ck_batch_status"),
    )


class MediaAssetModel(Base):
    __tablename__ = "product_media"
    media_id = Column(String(36), primary_key=True)
    batch_id = Column(
        String(36), ForeignKey("product_batches.batch_id"), nullable=False, index=True
    )
    sha256 = Column(String(64), nullable=False)
    original_key = Column(String(200), nullable=False)
    normalized_key = Column(String(200), nullable=False)
    content_type = Column(String(30), nullable=False)
    byte_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    created_at = Column(String(40), nullable=False)
    __table_args__ = (UniqueConstraint("media_id", "batch_id", name="uq_media_batch"),)


class ObservationModel(Base):
    __tablename__ = "product_observations"
    observation_id = Column(String(36), primary_key=True)
    batch_id = Column(
        String(36), ForeignKey("product_batches.batch_id"), nullable=False, index=True
    )
    media_id = Column(String(36), nullable=False)
    captured_at = Column(String(40), nullable=False)
    created_at = Column(String(40), nullable=False)
    source = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["media_id", "batch_id"], ["product_media.media_id", "product_media.batch_id"]
        ),
        CheckConstraint("source IN ('user_capture','fixture')", name="ck_observation_source"),
        CheckConstraint(
            "status IN ('captured','queued','running','complete','failed')",
            name="ck_observation_status",
        ),
    )


class SensorSessionLinkModel(Base):
    __tablename__ = "product_sensor_links"
    session_id = Column(String(36), primary_key=True)
    batch_id = Column(
        String(36), ForeignKey("product_batches.batch_id"), nullable=False, index=True
    )
    device_id = Column(String(120), nullable=False)
    protocol_version = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False)


class ModelCallModel(Base):
    __tablename__ = "product_model_calls"
    call_id = Column(String(36), primary_key=True)
    observation_id = Column(
        String(36), ForeignKey("product_observations.observation_id"), nullable=False, index=True
    )
    model = Column(String(120), nullable=False)
    prompt_version = Column(String(120), nullable=False)
    response_id = Column(String(200))
    status = Column(String(20), nullable=False)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    latency_ms = Column(Integer, nullable=False)
    error_code = Column(String(100))


class RequestReceiptModel(Base):
    __tablename__ = "product_requests"
    request_key = Column(String(100), primary_key=True)
    fingerprint = Column(String(64), nullable=False)
    resource_id = Column(String(36), nullable=False)
