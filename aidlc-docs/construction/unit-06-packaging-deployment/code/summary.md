# Unit 6 Code Generation Summary — Packaging & Deployment

## What was built

**Local (`docker-compose.yml`)**: new `frontend` service built from `frontend/Dockerfile` (multi-stage: `node:20-alpine` build → `nginx:alpine` serve), publishing `8080:80`. `frontend/nginx.conf` serves the static build with SPA fallback and reverse-proxies the backend's real (unprefixed) route groups — `/auth`, `/conversations`, `/metrics`, `/health` — to the `api` container by name, with `proxy_buffering off` so the SSE chat stream isn't buffered.

**Cloud (`k8s/`)**: `namespace.yaml`, `postgres-deployment.yaml` (Deployment + 20GB `local-path` PVC + Service), `api-deployment.yaml` (Deployment + Service, `envFrom` a Secret), `frontend-deployment.yaml` (Deployment + Service, same image/config as Compose), `cluster-issuer.yaml` (cert-manager Let's Encrypt HTTP-01 `ClusterIssuer`), `ingress.yaml` (Traefik Ingress, routes all traffic to the `frontend` Service — nginx does the internal backend split, not duplicated at the Ingress layer), `secrets.yaml.example` (template; real `secrets.yaml` is git-ignored).

**Docs**: `README.md` gained a one-command full-stack quickstart and a full 10-step Oracle Cloud k3s deployment walkthrough (VM provisioning → static IP → firewall → DuckDNS → k3s install → cert-manager → build/import images locally → secrets/hostname → apply → verify).

## Design correction found during generation, not just written and assumed correct

NFR Design's original plan assumed a generic `/api` prefix for the reverse proxy and Ingress path-splitting between `frontend` and `api` Services. Reading the actual backend router registration (`backend/src/main.py`) showed there is no `/api` prefix — routes are `/auth/*`, `/conversations/*`, `/metrics`, `/health` directly. Corrected the nginx proxy to match those real prefixes, and simplified the k8s Ingress to route everything to the `frontend` Service only (letting nginx do the internal split) instead of duplicating the same routing decision in two places. Both already-approved design docs (`nfr-design/logical-components.md`, `infrastructure-design/deployment-architecture.md`) were amended to match, logged in `audit.md`.

## End-to-end verification performed live (not simulated)

Built and ran the full `docker-compose up --build` stack (three services: postgres, api, frontend) and drove it through a real browser at `localhost:8080`:
- Existing Unit 5 session cookie carried over cleanly (host-only, not port-scoped)
- Conversation history loaded via the proxied `/conversations/{id}/resume` call
- A new message POSTed through the proxied, unbuffered SSE stream — reached the backend and streamed correctly (confirmed via network request inspection, not just UI appearance); terminates due to the dummy `GEMINI_API_KEY` used in this environment, matching Unit 5's documented behavior under the same constraint
- Direct navigation to `/dashboard` exercised the nginx SPA fallback (`try_files ... /index.html`) and rendered real aggregated data, including the just-failed call — confirming Units 3/4's ingestion pipeline and dashboard work end-to-end through the new packaging, not just standing alone

Cloud deployment (provisioning the actual Oracle VM, `kubectl apply`) is documented step-by-step in the README but was not executed in this session — no access to the user's cloud account.

## Known items for "what I'd improve with more time"

- No automated backup for the Postgres PVC (explicitly out of scope per NFR Requirements — acceptable for a single-VM demo)
- No CI/CD — deploys are manual by design (see NFR Requirements' maintainability decision)
- `frontend-deployment.yaml`/`api-deployment.yaml` use `imagePullPolicy: Never` since there's no registry; this only works because images are built directly on the same VM/node running k3s — would need to change if the cluster ever grew beyond one node

## Traceability

US-6.1 (one-command local setup) → `docker-compose.yml`, `frontend/Dockerfile`, `frontend/nginx.conf`. US-6.2 (live k8s deployment) → `k8s/`, README's cloud deployment section.
