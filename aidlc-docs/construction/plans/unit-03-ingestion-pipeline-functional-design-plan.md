# Functional Design Plan — Unit 3: Ingestion Pipeline Hardening

## Execution Checklist

- [x] Confirm PayloadValidator's actual responsibility (see Question 1) — kept as a stage, pass-through for v1
- [x] Confirm MetadataExtractor's actual responsibility (see Question 2) — kept as a stage, pass-through for v1
- [x] Confirm PII redaction patterns and denylist mechanism (see Question 3) — A: hardcoded + constructor denylist
- [x] Confirm worker startup/shutdown lifecycle (see Question 4) — A: FastAPI lifespan
- [x] Confirm the dead-letter mechanism flagged in Unit 1 (see Question 5) — A: failed_log_events table, metadata only (see PII resolution below)
- [x] Generate `business-logic-model.md`
- [x] Generate `business-rules.md`
- [x] Generate `domain-entities.md`
- No `frontend-components.md` — no UI in this unit

---

## Question 1: What does PayloadValidator actually validate?
`EventQueue.publish()` only ever accepts a `LogEvent`, which pydantic already validates at construction (Unit 1) — so by the time an event reaches this pipeline, it's already type-correct. A stage literally called "validate" needs a real job beyond what pydantic already guarantees.

A) **Business-level sanity checks pydantic doesn't enforce** — e.g. `latency_ms >= 0`, `timestamp` not absurdly in the future, `error_message` present iff `status == "error"`. Failures here are logged and the event is dropped (candidate for the dead-letter mechanism, Question 5) rather than crashing the worker.

B) **Drop the stage entirely** — if pydantic's type validation is considered sufficient, merge this into MetadataExtractor rather than keeping a stage that does nothing (revisits the 4-stage-pipeline granularity decided in Application Design Q1, but only for this one stage).

C) Other (please describe after [Answer]: tag below)

[Answer]: Neither A nor B cleanly — kept as its own stage (preserving the 4-stage pipeline already fixed in Application Design Q1, each independently testable), but implemented as a pass-through/identity step for v1: no business-level checks yet. Documented as the extension point for option A's checks later, not deleted or merged.

## Question 2: What does MetadataExtractor actually derive?
`LogEvent` already carries structured fields (model, provider, tokens, latency, status). What's left to "extract"?

A) **Normalize provider-specific `extra` fields into a queryable shape** — e.g. pull a known field like `finish_reason` out of the open `extra` dict into a first-class column on `LogRecord` if it's useful for the dashboard (Unit 4), leaving anything else in `extra` as-is

B) **Nothing beyond what Unit 1 already structured** — this stage becomes a pass-through / identity step, kept only for pipeline-shape consistency with the other three stages

C) Other (please describe after [Answer]: tag below)

[Answer]: Same treatment as Question 1 — kept as its own stage, implemented as a pass-through/identity step for v1 (nothing to normalize yet), documented as the extension point for option A later.

## Question 3: PII redaction patterns and denylist
Requirements Analysis (Q7) fixed regex + configurable denylist as the approach.

A) Hardcode a fixed pattern set (email, phone, SSN, credit card) as module-level compiled regexes, plus a denylist of field-name substrings passed to `PIIRedactor`'s constructor (Python list, not an external config file) — simplest, matches this project's scale

B) Same patterns, but the denylist is loaded from an environment variable (comma-separated) so it's configurable without a code change/redeploy

C) Other (please describe after [Answer]: tag below)

[Answer]: A — hardcoded regex patterns, denylist passed to the constructor (not env-var configurable for now; that's a reasonable later enhancement, not decided today).

## Question 4: Worker startup/shutdown lifecycle
`IngestionWorker` runs as a background `asyncio.Task` inside the same process as the API (fixed in Units Generation).

A) Started via FastAPI's `lifespan` context manager in `main.py` — the task is created on app startup and cancelled cleanly on shutdown, alongside whatever `EventQueue` instance `api/deps.py` wires in

B) Started lazily on first use (e.g. inside `get_chat_service()`) — simpler wiring, but means the worker's lifecycle isn't visible in `main.py` where a reviewer would expect to find it

C) Other (please describe after [Answer]: tag below)

[Answer]: A — started via FastAPI's lifespan context manager.

## Question 5: Dead-letter mechanism (flagged in Unit 1's BR9)
A pipeline-stage failure (Question 1/2's validation, or a persist failure) needs somewhere to go besides silently vanishing.

A) A `failed_log_events` table — same database, minimal new infrastructure, inspectable via a normal SQL query. The failed event's raw fields plus a `failure_reason` string.

B) Just log to stderr/structured logging, no persistence — simplest, but the failed event is gone once the log rotates, harder to point to as evidence of "failure handling" in the README's architecture notes

C) Other (please describe after [Answer]: tag below)

[Answer]: A — a failed_log_events table.
