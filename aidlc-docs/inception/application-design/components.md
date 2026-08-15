# Components

## Provider Layer

### `LLMProvider` (interface)
**Purpose**: Strategy interface abstracting a single LLM provider's completion + streaming capability.
**Responsibilities**: Define the contract for sending a message and streaming tokens. No logging, no persistence — purely the call boundary.
**Interface surface**: send a message list and get a completion; stream a message list and get tokens incrementally.

### `GeminiProvider` (implements `LLMProvider`)
**Purpose**: Concrete adapter to the Gemini API — the v1 (and initially only) provider.
**Responsibilities**: Translate the internal message format to/from Gemini's API shape; normalize provider-specific errors into a common error type so upstream code doesn't branch on provider.

### `InstrumentedProvider` (Decorator, implements `LLMProvider`)
**Purpose**: The auto-instrumentation boundary — wraps any `LLMProvider` and captures call metadata transparently, with zero call-site changes (per US-1.2, confirmed via Q2 of Application Design).
**Responsibilities**: Measure latency (including time-to-first-token for streams), count input/output tokens, capture request status/errors, and publish a `LogEvent` to the `EventQueue` once a call or stream completes (success or failure) — without altering the response passed through to the caller.

## Event/Queue Layer

### `EventQueue` (interface)
**Purpose**: Strategy interface abstracting the log-event broker, decoupled from any specific implementation (per US-3.3).
**Responsibilities**: Define a non-blocking publish contract and a consume contract, with no assumption baked in about in-process vs. distributed delivery.

### `InProcessEventQueue` (implements `EventQueue`)
**Purpose**: v1 concrete implementation, backed by an in-memory async queue.
**Responsibilities**: Bounded queue with backpressure awareness. Documented as the extension point for a future `RedisStreamsEventQueue` implementation — that implementation is out of scope for v1.

## Chat Layer

### `ChatService`
**Purpose**: Owns both LLM call orchestration and conversation lifecycle management (single service, per Q3 of Application Design).
**Responsibilities**: Start/continue conversations; truncate context when the window is exceeded; call the `InstrumentedProvider`; stream tokens to the API layer; persist resulting messages; manage conversation lifecycle state (active → cancelled, active → resumed — a State-pattern transition); handle the cancel signal by stopping the in-flight provider call, not just the client stream.

### `ConversationRepository`
**Purpose**: Persistence boundary for conversation records (including lifecycle state).
**Responsibilities**: User-scoped CRUD; enforces that queries are always scoped to the owning user (the isolation guarantee behind US-5.4).

### `MessageRepository`
**Purpose**: Persistence boundary for chat messages.
**Responsibilities**: Synchronous writes as part of the chat request/response flow (confirmed in Q4) — messages must be immediately queryable for resume.

## Ingestion Layer

### `PayloadValidator`
**Purpose**: First pipeline stage — validates the shape/schema of a raw `LogEvent` consumed from the queue.

### `MetadataExtractor`
**Purpose**: Second pipeline stage — derives/normalizes structured fields (model, provider, token counts, timestamps, status) from the raw event.

### `PIIRedactor`
**Purpose**: Third pipeline stage — regex + configurable denylist redaction of input/output previews (per US-3.2), applied before persistence.

### `LogPersister`
**Purpose**: Final pipeline stage — writes the validated, extracted, redacted record to the `LogRepository`.

### `LogRepository`
**Purpose**: Persistence boundary for inference logs and their extracted metadata.

### `IngestionWorker`
**Purpose**: Background consumer that drains the `EventQueue` and runs each event through the four pipeline stages in sequence (Chain of Responsibility — per Q1 of Application Design, each stage is an independently testable component).
**Responsibilities**: Consume loop; invoke stages in order; a single event's stage failure does not crash the worker loop or block subsequent events.

## Auth Layer

### `AuthService`
**Purpose**: Session-based authentication (per Q5 of Application Design).
**Responsibilities**: Verify seeded demo-user credentials on login; create and validate server-side sessions; expose the current-user context to the API layer for scoping every downstream query.

### `UserRepository`
**Purpose**: Persistence boundary for seeded demo users and server-side session records.

## Analytics Layer

### `AnalyticsService`
**Purpose**: Computes dashboard metrics (per US-4.1).
**Responsibilities**: Time-bucketed queries against `LogRepository` for p50/p95 latency, throughput, and error rate — computed on read, not as a maintained running aggregate.

## API Layer (FastAPI routers)

### `ChatRouter`, `ConversationRouter`, `DashboardRouter`, `AuthRouter`
**Purpose**: HTTP/SSE boundary between the frontend and the service layer.
**Responsibilities**: Request validation, auth enforcement (via `AuthService`), delegate to the relevant service, translate results to HTTP responses or SSE streams.

## Frontend

### React SPA
**Purpose**: User-facing UI (per Q2 of Requirements Analysis — single SPA serving both chat and dashboard).
**Responsibilities**: Chat view (streaming display, cancel action), conversation list/resume view, dashboard view, login view.
