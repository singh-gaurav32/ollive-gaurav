# Ollive — LLM Inference Logging & Ingestion System

A chatbot with an auto-instrumented logging layer: every LLM call is captured, validated, PII-redacted, and persisted through an event-driven ingestion pipeline, with an observability dashboard (latency/throughput/error-rate) built on top. See [`docs/architecture-notes.md`](docs/architecture-notes.md) for the ingestion flow, logging strategy, scaling considerations, and failure handling assumptions in detail.

**Live demo**: https://gaurav-ollive.duckdns.org (seeded demo users, no password — see below)

**Architecture & design decisions, in the app**: https://gaurav-ollive.duckdns.org/about (no login required)

## Getting Started (Backend)

Requires [uv](https://docs.astral.sh/uv/), Python 3.12, and Docker (for Postgres).

**Via `make`** (see `make help` for the full list):

```bash
cp .env.example .env        # fill in GEMINI_API_KEY
make up                     # start Postgres only
make install                # uv sync
make migrate                # alembic upgrade head
make test                   # run the test suite (real-Postgres tests skipped)
make test-db                # also run the real-Postgres integration tests
make up-all                 # build + start the full stack (Postgres + API)
make run                    # or run the API locally, outside Docker, with --reload
```

**Equivalent commands, without `make`:**

```bash
docker compose up -d postgres
cd backend && uv sync
DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive uv run alembic upgrade head
uv run pytest -v
RUN_DB_TESTS=1 DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive uv run pytest tests/db/test_sqlalchemy_repositories.py -v

# Full stack:
GEMINI_API_KEY=your-key-here docker compose up -d --build
curl http://localhost:8000/health

# Or the API locally, outside Docker:
DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive GEMINI_API_KEY=your-key-here uv run uvicorn main:app --reload --app-dir src
```

Environment variables — root `.env` (for `docker compose`, see `.env.example`) and `backend/.env` (for running `uv` commands locally, see `backend/.env.example`); neither is committed:

```
DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive
GEMINI_API_KEY=your-key-here
GEMINI_MAX_OUTPUT_TOKENS=2048   # optional, caps worst-case response length/cost; this is the default

# Multi-provider (optional) - defaults to gemini if unset:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-key-here
# LLM_MAX_OUTPUT_TOKENS=2048    # applies to whichever provider is active
```

## Getting Started (Frontend)

Requires Node 20+.

```bash
cd frontend
cp .env.example .env    # VITE_API_BASE_URL, defaults to http://localhost:8000
npm install
npm run dev              # http://localhost:5173
npm run test              # Vitest + React Testing Library
```

The backend must be running (see above) with `ALLOWED_ORIGINS` including `http://localhost:5173` (the default) for the frontend to reach it — CORS, not a dev proxy, is used, since the same setup needs to keep working once frontend and backend are genuinely different origins (as in the k3s deployment, before nginx unifies them behind one proxy).

On first run, log in as one of the seeded demo users (`alice`, `bob`, `carol`) — no password.

## Getting Started (Full Stack, One Command)

```bash
cp .env.example .env        # fill in GEMINI_API_KEY
docker compose up -d --build
open http://localhost:8080  # frontend, proxying auth/chat/dashboard calls to the api container
```

`docker compose up` now brings up `postgres`, `api`, and `frontend` together — no separate `npm run dev`, no manual CORS/URL configuration. The frontend is built with `VITE_API_BASE_URL=""`, so its `fetch()` calls are relative and get proxied by nginx (`frontend/nginx.conf`) to the `api` container by name; CORS (`ALLOWED_ORIGINS`) is only needed for the separate `npm run dev` workflow above.

## High-Level Design

System-level view: major subsystems, external dependencies, and how data flows between them. Same diagram, rendered, at [/about](https://gaurav-ollive.duckdns.org/about) in the live app — source at [`docs/diagrams/hld.mmd`](docs/diagrams/hld.mmd).

```mermaid
flowchart TB
    Browser["Browser<br/>React SPA"]

    subgraph Backend["FastAPI Backend — single process"]
        AuthMod["auth<br/>session-based, seeded demo users"]
        ChatMod["chat<br/>conversation lifecycle,<br/>streaming + cancel"]
        ProviderMod["provider<br/>LLMProvider interface<br/>+ InstrumentedProvider decorator"]
        EventsMod["events<br/>in-process async queue"]
        IngestionMod["ingestion<br/>validate → extract → redact → persist"]
        DashboardMod["api: dashboard router<br/>/metrics aggregation"]
    end

    LLM["External LLM API<br/>Gemini / OpenAI"]
    DB[("PostgreSQL")]

    Browser -- "session cookie" --> AuthMod
    Browser -- "chat requests (SSE stream)" --> ChatMod
    Browser -- "metrics queries" --> DashboardMod

    ChatMod --> ProviderMod
    ProviderMod -- "LLM API call" --> LLM
    ProviderMod -. "auto-captured LogEvent,<br/>never blocks the chat call" .-> EventsMod
    EventsMod --> IngestionMod

    ChatMod -- "conversations, messages" --> DB
    IngestionMod -- "logs, failed_log_events" --> DB
    DashboardMod -- "query_window()" --> DB
```

Frontend (`frontend/`) is a Vite/React SPA: login, chat with streaming responses and mid-stream cancel, conversation list/resume, and the observability dashboard. Deployment (`docker-compose.yml` / `k8s/`) packages `postgres`, `api` (worker runs in-process inside it, not a separate service), and `frontend` (its own nginx container that also reverse-proxies API calls) — the same three-service shape locally and on the live k3s deployment.

See [`docs/architecture-notes.md`](docs/architecture-notes.md) for the ingestion flow, logging strategy, scaling considerations, and failure handling assumptions.

## Low-Level Design

Two components carry the interesting design decisions in this system; the rest is a predictable, repetitive pattern (interface + one implementation) that's more useful to browse in the actual directory tree than to diagram class-by-class. Same diagrams, rendered, at [/about](https://gaurav-ollive.duckdns.org/about) — sources at [`docs/diagrams/lld-provider.mmd`](docs/diagrams/lld-provider.mmd) and [`docs/diagrams/lld-ingestion.mmd`](docs/diagrams/lld-ingestion.mmd).

**LLM provider — Strategy + Decorator**

```mermaid
classDiagram
    class LLMProvider {
        <<interface>>
        +send(messages) ProviderResponse
        +stream(messages) AsyncIterator~Token~
    }
    class GeminiProvider {
        +send(messages) ProviderResponse
        +stream(messages) AsyncIterator~Token~
    }
    class OpenAIProvider {
        +send(messages) ProviderResponse
        +stream(messages) AsyncIterator~Token~
    }
    class InstrumentedProvider {
        -wrapped: LLMProvider
        -event_queue: EventQueue
        +send(messages) ProviderResponse
        +stream(messages) AsyncIterator~Token~
    }
    class EventQueue {
        <<interface>>
        +publish(event)
    }

    LLMProvider <|.. GeminiProvider : Strategy
    LLMProvider <|.. OpenAIProvider : Strategy
    LLMProvider <|.. InstrumentedProvider : also implements LLMProvider
    InstrumentedProvider o-- LLMProvider : wraps (Decorator)
    InstrumentedProvider ..> EventQueue : publishes a LogEvent\nper call, never blocks

    note for LLMProvider "Selected at runtime by a small factory\nreading LLM_PROVIDER (deps.py) - ChatService\nonly ever depends on this interface, never\non a concrete provider."
    note for InstrumentedProvider "The single interception point for observability -\nno logging call exists anywhere else in the codebase.\nInstrumentation failures are swallowed here;\nprovider failures are always re-raised."
```

**Ingestion pipeline**

```mermaid
classDiagram
    class EventQueue {
        <<interface>>
        +consume() AsyncIterator~LogEvent~
    }
    class IngestionWorker {
        -_queue: EventQueue
        -_validator: PayloadValidator
        -_extractor: MetadataExtractor
        -_redactor: PIIRedactor
        -_persister: LogPersister
        -_failed_repo: FailedLogEventRepository
        +run()
        -_process(event)
    }
    class PayloadValidator {
        +validate(event) LogEvent
    }
    class MetadataExtractor {
        +extract(event) LogEvent
    }
    class PIIRedactor {
        +redact(event) LogEvent
    }
    class LogPersister {
        +persist(event)
    }
    class LogRepository {
        <<interface>>
    }
    class FailedLogEventRepository {
        <<interface>>
        +insert(record)
    }

    EventQueue --> IngestionWorker : consume()
    IngestionWorker --> PayloadValidator : 1. validate
    IngestionWorker --> MetadataExtractor : 2. extract
    IngestionWorker --> PIIRedactor : 3. redact
    IngestionWorker --> LogPersister : 4. persist
    LogPersister ..> LogRepository : maps to LogRecord
    IngestionWorker ..> FailedLogEventRepository : on any stage failure -\ndead-letter, no preview\ntext ever included

    note for IngestionWorker "One failure never stops the loop (BR5): each event\ngets its own try/except across all 4 stages. The\nredaction guarantee is structural - no code path\nwrites preview text to storage before PIIRedactor runs,\nsuccess or failure."
```

**Everything else, by directory:**

```
backend/src/
  auth/        session-based auth, seeded demo users
  chat/        ChatService - conversation lifecycle, streaming + cancel
  provider/    LLMProvider, GeminiProvider/OpenAIProvider, InstrumentedProvider (see above)
  events/      EventQueue interface + InProcessEventQueue
  ingestion/   IngestionWorker + pipeline stages (see above)
  api/         routers (auth, chat, dashboard) + deps.py, the composition root
  db/          repository interfaces + SQLAlchemy implementations + Alembic migrations
  analytics/   thin AnalyticsService delegating to LogRepository

frontend/src/
  api/         fetch wrappers, one file per backend router
  hooks/       React Query hooks + useChatStream (hand-parsed SSE client)
  components/  presentational components
  pages/       route-level composition
  context/     AuthContext
```

## Schema Design

- **`users`** — `id`, `username` (unique), `created_at`. No password column — auth is pick-a-seeded-user for demo purposes (see Tradeoffs).
- **`sessions`** — `id`, `user_id` (FK), `created_at`, indexed on `user_id`. Backs the session cookie; a session row existing and matching the cookie is the entire auth check.
- **`conversations`** — `id`, `user_id` (FK), `state` (`active`/`cancelled`), timestamps, indexed on `user_id` (every list-conversations query filters by user).
- **`messages`** — `id`, `conversation_id` (FK), `role` (`user`/`assistant`), `content`, `created_at`, indexed on `conversation_id`.
- **`logs`** — the inference log table: `model`, `provider`, `latency_ms`, `ttft_ms` (nullable, streaming only), `input_tokens`/`output_tokens` (nullable), `timestamp` (indexed — the dashboard's every query filters/sorts on this), `status` (`success`/`error`/`cancelled`), `error_message`, `conversation_id`, `session_id`, `input_preview`/`output_preview` (post-redaction), `extra` (JSONB catch-all for provider-specific fields, e.g. `finish_reason`).
- **`failed_log_events`** — the dead-letter table: `model`, `provider`, `conversation_id`, `session_id`, `timestamp`, `failure_stage` (which of validate/extract/redact/persist failed), `failure_reason`. Deliberately **no** preview fields — a pipeline failure before redaction completes must never risk persisting unredacted text.

`conversations`/`messages` (the chat data) and `logs`/`failed_log_events` (the observability data) are separate table families joined only loosely by `conversation_id`/`session_id` — a conversation can be fully reconstructed from `messages` alone even if every one of its `logs` rows were deleted, and vice versa. This was a deliberate boundary: chat functionality and observability shouldn't have a hard dependency on each other's schema.

## Tradeoffs

- **In-process event queue, not a real broker** (Redis/Kafka/SQS) — zero extra infrastructure for a demo-scale system, at the cost of events being lost on a process crash and no cross-process fan-out. The `EventQueue` interface boundary already exists to swap this later without touching `IngestionWorker` or `InstrumentedProvider`.
- **Ingestion worker runs in-process inside the API**, not as a separate service/container — one fewer moving part in `docker-compose.yml`/`k8s/`, at the cost of the API and ingestion sharing fate (a worker crash is caught and logged loudly, but the process itself is shared).
- **Window-based context truncation** (last 10 turns, hard cutoff) instead of summarization — simple, predictable token cost, at the cost of the model losing older context outright rather than gracefully.
- **Session-based demo auth, no passwords** — pick-a-seeded-user is enough to demonstrate real per-user data isolation (verified live: a second user sees zero conversations, and direct-URL access to another user's conversation returns a genuine backend `404`, not a UI-level hide) without building credential management that adds no value to what's being evaluated here.
- **pgvector extension provisioned but unused** — infrastructure headroom for a possible future retrieval/RAG feature; no vector-search requirement exists in this scope, so no vector columns exist yet either.
- **Hand-mirrored TypeScript types** (`frontend/src/types.ts`) instead of a codegen step from the backend's Pydantic models — no extra build tooling, at the cost of manual upkeep if a backend field changes.
- **No container registry originally planned, GHCR used in practice** — building directly on the deployment VM seemed simplest for a single-node cluster, but once a GitHub repo was already in play for the code, pushing images to GHCR turned out simpler in practice (images survive VM rebuilds, updates are `rebuild → push → rollout restart` instead of `SSH → rebuild → reimport`).
- **Single-node k3s, no HA** — deliberate: this satisfies "self-hosted k8s" for a demo, not a production SLA. No autoscaling, no multi-replica, no automated Postgres backup beyond what the PVC itself protects against (pod restarts, not VM loss).
- **`max_output_tokens` default of 2048, not a smaller number** — `gemini-3-flash-preview`'s internal "thinking" tokens count against the same budget as visible output; testing against the real API showed a small cap (~20) can be entirely consumed by thinking, leaving no room for actual response text. 2048 leaves real headroom, confirmed live rather than assumed.

## What I'd Improve With More Time

- **`OpenAIProvider` is unit-tested against a mocked client only, not verified against the real OpenAI API** — no chargeable API key was available to run it live the way `GeminiProvider` was (see Tradeoffs). The adapter follows the exact same shape/error-handling as the Gemini one and the interface contract is enforced by `LLMProvider`, but "the code looks right" and "confirmed against the real API" are different claims — this one only has the former.
- **No rate limiting on LLM calls** — `max_output_tokens` now bounds worst-case response length/cost (see Tradeoffs), but nothing stops rapid repeated requests. A provider-level or per-user rate limit would need adding.
- **No visible error toast on a failed chat send** — the app recovers correctly (input stays usable, no crash) but silently; a user has no in-UI signal that their message failed versus is still streaming.
- **No automated Postgres backup** for the live deployment — acceptable for a demo, not for anything meant to persist real data long-term.
- **No drill-down from the dashboard into individual failing requests** — `logs.error_message` captures real detail per row (this is exactly what caught two real Gemini model-deprecation errors during actual deployment), but there's no UI or endpoint to browse it; only the aggregate counts are surfaced.
