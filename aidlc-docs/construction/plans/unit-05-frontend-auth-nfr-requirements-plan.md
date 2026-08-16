# NFR Requirements Plan — Unit 5: Frontend Application + Auth/Isolation

## Category Coverage

- **Tech Stack / Dev workflow** — Questions 1 and 2.
- **Maintainability** — Question 3.
- **Security** — N/A beyond what Functional Design already fixed (`httpOnly`/`SameSite=Lax` cookie, no password to mishandle).
- **Scalability / Availability** — N/A, unchanged.

---

## Question 1: Frontend-to-backend connectivity in dev
The Vite dev server (port 5173) and the FastAPI backend (port 8000) are different origins.

A) **Vite dev-server proxy** — `server.proxy` forwards `/auth`, `/conversations`, `/metrics` to `http://localhost:8000`; the frontend calls relative URLs, so the browser sees everything as same-origin, no CORS configuration needed, cookies work with zero extra setup. Unit 6 will need to replicate this behavior in production (nginx reverse-proxying the same paths), noted for then, not solved now.

B) **CORS middleware on the backend**, explicit allowed origin (`http://localhost:5173`) with `allow_credentials=True` — more portable/explicit about the cross-origin nature, but real CORS configuration to get right (credentials mode disallows wildcard origins) for a problem the proxy sidesteps entirely in dev

C) Other (please describe after [Answer]: tag below)

[Answer]: B — CORS middleware. More portable across deployment topologies than a dev-only proxy that Unit 6 would just have to re-solve anyway.

## Question 2: Frontend TypeScript types
`ChatWindow`, `ConversationList`, etc. need TS shapes matching the backend's pydantic models (`Conversation`, `ChatMessage`, `MetricBucket`, `User`).

A) **Manually written**, hand-mirrored from `db/models.py` / `db/log_repository.py` — no build step, but can drift from the backend if a field changes and the mirror isn't updated

B) **Generated from FastAPI's OpenAPI schema** via `openapi-typescript` — stays in sync automatically, one more dev-dependency and a generation step to remember to run

C) Other (please describe after [Answer]: tag below)

[Answer]: A — manually hand-mirrored.

## Question 3: Frontend automated tests
A) **Vitest + React Testing Library** for the components/hooks with real logic (`ChatWindow`'s stream-parsing loop, the auth redirect behavior) — mirrors the backend's testing rigor

B) **No automated frontend tests** — verify manually in the browser (which happens regardless, per your own review process) given the project's already-large scope; document this as a "what I'd add with more time" item in the README

C) Other (please describe after [Answer]: tag below)

[Answer]: A — Vitest + React Testing Library.
