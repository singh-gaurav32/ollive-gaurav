# Ollive — LLM Inference Logging & Ingestion System

Built incrementally via AI-DLC. See `aidlc-docs/` for the full requirements, design, and decision trail behind every choice below.

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

The backend must be running (see above) with `ALLOWED_ORIGINS` including `http://localhost:5173` (the default) for the frontend to reach it — CORS, not a dev proxy, is used (see `aidlc-docs/construction/unit-05-frontend-auth/nfr-requirements/`).

On first run, log in as one of the seeded demo users (`alice`, `bob`, `carol`) — no password.

## Getting Started (Full Stack, One Command)

```bash
cp .env.example .env        # fill in GEMINI_API_KEY
docker compose up -d --build
open http://localhost:8080  # frontend, proxying auth/chat/dashboard calls to the api container
```

`docker compose up` now brings up `postgres`, `api`, and `frontend` together — no separate `npm run dev`, no manual CORS/URL configuration. The frontend is built with `VITE_API_BASE_URL=""`, so its `fetch()` calls are relative and get proxied by nginx (`frontend/nginx.conf`) to the `api` container by name; CORS (`ALLOWED_ORIGINS`) is only needed for the separate `npm run dev` workflow above.

## Deployment (Cloud — k3s on Oracle Cloud)

Full design and rationale: `aidlc-docs/construction/unit-06-packaging-deployment/`. Summary of the steps to take a clean Oracle Cloud "Always Free" account to a live, public HTTPS URL:

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

**7. Build and push the images to a registry** (GHCR — GitHub Container Registry — recommended over building on the VM: no Docker install needed there, and updates become rebuild-and-push instead of SSH-and-rebuild; see `aidlc-docs/operations/oracle-vm-provisioning-checklist.md` for the full rationale):
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

**Updating after changes**: repeat step 7's build/import for whichever image changed, then `sudo k3s kubectl -n ollive rollout restart deployment/api` (or `deployment/frontend`). No CI/CD — this is a manual, single-VM demo deployment by design (see NFR Requirements).

## Status

This README grows as each unit of work lands.

- **Unit 1 — Provider Abstraction & Auto-Instrumentation** (done): `backend/src/provider/` — the `LLMProvider` interface, `GeminiProvider` adapter, and the `InstrumentedProvider` auto-instrumentation decorator. See `aidlc-docs/construction/unit-01-provider-abstraction/`.
- **Unit 2 — Chatbot Spine** (done): `backend/src/chat/` (conversation lifecycle, context truncation, streaming orchestration), `backend/src/db/` (SQLAlchemy repositories + Alembic migrations), `backend/src/api/` (chat endpoints, manually verifiable — no frontend yet). `docker-compose.yml` and the `postgres`/`api` services started here. See `aidlc-docs/construction/unit-02-chatbot-spine/`.
- **Unit 3 — Ingestion Pipeline Hardening** (done): `backend/src/events/in_process_event_queue.py` (the real event broker, replacing Unit 2's temporary no-op stand-in), `backend/src/ingestion/` (validate → extract → redact → persist pipeline, PII redaction, dead-lettering), `logs` + `failed_log_events` tables. Verified end-to-end through the live API, not just unit tests. See `aidlc-docs/construction/unit-03-ingestion-pipeline/`.
- **Unit 4 — Observability Dashboard** (done): `GET /metrics` — latency (p50/p95), throughput, and error-rate buckets over `logs`, with sensible defaults and a cap against runaway queries. Backend only — the dashboard UI is Unit 5. See `aidlc-docs/construction/unit-04-observability-dashboard/`.
- **Unit 5 — Frontend Application + Auth/Isolation** (done): the full React SPA (login, chat with streaming/cancel, conversation list/resume, dashboard), plus real session-based auth (`backend/src/auth/`) replacing Unit 2's seeded-user stub. Multi-user isolation verified live: a second user sees zero conversations, and direct-URL access to another user's conversation returns a real `404` from the backend, not a UI-level hide. See `aidlc-docs/construction/unit-05-frontend-auth/`.
- **Unit 6 — Packaging & Deployment** (done): `frontend/Dockerfile` + `frontend/nginx.conf` (nginx-served frontend, reverse-proxying the backend's real route groups — `/auth`, `/conversations`, `/metrics`, `/health` — with SSE streaming left unbuffered), `docker-compose.yml`'s new `frontend` service for one-command local setup, and the full `k8s/` manifest set for a self-hosted k3s deployment on Oracle Cloud (Ampere A1 Free Tier, Traefik ingress, cert-manager + Let's Encrypt, DuckDNS). Local Compose stack verified live end-to-end (proxy routing, SSE streaming, SPA client-side routing, dashboard). See `aidlc-docs/construction/unit-06-packaging-deployment/`.

More sections (architecture overview, schema design, tradeoffs) will be added as the final polished README is assembled — the cloud deployment itself (provisioning the VM, `kubectl apply`) is documented above and still to be executed on the real Oracle Cloud account.
