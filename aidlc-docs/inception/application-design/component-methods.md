# Component Methods

High-level method signatures per component. Detailed business rules (exact truncation strategy, exact redaction regex set, exact bucket sizes) are deferred to Functional Design, per unit, in Construction.

## `LLMProvider` (interface)
- `send(messages: list[Message]) -> Message` — non-streaming completion.
- `stream(messages: list[Message]) -> AsyncIterator[Token]` — streaming completion.

## `GeminiProvider`
- `send(messages) -> Message` — implements the interface against the Gemini API.
- `stream(messages) -> AsyncIterator[Token]` — implements the interface against Gemini's streaming API.

## `InstrumentedProvider`
- `send(messages) -> Message` — delegates to the wrapped provider, times the call, publishes a `LogEvent` on completion/error.
- `stream(messages) -> AsyncIterator[Token]` — delegates to the wrapped provider's stream, times to first token and total duration, publishes a `LogEvent` once the stream ends (success, error, or cancellation).

## `EventQueue` (interface)
- `publish(event: LogEvent) -> None` — non-blocking enqueue.
- `consume() -> AsyncIterator[LogEvent]` — async iterator yielding events as they arrive.

## `InProcessEventQueue`
- `publish(event) -> None` — enqueues to the in-memory async queue.
- `consume() -> AsyncIterator[LogEvent]` — dequeues in FIFO order.

## `ChatService`
- `start_conversation(user_id) -> Conversation`
- `send_message(conversation_id, user_id, content) -> AsyncIterator[Token]` — orchestrates: load conversation, truncate context if needed, call `InstrumentedProvider.stream(...)`, yield tokens, persist the final message via `MessageRepository` once streaming completes.
- `cancel_conversation(conversation_id, user_id) -> None` — signals the in-flight provider call to stop, transitions conversation state to `cancelled`, persists the partial message.
- `resume_conversation(conversation_id, user_id) -> Conversation` — loads full history, transitions state back to `active`.
- `list_conversations(user_id) -> list[ConversationSummary]`

## `ConversationRepository`
- `create(user_id) -> Conversation`
- `get(conversation_id, user_id) -> Conversation | None` — user-scoped; returns `None` (not another user's data) if the conversation belongs to someone else.
- `list_for_user(user_id) -> list[Conversation]`
- `update_state(conversation_id, new_state) -> None`

## `MessageRepository`
- `append(conversation_id, role, content) -> Message`
- `list_for_conversation(conversation_id) -> list[Message]`

## `PayloadValidator`
- `validate(raw_event: dict) -> ValidatedEvent` — raises on malformed/missing required fields.

## `MetadataExtractor`
- `extract(event: ValidatedEvent) -> ExtractedEvent` — derives normalized fields (model, provider, token counts, latency, status).

## `PIIRedactor`
- `redact(event: ExtractedEvent) -> RedactedEvent` — applies regex patterns + denylist to input/output preview fields.

## `LogPersister`
- `persist(event: RedactedEvent) -> None` — writes to `LogRepository`.

## `LogRepository`
- `insert(log_record) -> None`
- `query_window(start_time, end_time, bucket_size) -> list[MetricBucket]` — used by `AnalyticsService`.

## `IngestionWorker`
- `run() -> None` — the consume loop: `async for event in queue.consume(): pipeline stages in sequence`.

## `AuthService`
- `login(username, password) -> Session`
- `validate_session(session_id) -> UserContext | None`
- `logout(session_id) -> None`

## `UserRepository`
- `get_by_username(username) -> User | None`
- `create_session(user_id) -> Session`
- `get_session(session_id) -> Session | None`

## `AnalyticsService`
- `get_latency_metrics(window) -> LatencyMetrics` (p50/p95)
- `get_throughput_metrics(window) -> ThroughputMetrics`
- `get_error_rate(window) -> ErrorRateMetrics`

## API Routers
- `ChatRouter`: `POST /conversations`, `POST /conversations/{id}/messages` (SSE response), `POST /conversations/{id}/cancel`
- `ConversationRouter`: `GET /conversations`, `GET /conversations/{id}`, `POST /conversations/{id}/resume`
- `DashboardRouter`: `GET /metrics/latency`, `GET /metrics/throughput`, `GET /metrics/errors`
- `AuthRouter`: `POST /login`, `POST /logout`
