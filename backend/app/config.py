"""Application settings.

All environment access funnels through this module. Nothing else in the
codebase reads os.environ directly — if a value isn't here, it doesn't
exist as far as the app is concerned.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Repo root: backend/app/config.py -> backend/app -> backend -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # ---- App ----
    APP_ENV: Literal["development", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # ---- HTTP server ----
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ---- CORS ----
    # CSV in env, list in code. NoDecode bypasses pydantic-settings' default
    # JSON-decoding of complex types so our `field_validator` below runs on
    # the raw string. No "*" allowed in production (enforced in main.py).
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_csv(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ---- Face detection (mediapipe) ----
    DETECTION_MIN_CONFIDENCE: float = Field(default=0.5, ge=0.0, le=1.0)

    # ---- ROI persistence ----
    ROI_SAMPLE_EVERY_N_FRAMES: int = Field(default=5, ge=1)

    # ---- Database (consumed Day 2) ----
    # Kept as `str` deliberately: pydantic's PostgresDsn rejects the
    # "+asyncpg" driver suffix that SQLAlchemy needs.
    DATABASE_URL: str = (
        "postgresql+asyncpg://face_app:change_me_in_real_env"
        "@localhost:5432/face_detections"
    )
    # Echo SQL to stdout. Off in prod; flip on for migration / query debugging.
    DB_ECHO: bool = False

    # ---- Rate limiting (consumed Day 3) ----
    RATE_LIMIT_PER_MINUTE: int = Field(default=30, ge=1)

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # Ignore VITE_* and other non-backend keys in the shared root .env.
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor.

    Use as a FastAPI dependency: `Depends(get_settings)`. The cache makes
    `Settings()` construction (which reads the env file) a one-shot cost.
    Tests can override with `app.dependency_overrides[get_settings] = ...`.
    """
    return Settings()