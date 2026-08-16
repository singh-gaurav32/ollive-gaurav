# Unit 3 Code Generation Summary — Ingestion Pipeline Hardening

## What was built

- `backend/src/events/in_process_event_queue.py` — the real `EventQueue` implementation; `noop_event_queue.py` deleted, no longer referenced anywhere
- `backend/src/ingestion/` — `payload_validator.py`, `metadata_extractor.py` (pass-through for v1), `pii_redactor.py` (real work: hardcoded regex + constructor denylist), `log_persister.py`, `worker.py`
- `backend/src/db/` — `FailedLogEvent` (models.py), `LogORM`/`FailedLogEventORM` (orm.py), `failed_log_event_repository.py` (new interface), `sqlalchemy_log_repository.py` (insert + `query_window` with real `percentile_cont` aggregation), `sqlalchemy_failed_log_event_repository.py`
- `backend/alembic/versions/0002_logs_and_failed_log_events.py`
- `backend/src/api/deps.py` — `get_event_queue()` (shared singleton between producer and consumer), `get_ingestion_worker()`, `get_chat_service()` updated
- `backend/src/main.py` — `lifespan` starts/stops the worker, attaches the crash-visibility `done_callback`

## A genuine bug found during verification, not just written and assumed correct

`LogORM.timestamp` and `FailedLogEventORM.timestamp` weren't declared `DateTime(timezone=True)` in the ORM layer, even though the Alembic migration created the actual Postgres columns as `timestamptz`. Inserting the timezone-aware Python `datetime` objects our pydantic models produce hit `asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes`. Fixed in both places, and proactively in every other ORM timestamp column carrying the same latent risk (`UserORM`, `SessionORM`, `ConversationORM`, `MessageORM`) even though those hadn't broken yet — they'd only avoided the bug because their timestamps are always DB-generated via `server_default`, never Python-supplied.

## Verified beyond unit tests — the first true end-to-end pass

Rebuilt the full Docker Compose stack and sent an actual chat request through the live API. No real `GEMINI_API_KEY` is available in this environment, so the call genuinely failed against Gemini ("API key not valid") — and that failure was traced all the way through: `InstrumentedProvider` (Unit 1) → the real `InProcessEventQueue` (not the `NoOp` stand-in anymore) → the real `IngestionWorker` background task → the 4-stage pipeline → a real row in the `logs` table, confirmed with a direct `psql` query showing the actual Gemini error message. This is the first time in the project an event has flowed through the entire system, not through a fake or a mock.

## Tests

48 total, all passing: 41 fast (including `tests/events/test_in_process_event_queue.py`'s `QueueFull`-on-backpressure test, `tests/ingestion/test_pii_redactor.py`'s per-pattern coverage, `tests/ingestion/test_worker.py`'s failure-isolation and BR-PII structural test) + 7 real-Postgres (including the `query_window` aggregation test, which checks actual computed counts and percentiles, not just that the query doesn't error).

## Traceability

- US-3.1 (non-blocking ingestion) → `in_process_event_queue.py` (`put_nowait`), `worker.py`
- US-3.2 (PII redaction) → `pii_redactor.py`
- US-3.3 (swappable broker) → satisfied structurally since Unit 1; this unit is the first real implementation behind that interface, proving the swap works
