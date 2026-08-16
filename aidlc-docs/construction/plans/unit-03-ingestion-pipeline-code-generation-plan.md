# Code Generation Plan — Unit 3: Ingestion Pipeline Hardening

**Stories**: US-3.1, US-3.2, US-3.3
**Dependencies**: Unit 1 (`provider/`, `events/`), Unit 2 (real chat call generates a real event end-to-end)
**Code location**: `backend/src/events/`, `backend/src/ingestion/`, `backend/src/db/`, `backend/alembic/`

## Scope Note: `query_window` is implemented here, not deferred to Unit 4

Per `unit-of-work.md`, `LogRepository` (`insert` *and* `query_window`) is Unit 3's to implement, since it's the natural owner of the `logs` table — Unit 4 only *reads* the result. `query_window` uses Postgres's `percentile_cont` for p50/p95 latency, time-bucketed via a floor-division expression on the epoch timestamp.

## Steps

### Step 1: Project Structure
- [x] `backend/alembic/versions/0002_logs_and_failed_log_events.py` — creates `logs`, `failed_log_events` (no indexes beyond primary key, per NFR Requirements)

### Step 2: Business Logic Generation
- [x] `backend/src/events/in_process_event_queue.py` — `InProcessEventQueue` (bounded, `put_nowait`)
- [x] `backend/src/ingestion/payload_validator.py`, `metadata_extractor.py` — pass-through stages (BR1)
- [x] `backend/src/ingestion/pii_redactor.py` — hardcoded regex + constructor denylist (BR2/BR3)
- [x] `backend/src/ingestion/log_persister.py` — `LogEvent` → `LogRecord` mapping + insert
- [x] `backend/src/ingestion/worker.py` — `IngestionWorker` (stage sequencing, per-event failure isolation, PII-safe dead-lettering)

**Story mapping**: `in_process_event_queue.py` + `worker.py` → US-3.1. `pii_redactor.py` → US-3.2. `worker.py` (broker swap-readiness, already satisfied by the `EventQueue` interface from Unit 1) → US-3.3.

### Step 3: Business Logic Unit Testing
- [x] `backend/tests/events/test_in_process_event_queue.py` — publish/consume round-trip, `QueueFull` on a full bounded queue (BR6)
- [x] `backend/tests/ingestion/doubles.py` — `FakeLogRepository`, `FakeFailedLogEventRepository`, `_FailingPersister`
- [x] `backend/tests/ingestion/test_pii_redactor.py` — each hardcoded pattern, the constructor denylist, non-PII fields untouched
- [x] `backend/tests/ingestion/test_worker.py` — success path (redacted + persisted), failure path (dead-lettered, **and asserts `FailedLogEvent` has no preview field at all** — the structural test of BR-PII), one event's failure doesn't affect the next, dead-letter-write-itself-fails falls back to logging without crashing

### Step 4: Repository Layer Generation
- [x] `backend/src/db/models.py` — add `FailedLogEvent`
- [x] `backend/src/db/orm.py` — add `LogORM`, `FailedLogEventORM`
- [x] `backend/src/db/failed_log_event_repository.py` — new interface
- [x] `backend/src/db/sqlalchemy_log_repository.py` — `insert` + `query_window` (percentile_cont aggregation)
- [x] `backend/src/db/sqlalchemy_failed_log_event_repository.py`

### Step 5: Repository Layer Testing
- [x] Extend `backend/tests/db/test_sqlalchemy_repositories.py` — real-Postgres tests for `LogRepository.insert`/`query_window` (including verifying the aggregation actually computes correct counts/percentiles, not just that it doesn't error) and `FailedLogEventRepository.insert`

### Step 6: Wiring
- [x] `backend/src/api/deps.py` — `get_event_queue()` (cached singleton `InProcessEventQueue`, shared between the producer and consumer sides), `get_chat_service()` updated to use it instead of `NoOpEventQueue`, new `get_ingestion_worker()`
- [x] `backend/src/main.py` — FastAPI `lifespan`: starts the worker task, attaches the crash-visibility `done_callback`, cancels cleanly on shutdown
- [x] Delete `backend/src/events/noop_event_queue.py` and its test — no longer referenced anywhere once the swap is wired in

### Step 7: Documentation
- [x] `aidlc-docs/construction/unit-03-ingestion-pipeline/code/summary.md`
- [x] Update root `README.md` — new migration step, updated Status section

## Explicitly Skipped for This Unit
- Frontend Components — no UI (Unit 5)
- Deployment Artifacts — Unit 6

## Verification Plan (not just unit tests) — all executed
1. `make migrate` — applied cleanly (Postgres container had been reset between sessions; its named volume had persisted, so only the new revision needed to run)
2. `RUN_DB_TESTS=1 make test-db` — 7/7 passing, including a genuine bug found and fixed: `LogORM`/`FailedLogEventORM` timestamp columns weren't marked `DateTime(timezone=True)` in the ORM layer (even though the migration created them as `timestamptz`), so asyncpg rejected the timezone-aware Python datetimes being inserted. Fixed there and proactively in every other ORM timestamp column carrying the same latent risk.
3. Full suite via `make test` — 48/48 passing
4. Rebuilt and restarted the full `docker-compose` stack, then sent an actual chat request through the live API. `GEMINI_API_KEY` isn't available in this environment, so the call genuinely failed against the real Gemini API ("API key not valid") - and that failure correctly flowed through `InstrumentedProvider` → the real `InProcessEventQueue` → the real `IngestionWorker` background task → the pipeline → a real row in `logs` (`status=error`, the actual Gemini error message), confirmed via a direct `psql` query. This is the first time an event has flowed through the entire system end to end, not simulated - and it's about as complete a proof as is possible without a valid API key.
