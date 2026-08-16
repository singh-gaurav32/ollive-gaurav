# Business Rules — Unit 5: Frontend Application + Auth/Isolation

**BR1 — Login is username-only, by design.** No password field, no credential storage beyond the username itself. Consistent with the Security Baseline extension being declined in Requirements Analysis and this being a demo/take-home context, not a real signup flow (Q1).

**BR2 — Demo users are seeded idempotently, the same idiom as Unit 2's single seed user, extended to a fixed list.** `DEMO_USERNAMES = ["alice", "bob", "carol"]`; each is get-or-created at startup, never duplicated across restarts.

**BR3 — The session cookie is `httpOnly` and `SameSite=Lax`, but not `Secure` yet.** Appropriate for local/plain-HTTP demo use; flagged explicitly in the README as a production-hardening gap rather than silently left unstated.

**BR4 — Every protected request now carries a real session identity, replacing Unit 2's placeholder.** `chat_router.py`'s calls into `ChatService`/`InstrumentedProvider` pass the actual `session.id` from the validated cookie, not `user.id`. This is a genuine correctness fix, not just a refactor — `LogEvent.session_id` was never a real session reference until this unit.

**BR5 — An invalid or missing session returns `401`, and the frontend redirects to `/login` on receiving one.** Handled once, centrally, in the frontend's `fetch` wrapper (`api/client.ts`) — not repeated per API call site.

**BR6 — Cancel stops the UI immediately, not just the backend.** The cancel button both calls `POST /conversations/{id}/cancel` and aborts the frontend's own in-progress stream read via `AbortController` (Q3) — the user sees the stream stop the moment they click, rather than waiting for the backend's cancellation to propagate back through a stream that's already closing.

**BR7 — Logout removes the session, not the user or their data.** `AuthService.logout` deletes the session row and the cookie is cleared; conversations and messages are untouched and reappear on the next login as that user.

**BR8 — The dashboard view is not scoped to "my data."** Consistent with Unit 4's design (`MetricBucket` carries no conversation content), any logged-in user can view the aggregate dashboard — there's no isolation rule to apply here, by construction, not by an access-control decision made in this unit.
