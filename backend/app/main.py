"""FastAPI application factory.

`create_app()` builds a fresh, fully-configured FastAPI instance. Tests use
the factory to construct isolated apps with overridden dependencies; the
module-level `app` below exists so `uvicorn app.main:app` works in production.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.router import api_router
from app.config import Settings, get_settings
from app.services.detector import FaceDetector
from app.services.roi_writer import roi_writer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks.

    Constructs long-lived resources (FaceDetector + ROI write-behind
    worker) on startup and tears them down in reverse order on shutdown.
    Each resource gets its own try/finally so a later startup failure
    can't leak earlier ones.
    """
    settings = get_settings()
    logger.info(
        f"starting face-detect-stream backend "
        f"(env={settings.APP_ENV}, log_level={settings.LOG_LEVEL})"
    )

    detector = FaceDetector.from_settings(settings)
    app.state.detector = detector
    logger.info("face detector initialized")

    try:
        await roi_writer.start()
        logger.info("roi_writer started")
        try:
            yield
        finally:
            await roi_writer.stop()
            logger.info("roi_writer stopped")
    finally:
        detector.close()
        logger.info("face detector closed; backend shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a FastAPI application.

    Tests should call `create_app(test_settings)` to get an isolated instance.
    Production uses the module-level `app` below.
    """
    settings = settings or get_settings()

    app = FastAPI(
        title="face-detect-stream",
        description=(
            "Real-time face detection over WebSocket. "
            "Webcam frames in, annotated frames + ROI bounding boxes out."
        ),
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    _configure_cors(app, settings)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


def _configure_cors(app: FastAPI, settings: Settings) -> None:
    """Attach CORS middleware. Hard-refuses the wildcard origin in production."""
    origins = settings.BACKEND_CORS_ORIGINS

    if settings.APP_ENV == "production" and "*" in origins:
        raise RuntimeError(
            "BACKEND_CORS_ORIGINS contains '*' in production — refusing to start."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],   # narrow on purpose; widen if needed
        allow_headers=["*"],
    )


# Uvicorn entrypoint: `uvicorn app.main:app`
app = create_app()