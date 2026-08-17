# Ollive — LLM Inference Logging & Ingestion System

A chatbot with an auto-instrumented logging layer: every LLM call is captured, validated, PII-redacted, and persisted through an event-driven ingestion pipeline, with an observability dashboard (latency/throughput/error-rate) built on top. See [`docs/architecture-notes.md`](docs/architecture-notes.md) for the ingestion flow, logging strategy, scaling considerations, and failure handling assumptions in detail.

**Live demo**: https://gaurav-ollive.duckdns.org (seeded demo users, no password — see below)

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

## Deployment (Cloud — k3s on Oracle Cloud)

Steps to take a clean Oracle Cloud account to a live, public HTTPS URL (this is exactly how the live demo above is running):

**1. Provision the VM** (OCI Console → Compute → Instances → Create):
- Shape: **Ampere A1 Flex**, 4 OCPU / 24GB RAM (the full Always Free allocation)
- Image: **Ubuntu 22.04 (ARM/aarch64)**
- Boot volume: 50GB
- Region: whichever you signed up under (e.g. `ap-mumbai-1`) — if you hit "out of host capacity", that's a known Always-Free ARM constraint; retry later or fall back to a cheap Hetzner/DigitalOcean VPS running the same steps below
- Attach your SSH key during creation

**2. Reserve a static public IP** (Networking → IP Management → Reserved Public IPs → Create, then attach it to the VM's VNIC in place of the ephemeral one) — this is what makes the DuckDNS hostname stable.

**3. Open the firewall**: in the VM's subnet Security List (or a Network Security Group), allow inbound TCP 80, 443, and 22 only.

**4. Point DNS at it**: sign up at [duckdns.org](https://www.duckdns.org), create a subdomain, set its IP to the reserved static IP from step 2.

**5. SSH in and install k3s**:
```bash
curl -sfL https://get.k3s.io | sh -
```
This also installs Traefik (ingress) and the `local-path` storage class — no separate install needed for either.

**6. Install cert-manager**:
```bash
sudo k3s kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
sudo k3s kubectl -n cert-manager rollout status deploy/cert-manager
```

**7. Build and push the images to a registry** (GHCR — GitHub Container Registry. Note: cross-compiling `linux/amd64` images from an Apple Silicon Mac needs `buildx`+QEMU set up; if that's not available, build directly on the target VM instead — same commands, just run there):
```bash
docker login ghcr.io -u <your-github-username>   # run this yourself, don't paste tokens into a shared session
docker build -t ghcr.io/<your-github-username>/ollive-api:latest ./backend
docker push ghcr.io/<your-github-username>/ollive-api:latest
docker build -t ghcr.io/<your-github-username>/ollive-frontend:latest --build-arg VITE_API_BASE_URL="" ./frontend
docker push ghcr.io/<your-github-username>/ollive-frontend:latest
```
First push only: GHCR packages default to private — go to your GitHub profile → **Packages** → each package → **Package settings → Change visibility → Public**, so the VM can pull without an `imagePullSecret`. Then, on the VM, just clone the repo (no build needed there):
```bash
git clone <your-repo-url> && cd ollive-gaurav
```

**8. Fill in secrets and confirm the hostname/registry references**:
```bash
cp k8s/secrets.yaml.example k8s/secrets.yaml   # edit with real values, this file is git-ignored
# k8s/ingress.yaml, k8s/cluster-issuer.yaml, and the image: fields in k8s/api-deployment.yaml /
# k8s/frontend-deployment.yaml already point at the real hostname/registry if you're using this repo as-is;
# double-check they match your own GHCR username/DuckDNS host if you forked/renamed anything
```

**9. Apply the manifests**:
```bash
sudo k3s kubectl apply -f k8s/namespace.yaml
sudo k3s kubectl apply -f k8s/
```

**10. Verify**:
```bash
sudo k3s kubectl -n ollive get pods
sudo k3s kubectl -n ollive get certificate   # wait for READY=True (Let's Encrypt issuance)
```
Then visit `https://YOUR-SUBDOMAIN.duckdns.org`.

**Updating after changes**: repeat step 7's build/push for whichever image changed, then `sudo k3s kubectl -n ollive rollout restart deployment/api` (or `deployment/frontend`). No CI/CD — this is a manual, single-VM demo deployment by design.

## Architecture Overview

```
Browser (React SPA)
   |  session cookie auth
   v
FastAPI backend
   |-- auth/         session-based auth, seeded demo users, no passwords
   |-- chat/         conversation lifecycle, context truncation, streaming + cancel
   |-- provider/     LLMProvider interface -> GeminiProvider, wrapped by
   |                 InstrumentedProvider (auto-captures a LogEvent per call,
   |                 zero manual logging calls elsewhere)
   |-- events/       in-process async queue (InProcessEventQueue)
   |-- ingestion/    IngestionWorker (background asyncio task, same process):
   |                 validate -> extract -> redact -> persist, dead-letters
   |                 failures instead of dropping or crashing the loop
   |-- api/          routers: auth, conversations (chat), dashboard (/metrics)
   `-- db/           SQLAlchemy repositories + Alembic migrations
   |
   v
PostgreSQL (+ pgvector extension provisioned, unused - see Tradeoffs)
```

Frontend (`frontend/`) is a Vite/React SPA: login, chat with streaming responses and mid-stream cancel, conversation list/resume, and the observability dashboard. Deployment (`docker-compose.yml` / `k8s/`) packages `postgres`, `api` (worker runs in-process inside it, not a separate service), and `frontend` (its own nginx container that also reverse-proxies API calls) — the same three-service shape locally and on the live k3s deployment.

See [`docs/architecture-notes.md`](docs/architecture-notes.md) for the ingestion flow, logging strategy, scaling considerations, and failure handling assumptions.

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

## What I'd Improve With More Time

- **Multi-provider support** — `LLMProvider` is already provider-agnostic by design (that's the whole point of the interface + `InstrumentedProvider` decorator), but only `GeminiProvider` is actually implemented. A second provider (OpenAI/Claude) would be close to a drop-in addition.
- **Dashboard filter controls** — the backend already supports `bucket_size_seconds`/`start`/`end` query params on `GET /metrics`, but the frontend never exposes them; it's always the last-1h/60s default.
- **No output token cap or rate limiting on LLM calls** — a very long response or a request flood has no guardrail today beyond whatever Google's own API enforces.
- **No visible error toast on a failed chat send** — the app recovers correctly (input stays usable, no crash) but silently; a user has no in-UI signal that their message failed versus is still streaming.
- **No automated Postgres backup** for the live deployment — acceptable for a demo, not for anything meant to persist real data long-term.
- **No drill-down from the dashboard into individual failing requests** — `logs.error_message` captures real detail per row (this is exactly what caught two real Gemini model-deprecation errors during actual deployment), but there's no UI or endpoint to browse it; only the aggregate counts are surfaced.
