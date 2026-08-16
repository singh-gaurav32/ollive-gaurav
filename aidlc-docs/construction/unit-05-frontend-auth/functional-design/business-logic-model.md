# Business Logic Model — Unit 5: Frontend Application + Auth/Isolation

## Backend: login flow
1. `GET /auth/users` → `AuthService.list_demo_users()` → the login screen's picker list.
2. User selects a username → `POST /auth/login {username}`.
3. `AuthService.login(username)`: `UserRepository.get_by_username(username)` (404 if somehow absent — shouldn't happen given BR2's startup seeding) → `UserRepository.create_session(user.id)` → set the `httpOnly`/`SameSite=Lax` cookie to the new session ID → return the `User`.

## Backend: session validation (replaces `get_current_user`'s Unit 2 stub)
1. Read the session cookie from the request.
2. No cookie, or `AuthService.validate_session(session_id)` returns `None` → `401`.
3. Otherwise: attach both `User` and `Session` to the request context (BR4) — every downstream call that used to receive `user.id` as a `session_id` placeholder now receives the real `session.id`.

## Backend: logout
1. `POST /auth/logout` → `AuthService.logout(session_id)` → `UserRepository.delete_session(session_id)` → clear the cookie (BR7).

## Frontend: chat streaming (the `fetch` + `ReadableStream` path)
1. `POST /conversations/{id}/messages` via `fetch`, `credentials: 'include'` (carries the session cookie), body `{content}`.
2. Read `response.body.getReader()` in a loop; decode chunks, split on the SSE `event:`/`data:` framing already produced by the backend (Unit 2's `chat_router.py`), append `token` events to the rendered message as they arrive.
3. `done` event ends the loop; the reader naturally completes.
4. An `AbortController` is created per request and passed to `fetch`'s `signal` — both for the cancel button (BR6) and for cleanup if the component unmounts mid-stream (navigating away shouldn't leave a dangling read).

## Frontend: cancel button
1. `onClick`: call `abortController.abort()` (stops the local read/render immediately) **and** `POST /conversations/{id}/cancel` (stops the backend's in-flight provider call) — both fire, neither waits on the other (BR6).

## Frontend: auth-aware routing
1. `AuthContext` loads the current user once on mount via `GET /auth/me` (or reuses the result of a successful login already in memory).
2. A route guard component redirects to `/login` if `user` is `null` and the target route isn't `/login` itself.
3. The `api/client.ts` fetch wrapper checks every response for `401` and triggers the same redirect centrally (BR5), so individual API calls (`chat.ts`, `metrics.ts`) don't each need their own auth-failure handling.

## Key Invariant

Every piece of "who is making this request" logic lives in exactly two places: the backend's session-validation dependency, and the frontend's `AuthContext` + fetch wrapper. No component or route calls a protected endpoint without going through one of these two chokepoints.
