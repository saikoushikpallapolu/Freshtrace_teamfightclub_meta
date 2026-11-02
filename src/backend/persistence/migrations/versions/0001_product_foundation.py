"""Initial additive product schema. Legacy telemetry tables are not changed."""

import sqlalchemy as sa
from alembic import op

revision = "0001_product_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_batches",
        sa.Column("batch_id", sa.String(36), primary_key=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("produce_type", sa.String(120), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("quantity_unit", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_batch_positive_quantity"),
        sa.CheckConstraint("quantity_unit IN ('items','kg')", name="ck_batch_unit"),
        sa.CheckConstraint("status IN ('active','archived')", name="ck_batch_status"),
    )
    op.create_table(
        "product_media",
        sa.Column("media_id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id", sa.String(36), sa.ForeignKey("product_batches.batch_id"), nullable=False
        ),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("original_key", sa.String(200), nullable=False),
        sa.Column("normalized_key", sa.String(200), nullable=False),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("byte_size", sa.Integer, nullable=False),
        sa.Column("width", sa.Integer, nullable=False),
        sa.Column("height", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.UniqueConstraint("media_id", "batch_id", name="uq_media_batch"),
    )
    op.create_table(
        "product_observations",
        sa.Column("observation_id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id", sa.String(36), sa.ForeignKey("product_batches.batch_id"), nullable=False
        ),
        sa.Column("media_id", sa.String(36), nullable=False),
        sa.Column("captured_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id", "batch_id"], ["product_media.media_id", "product_media.batch_id"]
        ),
        sa.CheckConstraint("source IN ('user_capture','fixture')", name="ck_observation_source"),
        sa.CheckConstraint(
            "status IN ('captured','queued','running','complete','failed')",
            name="ck_observation_status",
        ),
    )
    op.create_table(
        "product_sensor_links",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id", sa.String(36), sa.ForeignKey("product_batches.batch_id"), nullable=False
        ),
        sa.Column("device_id", sa.String(120), nullable=False),
        sa.Column("protocol_version", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.create_table(
        "product_model_calls",
        sa.Column("call_id", sa.String(36), primary_key=True),
        sa.Column(
            "observation_id",
            sa.String(36),
            sa.ForeignKey("product_observations.observation_id"),
            nullable=False,
        ),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("prompt_version", sa.String(120), nullable=False),
        sa.Column("response_id", sa.String(200)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("error_code", sa.String(100)),
    )
    for table, column in [
        ("product_media", "batch_id"),
        ("product_observations", "batch_id"),
        ("product_sensor_links", "batch_id"),
        ("product_model_calls", "observation_id"),
    ]:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; restore a verified backup instead")
