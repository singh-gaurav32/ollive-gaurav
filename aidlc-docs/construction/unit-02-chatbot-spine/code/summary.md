# Unit 2 Code Generation Summary — Chatbot Spine

## What was built

**Business logic** (`backend/src/chat/`): `truncation.py` (`ContextTruncationStrategy` + `WindowTruncationStrategy`), `service.py` (`ChatService`, `ConversationNotFoundError`, `ConversationDetail`).

**Shared package additions**: `backend/src/events/noop_event_queue.py` (temporary `EventQueue` stand-in, see below).

**Persistence** (`backend/src/db/`): `orm.py` (SQLAlchemy tables), `engine.py` (async engine + session factory), `sqlalchemy_conversation_repository.py`, `sqlalchemy_message_repository.py`, `sqlalchemy_user_repository.py`. `backend/alembic/` with the initial migration (`users`, `sessions`, `conversations`, `messages`).

**API layer** (`backend/src/api/`): `deps.py` (dependency wiring), `chat_router.py` (5 endpoints). `backend/src/main.py` (FastAPI app entrypoint).

**Infrastructure**: `docker-compose.yml` (repo root, `postgres` + `api` services), `backend/Dockerfile`, `backend/.env.example`.

## Design decisions made during implementation, beyond the approved functional/NFR design

- **`send_message` runs the actual provider call in a background `asyncio.Task`, bridged to the caller via a queue**, rather than being a plain async generator that does the work inline. This was necessary, not stylistic: `cancel_conversation` is invoked from a *separate* HTTP request than the one running `send_message`, and only a real `Task` object can be `.cancel()`-ed from outside. A plain async generator has no such handle. This is the concrete mechanism behind BR6, worked out at the code level since the functional design specified the requirement but not this particular asyncio pattern.
- **`get_conversation` added to `ChatService`** as a small new public method — the ownership pre-check the API layer needs before starting an SSE stream (an async generator's body, including its own internal ownership check, doesn't execute until first iterated, so a 404 can't be raised from inside one once streaming has already started). A direct, minor extension of the already-approved ownership-check pattern (BR5), not new business logic.
- **`ConversationDetail`** (conversation + full message history) added as `resume_conversation`'s actual return type, matching what `business-logic-model.md` specified in prose but hadn't been given a concrete shape.

## Verified end-to-end, not just by unit tests

- `docker compose up -d postgres` → healthy
- `alembic upgrade head` → applied cleanly against real Postgres
- `RUN_DB_TESTS=1 pytest tests/db/test_sqlalchemy_repositories.py` → 5/5 passing against that real database (caught and fixed a genuine bug in the process: the async engine's connection pool breaking across pytest-asyncio's per-test event loops — fixed by creating a fresh engine per test rather than reusing the module-level singleton)
- `docker compose up -d --build api` → image builds, container runs migrations on startup, `/health` returns 200
- `curl -X POST /conversations` and `curl /conversations` against the live container → real rows created and returned from real Postgres

## Tests

33 total, all passing: `tests/chat/` (truncation + `ChatService`, including a deterministic event-synchronized test of the cancellation registry mechanism itself, not just a scripted cancellation), `tests/db/` (pydantic model tests + 5 real-Postgres repository tests), `tests/api/` (FastAPI `TestClient` with dependency overrides, no real DB or Gemini).

## Traceability

- US-2.1 (multi-turn conversation) → `chat/service.py`, `db/` repositories
- US-2.2 (streaming) → `chat/service.py`'s task+queue bridge, `api/chat_router.py`'s SSE endpoint
- US-2.3 (long conversations stay usable) → `chat/truncation.py`
