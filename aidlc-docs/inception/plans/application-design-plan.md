# Application Design Plan

**Input**: `requirements.md`, `stories.md`, `personas.md`

## Execution Checklist

- [x] Confirm pipeline component granularity (see Question 1) — A: separate component per stage
- [x] Confirm auto-instrumentation mechanism (see Question 2) — A: Decorator
- [x] Confirm chat vs. conversation service boundary (see Question 3) — A: single ChatService
- [x] Confirm dual-write pattern for messages vs. logs (see Question 4) — A: confirmed, two distinct paths
- [x] Confirm auth/session mechanism (see Question 5) — A: server-side session store
- [x] Generate `components.md` — component definitions and responsibilities
- [x] Generate `component-methods.md` — method signatures per component
- [x] Generate `services.md` — service definitions and orchestration
- [x] Generate `component-dependency.md` — dependency matrix, communication patterns, data flow
- [x] Generate `application-design.md` — consolidated view of the above
- [x] Validate design completeness against requirements.md and stories.md — every FR and story has a home in some component

## Proposed Component Sketch (for context, not final until questions answered)

Based on requirements.md and the patterns agreed during discussion (Strategy/Adapter for providers, Decorator for the SDK wrapper, Chain of Responsibility for the ingestion pipeline, State for conversation lifecycle, producer-consumer for async logging):

- **Provider Adapter Layer**: `LLMProvider` interface + `GeminiProvider` implementation
- **Instrumentation Wrapper**: wraps the provider interface, captures call metadata, publishes to the event queue
- **Conversation Manager**: conversation CRUD + lifecycle state (active/cancelled/resumed)
- **Chat Orchestration**: coordinates a chat turn — loads conversation, truncates context, calls the (wrapped) provider, streams tokens back, persists the resulting message
- **Event Queue**: interface + in-process implementation, swappable for Redis Streams later
- **Ingestion Worker**: consumes the queue; runs validate → parse → extract metadata → redact PII → persist as pipeline stages
- **PII Redactor**: regex + denylist redaction, used by the ingestion worker
- **Log Repository / Message Repository / Conversation Repository**: persistence boundaries per entity
- **Auth Service**: session-based auth, per-user scoping
- **Analytics Service**: windowed aggregation queries over logs for the dashboard
- **API Layer**: FastAPI routers exposing chat, conversation, dashboard, and auth endpoints
- **Frontend**: React SPA — chat view, conversation list/resume, dashboard view, login

---

## Question 1: Pipeline component granularity
The ingestion pipeline (validate → parse → extract metadata → redact PII → persist) is a Chain-of-Responsibility-style sequence.

A) Separate component per stage (e.g. `PayloadValidator`, `MetadataExtractor`, `PIIRedactor`, `LogPersister`), each independently testable and swappable — more files, cleanest separation

B) One `IngestionPipeline` component with the stages as private internal methods/steps — fewer moving parts, still testable via the pipeline's public entry point

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2: Auto-instrumentation mechanism
How should the SDK "wrap" provider calls to capture metadata without call-site changes?

A) Decorator class — `InstrumentedProvider` wraps any `LLMProvider` implementation, implements the same interface, and every method call passes through it transparently

B) Python context manager / middleware injected at the orchestration layer — Chat Orchestration explicitly enters an instrumentation context around each provider call

C) Other (please describe after [Answer]: tag below)

[Answer]: A — Decorator. Delivers the actual "auto-instrument, no call-site changes" requirement from US-1.2; the context-manager alternative reintroduces the risk of a forgotten wrap at a future call site.

## Question 3: Chat vs. Conversation service boundary
A) Single `ChatService` owns both the LLM call orchestration (streaming, context truncation) AND conversation state/lifecycle (list, resume, cancel, active/cancelled state transitions)

B) Split into two services — `ChatOrchestrationService` (the LLM call flow only) and `ConversationService` (CRUD + lifecycle state), with ChatOrchestrationService depending on ConversationService for context loading

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: Dual-write pattern — messages vs. logs
Chat messages need to be immediately queryable (for list/resume), while inference logs are explicitly async/non-blocking per US-3.1.

A) Confirm: chat messages are written synchronously as part of the chat request/response flow (needed immediately for resume); inference logs go through the async event queue separately — these are two distinct write paths, not one

B) Something else — describe after [Answer]: tag below

[Answer]: A

## Question 5: Auth/session mechanism
A) Server-side session store (session ID in an httpOnly cookie, session data kept server-side, e.g. in Postgres or in-memory) — simplest to reason about for a demo with a few seeded users

B) JWT stored in a cookie — stateless, more typical of production systems, slightly more moving parts (signing/verification) for a demo that doesn't need statelessness

C) Other (please describe after [Answer]: tag below)

[Answer]: A
