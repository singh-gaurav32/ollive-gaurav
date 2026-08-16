# Domain Entities — Unit 3: Ingestion Pipeline Hardening

## `InProcessEventQueue` (concrete `EventQueue`)

Backed by a bounded `asyncio.Queue` (maxsize 1000, tunable). Critically, `publish()` uses `put_nowait()`, not `await put()` — a bounded queue's blocking `put()` would violate `EventQueue`'s non-blocking contract (Unit 1) once full. `put_nowait()` raises `QueueFull` immediately instead, which `InstrumentedProvider._publish()` (Unit 1, BR5/BR9) already catches and swallows — an event dropped because the queue is full is handled by the exact same path as any other publish failure, no new error handling needed upstream.

## Pipeline stages (Chain of Responsibility, per Application Design Q1)

All four remain separate, independently testable classes — the granularity decision from Application Design isn't revisited, only what two of the four stages *do* right now:

- **`PayloadValidator`**: pass-through for v1 (identity — returns the `LogEvent` unchanged). Extension point for future business-level checks (e.g. `latency_ms >= 0`) that pydantic's type validation doesn't cover.
- **`MetadataExtractor`**: pass-through for v1. Extension point for normalizing provider-specific `extra` fields into first-class columns later, if the dashboard (Unit 4) ends up needing one.
- **`PIIRedactor`**: the stage that does real work. Returns a new `LogEvent` with `input_preview`/`output_preview` redacted; every other field passes through unchanged.
- **`LogPersister`**: maps the (validated, extracted, redacted) `LogEvent` into a `LogRecord` (generating its `id`) and calls `LogRepository.insert`.

## `IngestionWorker`

Consumes `InProcessEventQueue`, runs each event through the four stages in sequence, tracking which stage is in progress so a failure can be attributed correctly. A single event's failure at any stage does not stop the consume loop or affect any other event.

## `FailedLogEvent` (new domain model, `db/models.py`)

The dead-letter record. Deliberately **omits `input_preview`/`output_preview`** — see `business-rules.md` BR-PII for why. Carries: `id`, `model`, `provider`, `conversation_id`, `session_id`, `timestamp` (from the original event), `failure_stage` (`"validate"` | `"extract"` | `"redact"` | `"persist"`), `failure_reason` (the exception message), `created_at`.

## `FailedLogEventRepository` (new interface, `db/failed_log_event_repository.py`)

`insert(record: FailedLogEvent) -> None`. Lives in `db/` alongside the other repositories, per `project-structure.md`'s consistency rule (every repository lives there, regardless of how many units currently use it) — even though only Unit 3 reads/writes it today.

## `LogRepository` (interface already fixed in the shared-contracts pass — implemented here)

`SqlAlchemyLogRepository` is this unit's implementation of the interface `db/log_repository.py` already defined. This is also where the `logs` table itself is finally created via Alembic — the interface existed since the shared-contracts pass, but no table backed it until now.
