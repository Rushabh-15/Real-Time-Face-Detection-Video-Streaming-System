# face-detect-stream

Real-time face detection over a WebSocket video stream. Webcam frames go in, annotated frames + ROI bounding boxes come back, ROIs are persisted to Postgres for time-range queries.

> **Status:** in development (3-day take-home build). See [Roadmap](#roadmap).

---

## Quick start

**Prerequisites**

- Docker 24+ and Docker Compose v2
- A modern browser with webcam access (Chrome, Firefox, Safari)

```bash
git clone <repo-url> face-detect-stream
cd face-detect-stream
cp .env.example .env
docker compose up --build
```

Then open <http://localhost:5173> and grant webcam permission.

**Verify the backend independently**

- API docs (Swagger UI): <http://localhost:8000/api/v1/docs>
- Health check: <http://localhost:8000/api/v1/health>

**Tear down**

```bash
docker compose down -v
```

---

## What it does

1. The React frontend captures webcam frames, JPEG-encodes them in a `<canvas>`, and ships them over a WebSocket.
2. The FastAPI backend decodes each frame with Pillow, runs MediaPipe face detection (single face), draws the axis-aligned bounding box with `PIL.ImageDraw`, re-encodes to JPEG.
3. The annotated frame + ROI JSON come back in the same WebSocket envelope — frame and box can't desync.
4. ROIs are sampled and persisted to PostgreSQL for time-range queries via `GET /api/v1/roi`.

> **No `opencv-python`.** All image work is Pillow + numpy + MediaPipe.

---

## Architecture

> *Diagram coming Day 2 → `docs/architecture.png`.*

```
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

> *Filled in Day 2 — OpenAPI is auto-generated at `/api/v1/docs`.*

- `GET  /api/v1/health` — liveness
- `WS   /api/v1/ws/face-stream` — bidirectional: send JPEG bytes, receive `{frame, roi}` envelope
- `GET  /api/v1/roi?session_id=<uuid>&since=<iso8601>&limit=<int>` — paginated ROI history

---

## Project structure

```
backend/    FastAPI app, MediaPipe detector, SQLAlchemy + Alembic
frontend/   React 18 + Vite + TypeScript
docs/       Architecture diagram, screenshots
```

---

## Design decisions

> *Expanded Day 2.* Each decision will document the alternatives considered.

- **One bidirectional WebSocket** instead of MJPEG + REST polling — frame/ROI sync is free.
- **PostgreSQL** for ROI persistence — structured, time-indexed, range-queried; relational fits cleanly.
- **MediaPipe** instead of dlib / face_recognition — CPU-only, fast, no native build pain in Docker.
- **Sampled persistence** (1-of-N frames, configurable) — 30 rows/sec is wasteful; sampling is a knob, not a hardcode.

---

## Testing

```bash
cd backend
pytest
```

> *Test layout finalized Day 3.*

---

## Roadmap

- [x] Day 1: detection loop end-to-end (no DB) — backend, frontend, dockerized backend, 19 unit tests
- [ ] Day 2: persistence, `/roi`, structured logging, architecture diagram
- [ ] Day 3: full test suite, hardening, release

---

## AI usage

This project was built with AI pair-programming. See [AI_USAGE.md](AI_USAGE.md) for the per-change log.

---

## License

MIT.