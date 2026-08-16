# Unit Test Execution

## Backend (`backend/`)

### 1. Fast tests (no external dependencies, DB tests mocked/skipped)
```bash
cd backend && uv run pytest -v
```
- **Expected**: 57 passed, 8 skipped (the skipped ones are the real-Postgres tests below, gated by `RUN_DB_TESTS`)

### 2. Real-Postgres tests
Requires a running Postgres (via `docker compose up -d postgres` or the full stack):
```bash
RUN_DB_TESTS=1 DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive \
  uv run pytest tests/db/test_sqlalchemy_repositories.py -v
```
- **Expected**: 8 passed

**Coverage by area**: `tests/provider/` (Unit 1 — LLM provider abstraction, auto-instrumentation), `tests/chat/` (Unit 2 — conversation lifecycle, streaming), `tests/db/` (Units 2-5 — SQLAlchemy repositories, real + fake), `tests/events/` (Unit 3 — in-process event queue), `tests/ingestion/` (Unit 3 — validate/extract/redact/persist pipeline), `tests/analytics/` (Unit 4 — dashboard metrics/bucketing), `tests/auth/` (Unit 5 — session auth), `tests/api/` (cross-cutting router tests).

## Frontend (`frontend/`)

### 1. Run the test suite
```bash
cd frontend && npm run test
```
- **Expected**: 4 test files, 9 tests passed — `AuthContext` (login/logout/session-restore), `LoginPage` (demo-user picker), `ChatWindow` (streaming/cancel), `CancelButton`

### 2. Type-check (part of the production build, worth running standalone during development)
```bash
npx tsc -b --noEmit
```
- **Expected**: no errors

## Actually run in this session (2026-08-16, against `main` @ `f5823ff`)
- Backend: **57 passed, 8 skipped** (fast) → **8 passed** (real-Postgres, run separately) = **65/65 total**
- Frontend: **9/9 passed**, `tsc -b --noEmit` clean
- **Combined: 74/74 automated unit tests passing**, 0 failures

## If tests fail
1. Re-run with `-v`/verbose output to see the specific assertion
2. Check whether it's a real-Postgres test that needs `RUN_DB_TESTS=1` and a running `postgres` container — most "failures" in a fresh environment are actually 8 tests being skipped, not failing, if that flag/DB isn't set up
3. Fix the code, re-run until green — do not skip or delete a failing test to make the suite pass
