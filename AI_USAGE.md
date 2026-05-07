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