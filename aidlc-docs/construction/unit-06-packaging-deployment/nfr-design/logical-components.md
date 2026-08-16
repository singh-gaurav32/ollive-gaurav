# Logical Components — Unit 6: Packaging & Deployment

## Docker Compose (local, `docker compose up`)

- `docker-compose.yml` — add a `frontend` service (new `frontend/Dockerfile`, nginx-served build), alongside the existing `postgres` and `api` services. No `worker` service (stays in-process in `api`, unchanged).
- `frontend/Dockerfile` — multi-stage: `node` stage runs `vite build`, `nginx:alpine` stage serves `dist/`.
- `frontend/nginx.conf` — static file serving (SPA fallback to `index.html`) + reverse-proxy for the backend's actual (unprefixed) route groups — `/auth`, `/conversations`, `/metrics`, `/health` — to the `api` service by container name. **Correction from the original plan**: the backend has no `/api` prefix (see `backend/src/main.py`'s router registration), so the proxy matches those real path prefixes instead of a generic `/api` rewrite. This same image/config is reused unchanged in k8s (the `api` Service name resolves the same way the compose service name does).
- `backend/Dockerfile` — likely already exists from Unit 1-5 dev setup; confirm/adjust for a production build (no `--reload`, multi-stage if not already).

## Kubernetes manifests (`k8s/`)

```
k8s/
  namespace.yaml            # single ollive namespace
  postgres-deployment.yaml  # Deployment + PVC + Service (ClusterIP)
  api-deployment.yaml       # Deployment + Service (ClusterIP), envFrom secrets.yaml
  frontend-deployment.yaml  # Deployment + Service (ClusterIP)
  ingress.yaml              # Traefik Ingress -> frontend Service only, cert-manager annotation, DuckDNS host
  cluster-issuer.yaml       # cert-manager ClusterIssuer (Let's Encrypt HTTP-01)
  secrets.yaml.example      # documents required keys; actual secrets.yaml is git-ignored
```

## Infrastructure (outside the repo, provisioned once)

- Oracle Cloud ARM VM (Always Free shape), k3s installed on it.
- Oracle Cloud reserved static public IP, attached to the VM.
- DuckDNS subdomain, `A` record pointed at the reserved IP.
- cert-manager installed into the cluster (Helm or static manifest) as a one-time cluster setup step, separate from the app's own `k8s/` manifests.

## Documentation

- `README.md` — updated with both the `docker compose up` quickstart (US-6.1) and the k3s deployment steps (US-6.2): VM setup, k3s install, cert-manager install, `kubectl apply -f k8s/`, DuckDNS configuration.
