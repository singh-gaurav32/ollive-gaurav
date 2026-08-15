# Domain Entities — Unit 1: Provider Abstraction & Auto-Instrumentation

## `LogEvent` (value object)

The core domain object of this unit — what `InstrumentedProvider` produces and what Unit 3's ingestion pipeline consumes. Immutable once created; has no identity of its own until Unit 3 persists it (a database-assigned ID is Unit 3's concern, not this one's).

| Field | Type | Notes |
|---|---|---|
| `model` | string | e.g. `"gemini-2.0-flash"` |
| `provider` | string | e.g. `"gemini"` — the adapter's identifier, not a Python type name |
| `latency_ms` | float | Wall-clock duration of the entire call, always populated (per BR1) |
| `ttft_ms` | float \| null | Time-to-first-token; populated only for `stream()` calls (per BR2) |
| `input_tokens` | int \| null | From the provider's own usage metadata; null if unavailable (per BR3) |
| `output_tokens` | int \| null | Same as above; for cancelled streams, reflects only the partial output captured before cancellation |
| `timestamp` | datetime (UTC) | Call start time |
| `status` | enum: `"success"` \| `"error"` \| `"cancelled"` | Exactly one of these three (per BR4) |
| `error_message` | string \| null | Populated only when `status = "error"` |
| `conversation_id` | UUID | |
| `session_id` | UUID | |
| `input_preview` | string | Raw (unredacted), truncated — redaction is explicitly Unit 3's responsibility, not this unit's |
| `output_preview` | string | Same as above |
| `extra` | dict[string, Any] | Open field for provider-specific metadata that doesn't fit the fixed schema (per BR6) — e.g. Gemini's `finish_reason`, safety ratings |

## Relationships

`LogEvent` has no relationships to other entities at this unit's boundary — it's a self-contained snapshot of one provider call, published once and handed off. `conversation_id` and `session_id` are foreign-key-shaped references to entities owned by Unit 2 (`ConversationRepository`) and Unit 5 (`AuthService`/`UserRepository`) respectively, but this unit doesn't dereference them — it just carries the IDs through.
