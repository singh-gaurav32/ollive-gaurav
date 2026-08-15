# Units of Work

Six units, 1:1 with the story epics in `stories.md` (per Q3), built in the confirmed delivery sequence. All backend units run as **one Python process** (Q1) — `IngestionWorker` is a background asyncio task inside the same FastAPI app, not a separate service. The full frontend is built as **one unit, last** (Q2), covering the UI for every earlier unit's stories, not just its own.

**Code organization**: superseded by `project-structure.md`, written after Unit 1 revealed that a naive one-package-per-unit split (what Q4 originally specified) misplaces anything shared *between* units — `EventQueue` and the repositories are the concrete examples. `project-structure.md` adds two shared packages (`db/`, `events/`) alongside the per-unit ones below; see `shared-contracts.md` for every interface defined in them.

**Cross-cutting schema decision**: `user_id` scoping is designed into the `conversations`, `messages`, and `logs` tables starting in **Unit 2**, even though real login/session auth doesn't arrive until Unit 5. A single seeded demo user is used as a stand-in until then. This avoids a schema migration later — multi-user scoping is a day-one column, not a bolt-on.

---

## Unit 1: Provider Abstraction & Auto-Instrumentation

**Goal**: The pluggable LLM provider interface and the auto-instrumentation boundary — the foundation everything else depends on.

**Stories**: US-1.1, US-1.2

**Components**: `LLMProvider` (interface), `GeminiProvider`, `InstrumentedProvider`, `EventQueue` (interface only — implementation is Unit 3), a stub/no-op queue for Unit 1's own testing.

**Code location**: `backend/src/provider/`

**Verification**: Testable standalone via unit tests — no chat flow, no DB, no UI needed. A test double for `EventQueue` confirms `InstrumentedProvider` publishes on every call/stream/error.

---

## Unit 2: Chatbot Spine (Streaming Chat + Memory)

**Goal**: Multi-turn conversation with streaming responses and context truncation, backed by real persistence.

**Stories**: US-2.1, US-2.2, US-2.3

**Components**: `ChatService`, `ConversationRepository`, `MessageRepository`, database schema for `users` (seeded stub), `conversations`, `messages`.

**Code location**: `backend/src/chat/`, plus initial `backend/src/api/chat_router.py` exposing endpoints for manual/curl-based verification (no frontend yet, per Q2).

**Verification**: Streaming and truncation are verified via a raw SSE client (curl `--no-buffer` or a small script) — the full chat UI arrives in Unit 5.

**Depends on**: Unit 1 (`InstrumentedProvider` as the call boundary).

---

## Unit 3: Ingestion Pipeline Hardening

**Goal**: The async, non-blocking log path — queue, pipeline stages, PII redaction.

**Stories**: US-3.1, US-3.2, US-3.3

**Components**: `InProcessEventQueue` (concrete `EventQueue` implementation), `IngestionWorker` (background asyncio task), `PayloadValidator`, `MetadataExtractor`, `PIIRedactor`, `LogPersister`, `LogRepository`, database schema for `logs`.

**Code location**: `backend/src/ingestion/`

**Verification**: Integration test driving a chat call from Unit 2 and asserting a redacted log record lands in `logs` without adding latency to the chat response. Redis Streams swap remains a documented extension point only (per the deferred-scope decision) — not implemented or tested in this unit.

**Depends on**: Unit 1 (events originate in `InstrumentedProvider`), Unit 2 (needs a real chat call to generate an event end-to-end).

---

## Unit 4: Observability Dashboard (backend)

**Goal**: Windowed aggregation queries over the logs produced by Unit 3.

**Stories**: US-4.1

**Components**: `AnalyticsService`, `backend/src/api/dashboard_router.py`.

**Code location**: `backend/src/analytics/`

**Verification**: Query endpoints tested directly (curl/Postman) against seeded log data — the dashboard UI itself arrives in Unit 5.

**Depends on**: Unit 3 (needs real log data to query against).

---

## Unit 5: Frontend Application + Auth/Isolation

**Goal**: The entire React SPA (chat, dashboard, conversation list/resume/cancel, login) plus the real `AuthService`, replacing Unit 2's seeded stub user with real session-based multi-user auth.

**Stories**: US-5.1, US-5.2, US-5.3, US-5.4 — **plus the frontend/UI completion of** US-2.1, US-2.2, US-2.3 (chat UI), and US-4.1 (dashboard UI), whose backends were built in earlier units.

**Components**: `AuthService`, `UserRepository`, `backend/src/api/auth_router.py`, `backend/src/api/conversation_router.py` (list/resume/cancel endpoints), and the full `frontend/` React app.

**Code location**: `backend/src/auth/`, `frontend/src/`

**Verification**: End-to-end, in-browser — this is the first unit demoable as a normal user, not via curl.

**Depends on**: Units 1-4 (wraps a UI and real auth around everything they built).

---

## Unit 6: Packaging & Deployment

**Goal**: One-command local setup and a real cloud k8s deployment for a live demo.

**Stories**: US-6.1, US-6.2

**Components**: `docker-compose.yml`, Kubernetes manifests, README deployment instructions.

**Code location**: repo root, `k8s/`

**Verification**: `docker compose up` brings up a fully working system from a clean clone; the k8s deployment is reachable at a public URL.

**Depends on**: Units 1-5 (packages the complete system).
