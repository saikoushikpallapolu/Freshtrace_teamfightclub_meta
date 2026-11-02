"""Local product API with an opt-in perception worker and no AWS clients."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from backend.api.endpoints.batches import router
from backend.api.endpoints.inspection import router as inspection_router
from backend.api.endpoints.samples import router as sample_router
from backend.persistence.runtime import initialize_schema, make_engine
from backend.storage.media import LocalMediaStore


def configure_product(app, engine, media_root):
    app.state.product_sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.product_media = LocalMediaStore(media_root)
    app.include_router(router)
    app.state.analysis_enabled = False
    app.include_router(inspection_router)
    app.include_router(sample_router)


def create_app(database_url=None, media_root=None, provider_factory=None):
    # Intentionally does not load .env or infer cloud credentials in local mode.
    url = database_url or os.getenv("PRODUCT_DATABASE_URL", "sqlite:///product_local.db")
    root = media_root or os.getenv("PRODUCT_MEDIA_ROOT", "data/media/uploads")
    engine = make_engine(url)
    key = os.getenv("MODEL_API_KEY", "").strip()
    if provider_factory is None and key:
        from backend.meta.client import make_client

        def provider_factory():
            return make_client(key)

    @asynccontextmanager
    async def lifespan(app):
        initialize_schema(engine)
        worker = None
        if provider_factory:
            from backend.workflows.perception import PerceptionWorker

            worker = PerceptionWorker(
                app.state.product_sessions, app.state.product_media, provider_factory
            )
            worker.start()
        try:
            yield
        finally:
            if worker:
                worker.stop()
            engine.dispose()

    app = FastAPI(title="Produce Inspection API", version="0.4.0", lifespan=lifespan)
    configure_product(app, engine, root)
    app.state.analysis_enabled = provider_factory is not None

    @app.get("/health")
    def health():
        return {"status": "healthy", "phase": "visual_inspection"}

    return app
