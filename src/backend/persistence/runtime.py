"""Database construction with explicit configuration and no silent cloud fallback."""

from sqlalchemy import create_engine, event

from backend.persistence.migrate import upgrade_database
from backend.persistence.models import Base

LEGACY_TABLES = ("sessions", "raw_telemetry", "events", "state_snapshots")


def make_engine(url):
    engine = create_engine(
        url, connect_args={"check_same_thread": False} if str(url).startswith("sqlite") else {}
    )
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


def initialize_schema(engine):
    # Existing installations already have these tables; never drop or rebuild them.
    Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in LEGACY_TABLES])
    upgrade_database(engine)
