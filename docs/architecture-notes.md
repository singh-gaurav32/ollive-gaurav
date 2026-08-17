# Architecture Notes

## Ingestion Flow

Every LLM call goes through `InstrumentedProvider`, a decorator wrapping the concrete `LLMProvider` (`GeminiProvider`). It's the single interception point — no manual logging calls anywhere else in the codebase. After each call (success, provider error, or client cancellation), it builds a `LogEvent` and publishes it to an in-process `asyncio.Queue` (`InProcessEventQueue`) and returns/re-raises immediately — publishing never blocks or fails the caller's request.

A background `IngestionWorker`, running as an asyncio task inside the same API process (not a separate service or container), consumes that queue and runs each event through a 4-stage pipeline:

```
validate → extract → redact → persist
```

- **validate**: structural checks on the incoming event
- **extract**: metadata extraction (currently a pass-through stage — the event already carries model/provider/latency/tokens from instrumentation; kept as a distinct stage so a real extraction step, e.g. deriving fields from raw provider responses, has an obvious place to go)
- **redact**: regex-based PII redaction (email, phone, SSN, credit card patterns, plus an optional caller-supplied denylist) applied to `input_preview`/`output_preview` only — every other field passes through unchanged
- **persist**: writes the finished `LogRecord` to the `logs` table

If a stage throws, the worker catches it, records which stage failed, and writes a `FailedLogEvent` to a separate `failed_log_events` table (dead-letter) — then continues consuming, so one bad event never stops the pipeline. Critically, `FailedLogEvent` has no `input_preview`/`output_preview` fields at all: a failure that happens *before* redaction completes must never risk writing unredacted text to durable storage, so preview text is omitted entirely for dead-lettered events rather than conditionally redacted.

## Logging Strategy

"Auto-instrumentation" here means: any code that wants to call an LLM does so through the `LLMProvider` interface, and gets logging for free by virtue of the concrete instance being an `InstrumentedProvider` — nothing about capturing metadata lives in `ChatService` or the API routers. This makes the logging strategy provider-agnostic by construction: adding a second `LLMProvider` implementation (e.g. OpenAI) requires zero changes to instrumentation, ingestion, or the dashboard.

Captured per call: `model`, `provider`, `latency_ms`, `ttft_ms` (time-to-first-token, streaming only), `input_tokens`/`output_tokens`, `status` (`success`/`error`/`cancelled`), `error_message`, `conversation_id`, `session_id`, and truncated `input_preview`/`output_preview`. Streaming responses accumulate partial output across all yielded tokens so a cancelled or failed stream still logs whatever was actually produced before the interruption.

## Scaling Considerations

Current design deliberately trades scalability for simplicity at v1's scope (a single-demo-VM deployment, not a production SLA):

- **In-process event queue**: `InProcessEventQueue` is an `asyncio.Queue` (bounded at 1000), living in the same process as the API. This means zero infra to run, but also: events are lost on a process crash before they're consumed, there's no cross-process/cross-replica fan-out, and the API and ingestion worker can't be scaled independently. A real deployment beyond single-node would swap this for an actual broker (Redis Streams, SQS, Kafka) behind the same `EventQueue` interface — the interface boundary already exists, so this is a swap-the-implementation change, not a rewrite of `IngestionWorker` or `InstrumentedProvider`.
- **Single Postgres, single node**: no read replicas, no partitioning on `logs` (which is the table that grows unbounded over time). The dashboard's `bucket_size_seconds`/time-range query params plus a hard cap (`MAX_BUCKET_COUNT = 10_000`) protect against a single runaway aggregation query, but there's no retention/archival policy — `logs` grows forever.
- **k3s single-node**: the actual deployment (see `k8s/`) runs one replica of each service on one VM. Horizontal scaling of `api`/`frontend` would need the ingestion worker split out of the API process first (it currently runs in-process specifically to avoid a 4th service for a demo-scale deployment — that decision would need revisiting for multi-replica `api`).
- **Context truncation**: `WindowTruncationStrategy` keeps only the last 10 conversation turns before calling the provider — bounds input token cost and request size regardless of how long a conversation gets, at the cost of the model losing older context outright (no summarization).

## Failure Handling Assumptions

- **Provider call failures are always surfaced, never swallowed silently**: `InstrumentedProvider` re-raises after logging, so a Gemini API error (auth failure, deprecated model, rate limit, etc.) propagates to the chat layer and ultimately to the user as a visible failure — not a silent empty response. This is exactly what caught the two real Gemini model-deprecation errors hit during actual deployment (see `logs.error_message` for those events).
- **Instrumentation failures are always swallowed**: if publishing a `LogEvent` to the queue itself fails (e.g. queue full), that's logged locally (`logger.warning`) and dropped — it never propagates to or affects the caller. Observability failing must not take down the chat feature it's observing.
- **Ingestion pipeline failures are dead-lettered, never dropped silently and never crash the worker loop**: each event is wrapped in its own try/except inside `IngestionWorker._process`; a failure at any of the 4 stages writes a `FailedLogEvent` and the loop continues. If *that* dead-letter write itself fails (last-resort case), it's logged at `critical` level rather than raised — there's genuinely nowhere further to escalate to.
- **Worker crash is loud, not silent**: if the entire `IngestionWorker.run()` task dies (an unhandled exception outside the per-event try/except), `main.py`'s `_log_if_crashed` callback logs it at `critical` immediately. Left to Python's default behavior, an asyncio task's unhandled exception isn't surfaced until the task object is garbage collected — arbitrarily delayed and easy to miss in production.
- **Client-initiated cancellation is a first-class status, not an error**: aborting an in-flight SSE request is detected server-side (not just a client-side UI change) and logged with `status: "cancelled"`, distinct from `"error"` — cancelling a conversation and a provider failure are different, deliberately distinguishable events in the data.
