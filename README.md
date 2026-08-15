# Ollive — LLM Inference Logging & Ingestion System

Built incrementally via AI-DLC. See `aidlc-docs/` for the full requirements, design, and decision trail behind every choice below.

## Getting Started (Backend)

Requires [uv](https://docs.astral.sh/uv/), Python 3.12, and Docker (for Postgres).

**Via `make`** (see `make help` for the full list):

```bash
cp .env.example .env        # fill in GEMINI_API_KEY
make up                     # start Postgres only
make install                # uv sync
make migrate                # alembic upgrade head
make test                   # run the test suite (real-Postgres tests skipped)
make test-db                # also run the real-Postgres integration tests
make up-all                 # build + start the full stack (Postgres + API)
make run                    # or run the API locally, outside Docker, with --reload
```

**Equivalent commands, without `make`:**

```bash
docker compose up -d postgres
cd backend && uv sync
DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive uv run alembic upgrade head
uv run pytest -v
RUN_DB_TESTS=1 DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive uv run pytest tests/db/test_sqlalchemy_repositories.py -v

# Full stack:
GEMINI_API_KEY=your-key-here docker compose up -d --build
curl http://localhost:8000/health

# Or the API locally, outside Docker:
DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive GEMINI_API_KEY=your-key-here uv run uvicorn main:app --reload --app-dir src
```

Environment variables — root `.env` (for `docker compose`, see `.env.example`) and `backend/.env` (for running `uv` commands locally, see `backend/.env.example`); neither is committed:

```
DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive
GEMINI_API_KEY=your-key-here
```

## Status

This README grows as each unit of work lands.

- **Unit 1 — Provider Abstraction & Auto-Instrumentation** (done): `backend/src/provider/` — the `LLMProvider` interface, `GeminiProvider` adapter, and the `InstrumentedProvider` auto-instrumentation decorator. See `aidlc-docs/construction/unit-01-provider-abstraction/`.
- **Unit 2 — Chatbot Spine** (done): `backend/src/chat/` (conversation lifecycle, context truncation, streaming orchestration), `backend/src/db/` (SQLAlchemy repositories + Alembic migrations), `backend/src/api/` (chat endpoints, manually verifiable — no frontend yet). `docker-compose.yml` and the `postgres`/`api` services started here. See `aidlc-docs/construction/unit-02-chatbot-spine/`.

More sections (architecture overview, schema design, tradeoffs, frontend setup, full deployment) will be added as later units land — the final polished README is a deliverable of its own, assembled once the system is complete.
