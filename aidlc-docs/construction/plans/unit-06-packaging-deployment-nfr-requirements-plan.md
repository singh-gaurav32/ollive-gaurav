# Unit 6 — Packaging & Deployment — NFR Requirements Plan

## Context
Unit 6 packages Units 1–5 into a one-command local stack (US-6.1) and a live Kubernetes deployment (US-6.2). No new business logic — this stage focuses on deployment topology, tech stack for packaging, and operational NFRs.

**Already decided** (carried in from prior planning, not re-asked below):
- Deployment target: self-hosted **k3s on an Oracle Cloud "Always Free" ARM VM**. Account is now created; VM not yet provisioned.
- The ingestion worker runs as an in-process asyncio background task inside the `api` process/container (not a separate container/pod) — this satisfies US-6.2's "worker" acceptance criterion via the same deployable unit as the API, not a fourth standalone service.
- HTTPS: `cert-manager` + Let's Encrypt once a hostname is pointed at the VM.
- Fallback host if Oracle ARM capacity is unavailable: Hetzner/DigitalOcean VPS running the same k3s setup (manifests should stay portable).

## Steps
- [x] Collect answers to the questions below
- [x] Resolve any ambiguous answers with follow-ups
- [x] Generate `nfr-requirements.md` and `tech-stack-decisions.md`

## Questions

### Tech Stack Selection

**Q1. Frontend serving strategy for both Docker Compose and k8s.**
The current `frontend/` is a Vite/React SPA with no server of its own.
A) Build to static files, serve via a lightweight `nginx` container (separate image/container/pod from the API)
B) Build to static files, serve them directly from the FastAPI `api` service (one fewer moving part, but couples frontend deploys to backend restarts)
C) Something else (specify)

[Answer]: A

**Q2. Container registry for the images `docker build` produces.**
The k3s VM needs to pull `api` and (if Q1=A) `frontend` images from somewhere.
A) GitHub Container Registry (ghcr.io) — free, ties to the existing GitHub repo
B) Docker Hub free tier
C) Build directly on the VM (no registry, no push/pull step — simplest for a single-node demo)

[Answer]: C

**Q3. Domain / hostname for the public URL (US-6.2's "reachable via a public URL").**
A) `nip.io` wildcard hostname (zero signup, maps `<ip>.nip.io` straight to the VM's IP)
B) DuckDNS free subdomain (requires a quick free signup, gives a stable name independent of IP)
C) A domain you already own (specify)

[Answer]: B

### Availability & Reliability

**Q4. Is the Oracle VM already provisioned, or still to be created?**
This determines whether Infrastructure Design can reference a real IP/region or has to stay parametric.
A) Not yet provisioned — will create it during Infrastructure Design / Code Generation
B) Already provisioned — here's the IP/region: ______

[Answer]: A

**Q5. Postgres data durability on the single VM.**
This is a single-node demo deployment (per the problem statement's bonus item, not a production HA system).
A) PVC on local VM disk is enough — no automated backup needed for a demo
B) Add a simple periodic `pg_dump` cron/backup job to a file (still local, just guards against accidental data loss beyond what a PVC already protects against)
C) Out of scope for this unit

[Answer]: A

### Security

**Q6. Secrets management (GEMINI_API_KEY, DB credentials) in k8s.**
A) Kubernetes `Secret` objects, applied via `kubectl apply` from a git-ignored local file (not committed)
B) Same, but via `.env` + `envsubst`/`kustomize` into the manifest at deploy time
C) Other (specify)

[Answer]: A

**Q7. Any inbound access restriction on the Oracle VM beyond 80/443 (HTTP/HTTPS) and 22 (SSH)?**
A) No — 80/443/22 only is fine for a demo
B) Yes — restrict SSH to your IP / add other rules (specify)

[Answer]: A

### Maintainability

**Q8. Deploy workflow for updates after the initial deployment.**
A) Manual: `docker build` + push + `kubectl apply`/`kubectl rollout restart`, run by hand when needed
B) A simple GitHub Actions workflow that builds/pushes images on push to `main` (still manual `kubectl apply`/`helm upgrade` on the VM)
C) Full CI/CD (build, push, and auto-deploy to the VM on every merge)

[Answer]: A
