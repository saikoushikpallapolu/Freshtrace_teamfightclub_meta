import os

from dotenv import load_dotenv
from sqlalchemy import URL
from sqlalchemy.orm import sessionmaker

from backend.persistence.runtime import initialize_schema, make_engine

load_dotenv()


def get_database_url() -> str | URL:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    db_host = os.getenv("AWS_RDS_ENDPOINT")
    db_user = os.getenv("AWS_RDS_USER", "backendadmin")
    db_pass = os.getenv("AWS_RDS_PASSWORD")
    db_name = os.getenv("AWS_RDS_DBNAME", "backend")
    db_port = os.getenv("AWS_RDS_PORT", "5432")

    if bool(db_host) != bool(db_pass):
        raise ValueError("Incomplete RDS configuration: set both endpoint and password")

    if db_host and db_pass:
        return URL.create(
            "postgresql+psycopg2",
            username=db_user,
            password=db_pass,
            host=db_host,
            port=int(db_port),
            database=db_name,
        )

    # Local default only when no database has been configured; never an offline fallback.
    return "sqlite:///backend_local.db"


DATABASE_URL = get_database_url()

engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Preserve legacy tables and apply ordered product migrations."""
    initialize_schema(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
