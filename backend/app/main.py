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


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks. Stateful services (DB engine, mediapipe model)
    will be wired in here as we add them."""
    settings = get_settings()
    logger.info(
        f"starting face-detect-stream backend "
        f"(env={settings.APP_ENV}, log_level={settings.LOG_LEVEL})"
    )
    yield
    logger.info("shutting down face-detect-stream backend")


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