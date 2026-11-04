"""Retain full sensor inference results for cross-process status queries."""

import sqlalchemy as sa
from alembic import op

revision = "0004_sensor_snapshot"
down_revision = "0003_perception_jobs"
branch_labels = None
depends_on = None


def upgrade():
    # New installations bootstrap legacy tables from the current models first.
    columns = sa.inspect(op.get_bind()).get_columns("state_snapshots")
    if "payload" not in {column["name"] for column in columns}:
        op.add_column("state_snapshots", sa.Column("payload", sa.JSON(), nullable=True))


def downgrade():
    raise RuntimeError("Sensor evidence migrations are forward-only.")
