# Build Instructions

## Prerequisites
- **Build tools**: Docker (with either the `docker compose` plugin or standalone `docker-compose`), [uv](https://docs.astral.sh/uv/) (Python 3.12) for the backend, Node 20+ for the frontend
- **Environment variables**: `GEMINI_API_KEY` (root `.env`, see `.env.example`), `DATABASE_URL` (defaulted in `docker-compose.yml`)
- **System requirements**: any machine that can run Docker; the target production host is a 4 OCPU/24GB ARM VM (see `aidlc-docs/construction/unit-06-packaging-deployment/infrastructure-design/`), but local builds run fine on x86 or ARM dev machines

## Build Steps

### 1. Install dependencies
```bash
cd backend && uv sync
cd ../frontend && npm install
```

### 2. Configure environment
```bash
cp .env.example .env   # fill in GEMINI_API_KEY
```

### 3. Build all services
```bash
docker compose build          # or: docker-compose build, if the compose plugin isn't installed
```
Builds three images: `ollive-postgres` (pulled, not built — `pgvector/pgvector:pg16`), `ollive-api` (`backend/Dockerfile`, multi-stage not required — single-stage `python:3.12-slim` + `uv sync --frozen`), `ollive-frontend` (`frontend/Dockerfile`, multi-stage: `node:20-alpine` build → `nginx:alpine` serve).

### 4. Verify build success
- **Expected output**: `Successfully tagged ollive-api:latest` and `Successfully tagged ollive-frontend:latest`, no errors
- **Build artifacts**: local Docker images `ollive-api:latest`, `ollive-frontend:latest`
- **Actually verified in this session**: ran `docker-compose build` against `main` at commit `f5823ff` — both images built cleanly, `tsc -b && vite build` (frontend) and the backend's `uv sync` completed with no errors or warnings beyond routine `npm audit` advisories (unrelated dependency CVEs, not a build failure)

## Troubleshooting

### Build fails with dependency errors
- **Cause**: stale `uv.lock` or `package-lock.json` vs. source
- **Solution**: `uv lock --check` / `npm ci` locally first to confirm lockfiles are current before rebuilding the image

### Build fails with compilation errors (frontend)
- **Cause**: TypeScript errors — the frontend build runs `tsc -b` before `vite build`, so type errors fail the build, not just linting
- **Solution**: run `npx tsc -b --noEmit` locally to see the exact error before rebuilding the image
