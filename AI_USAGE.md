# AI Usage Log

This project uses AI pair-programming. This document records, per commit, what was AI-generated vs. human-written or edited.

## Tool

**Claude (Anthropic)** — drafts code and docs, recommends design decisions, suggests commit messages.

## Policy

- AI drafts; human reviews every line before commit.
- When a decision has >1 reasonable answer, the AI recommends with reasoning, the human decides.
- All Git operations are human actions. No AI commits.
- No real secrets shared with the AI; `.env` is filled by hand from `.env.example`.

## Used for

Boilerplate (`.gitignore`, `.env.example`, README, Dockerfiles), service-layer drafting from a stated interface, test scaffolding, design-decision sounding board, conventional-commit messages.

## Not used for

Final architecture calls, runtime debugging against the live system, review of AI output, anything involving real credentials.

## Log

Each entry corresponds to one commit. Chronological (oldest first). Append a new entry after every commit that involved AI assistance.

Format: `- **YYYY-MM-DD** — <AI-COLLAB-LOG line>`

- **2026-05-07** — `.gitignore` AI-drafted (Python + Node + Docker + secrets coverage). Human reviewed and accepted without edits.
- **2026-05-07** — `.env.example` AI-drafted (variable names, defaults, inline rationale comments). Human reviewed and committed without edits.
- **2026-05-07** — `README.md` AI-drafted (structure, quick-start, ASCII architecture, design-decisions stubs, roadmap). Human reviewed and committed without edits.
- **2026-05-07** — `backend/pyproject.toml` AI-drafted (PEP 621 metadata, conservative version pins for runtime/dev/test groups, ruff/black/pytest/mypy config including the mediapipe mypy escape and the integration pytest marker). Human reviewed and committed without edits.
- **2026-05-07** — `backend/app/__init__.py (empty package marker) and backend/app/config.py` AI-drafted (Pydantic v2 BaseSettings with CORS CSV validator, bounded confidence/sample-rate fields, lru_cache'd get_settings(), and a deliberate str typing for DATABASE_URL to accommodate +asyncpg). Human reviewed and committed without edits.
- **2026-05-07** — `backend/app/main.py` AI-drafted (factory pattern with create_app(), lifespan context for future stateful services, CORS middleware sourced from settings with hard-refusal of * in production, narrow allow_methods allowlist, module-level app for uvicorn). Human reviewed, ran install + boot smoke test, committed without edits.
- **2026-05-08** — `backend/app/api/__init__.py` and `backend/app/api/v1/__init__.py` (empty package markers) plus `backend/app/api/v1/router.py` (aggregate `APIRouter` with placeholder include comments) AI-drafted; `backend/app/main.py` edited to mount the v1 router under `settings.API_V1_PREFIX`. Human reviewed, ran boot smoke test (verified empty `/api/v1/openapi.json` and 404 on `/api/v1/health`), committed.
- **2026-05-08** — `backend/app/api/v1/health.py` AI-drafted (liveness endpoint with `Literal["ok"]` status, inline `HealthResponse` schema, `response_model` for OpenAPI typing, `tags=["health"]`, summary/description for Swagger) and `backend/app/api/v1/router.py` edited to include it. Human reviewed, verified `curl /api/v1/health` returns 200 with expected payload, committed.
- **2026-05-08** — `backend/app/services/detector.py` rewritten to use `mp.tasks.vision.FaceDetector` (legacy `mp.solutions.face_detection` is broken upstream in mediapipe 0.10.31+ across platforms — confirmed via open GitHub issues 6200/6204/6241/6261). BlazeFace short-range model (~230KB, Apache 2.0) downloaded from Google's official model bucket and committed to `backend/app/services/models/`. `DETECTION_MODEL_SELECTION` removed from `Settings` and `.env.example` (Tasks API picks model by file, making the integer flag dead). Original solutions-API draft was AI-generated based on stale info; migration AI-drafted after web search confirmed the upstream regression. Human reproduced the failure, ran sanity import on the rewrite, committed.
- **2026-05-08** — `backend/app/services/drawing.py` AI-drafted: three pure functions (`decode_jpeg`, `encode_jpeg`, `draw_bbox`), all RGB-uint8 numpy ↔ JPEG bytes via Pillow. Shape validation on encode/draw paths, non-mutating `draw_bbox` that handles `bbox=None`, configurable color/thickness/quality with module-level defaults, `BBox` imported under `TYPE_CHECKING` to keep the module mediapipe-free at runtime. Rubric-direct: `PIL.ImageDraw.rectangle` is the drawing primitive. Human reviewed, ran codec roundtrip + draw sanity check, committed.
- **2026-05-08** — `backend/pyproject.toml` patched: added `pythonpath = ["."]` to `[tool.pytest.ini_options]` so pytest's collection sees `app/` as importable from the rootdir. Bug introduced by AI in original `pyproject.toml` — missed a default-pytest pitfall where prepend import mode puts the test dir on `sys.path` first, hiding the source package. Human reproduced via `pytest`, AI diagnosed and proposed the fix, human verified all 8 drawing tests pass, committed.
- **2026-05-08** — `backend/tests/unit/test_detector.py` AI-drafted: 7 tests covering the rubric-critical paths (face detected → returns `BBox`, bbox within image bounds, positive dimensions, confidence in [0, 1], blank image → returns `None`) and validation guards (rejects grayscale and RGBA arrays). Module-scoped `detector` fixture amortizes the ~1.5s TFLite warmup. `face_image` fixture uses `pytest.skip` on missing JPEG so unrelated tests still run. Face JPEG (`backend/tests/fixtures/face.jpg`) provided by the human (their own photo, resized to ≤640px via Pillow `thumbnail`) — AI explicitly did not pick the image to keep license provenance the candidate's call. Human reviewed, ran `pytest tests/unit/ -v` (15 passed), committed.
- **2026-05-08** — `backend/app/schemas/__init__.py` (empty package marker) and `backend/app/schemas/ws.py` AI-drafted: `ROI` Pydantic model with field-level bounds (`ge=0` on x/y, `gt=0` on w/h, confidence in [0, 1]) as a safety net behind detector validation; `FaceFrameMessage` envelope with base64-encoded JPEG + `ROI | None`. Outbound-only — inbound stays raw binary to avoid a 33% base64 tax on the upstream path. No `session_id` / `timestamp` on the wire message (client already knows both). Human reviewed, ran the verify snippet (round-trip OK, validation rejects out-of-range confidence), committed.