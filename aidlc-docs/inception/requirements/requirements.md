# Requirements — LLM Inference Logging & Ingestion System

## Intent Analysis Summary

- **User Request**: Build a lightweight inference logging and ingestion system for an LLM chatbot application (per `problem-statement.md`), pursuing full bonus coverage (multi-provider support, streaming, dashboards, Docker Compose, event-based architecture, PII redaction, self-hosted k8s deployment, frontend conversation lifecycle controls) for a guaranteed interview.
- **Request Type**: New Project (Greenfield)
- **Scope Estimate**: System-wide — chatbot API, SDK, ingestion pipeline, database, dashboard, deployment packaging all in scope.
- **Complexity Estimate**: Complex — multiple integrated subsystems, concurrency (producer-consumer), external LLM integration, cloud deployment.

## Design Principles to Incorporate

Carried forward from prior discussion mapping this problem to the user's three personal syllabi (`ml-system-design/learning-plan.md`, `system-design/hld/SYLLABUS.md`, `system-design/lld/LLD-SYLLABUS.md`). These are directional design constraints, not features in themselves:

- **Provider abstraction (Strategy/Adapter, LLD)**: One `LLMProvider` interface; the auto-instrumentation SDK wraps this single boundary so every provider call is logged without touching call sites. Built to support multiple providers even though only one is implemented in v1.
- **Producer-consumer concurrency (LLD Logging Service pattern)**: SDK never blocks the chat response on a log write. Logs go through a queue; a background worker persists them.
- **Broker abstraction (Strategy, applied to the event bus)**: The queue is an interface with an in-process implementation now and a documented swap path to Redis Streams later — decided in Q6, not built as a live feature.
- **Conversation lifecycle as a State machine (LLD)**: active → cancelled, active → resumed maps directly to the frontend's cancel/list/resume requirement.
- **Ingestion pipeline as stages (Chain of Responsibility, LLD)**: validate → parse → extract metadata → redact PII → persist.
- **Windowed aggregation (HLD Tier 8)**: latency/throughput/error dashboards computed via time-bucketed queries at dashboard-load time (poll-based, per Q10) rather than maintained as live running aggregates — the simpler, still-correct version of the pattern.
- **Context window management (ml-system-design Project 2)**: short conversational context maintained with truncation when it exceeds the model's window.
- **Multi-tenant isolation (ml-system-design Project 5, applied to logs/conversations instead of RAG documents)**: session-based auth means conversation and log data must be scoped per user, provably isolated.

## Functional Requirements

### FR1 — Chatbot Application
- Multi-turn conversation support with short conversational context maintained server-side; truncate older turns when the context window is exceeded.
- LLM provider: Gemini for v1 (Q4), behind a provider-agnostic interface designed to add more providers later.
- Streaming token-by-token responses via SSE (Q5).
- Cancel an in-flight conversation: client aborts the SSE request; server detects the disconnect and stops calling the provider (not just stops streaming to a dead connection).
- List a user's conversations; resume a previously parked conversation.
- React SPA UI serving both the chat interface and the observability dashboard (Q2).
- Session-based auth with multiple seeded demo users, sufficient to demonstrate per-user data isolation (Q8).

### FR2 — SDK / Auto-Instrumentation Wrapper
- Wraps the provider adapter interface as the single interception point — no manual logging calls at chat call sites.
- Captures per call: model, provider, latency, token usage (input/output), timestamps, request status/errors, conversation/session ID, input/output previews (post-redaction).
- Publishes captured events to an in-process async queue; does not block the caller.

### FR3 — Ingestion Pipeline
- Background worker consumes from the queue (producer-consumer, decoupled from the request path).
- Pipeline stages: validate/parse payload → extract metadata → redact PII → persist.
- PII redaction: regex-based detection (emails, phone numbers, SSNs, credit card numbers) plus a configurable denylist of field names/patterns (Q7), applied to input/output previews before they're persisted.
- Queue/worker built behind an interface so the in-process implementation can be swapped for Redis Streams without changing producer (SDK) code (Q6).

### FR4 — Database Storage
- PostgreSQL with the pgvector extension provisioned (Q3) — pgvector is infrastructure headroom for possible future retrieval features; no vector-search functional requirement exists in this scope.
- Store: chat messages, inference logs (latency/tokens/status/timestamps), extracted+redacted metadata, conversation records with lifecycle state (active/cancelled/resumed), user/session records.
- Schema design and normalization tradeoffs must be documented in the README, including what's stored as structured columns vs. JSONB for provider-variable metadata.

### FR5 — Observability Dashboard
- Latency (p50/p95), throughput, and error-rate views.
- Poll-based updates — dashboard queries the API on load/interval; no live push (Q10).
- Computed via time-bucketed aggregation queries against stored logs (compute-on-read, not a maintained running aggregate).

### FR6 — Packaging & Deployment
- Docker Compose one-command setup for local development (API, worker, frontend, Postgres).
- Kubernetes manifests targeting a real cloud-hosted cluster for a live demo link (Q9) — specific cloud provider to be selected during Infrastructure Design.

## Non-Functional Requirements

- **Latency**: Async logging must not add perceptible latency to the chat response path (queue publish is non-blocking).
- **Isolation**: A user must never be able to list, resume, or view logs for another user's conversations.
- **Extensibility**: Adding a second LLM provider or swapping the queue broker must not require changes to SDK call sites or ingestion pipeline stages — only a new adapter/implementation behind the existing interfaces.
- **Documentation**: README must cover setup, architecture overview, schema design decisions, tradeoffs made, and what would be improved with more time, per the problem statement's deliverables. Architecture Notes must separately cover ingestion flow, logging strategy, scaling considerations, and failure handling assumptions.

## Extension Configuration (decided this stage)

| Extension | Enabled | Rationale |
|---|---|---|
| Security Baseline | No | User opted out (Q: Security Extensions = B). Security is still addressed as functional requirements (session auth, PII redaction) but not gated by the formal blocking rule set. Noted as a deliberate scope trade-off given this system also targets a real cloud cluster. |
| Resiliency Baseline | No | User opted out (Q: Resiliency Extensions = B). Failure handling will be documented pragmatically per the problem statement's own "failure handling assumptions" deliverable, not driven by the formal AWS Well-Architected checklist. |
| Property-Based Testing | No | User opted out (Q: PBT = C). Standard unit/integration tests will cover redaction, metadata extraction, and aggregation logic instead. |

## Explicitly Out of Scope (v1)

- Additional LLM providers beyond Gemini (interface supports it; not implemented unless time permits).
- Any retrieval/RAG functionality using pgvector — extension is provisioned, not used as a feature.
- ML/NER-based PII detection — regex + denylist only.
- Live-push dashboard updates — poll-based only.
- Kafka or other heavyweight brokers — in-process queue with a swap-ready interface only.

## Delivery Sequencing (confirmed, Q11)

Build in dependency order, one unit reviewed before the next starts:
1. Provider abstraction (Strategy/Adapter) + SDK auto-instrumentation hook
2. Chatbot spine (streaming chat + memory/context truncation + DB persistence)
3. Ingestion pipeline hardening (async queue, PII redaction, event-based swap-readiness)
4. Observability dashboard (windowed aggregation, poll-based)
5. Frontend conversation lifecycle (cancel/list/resume) + auth/isolation
6. Packaging & deployment (Docker Compose, k8s manifests)

## Open Item Carried Forward

- **Cloud provider for k8s target** (Q9): not yet selected. Will be resolved during Infrastructure Design for the packaging/deployment unit, not blocking earlier units.
