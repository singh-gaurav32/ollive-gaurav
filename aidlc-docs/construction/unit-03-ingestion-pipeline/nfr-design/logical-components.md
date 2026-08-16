# Logical Components — Unit 3: Ingestion Pipeline Hardening

## `InProcessEventQueue`

`backend/src/events/in_process_event_queue.py` — a thin wrapper around `asyncio.Queue(maxsize=1000)`. This is the component `api/deps.py` swaps in for Unit 2's `NoOpEventQueue` (one line, per the scope note recorded when the stand-in was added).

## Pipeline stage components

`backend/src/ingestion/payload_validator.py`, `metadata_extractor.py` (both pass-through for v1), `pii_redactor.py` (hardcoded compiled regex constants + constructor denylist), `log_persister.py` — each a small, independently testable class per Application Design's Chain-of-Responsibility decision.

## `IngestionWorker`

`backend/src/ingestion/worker.py` — owns the consume loop, the per-event stage sequencing with failure-stage tracking, and the dead-letter write on failure.

## Crash-visibility wiring

Lives in `main.py`'s `lifespan`, not inside `IngestionWorker` itself — the worker's own code stays focused on processing; the "make failures loud" concern is attached externally via `task.add_done_callback(...)` at the point the task is created, keeping the pattern visible where a reviewer would look for startup/shutdown behavior.

## `db/` additions

`orm.py` gains `LogORM` and `FailedLogEventORM`. Two new repository implementations: `sqlalchemy_log_repository.py`, `sqlalchemy_failed_log_event_repository.py`. A new Alembic migration adds `logs` and `failed_log_events` tables — no indexes beyond primary keys, per NFR Requirements.
