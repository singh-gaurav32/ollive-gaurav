# Unit 1 Code Generation Summary — Provider Abstraction & Auto-Instrumentation

## What was built

- `backend/src/provider/models.py` — `LogEvent`, `Message`, `Token`, `Role`, and the `truncate_preview` helper (BR7).
- `backend/src/provider/interface.py` — `LLMProvider` (Strategy interface), `ProviderResponse`, `ProviderError`.
- `backend/src/provider/event_queue.py` — `EventQueue` interface only (the concrete implementation is Unit 3's deliverable).
- `backend/src/provider/gemini_provider.py` — `GeminiProvider`, the v1 concrete adapter, built against `google-genai`.
- `backend/src/provider/instrumented_provider.py` — `InstrumentedProvider`, the Decorator implementing the full logic model and all 9 business rules.

## Design decisions beyond the functional design docs

These weren't specified at the functional-design level and were resolved during implementation:

- **`conversation_id`/`session_id` are part of the `LLMProvider` interface itself**, not bolted onto `InstrumentedProvider` only. `GeminiProvider` accepts and ignores them. This keeps the Decorator relationship strictly substitutable — every `LLMProvider` implementation honors the same contract, rather than `InstrumentedProvider` silently requiring more than the interface it claims to implement.
- **`Token` carries optional `input_tokens`/`output_tokens`**, populated by `GeminiProvider` only on the chunk(s) where the API actually reports usage (typically the final chunk). `InstrumentedProvider` keeps the last non-null values it observes as the call's final tallies. This is how BR3 (provider-reported token counts, no independent tokenizer) is satisfied for the *streaming* path specifically — the functional design specified the rule but not this wire-level mechanism.
- **`asyncio.CancelledError` is not caught by the generic error handler** in either `send()` or `stream()`'s exception blocks, because it's a `BaseException` subclass in Python 3.8+, not an `Exception` subclass. This is what makes BR8 (cancellation gets its own status) and BR5 (provider errors get "error" status) mutually exclusive without extra branching logic.

## Tests

`backend/tests/provider/`:
- `doubles.py` — `FakeLLMProvider` (scriptable success/error/cancel), `FakeEventQueue` (records published events, can simulate publish failure)
- `test_instrumented_provider.py` — 5 tests: success-path field population, provider-error re-raise + logging, publish-failure swallowing, streaming ttft/token accumulation, cancellation with partial output
- `test_gemini_provider.py` — 2 tests: adapter shape against a mocked `google-genai` client, error normalization into `ProviderError`

Run with:
```bash
cd backend && uv run pytest -v
```

## Traceability

- US-1.1 (pluggable provider interface) → `interface.py`, `gemini_provider.py`
- US-1.2 (auto-instrumented logging) → `instrumented_provider.py`

## Post-review restructuring

Before merge, review caught that `EventQueue` (and `LogEvent`) were nested inside `provider/`, which misrepresented ownership — both are a contract between Unit 1 (producer) and Unit 3 (implementer/consumer), not something Unit 1 owns. Relocated to a new shared `events/` package, and — since the same problem would have recurred for every repository (`LogRepository` is written by Unit 3 but read directly by Unit 4; `UserRepository` is needed in stub form by Unit 2 before Unit 5 completes it) — defined a full shared `db/` package up front for every persistence contract in the system. See `aidlc-docs/inception/application-design/project-structure.md` and `shared-contracts.md`. `provider/` now contains only `Message`/`Token`/`Role`/`LLMProvider`/`ProviderResponse`/`ProviderError`/`GeminiProvider`/`InstrumentedProvider` — everything intrinsic to the provider-call boundary and nothing else. Full suite re-verified: 14/14 passing (7 original + 3 new `events/` tests + 4 new `db/` tests).
