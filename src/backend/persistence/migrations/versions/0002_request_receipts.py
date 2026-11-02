"""Durable idempotency receipts for capture mutations."""

import sqlalchemy as sa
from alembic import op

revision = "0002_request_receipts"
down_revision = "0001_product_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_requests",
        sa.Column("request_key", sa.String(100), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
    )


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; restore a verified backup instead")
