# Business Logic Model — Unit 3: Ingestion Pipeline Hardening

## `InProcessEventQueue`
- `publish(event) -> None`: `self._queue.put_nowait(event)` — raises `QueueFull` if at capacity (BR6), letting `InstrumentedProvider`'s existing swallow-on-failure handling deal with it.
- `consume() -> AsyncIterator[LogEvent]`: `while True: yield await self._queue.get()`.

## `IngestionWorker.run()`
```
async for event in self._queue.consume():
    await self._process(event)
```

## `IngestionWorker._process(event)`
1. `stage = "validate"`; `event = self._validator.validate(event)`
2. `stage = "extract"`; `event = self._extractor.extract(event)`
3. `stage = "redact"`; `event = self._redactor.redact(event)`
4. `stage = "persist"`; `await self._persister.persist(event)`
5. **On any exception** at any of the above steps: build a `FailedLogEvent` from whatever fields are available on `event` at that point (BR-PII: never including preview text, regardless of whether redaction had already run), with `failure_stage = stage` and `failure_reason = str(exc)`. Write it via `FailedLogEventRepository.insert`. If *that* write also fails (e.g. DB fully unavailable), fall back to structured logging as a last resort — no further fallback layers beyond that (accepted scope boundary).
6. The loop in `run()` continues to the next event regardless of outcome (BR5).

## `PayloadValidator.validate(event) -> LogEvent`
Pass-through for v1: `return event` (BR1).

## `MetadataExtractor.extract(event) -> LogEvent`
Pass-through for v1: `return event` (BR1).

## `PIIRedactor.redact(event) -> LogEvent`
1. Apply each hardcoded pattern (email, phone, SSN, credit card) plus any constructor-supplied denylist patterns to `event.input_preview` and `event.output_preview`, replacing matches with a fixed marker (e.g. `[REDACTED]`).
2. Return `event.model_copy(update={"input_preview": ..., "output_preview": ...})` — every other field unchanged (BR2).

## `LogPersister.persist(event)`
1. Map `LogEvent` fields into a new `LogRecord` (generating `id`).
2. `await self._log_repository.insert(record)`.

## Worker lifecycle (`main.py`, via FastAPI `lifespan`)
1. On startup: construct `InProcessEventQueue`, `IngestionWorker` (wired with the four stages + repositories), start `asyncio.create_task(worker.run())`. This same `InProcessEventQueue` instance replaces Unit 2's `NoOpEventQueue` in the `InstrumentedProvider` constructed by `api/deps.py` — the one-line wiring change anticipated when `NoOpEventQueue` was added.
2. On shutdown: cancel the worker task, await it (swallowing the resulting `CancelledError`), dispose the engine.

## Key Invariant

The redaction guarantee is structural on both the success path (BR2 of US-3.2) and the failure path (BR-PII) — there is no code path in this unit that writes preview text to durable storage before `PIIRedactor` has run on it.
