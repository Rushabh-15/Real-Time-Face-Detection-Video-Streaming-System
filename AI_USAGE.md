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