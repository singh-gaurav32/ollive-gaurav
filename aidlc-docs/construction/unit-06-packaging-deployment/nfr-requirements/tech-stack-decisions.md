# Tech Stack Decisions — Unit 6: Packaging & Deployment

## k3s on Oracle Cloud Free Tier (ARM) over managed serverless

Reaffirms the pre-existing decision (see prior planning). Oracle's free tier is free forever, not a 12-month trial, and gives genuinely self-hosted Kubernetes — satisfying the problem statement's bonus item literally. Fallback if ARM capacity/account friction blocks provisioning: a cheap Hetzner/DigitalOcean VPS running the same k3s manifests, unchanged.

## nginx container for the frontend, not FastAPI-served static files

Keeps the frontend an independently deployable/restartable unit with its own Deployment/Service in k8s, and mirrors the existing per-service shape of `docker-compose.yml`. New artifact: a small `frontend/Dockerfile` (multi-stage: `vite build` → `nginx:alpine` serving `dist/`).

## No container registry — build directly on the VM

**Superseded during actual provisioning** (see `aidlc-docs/operations/oracle-vm-provisioning-checklist.md`, step H) — switched to **GHCR**. The original reasoning held for the theoretical single-node case, but in practice: Docker was already working locally (used throughout Unit 6's own verification), and a GitHub repo was already being set up for this deployment anyway, so GHCR added no new account/setup — it removed the need to install Docker on the VM at all, and turned every future update from "SSH in, rebuild, re-import into containerd" into "rebuild locally, push, `kubectl rollout restart`". `k8s/api-deployment.yaml` and `k8s/frontend-deployment.yaml` now reference `ghcr.io/singh-gaurav32/ollive-{api,frontend}:latest` with `imagePullPolicy: Always`, not `imagePullPolicy: Never` against a locally-built image.

<details><summary>Original reasoning (superseded)</summary>

For a single-node cluster there's no second node that needs to *pull* an image from anywhere; a registry (ghcr.io/Docker Hub) would add an account, auth, and a push/pull round-trip for zero benefit at this scale. Images are built on the VM itself and loaded into k3s's local `containerd` store (`k3s ctr images import` or an equivalent local-build flow).

</details>

## DuckDNS over nip.io

`nip.io` requires no signup but its hostname is derived from the IP itself — if the VM's IP ever changes, the URL changes with it. DuckDNS decouples the hostname from the IP (one quick free signup, then `A` record updates point the same name at a new IP if needed), which the user explicitly wants for a stable, shareable demo link.

## Kubernetes `Secret` objects, no secrets manager

Vault/Sealed Secrets/External Secrets Operator solve problems (rotation, audit, multi-cluster) this single-VM demo doesn't have. A git-ignored local secrets manifest applied via `kubectl apply` is the minimum that keeps credentials out of version control.

## No CI/CD pipeline

Directly follows from "build on the VM, no registry" — there's no push step for a pipeline to automate, and a single demo deployment doesn't need build-on-every-merge. Deploys stay a manual, documented (README) command sequence.
