# User Stories

Organized by epic, matching the confirmed delivery sequence. Each story is INVEST-compliant (Independent, Negotiable, Valuable, Estimable, Small, Testable) and traces back to a requirement in `requirements.md`.

---

## Epic 1: Provider Abstraction & Auto-Instrumentation

### US-1.1 — Pluggable LLM provider interface
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want the chatbot's LLM calls to go through a single pluggable provider interface, so that adding a new provider later requires no changes to the SDK, ingestion pipeline, or call sites.

**Acceptance Criteria**:
- [ ] A provider interface exists with methods for sending a message and streaming a response
- [ ] Gemini is implemented as one concrete provider behind this interface
- [ ] No chat-handling or logging code references the Gemini SDK directly outside the adapter
- [ ] A second (stub/mock) provider can be added and pass the same interface contract tests

### US-1.2 — Auto-instrumented call logging
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want every LLM call to be automatically logged without any manual logging code at the call site, so that instrumentation can't be forgotten as new call sites are added.

**Acceptance Criteria**:
- [ ] Wrapping the provider interface captures model, provider, latency, token usage, timestamps, status/error, conversation/session ID, and input/output previews for every call
- [ ] A new call site that uses the provider interface is logged automatically, with no additional code
- [ ] Failed/errored provider calls are captured with status and error detail, not silently dropped

---

## Epic 2: Chatbot Spine (Streaming Chat + Memory)

### US-2.1 — Start and continue a multi-turn conversation
**Persona**: Chat User
**Story**: As a Chat User, I want to have a multi-turn conversation with the chatbot, so that I can ask follow-up questions with the assistant remembering earlier context.

**Acceptance Criteria**:
- [ ] A new conversation can be started
- [ ] Follow-up messages in the same conversation receive responses that account for prior turns
- [ ] Conversation and message history persist to the database

### US-2.2 — Receive streamed responses
**Persona**: Chat User
**Story**: As a Chat User, I want to see the assistant's response appear token-by-token as it's generated, so that I get immediate feedback instead of waiting for the full response.

**Acceptance Criteria**:
- [ ] Response tokens appear incrementally in the UI via SSE as they're generated
- [ ] The UI clearly indicates when streaming is complete
- [ ] A network interruption during streaming is surfaced to the user, not silently swallowed

### US-2.3 — Long conversations stay usable
**Persona**: Chat User
**Story**: As a Chat User, I want the assistant to keep responding sensibly even in a long conversation, so that I don't hit an error or a nonsensical answer once the conversation gets long.

**Acceptance Criteria**:
- [ ] When conversation history exceeds the model's context window, older turns are truncated (or summarized) before the next call
- [ ] The user is never shown a raw context-length error from the provider
- [ ] The truncation strategy is documented (which turns are dropped/summarized, and why)

---

## Epic 3: Ingestion Pipeline Hardening

### US-3.1 — Non-blocking log ingestion
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want inference logs captured without adding latency to the user's chat response, so that observability never degrades the product experience.

**Acceptance Criteria**:
- [ ] Publishing a log event to the queue does not block the chat response path
- [ ] A slow or temporarily unavailable ingestion worker does not cause the chat request to fail or hang
- [ ] Log events are still persisted (not silently dropped) under normal operation

### US-3.2 — PII redaction before storage
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want input/output previews redacted of common PII before they're persisted, so that raw PII never lands in the database.

**Acceptance Criteria**:
- [ ] Emails, phone numbers, SSNs, and credit card numbers are redacted from stored previews via regex-based detection
- [ ] A configurable denylist of additional field names/patterns can also be redacted
- [ ] Redaction happens before the persist step — raw PII is never written, even transiently, to durable storage
- [ ] A redaction test suite covers each supported PII pattern

### US-3.3 — Swappable event broker
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want the log event queue to sit behind a swappable interface, so that I can move from an in-process queue to Redis Streams later without changing SDK or worker code.

**Acceptance Criteria**:
- [ ] The SDK publishes events through a queue interface, not a concrete implementation
- [ ] The in-process implementation satisfies that interface
- [ ] The interface is documented as the extension point for a future Redis Streams implementation (that implementation itself is out of scope for v1)

