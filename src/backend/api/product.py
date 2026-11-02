"""Local product API. No AWS worker, sensor stream or model calls on startup."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from backend.api.endpoints.batches import router
from backend.persistence.runtime import initialize_schema, make_engine
from backend.storage.media import LocalMediaStore


def configure_product(app, engine, media_root):
    app.state.product_sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.product_media = LocalMediaStore(media_root)
    app.include_router(router)


def create_app(database_url=None, media_root=None):
    # Intentionally does not load .env or infer cloud credentials in local mode.
    url = database_url or os.getenv("PRODUCT_DATABASE_URL", "sqlite:///product_local.db")
    root = media_root or os.getenv("PRODUCT_MEDIA_ROOT", "data/media/uploads")
    engine = make_engine(url)

    @asynccontextmanager
    async def lifespan(app):
        initialize_schema(engine)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Produce Inspection API", version="0.3.0", lifespan=lifespan)
    configure_product(app, engine, root)

    @app.get("/health")
    def health():
        return {"status": "healthy", "phase": "data_foundation"}

    return app
