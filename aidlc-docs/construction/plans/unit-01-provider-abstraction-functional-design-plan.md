# Functional Design Plan — Unit 1: Provider Abstraction & Auto-Instrumentation

## Execution Checklist

- [x] Confirm `LogEvent` contract shape (see Question 1) — B: fixed fields + open `extra` dict
- [x] Confirm streaming latency measurement approach (see Question 2) — A: time-to-first-token + total duration
- [x] Confirm token counting source (see Question 3) — A: provider's own usage metadata
- [x] Confirm publish-failure behavior (see Question 4) — A: swallow + log locally
- [x] Confirm cancellation status handling (see Question 5) — A: dedicated "cancelled" status
- [x] Generate `business-logic-model.md`
- [x] Generate `business-rules.md`
- [x] Generate `domain-entities.md` (the `LogEvent` entity is the core domain object for this unit)
- No frontend-components.md — this unit has no UI surface (backend-only, per unit-of-work.md)

---

## Question 1: `LogEvent` contract shape
Unit 3 (Ingestion Pipeline) consumes whatever `InstrumentedProvider` publishes, so this contract needs to be stable before Unit 3 starts.

A) A flat structure with fixed fields: `model`, `provider`, `latency_ms`, `input_tokens`, `output_tokens`, `timestamp`, `status` (enum), `error_message` (nullable), `conversation_id`, `session_id`, `input_preview`, `output_preview`

B) Same as A, plus an open `extra: dict` field for provider-specific metadata that doesn't fit the fixed fields (e.g. Gemini-specific fields), so adding a second provider later doesn't require a schema change

C) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 2: Streaming latency measurement
A) Measure two values: time-to-first-token (from call start to the first yielded token) and total duration (call start to stream completion) — both included in `LogEvent`

B) Measure only total duration — simpler, but loses the "does it feel slow to start" signal that streaming UX actually cares about

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3: Token counting source
A) Use the token counts Gemini's API returns in its response metadata (usage field) — accurate, no extra dependency

B) Count tokens independently using a tokenizer library, ignoring what the provider reports — needed only if a provider doesn't return usage data, adds a dependency and a source of mismatch with the provider's own accounting

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: Publish-failure behavior
If `EventQueue.publish()` fails or the queue is full (e.g. `InProcessEventQueue` is backed by a bounded queue), what should `InstrumentedProvider` do?

A) Swallow the failure and log a warning locally — the chat response to the user must never fail because logging failed. A dropped log event is an acceptable loss; a broken chat response is not.

B) Propagate the failure — a publish failure should raise from `InstrumentedProvider`, failing the chat call too

C) Other (please describe after [Answer]: tag below)

[Answer]: A — a dropped log event is an acceptable loss; a broken chat response is not. (A dead-letter queue doesn't apply at this point — the event never successfully entered the queue, so there's nothing to dead-letter; that pattern is more relevant to Unit 3's pipeline-stage failures, flagged for that unit's own Functional Design.)

## Question 5: Cancellation status
When Unit 2/5 cancels an in-flight stream, does `InstrumentedProvider` still publish a `LogEvent`?

A) Yes — publish with `status = "cancelled"` (a third value alongside `"success"` and `"error"`), including whatever partial token count was captured before cancellation. Needed for the dashboard's error/status breakdown to be meaningful (US-4.1) and for US-5.1's acceptance criteria around cancel behavior to be verifiable via logs.

B) No — cancellation is treated as a special case of error, reusing the existing `"error"` status with a specific error message

C) Other (please describe after [Answer]: tag below)

[Answer]: A
