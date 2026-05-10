# face-detect-stream

Real-time face detection over a WebSocket video stream. Webcam frames go in, annotated frames + ROI bounding boxes come back, ROIs are persisted to Postgres for time-range queries.

> **Status:** active take-home assignment implementation (Day 1 complete, Day 2 mostly complete, Day 3 planned).

---

## Quick start

### Prerequisites

- Docker 24+ and Docker Compose v2
- A modern browser with webcam access (Chrome, Firefox, Safari)

```bash
git clone <repo-url> face-detect-stream
cd face-detect-stream
cp .env.example .env
docker compose up --build
```

Then open <http://localhost:5173> and grant webcam permission.

### Verify the backend independently

- API docs (Swagger UI): <http://localhost:8000/api/v1/docs>
- Health check: <http://localhost:8000/api/v1/health>

### Tear down

```bash
docker compose down -v
```

---

## What it does

1. The React frontend captures webcam frames, JPEG-encodes them in a `<canvas>`, and ships them over a WebSocket.
2. The FastAPI backend decodes each frame with Pillow, runs MediaPipe face detection (single face), draws the axis-aligned bounding box with `PIL.ImageDraw`, and re-encodes to JPEG.
3. The annotated frame + ROI JSON come back in the same WebSocket envelope — frame and box cannot desync.
4. ROIs are sampled and persisted to PostgreSQL for time-range queries via `GET /api/v1/roi`.

> **No `opencv-python`.** All image processing is handled with Pillow + numpy + MediaPipe.

---

## Architecture

> *Architecture diagram planned for Day 3 (`docs/architecture.png`).*

```text
[Browser webcam] --JPEG/WS--> [FastAPI WS handler]
                                     |
                               [pipeline service]
                                /     |      \
                       [detector] [drawing]  [repo → Postgres]
                                     |
[Browser <img>] <--JPEG+ROI/WS-- [pipeline service]

[Browser ROI viewer] --HTTP GET--> [/api/v1/roi] --> [Postgres]
```

---

## API contract

OpenAPI docs are auto-generated at `/api/v1/docs`.

- `GET  /api/v1/health`
  - Liveness/health endpoint

- `WS /api/v1/ws/face-stream`
  - Bidirectional WebSocket endpoint
  - Client sends JPEG frames
  - Server returns `{frame, roi}` envelope

- `GET /api/v1/roi`
  - Query persisted ROI history
  - Supports:
    - `session_id`
    - `since`
    - `limit`

---

## Project structure

```text
backend/    FastAPI app, MediaPipe detector, SQLAlchemy + Alembic
frontend/   React 18 + Vite + TypeScript
docs/       Architecture diagram, screenshots
```

---

## Design decisions

### Single bidirectional WebSocket

A single WebSocket keeps frame transport and ROI metadata synchronized without requiring polling or multiple transport layers.

### PostgreSQL for ROI persistence

ROI data is structured, timestamped, and query-oriented. PostgreSQL provides clean indexing and range-query support.

### MediaPipe over dlib / face_recognition

MediaPipe provides CPU-friendly inference with significantly easier Docker setup and fewer native dependency issues.

### Sampled persistence

Persisting every frame is unnecessary and expensive. Sampling persistence frequency keeps storage practical while remaining configurable.

### Pillow instead of OpenCV

The project intentionally avoids `opencv-python` to reduce image-processing overhead and native dependency complexity.

---

## Testing

```bash
cd backend
pytest
```

> Current tests focus primarily on the detection pipeline and backend functionality.

---

## Current implementation status

### Completed

- End-to-end realtime webcam → WebSocket → detection → annotated frame pipeline
- FastAPI backend with MediaPipe face detection
- React/Vite frontend webcam streaming
- ROI extraction and persistence pipeline
- PostgreSQL integration
- Dockerized local development setup
- Health endpoint + Swagger docs
- Initial SQLAlchemy + Alembic setup
- Unit tests for detection pipeline (19 tests)

### Remaining Day 2 items

| Item | Status | Notes |
|---|---|---|
| Frontend `session_id` handshake | Remaining | Small integration task (~20 min) |
| Client-side overlay sanity check | Optional | Visual polish task |
| Global/custom exception handlers | Partially complete | WebSocket handler implemented; REST/global handler pending |
| JSON logging polish | Deferred | Existing Loguru setup already structured |

### Planned Day 3 work

- Full integration test suite
- Alembic migration hardening
- Production-oriented exception handling
- Architecture diagram
- Additional documentation/screenshots
- Performance cleanup and release polish

The repository reflects incremental development with commits preserved throughout the implementation process.

---

## Roadmap

- [x] Day 1: realtime detection loop, backend/frontend integration, Docker setup, initial tests
- [~] Day 2: persistence layer, `/roi` API, logging, database integration
- [ ] Day 3: integration tests, hardening, release polish

---

## AI usage

This project was built with AI-assisted pair programming. Development decisions, prompts, and AI-assisted changes are documented in [AI_USAGE.md](AI_USAGE.md).

---

## License

MIT.