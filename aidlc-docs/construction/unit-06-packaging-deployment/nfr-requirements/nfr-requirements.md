# NFR Requirements — Unit 6: Packaging & Deployment

## Deployment Environment / Availability

- **Target**: k3s on a single Oracle Cloud "Always Free" ARM VM. Not yet provisioned — provisioning happens in this unit (Infrastructure Design / Code Generation), not before it.
- Single-node, single-replica demo deployment. No HA, no autoscaling, no multi-region — matches the problem statement's "self-hosted k8s" bonus item, not a production SLA.
- **Domain**: DuckDNS free subdomain, chosen over `nip.io` specifically because the user wants a stable name that doesn't change if the VM's IP does (e.g. after a reboot or re-provision). `cert-manager` + Let's Encrypt issues a real cert against that hostname.

## Tech Stack / Packaging

- **Frontend serving**: a dedicated `nginx` container serving the Vite production build, separate from the `api` image — not served off FastAPI. Mirrors the existing `docker-compose.yml` shape (one service per concern) and gives the frontend its own k8s Deployment/Service, independently scalable/restartable from the API.
- **Image build/distribution**: no container registry. Images are built directly on the Oracle VM (`docker build` / `k3s ctr` importing a locally-built image), consumed by k3s from local storage. Simplest path for a single-node cluster — there's nothing to push to or pull from.
- **Worker**: confirmed still in-process inside the `api` container (asyncio background task), not a fourth service. Satisfies US-6.2's "worker" acceptance criterion as part of the `api` Deployment.

## Security

- **Secrets** (`GEMINI_API_KEY`, DB credentials): plain Kubernetes `Secret` objects, applied with `kubectl apply -f` from a **git-ignored** local manifest — never committed. No external secrets manager (Vault, Sealed Secrets) — out of scope for a demo deployment.
- **Network exposure**: only 80 (HTTP, redirects to HTTPS), 443 (HTTPS), and 22 (SSH) open on the VM's firewall/security list. No SSH IP allowlisting.
- Carries forward Unit 5's `ALLOWED_ORIGINS` CORS env var — this unit is what finally sets it to the real DuckDNS hostname instead of `localhost:5173`.

## Reliability

- **Postgres durability**: a k8s PVC backed by the VM's local disk. No automated backup/snapshot job — acceptable for a demo; data survives pod restarts (that's what the PVC is for) but not VM loss.

## Maintainability

- **Deploy workflow**: manual. Local `docker build` → transfer/build the image on the VM → `kubectl apply` / `kubectl rollout restart` for updates. No CI/CD pipeline — consistent with the "build directly on the VM, no registry" decision above (there is no push step to automate).
- Deployment steps get written up in the README per US-6.2's acceptance criteria.

## Scalability / Performance

N/A beyond what's already implied by "single Always-Free ARM VM" — this unit doesn't add load-testing or capacity-planning requirements. The VM's 4 ARM cores / 24GB RAM is treated as a fixed, generous ceiling for a demo-level workload, not something to be tuned against.
