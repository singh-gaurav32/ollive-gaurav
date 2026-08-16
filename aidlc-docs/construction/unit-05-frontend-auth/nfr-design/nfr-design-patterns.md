# NFR Design Patterns — Unit 5: Frontend Application + Auth/Isolation

No question round: both NFR Requirements decisions (CORS, manual types, Vitest+RTL) are mechanical to realize.

## CORS

`CORSMiddleware` added in `main.py`, reading `ALLOWED_ORIGINS` (comma-separated) from the environment, defaulting to `http://localhost:5173`. `allow_credentials=True` is what makes the session cookie actually travel on cross-origin requests from the Vite dev server — without it, the browser strips the cookie regardless of `SameSite`.

## Session validation

A FastAPI dependency reads the session cookie via `Request.cookies.get("session_id")` (not a `Cookie()` parameter — keeps the cookie name as a single named constant shared between the login endpoint that sets it and the dependency that reads it, rather than duplicated as a literal in two places). Returns a small `AuthContext` (user + session), replacing `get_current_user`'s Unit 2 stub. Existing call sites that only need the user unpack `.user` from it; `chat_router.py` additionally uses `.session.id` where it previously used `.user.id` (BR4).

## Vitest configuration

`vite.config.ts` gets a `test` block: `environment: 'jsdom'`, a `setupFiles` entry loading `@testing-library/jest-dom`'s matchers globally. Test files are colocated (`ChatWindow.test.tsx` next to `ChatWindow.tsx`), not in a separate `__tests__` tree — keeps a component and its test moving together in refactors.
