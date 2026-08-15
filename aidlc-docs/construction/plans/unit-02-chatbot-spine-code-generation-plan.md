# Code Generation Plan — Unit 2: Chatbot Spine

**Stories**: US-2.1, US-2.2, US-2.3
**Dependencies**: Unit 1 (`provider/`, `events/`)
**Code location**: `backend/src/chat/`, `backend/src/db/`, `backend/src/api/`, `backend/alembic/`, `docker-compose.yml`

## Scope Note: a temporary `NoOpEventQueue`

`ChatService` must call `InstrumentedProvider`, which needs a real `EventQueue` to publish to — but `InProcessEventQueue` is explicitly Unit 3's deliverable, not built yet. Rather than pull Unit 3's scope forward or bypass `InstrumentedProvider` (which would contradict the already-approved functional design), this plan adds a minimal `NoOpEventQueue` in `events/` — implements the interface, `publish()` does nothing. Log events are silently dropped until Unit 3 lands; this is safe because BR5 (Unit 1) already established that publish failures/no-ops must never affect the chat response. Unit 3 wires in the real implementation; this unit's API layer wiring changes one line, nothing else.

## Steps

### Step 1: Project Structure Additions
- [x] `backend/pyproject.toml` — add `sqlalchemy[asyncio]`, `asyncpg`, `alembic` dependencies
- [x] `backend/.env.example` — documents `DATABASE_URL`, `GEMINI_API_KEY`
- [x] `docker-compose.yml` (repo root) — `postgres` service (`pgvector/pgvector:pg16`, named volume, `pg_isready` healthcheck)
- [x] `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`

### Step 2: Business Logic Generation
- [x] `backend/src/chat/truncation.py` — `ContextTruncationStrategy` (ABC), `WindowTruncationStrategy`
- [x] `backend/src/chat/service.py` — `ChatService` (full flow per `business-logic-model.md`)
- [x] `backend/src/events/noop_event_queue.py` — temporary stand-in (see scope note above)

**Story mapping**: `truncation.py` + `service.py` → US-2.1, US-2.3. `service.py`'s streaming path → US-2.2.

### Step 3: Business Logic Unit Testing
- [x] `backend/tests/chat/doubles.py` — `FakeConversationRepository`, `FakeMessageRepository`, `FakeUserRepository` (in-memory, implementing the `db/` interfaces)
- [x] `backend/tests/chat/test_truncation.py` — window boundary behavior
- [x] `backend/tests/chat/test_service.py` — the real coverage target: ownership checks reject wrong-user access (BR5, BR7); success/cancellation/error paths persist messages differently (BR4); cancellation reaches the correct task via the registry (BR6); user message persists even when the assistant call fails (BR3). Uses the fakes above plus Unit 1's `FakeLLMProvider`/`FakeEventQueue` test doubles (reused via import, not duplicated)

### Step 4: Repository Layer Generation
- [x] `backend/src/db/orm.py` — SQLAlchemy `DeclarativeBase` tables: `UserORM`, `SessionORM`, `ConversationORM`, `MessageORM`
- [x] `backend/src/db/engine.py` — async engine + `async_sessionmaker`, reads `DATABASE_URL`
- [x] `backend/src/db/sqlalchemy_conversation_repository.py`, `sqlalchemy_message_repository.py`, `sqlalchemy_user_repository.py` — concrete implementations, session-per-operation (per NFR design)
- [x] `backend/alembic/versions/0001_initial_schema.py` — creates `users`, `sessions`, `conversations`, `messages`

### Step 5: Repository Layer Testing
- [x] `backend/tests/db/test_sqlalchemy_repositories.py` — integration tests against a **real Postgres** (via `docker compose up -d postgres` + `alembic upgrade head`, documented in README). Covers the actual SQL round-trip that the fakes in Step 3 can't: constraint enforcement, the user-scoping `WHERE` clause in `ConversationRepository.get`, migration correctness.

### Step 6: API Layer Generation
- [x] `backend/src/api/deps.py` — FastAPI dependencies: DB session, current-user (temporary: always resolves to the seeded demo user via `UserRepository.get_or_create_seed_user()`, per Unit 2's Q4), wired `ChatService` instance
- [x] `backend/src/api/chat_router.py` — `POST /conversations`, `POST /conversations/{id}/messages` (SSE), `POST /conversations/{id}/cancel`, `GET /conversations`, `POST /conversations/{id}/resume`
- [x] `backend/src/main.py` — FastAPI app entrypoint, wires `GeminiProvider` → `InstrumentedProvider` → `NoOpEventQueue`, includes `chat_router`

### Step 7: API Layer Testing
- [x] `backend/tests/api/test_chat_router.py` — FastAPI `TestClient`, dependency-overridden with the Step 3 fakes (no real DB, no real Gemini) — verifies routing, request/response shapes, and that cancel/resume reject wrong-user access at the HTTP layer too

### Step 8: Documentation
- [x] `aidlc-docs/construction/unit-02-chatbot-spine/code/summary.md`
- [x] Update root `README.md` — Docker Compose + Alembic setup instructions, updated Status section

## Explicitly Skipped for This Unit
- Frontend Components Generation — no UI (Unit 5)
- Deployment Artifacts beyond `postgres` + `api` in Compose — full deployment (worker, frontend, k8s) is Unit 6

## Notes from Generation
- `FakeUserRepository` (mentioned in Step 3's original plan) wasn't needed — `ChatService` doesn't depend on `UserRepository` at all (only `api/deps.py`'s `get_current_user` does), so API-layer tests override the current-user dependency directly with a fixed `User` instead.
- `docker-compose.yml` ended up with both `postgres` and `api` services, not just `postgres` — matches what `nfr-design/logical-components.md` already described (the `api` container's healthcheck dependency on `postgres`), so this was implementing the approved NFR design, not scope creep.
- Verification: 33/33 tests passing including 5 real-Postgres integration tests; full Docker Compose stack (`postgres` + `api`) built and exercised end-to-end via curl, not just pytest.
