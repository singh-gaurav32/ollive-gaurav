# NFR Requirements — Unit 5: Frontend Application + Auth/Isolation

## Tech Stack / Dev Workflow

- **CORS**, not a dev proxy. FastAPI's `CORSMiddleware` with `allow_credentials=True` and an explicit allowed-origins list (not a wildcard — credentials mode disallows that). The allowed origins come from an `ALLOWED_ORIGINS` environment variable (defaulting to `http://localhost:5173` for local dev), so Unit 6 configures it for whatever production domain the frontend actually deploys to, without a code change.
- **TypeScript types**: manually hand-mirrored in `frontend/src/types.ts` from the backend's pydantic models. Accepted risk of drift if a backend field changes without the mirror being updated — no generation step, no new dev-dependency.

## Maintainability / Testing

- **Vitest + React Testing Library** for components and hooks carrying real logic: `ChatWindow`'s stream-parsing loop, the auth redirect behavior, `CancelButton`'s dual-abort behavior. Presentational components (`MessageBubble`, `NavBar`) aren't independently tested — their behavior is exercised through the components that use them.

## Security

N/A beyond what Functional Design already fixed (`httpOnly`/`SameSite=Lax` cookie, no password to mishandle).

## Scalability / Availability

N/A, unchanged from earlier units.
