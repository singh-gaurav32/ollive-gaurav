# Business Logic Model — Unit 1: Provider Abstraction & Auto-Instrumentation

## `InstrumentedProvider.send(messages)` — non-streaming path

1. Record `start_time`.
2. Call the wrapped provider's `send(messages)`.
3. **On success**: record `end_time`; compute `latency_ms`. Extract token counts from the response's usage metadata (BR3). Build a `LogEvent` with `status = "success"`. Attempt `event_queue.publish(event)` inside a try/except that swallows and locally logs any failure (BR5). Return the response to the caller unchanged.
4. **On exception from the wrapped provider**: record `end_time`, `latency_ms`. Build a `LogEvent` with `status = "error"`, `error_message` set from the exception. Attempt to publish (same swallow-on-publish-failure behavior). **Re-raise the original provider exception** — instrumentation observes the failure, it does not absorb it (BR5).

## `InstrumentedProvider.stream(messages)` — streaming path

1. Record `start_time`; initialize `first_token_time = None` and an output token accumulator.
2. `async for token in wrapped_provider.stream(messages):`
   - If `first_token_time` is still `None`, set it now and compute `ttft_ms` (BR2).
   - Accumulate the token toward the running output count.
   - `yield token` — pass-through to the caller, transparent; the caller has no awareness that instrumentation is happening.
3. **On normal stream completion**: record `end_time`, `latency_ms`. Build a `LogEvent` with `status = "success"`, the accumulated token counts, and `ttft_ms`. Publish (swallow-on-failure, BR5).
4. **On `asyncio.CancelledError`** (raised when Unit 2/5's cancel action tears down the streaming task): build a `LogEvent` with `status = "cancelled"`, the *partial* accumulated output tokens and whatever `ttft_ms` was captured (BR8). Publish (swallow-on-failure). **Re-raise `CancelledError`** so the task cancellation completes normally — swallowing it here would leave the underlying async task in a broken state.
5. **On any other exception during iteration**: build a `LogEvent` with `status = "error"`, `error_message` set. Publish (swallow-on-failure). Re-raise.

## Key Invariant

Two independent failure modes exist in this unit, and they must never be handled the same way:
- **Instrumentation failure** (can't publish to the queue) → always swallowed, never visible to the caller.
- **Provider call failure** (Gemini API errors, or cancellation) → always observed and recorded as a `LogEvent`, and always re-raised to the caller afterward.

This is what makes `InstrumentedProvider` safe to use as a transparent wrapper: adding instrumentation to a call site can never change that call site's error-handling behavior, only add a side-channel log of what happened.
