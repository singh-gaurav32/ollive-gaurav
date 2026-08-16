# Domain Entities — Unit 5: Frontend Application + Auth/Isolation

## `AuthService` (backend, completes the interface from `component-methods.md`)

| Method | Signature | Notes |
|---|---|---|
| `list_demo_users` | `() -> list[User]` | New — powers the login picker |
| `login` | `(username: str) -> Session` | No password (Q1) |
| `validate_session` | `(session_id: UUID) -> User \| None` | Collapsed from the originally-sketched `UserContext` return type back in the shared-contracts pass |
| `logout` | `(session_id: UUID) -> None` | New |

## `UserRepository` additions

The interface (`db/user_repository.py`, fixed in the shared-contracts pass) needs two new methods to support this unit:
- `list_users() -> list[User]`
- `delete_session(session_id: UUID) -> None`

Both are additive — no existing method signature changes.

## Demo user seeding

A fixed list, `DEMO_USERNAMES = ["alice", "bob", "carol"]`, seeded idempotently (get-or-create per username, same idiom as Unit 2's single seed user) at app startup via `main.py`'s `lifespan`. Unit 2's original single `"demo"` seed user is no longer used by the auth flow once this lands — its data (if any exists from earlier testing) is harmless leftover, not cleaned up.

## Session cookie

`httpOnly`, `SameSite=Lax`, carries the session UUID. Not marked `Secure` yet — this project runs over plain HTTP locally and in the Unit 6 demo; flagged in the README as a production-hardening item, not fixed here.

## `AuthContext` (frontend)

Holds the current `User` (or `null`), a `loading` flag, and `login`/`logout` functions. Wraps the app; pages read from it via a `useAuth()` hook.

## Frontend routes

`/login`, `/chat` (conversation list + active view, no ID selected shows an empty state), `/chat/:conversationId` (resumes that conversation), `/dashboard`. Unauthenticated access to anything but `/login` redirects to `/login` (BR5).

## The `session_id` placeholder retirement

Unit 2 passed `user.id` as a stand-in for `session_id` in `ChatService`/`InstrumentedProvider` calls, documented at the time as a placeholder "until Unit 5." This unit replaces it: the auth dependency now exposes both the current `User` and the current `Session`, and `chat_router.py` passes the real `session.id` through. `LogEvent.session_id` (and the persisted `LogRecord`) now carries a real auth session reference for the first time.