---

## Epic 4: Observability Dashboard

### US-4.1 — View latency, throughput, and error metrics
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want a dashboard showing latency (p50/p95), throughput, and error rate over time, so that I can assess system health at a glance.

**Acceptance Criteria**:
- [ ] Dashboard displays p50/p95 latency, requests per time window, and error rate, bucketed by time window
- [ ] Metrics reflect real logged inference calls, not mocked data
- [ ] Dashboard refreshes on a poll interval (no live push required)
- [ ] Metrics are computed from stored logs at query time, not a separately maintained running aggregate

---

## Epic 5: Frontend Conversation Lifecycle + Auth/Isolation

### US-5.1 — Cancel an in-flight conversation
**Persona**: Chat User
**Story**: As a Chat User, I want to cancel a response while it's still generating, so that I'm not stuck waiting for an answer I no longer want.

**Acceptance Criteria**:
- [ ] A cancel action is available while a response is streaming
- [ ] Cancelling stops new tokens from appearing in the UI immediately
- [ ] Cancelling also stops the server from continuing to call the LLM provider — not just from streaming to the client
- [ ] The partial response up to the cancel point is saved to conversation history

### US-5.2 — List my conversations
**Persona**: Chat User
**Story**: As a Chat User, I want to see a list of my past conversations, so that I can find and return to one.

**Acceptance Criteria**:
- [ ] The list shows only conversations belonging to the logged-in user
- [ ] Each entry shows enough context to identify it (e.g. first message or a title, last-updated time)

### US-5.3 — Resume a conversation
**Persona**: Chat User
**Story**: As a Chat User, I want to resume a previous conversation, so that I can continue where I left off with full context intact.

**Acceptance Criteria**:
- [ ] Selecting a past conversation loads its full message history
- [ ] A new message sent after resuming receives a response that accounts for the resumed conversation's prior context
- [ ] Resuming a previously-cancelled conversation works the same way as resuming any other

### US-5.4 — My data stays mine
**Persona**: Chat User
**Story**: As a Chat User, I want assurance that no other user can see my conversations or logs, so that I can trust the system with what I ask it.

**Acceptance Criteria**:
- [ ] Attempting to access another user's conversation by ID (e.g. a guessed/modified URL) is rejected
- [ ] The Operator/Analyst dashboard shows aggregated metrics only, never another user's raw conversation content
- [ ] Session auth is required to access any chat or conversation-list endpoint

---

## Epic 6: Packaging & Deployment

### US-6.1 — One-command local setup
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want to bring up the entire system locally with a single command, so that I can run and demo it without manual multi-step setup.

**Acceptance Criteria**:
- [ ] `docker compose up` (or equivalent single command) starts the API, worker, frontend, and database
- [ ] The chatbot is usable end-to-end immediately after startup, with no extra manual steps beyond providing an API key

### US-6.2 — Deploy to a live cloud environment
**Persona**: Operator/Analyst
**Story**: As an Operator/Analyst, I want the system deployable to a real Kubernetes cluster, so that I can share a live demo link.

**Acceptance Criteria**:
- [ ] Kubernetes manifests exist for all services (API, worker, frontend, database)
- [ ] The deployed system is reachable via a public URL
- [ ] Deployment steps are documented in the README

---

## Persona → Story Map

| Persona | Stories |
|---|---|
| Chat User | US-2.1, US-2.2, US-2.3, US-5.1, US-5.2, US-5.3, US-5.4 |
| Operator/Analyst | US-1.1, US-1.2, US-3.1, US-3.2, US-3.3, US-4.1, US-6.1, US-6.2 |

## Traceability

Every story traces to a functional requirement in `requirements.md` (FR1–FR6). No orphan stories: Epic 1 → provider abstraction principle + FR2; Epic 2 → FR1; Epic 3 → FR2/FR3; Epic 4 → FR5; Epic 5 → FR1 (cancel/list/resume, auth) + isolation NFR; Epic 6 → FR6.
