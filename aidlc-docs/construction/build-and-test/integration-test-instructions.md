# Integration & End-to-End Test Instructions

## Purpose
Test interactions between units through the actual packaged system (Unit 6), not each unit in isolation. Ollive has no separate integration-test framework/directory — cross-unit correctness is verified live through the running stack, the same way it was verified at the end of each unit's own Code Generation stage. This document consolidates that into one system-wide pass now that all 6 units are merged.

## Setup

### 1. Start the full stack
```bash
cp .env.example .env   # fill in GEMINI_API_KEY for a real chat integration test; a dummy value still exercises everything except the actual Gemini call
docker compose up -d --build   # or docker-compose, see build-instructions.md
```

### 2. Service endpoints
- Frontend (entry point): `http://localhost:8080`
- API directly (for curl-level checks): `http://localhost:8000`
- Postgres: `localhost:5432`

## Test Scenarios

### Scenario 1: Chat message → Ingestion → Dashboard (Units 1, 2, 3, 4)
- **Description**: sending a chat message exercises the provider abstraction (Unit 1), conversation/streaming logic (Unit 2), and — whether the underlying LLM call succeeds or fails — the ingestion pipeline logs it (Unit 3), which the dashboard then aggregates (Unit 4).
- **Test steps**: log in, send a message in a conversation, then visit `/dashboard`.
- **Expected results**: the message send returns a streamed response (SSE); regardless of success/failure, `/dashboard` shows an incremented request count and, on failure, a corresponding error-rate bump — confirming the events actually flowed `chat → ingestion → logs table → dashboard aggregation`, not just that each piece works alone.
- **Actually verified in this session** (dummy `GEMINI_API_KEY`, so the underlying call fails by design): dashboard showed `Requests (last 1h): 1`, `Error rate: 100.0%`, `p95 latency: 360ms` — a real row flowed end-to-end through all four units.

### Scenario 2: Auth-gated access + multi-user isolation (Units 2, 5)
- **Description**: session auth (Unit 5) must actually gate conversation access (Unit 2's data model), not just hide it in the UI.
- **Test steps**: log in as user A, create/note a conversation ID. Log out, log in as user B (a user with zero conversations). Confirm B's conversation list is empty, then navigate directly to A's conversation URL by ID.
- **Expected results**: B's list is empty (not just A's data filtered out client-side); direct URL access returns a genuine `404` from the backend (`POST /conversations/{id}/resume`), not a client-side redirect or hidden state.
- **Actually verified in this session**: logged in as `carol` (zero conversations shown), navigated directly to `bob`'s conversation URL — network log confirms `POST .../resume → 404 Not Found`, and the UI degraded gracefully (empty pane, no crash, no data leak).

### Scenario 3: Full stack through the Unit 6 packaging, not raw service calls (Units 5, 6)
- **Description**: Units 1-5 were each verified by talking to `localhost:8000` directly or via the Vite dev server. This scenario confirms the same behavior holds when everything goes through Unit 6's actual production packaging (nginx-proxied frontend), which is what a real deployment looks like.
- **Test steps**: through `http://localhost:8080` only (never `:8000` directly) — log in, resume a conversation (loads history), send a new message (SSE stream), navigate directly to `/dashboard` by URL (tests the SPA fallback, not client-side routing from an in-app link).
- **Expected results**: every request proxies correctly (`/auth`, `/conversations`, `/metrics` all reach the `api` container by way of nginx), the SSE stream isn't buffered/truncated by the proxy, and direct-URL navigation to a client-side route still serves the app (not a 404 from nginx).
- **Actually verified in this session**: all of the above passed — see `aidlc-docs/construction/unit-06-packaging-deployment/code/summary.md` for the detailed network-level confirmation (200s on `/health`, `/auth/users`, `/conversations/.../resume`; unbuffered SSE on `/conversations/.../messages`).

## Run

There's no single "integration test suite" command — the above scenarios are executed manually (or via the Browser tool, as done in this session) against the running Compose stack. Automating them (e.g. Playwright) is a reasonable future addition but wasn't part of this project's scope.

## Cleanup
```bash
docker compose down          # stop and remove containers, keep the postgres-data volume
docker compose down -v       # also wipe the database (fresh demo-user reseed on next `up`)
```
