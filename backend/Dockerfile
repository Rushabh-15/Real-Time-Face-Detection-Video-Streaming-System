# syntax=docker/dockerfile:1.6

# ============================================================================
# Stage 1: install dependencies into an isolated prefix
# ============================================================================
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Copy the project metadata + source needed to build the local package.
COPY pyproject.toml ./
COPY app/ ./app/

# BuildKit cache mount keeps the ~150MB mediapipe wheel cached across builds
# even when source code changes invalidate this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --prefix=/install .

# ============================================================================
# Stage 2: lean runtime image
# ============================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.11/site-packages"

# MediaPipe needs libGL and glib at runtime; without these, `import mediapipe`
# fails with shared-library errors that aren't covered by the wheel.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Non-root system user; no shell, no home dir.
RUN groupadd --system app && \
    useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Copy the installed Python prefix from the builder, then app source.
COPY --from=builder /install /install
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app app/ ./app/

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]