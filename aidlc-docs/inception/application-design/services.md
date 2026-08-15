# Services

Service-layer orchestration — how components are coordinated to fulfill a user story end to end.

## ChatOrchestration (realized by `ChatService`)
**Orchestrates**: `ConversationRepository`, `MessageRepository`, `InstrumentedProvider` (→ `GeminiProvider`).
**Flow** (fulfills US-2.1, US-2.2, US-2.3, US-5.1, US-5.3):
1. API layer calls `ChatService.send_message(...)`.
2. `ChatService` loads the conversation via `ConversationRepository`, truncates history if it exceeds the context window.
3. `ChatService` calls `InstrumentedProvider.stream(...)` — instrumentation happens transparently here; `ChatService` has no awareness of logging.
4. Tokens are yielded back through the API layer to the client via SSE as they arrive.
5. On stream completion, the final message is persisted via `MessageRepository` (synchronous write, per Q4).
6. On cancel, `ChatService` stops the in-flight provider call, transitions conversation state via `ConversationRepository.update_state(..., cancelled)`, and persists the partial message.
7. On resume, `ChatService` transitions state back to `active` and returns full history.

**Note**: `InstrumentedProvider`'s publish to the `EventQueue` happens inside the provider layer, not inside `ChatService` — `ChatService` is deliberately unaware that logging exists. This is the practical payoff of the Decorator boundary agreed in Q2.

## Ingestion (realized by `IngestionWorker` + pipeline stage components)
**Orchestrates**: `EventQueue` (consume side), `PayloadValidator`, `MetadataExtractor`, `PIIRedactor`, `LogPersister`.
**Flow** (fulfills US-3.1, US-3.2, US-3.3):
1. `IngestionWorker.run()` consumes events from `EventQueue` as `InstrumentedProvider` publishes them — fully decoupled from the chat request path (non-blocking, per US-3.1).
2. Each event passes through the four pipeline stages in sequence: validate → extract → redact → persist.
3. A failure in one event's pipeline (e.g. malformed payload) is caught and logged without crashing the consume loop or affecting other events.

## Analytics (realized by `AnalyticsService`)
**Orchestrates**: `LogRepository`.
**Flow** (fulfills US-4.1):
1. `DashboardRouter` calls `AnalyticsService` methods on each poll interval.
2. `AnalyticsService` issues time-bucketed queries directly against `LogRepository` — no separate maintained aggregate, computed at query time.

## Auth (realized by `AuthService`)
**Orchestrates**: `UserRepository`.
**Flow** (fulfills US-5.4, session mechanics):
1. `AuthRouter` calls `AuthService.login(...)`, which verifies credentials via `UserRepository` and creates a server-side session (Q5).
2. Every subsequent request's session cookie is validated via `AuthService.validate_session(...)`, producing a `UserContext` that every repository call is scoped to — this is the mechanism behind the isolation guarantee, not a policy layered on afterward.

## Cross-Service Note: Two Independent Write Paths
Per Q4, `ChatOrchestration`'s message writes (synchronous, via `MessageRepository`) and `Ingestion`'s log writes (asynchronous, via `LogRepository`, arriving through the queue) are intentionally independent. A slow or backed-up `IngestionWorker` never delays a chat response; a chat response is never blocked waiting on log persistence.
