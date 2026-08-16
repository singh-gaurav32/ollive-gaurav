# Unit 5 Code Generation Summary — Frontend Application + Auth/Isolation

## What was built

**Backend auth**: `backend/src/auth/` (`AuthService`, `cookies.py`), `db/user_repository.py` extended (`get_by_id`, `create_user`, `list_users`, `delete_session`), `api/auth_router.py` (`/auth/users`, `/auth/login`, `/auth/logout`, `/auth/me`), `api/deps.py`'s `AuthContext`/`get_auth_context` replacing Unit 2's `get_current_user` stub everywhere (`chat_router.py`, `dashboard_router.py`), CORS middleware and demo-user seeding in `main.py`.

**Frontend** (`frontend/`, new): Vite + React + TypeScript + Tailwind + TanStack Query + React Router. Full page/component tree per the NFR design: `LoginPage`, `ChatPage` (`ConversationList` + `ChatWindow` + `ChatInput` + `CancelButton` + `MessageBubble`), `DashboardPage` (`MetricsSummary`), `AuthContext`, hooks (`useConversations`, `useMessages`, `useMetrics`, `useChatStream`), and the `api/` client layer.

## Real bugs found and fixed during live verification, not just written and assumed correct

1. **`API_BASE` was empty (relative paths)** — NFR Requirements chose CORS specifically so frontend/backend could be different origins, but the client was calling relative paths, which silently hit Vite's own dev server (which SPA-fallback-serves `index.html` for any unmatched route, masking the bug as an empty-but-not-erroring response). Fixed with an env-configurable absolute `API_BASE` (`VITE_API_BASE_URL`, defaulting to `http://localhost:8000`).
2. **Black background on an unstyled page** — no explicit background color meant the page inherited the browser's default color scheme. Fixed with an explicit `bg-white text-gray-900` on `html, body`.
3. **"New conversation" didn't navigate into the new conversation** — it invalidated the list query but never routed to `/chat/:newId`, leaving the user looking at an empty state despite the conversation existing. Fixed by navigating on the mutation's `onSuccess`.
4. **`apiFetch`'s 401-redirect would have fired on `AuthContext`'s own initial "am I logged in" check** — that check is *supposed* to see a 401 for a logged-out user; redirecting on it would cause a jarring hard reload before React Router ever got to render `/login`. Fixed with a `skipAuthRedirect` escape hatch used only by that one call site.

All four were caught by actually running the app in a browser and clicking through it, not by reading the code.

## End-to-end verification performed live (not simulated)

- Login as `alice`, full session persists across page reload
- Real chat message sent through the live API; the underlying Gemini call genuinely failed (no valid key in this environment) and the failure correctly propagated to the UI without crashing it — `isStreaming` cleanly reset, input usable again
- Dashboard rendered **real aggregated data** from the actual `logs` table populated by earlier verification passes
- Resumed a conversation and saw its full message history, including a message sent via a raw API call outside the UI
- **Isolation verified two ways**: logged in as `bob`, confirmed zero conversations visible (not just alice's data absent from a shared list); then navigated directly to alice's conversation URL by ID and got a `404` from the server itself — not a UI-level hide, an actual backend rejection

## Tests

74 automated tests total: 57 backend fast + 8 backend real-Postgres + 9 frontend (Vitest + React Testing Library, covering `AuthContext`'s login/logout/session-restore, `LoginPage`'s user picker, and `ChatWindow`'s streaming/cancel behavior).

## Known items for "what I'd improve with more time"

- No visible error toast when a chat send fails — the app recovers correctly but silently
- `react-router-dom`'s moderate CVE fix requires a breaking major-version bump, not applied
- Session cookie isn't marked `Secure` yet (documented in NFR design as a deliberate scope boundary, not an oversight)

## Traceability

US-5.1/5.2/5.3/5.4 → `auth/`, `api/auth_router.py`, `frontend/src/pages/`, `frontend/src/components/`. UI completion of US-2.1/2.2/2.3 → `ChatWindow`, `useChatStream`. UI completion of US-4.1 → `DashboardPage`, `MetricsSummary`.
