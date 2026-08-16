# Code Generation Plan — Unit 5: Frontend Application + Auth/Isolation

**Stories**: US-5.1, US-5.2, US-5.3, US-5.4, plus the UI completion of US-2.1/2.2/2.3 and US-4.1
**Dependencies**: Units 1-4 (wraps a UI and real auth around everything they built)
**Code location**: `backend/src/auth/`, `backend/src/api/`, `backend/src/db/`, `backend/alembic/`, `frontend/` (new)

## Steps

### Step 1: Backend — Auth
- [x] `backend/src/db/user_repository.py` — add `list_users`, `delete_session` to the interface
- [x] `backend/src/db/sqlalchemy_user_repository.py` — implement both
- [x] `backend/src/auth/service.py` — `AuthService` (`list_demo_users`, `login`, `validate_session`, `logout`)
- [x] `backend/src/api/auth_router.py` — `GET /auth/users`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
- [x] `backend/src/api/deps.py` — `get_auth_context()` (replaces `get_current_user`), `get_auth_service()`
- [x] `backend/src/api/chat_router.py` — switch every route from `get_current_user` to `get_auth_context`; `send_message` passes `auth.session.id` instead of `auth.user.id` (BR4 — the real fix)
- [x] `backend/src/main.py` — `CORSMiddleware`, demo-user seeding in `lifespan`

### Step 2: Backend — Auth Testing
- [x] `backend/tests/auth/` — `AuthService` tests (login creates a session, validate_session round-trips, logout deletes the session and a subsequent validate returns `None`)
- [x] `backend/tests/api/test_auth_router.py` — full login → cookie set → `/auth/me` → logout → cookie invalidated flow, via `TestClient`
- [x] Update `backend/tests/api/test_chat_router.py`'s overrides from `get_current_user` to `get_auth_context`

### Step 3: Frontend — Project Setup
- [x] Scaffold `frontend/` (Vite + React + TypeScript), `package.json`, `tailwind.config.js`, `postcss.config.js`, `vite.config.ts` (with the Vitest `test` block, per NFR design), `tsconfig.json`
- [x] `frontend/src/types.ts` — hand-mirrored shapes

### Step 4: Frontend — API Client & Auth
- [x] `frontend/src/api/client.ts` — fetch wrapper, `credentials: 'include'`, central 401 handling
- [x] `frontend/src/api/auth.ts`, `chat.ts`, `metrics.ts`
- [x] `frontend/src/context/AuthContext.tsx` + test

### Step 5: Frontend — Pages & Components
- [x] `frontend/src/hooks/` — `useConversations`, `useMessages`, `useMetrics`, `useChatStream` (+ test)
- [x] `frontend/src/components/` — `NavBar`, `ConversationList`, `ChatWindow` (+ test), `MessageBubble`, `ChatInput`, `CancelButton` (+ test), `MetricsSummary`
- [x] `frontend/src/pages/` — `LoginPage` (+ test), `ChatPage`, `DashboardPage`
- [x] `frontend/src/App.tsx`, `main.tsx` — routing, `AuthProvider`, `QueryClientProvider`

### Step 6: Documentation
- [x] `aidlc-docs/construction/unit-05-frontend-auth/code/summary.md`
- [x] Update root `README.md` — frontend setup instructions, updated Status

## Verification Plan — all executed
1. Backend: `make test` (57 passed) / `make test-db` (8 passed)
2. Frontend: `npm run test` (9 passed), `npx tsc -b` (clean)
3. **Live, in-browser verification** via the Browser tool: logged in as alice, sent a chat message (persisted correctly, provider failure handled gracefully without crashing), viewed real aggregated data on the dashboard, resumed a conversation with full history, logged out and back in as bob, confirmed zero conversations visible, confirmed direct-URL access to alice's conversation returns a real 404 from the backend. Cancel-during-streaming verified via the Vitest component test rather than live (Gemini's auth failure is near-instant with no valid key in this environment, leaving no real window to click cancel against).
4. **4 real bugs found and fixed during live verification** (not written-and-assumed-correct): relative API_BASE hitting the wrong origin, unstyled black background, "new conversation" not navigating in, and a redirect-loop risk in the 401 handler. See code/summary.md for details.
