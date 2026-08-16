# Unit 6 — Packaging & Deployment — Code Generation Plan

## Unit Context
- **Stories**: US-6.1 (one-command local setup), US-6.2 (live k8s deployment)
- **Depends on**: Units 1-5 (packages the complete system, no new business logic)
- **Design source**: `aidlc-docs/construction/unit-06-packaging-deployment/{nfr-requirements,nfr-design,infrastructure-design}/`

## Scope note — Local vs. Cloud verification
This plan generates all deployment artifacts (Dockerfiles, `docker-compose.yml` changes, `k8s/` manifests, README docs) for both targets. I can **execute and verify the local Docker Compose stack** directly (build, run, browser-check it — same as prior units). I do **not** have access to your Oracle Cloud account or a provisioned VM, so the actual cloud steps (create the VM, run `k3s` install, `kubectl apply`, DNS setup) are **documented precisely enough to follow, not executed by me** — you'd run them yourself (or bring me in for the parts you want help with, e.g. via SSH, once the VM exists).

## Routing detail (implementation-level, doesn't change approved design)
Backend routes have no `/api` prefix — they're `/auth/*`, `/conversations/*`, `/metrics`, `/health` directly. So the reverse proxy (nginx locally, Traefik in k8s) routes those exact path prefixes to the `api` service and everything else to the `frontend` service, instead of a generic `/api` rewrite. Frontend is built with `VITE_API_BASE_URL=""` (relative), so `fetch()` calls become same-origin — no CORS needed in either deployment target (CORS stays configured for local `npm run dev` against the Vite dev server, unchanged from Unit 5). I'll correct the one `/api`-prefix mention in the already-approved `nfr-design/logical-components.md` and `infrastructure-design/deployment-architecture.md` to reflect this concretely, noted in audit.md as a same-stage implementation correction, not a design change requiring re-approval.

## Steps

### Deployment Artifacts Generation
- [x] **Step 1**: `frontend/Dockerfile` — multi-stage build (Node build stage → `nginx:alpine` serve stage), `ARG VITE_API_BASE_URL=""` passed through to the Vite build
- [x] **Step 2**: `frontend/nginx.conf` — serves `dist/` with SPA fallback (`try_files ... /index.html`) for React Router routes; `location` blocks proxying `/auth`, `/conversations`, `/metrics`, `/health` to `api:8000` (with `proxy_buffering off` for the SSE chat stream)
- [x] **Step 3**: `docker-compose.yml` — add `frontend` service (build from `frontend/Dockerfile`, depends on `api`, publish port 80→8080 locally); confirmed `backend/Dockerfile` needs no changes (already prod-suitable: no `--reload`, multi-arch `python:3.12-slim` base image)
- [x] **Step 4**: `k8s/namespace.yaml` — `ollive` namespace
- [x] **Step 5**: `k8s/postgres-deployment.yaml` — Deployment (1 replica) + PVC (20GB, `local-path`) + ClusterIP Service
- [x] **Step 6**: `k8s/api-deployment.yaml` — Deployment (1 replica, `envFrom` the Secret) + ClusterIP Service
- [x] **Step 7**: `k8s/frontend-deployment.yaml` — Deployment (1 replica) + ClusterIP Service
- [x] **Step 8**: `k8s/cluster-issuer.yaml` — cert-manager `ClusterIssuer` (Let's Encrypt, HTTP-01)
- [x] **Step 9**: `k8s/ingress.yaml` — **simplified from plan**: routes ALL traffic to the `frontend` Service only (not split by path). The frontend's own `nginx.conf` already proxies `/auth`, `/conversations`, `/metrics`, `/health` to the `api` Service internally (k8s Service DNS name `api` resolves the same way Docker Compose's service name does) — duplicating that routing in the Ingress would just be two copies of the same logic. `cert-manager.io/cluster-issuer` annotation + TLS block for the DuckDNS host.
- [x] **Step 10**: `k8s/secrets.yaml.example` — documents required keys (`GEMINI_API_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`); added real `k8s/secrets.yaml` to `.gitignore`

### Documentation Generation
- [x] **Step 11**: `README.md` — added "Getting Started (Full Stack, One Command)" and a full "Deployment (Cloud — k3s on Oracle Cloud)" walkthrough (10 steps: provision → static IP → firewall → DuckDNS → k3s → cert-manager → build/import images → secrets/hostname → apply → verify)
- [x] **Step 12**: Amended `nfr-design/logical-components.md` and `infrastructure-design/deployment-architecture.md` — corrected `/api` references to the real path list, and documented the Ingress simplification (routes to `frontend` only; nginx does the internal split, not duplicated at the Ingress layer)

### Local Verification (executed by me)
- [x] **Step 13**: `docker-compose up -d --build` (the `docker compose` plugin isn't installed in this environment; standalone `docker-compose` v5 was used instead — no manifest changes needed, purely a local CLI difference). All three containers built and started; `curl` confirmed the frontend root (200) and proxied `/health` and `/auth/users` (200, real JSON). Real browser check through `localhost:8080`: existing session cookie carried over from Unit 5 (host-only, port-independent), conversation history loaded via the proxied `/resume` call, a new message POSTed through the proxied, unbuffered SSE stream (`proxy_buffering off` confirmed working — request reached the backend and streamed rather than being buffered/rejected; it terminates due to the dummy `GEMINI_API_KEY` in this environment, same expected behavior as Unit 5's verification), and `/dashboard` (direct URL, testing the nginx SPA fallback) correctly rendered via client-side routing and showed the failed call logged (100% error rate, 1 request) — confirming the ingestion pipeline and dashboard both work end-to-end through the new proxy path.

## Story Traceability
- US-6.1 (one-command local setup) → Steps 1-3, 13
- US-6.2 (live k8s deployment) → Steps 4-11 (artifacts + documented steps; live execution is yours to run per the scope note above)
