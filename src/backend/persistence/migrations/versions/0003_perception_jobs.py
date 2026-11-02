"""Durable analysis jobs and append-only human reviews."""

import sqlalchemy as sa
from alembic import op

revision = "0003_perception_jobs"
down_revision = "0002_request_receipts"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("product_observations", sa.Column("sample_id", sa.String(60)))
    op.create_table(
        "product_perception_jobs",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column(
            "observation_id",
            sa.String(36),
            sa.ForeignKey("product_observations.observation_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
        sa.Column("lease_until", sa.String(40)),
        sa.Column("result", sa.JSON),
        sa.Column("error_code", sa.String(60)),
        sa.CheckConstraint(
            "status IN ('queued','running','complete','failed')", name="ck_job_status"
        ),
    )
    op.create_table(
        "product_item_reviews",
        sa.Column("review_id", sa.String(36), primary_key=True),
        sa.Column(
            "job_id", sa.String(36), sa.ForeignKey("product_perception_jobs.job_id"), nullable=False
        ),
        sa.Column("object_id", sa.String(30), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("note", sa.String(500), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_product_item_reviews_job_id", "product_item_reviews", ["job_id"])


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; restore a verified backup instead")
