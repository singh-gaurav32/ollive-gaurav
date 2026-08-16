# Business Rules — Unit 3: Ingestion Pipeline Hardening

**BR1 — `PayloadValidator` and `MetadataExtractor` are pass-through for v1, not deleted.** They remain real stages in the pipeline (preserving Application Design Q1's four-stage decision) so the pipeline's shape doesn't need to change when real logic is added to either later — only their bodies change.

**BR2 — Redaction targets only free-text preview fields.** `PIIRedactor` transforms `input_preview` and `output_preview`; every other `LogEvent` field (model, provider, timestamps, token counts, IDs) passes through untouched — those aren't free text and were never a redaction concern.

**BR3 — Redaction patterns are hardcoded; the denylist is constructor-supplied, not env-configurable (for now).** Four hardcoded regexes (email, phone, SSN, credit card) plus an optional list of additional patterns passed to `PIIRedactor.__init__`. Making the denylist configurable via environment variable was explicitly deferred, not rejected.

**BR4 — A pipeline failure at any stage is attributed to that specific stage, not reported generically.** `IngestionWorker` tracks which of validate/extract/redact/persist was executing when an exception occurred, and records that stage name in the dead-letter entry.

**BR5 — A single event's failure never stops the consume loop or affects any other event.** Each event is processed inside its own try/except; the loop continues to the next event regardless of outcome.

**BR-PII — The redaction guarantee (US-3.2: "raw PII is never written, even transiently, to durable storage") holds on the failure path too, not just the success path.** If a pipeline failure happens *before* redaction completes (e.g. `PayloadValidator` or `MetadataExtractor` throws), the event being dead-lettered may not have had its preview text redacted yet. Rather than risk writing unredacted text to `failed_log_events`, `FailedLogEvent` **omits preview text entirely** — it carries only metadata (model, provider, IDs, timestamp, failure stage, failure reason). This is a deliberate scope boundary: the dead-letter table exists to answer "what failed and why," not to preserve the failed content for replay. Replaying a truly failed event isn't supported in v1.

**BR6 — `InProcessEventQueue.publish` is non-blocking even under backpressure.** A bounded queue's default `put()` would block once full, which would violate `EventQueue`'s contract (Unit 1). `put_nowait()` is used instead — a full queue raises `QueueFull` immediately, which is just another publish failure from `InstrumentedProvider`'s perspective (already swallowed per BR5/BR9, Unit 1). No new error handling needed upstream; the existing contract already covers this case correctly.

**BR7 — The worker's lifecycle is explicit, not implicit.** `IngestionWorker` starts via FastAPI's `lifespan` context manager and is cancelled cleanly on shutdown — visible in `main.py` where a reviewer would expect to find it, not hidden inside a lazily-triggered dependency.
