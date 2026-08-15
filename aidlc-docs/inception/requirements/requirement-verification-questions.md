# Requirements Clarification Questions

Please answer each question by filling in the letter choice after the `[Answer]:` tag. If none of the options match your needs, choose the last option (Other) and describe your preference. Let me know when you're done.

---

## Question 1: Primary implementation language / stack
The problem statement doesn't mandate a stack. Given the ML-system-design plan leans Python and the HLD syllabus leans toward Go-style concurrency (worker pools, goroutines), which do you want as the backend language for the chatbot API + SDK + ingestion service?

A) Python (FastAPI) — natural fit for LLM SDKs, async support, matches the ml-system-design plan's implied stack

B) Go — matches the HLD syllabus's concurrency vocabulary (worker pools, channels) directly, strong fit for the ingestion pipeline

C) TypeScript/Node — unifies frontend and backend in one language, good streaming (SSE/WebSocket) support

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2: Frontend approach
The bonus asks for a UI supporting cancel/list/resume conversation plus a dashboard.

A) Single React (or similar SPA) app serving both the chat UI and the observability dashboard

B) Two separate small frontends — one minimal chat UI, one separate dashboard app

C) Server-rendered UI (e.g. Next.js/HTMX) instead of a pure SPA

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3: Database
"Sensible schema design" is called out explicitly as something you're graded on.

A) PostgreSQL — relational, good fit for structured logs + JSONB for flexible metadata/raw provider responses

B) PostgreSQL + a vector extension (pgvector) — same as A, kept open in case retrieval-style features get added later

C) A NoSQL document store (MongoDB/DynamoDB) — schema-flexible, fits variable per-provider metadata shapes better

D) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 4: LLM provider(s) to build against first
Multi-provider support is in scope, but the Strategy/Adapter interface still needs at least one concrete provider to design against first.

A) Anthropic Claude only for the first working version, add a second provider once the adapter interface is proven

B) Build two providers from the start (e.g. Anthropic + OpenAI) so the abstraction is forced to be correct immediately

C) Anthropic + a local/open model (e.g. via Ollama) — avoids needing multiple paid API keys

D) Other (please describe after [Answer]: tag below)

[Answer]: one providder gemini for now can be extended later

## Question 5: Streaming transport
For token-by-token streaming responses.

A) Server-Sent Events (SSE) — simpler, one-directional, fits LLM token streaming well, easier to proxy/deploy

B) WebSocket — bidirectional, needed anyway if "cancel conversation" requires a client-to-server signal mid-stream

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 6: Event-based architecture — broker choice
This determines the Docker Compose and k8s manifests later.

A) In-process async queue (e.g. Python asyncio.Queue / Go channel) with a background worker — no extra infra container, still demonstrates the producer-consumer pattern

B) Redis Streams — lightweight external broker, easy to run in Docker Compose and k8s, decouples SDK from ingestion process entirely

C) Kafka — heavier, but the "real" answer for production event-driven log ingestion at scale

D) Other (please describe after [Answer]: tag below)

[Answer]: lets Go with A here first but with a pattern we can switch to B

## Question 7: PII redaction scope
A) Regex/pattern-based redaction for common PII (emails, phone numbers, SSNs, credit card numbers) applied to logged input/output previews

B) Regex-based redaction plus a configurable denylist of field names/patterns per org

C) ML/NER-based redaction (e.g. a lightweight NER model) for broader coverage beyond pattern matching

D) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 8: Multi-user / auth scope
A) Single-user demo — no auth, one implicit user, focus effort on the ingestion/observability system instead

B) Simple session-based auth (e.g. a login with a few seeded demo users) — enough to demonstrate multi-tenant log isolation

C) Other (please describe after [Answer]: tag below)

[Answer]:B

## Question 9: k8s deployment target
A) Local cluster only (kind/minikube) with manifests — demonstrates the deployment story without cloud cost/credentials

B) A real cloud-hosted cluster (EKS/GKE/etc.) for a live demo link

C) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 10: Dashboard update mechanism
A) Poll-based (dashboard re-queries the API every N seconds) — simplest, matches "query at dashboard-load time" approach discussed earlier

B) Live-updating (push via WebSocket/SSE from the aggregation layer) — more impressive, more moving parts

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 11: Delivery pacing
Earlier we discussed building the provider abstraction first since streaming, multi-provider, and auto-instrumentation all hang off it.

A) Confirm: build in dependency order (provider abstraction → spine → pipeline hardening → dashboards → frontend lifecycle → packaging/deploy), one unit at a time, reviewing each before moving on

B) I want to reorder — describe the order you'd prefer after [Answer]: tag below

[Answer]: A

---

## Question: Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question: Resiliency Extensions
Should the resiliency baseline be applied to this project?

**What this extension is.** Enabling it applies a set of directional, design-time best practices for building resilient systems, derived from the AWS Well-Architected Framework (Reliability Pillar). It steers requirements, design, and code toward fault tolerance, high availability, observability, and recoverability.

**What this extension is NOT.** It does not make your workload production-ready or certify any availability/RTO/RPO target. It's a starting point, not a substitute for a formal review.

A) Yes — apply the resiliency baseline as directional best practices and design-time guidance

B) No — skip the resiliency baseline (suitable for PoCs/prototypes)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question: Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components — this project has PII redaction, metadata extraction, and windowed aggregation, all good PBT candidates)

B) Partial — enforce PBT rules only for pure functions and serialization round-trips

C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers)

X) Other (please describe after [Answer]: tag below)

[Answer]: C
