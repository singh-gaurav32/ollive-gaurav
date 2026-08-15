# Business Rules — Unit 1: Provider Abstraction & Auto-Instrumentation

**BR1 — Latency is always measured, never estimated.** `latency_ms` is wall-clock time from call initiation to call completion, regardless of outcome (success, error, or cancellation).

**BR2 — Time-to-first-token only applies to streaming.** `ttft_ms` is populated for `stream()` calls only; it is always `null` for non-streaming `send()` calls.

**BR3 — Token counts come only from the provider's own reporting.** No independent tokenizer is used (Q3 explicitly rejected that option). If a provider's response doesn't include usage data, `input_tokens`/`output_tokens` are `null` — never estimated or guessed.

**BR4 — Status is a closed set.** `status` is exactly one of `"success"`, `"error"`, `"cancelled"` — no other values, and never null.

**BR5 — Instrumentation failures never break the chat response; provider failures always propagate.** These are two different kinds of failure and must not be conflated:
- If `EventQueue.publish()` fails (queue full, etc.), the failure is caught, logged locally via standard logging (not through the `LogEvent` pipeline itself — that would recurse), and swallowed. The caller of `InstrumentedProvider` never sees this failure.
- If the *wrapped provider* raises (the actual Gemini API call fails), that exception is captured into a `LogEvent` with `status = "error"`, then **re-raised** to the caller after the (best-effort) publish attempt. Auto-instrumentation observes provider failures; it never hides them.

**BR6 — Provider-specific data goes into `extra`, never invented as new top-level fields.** Keeps the `LogEvent` contract stable as more providers are added later; a second provider's unique metadata doesn't require a schema change.

**BR7 — Previews are raw and truncated, not redacted.** `input_preview`/`output_preview` carry unredacted text truncated to a fixed length. Redaction is explicitly out of scope for this unit — Unit 3's `PIIRedactor` pipeline stage owns it. This is safe because these previews only exist transiently in the in-process queue before Unit 3 processes them; nothing in this unit writes to durable storage.

**BR8 — Cancellation produces its own `LogEvent`, not a suppressed one.** When the wrapped provider's stream is cancelled mid-flight (via `asyncio.CancelledError`, triggered by Unit 2/5's cancel action), `InstrumentedProvider` still publishes a `LogEvent` with `status = "cancelled"` and whatever partial `output_tokens`/`ttft_ms` had been captured up to that point, then re-raises `CancelledError` so the underlying task cancellation completes normally.

**BR9 — A dead-letter mechanism does not belong in this unit.** A publish failure here means the event never entered the queue — there is nothing to dead-letter. (Flagged for Unit 3's own Functional Design: a dead-letter table for events that fail *during* pipeline processing, after being successfully dequeued, is a good fit there.)
