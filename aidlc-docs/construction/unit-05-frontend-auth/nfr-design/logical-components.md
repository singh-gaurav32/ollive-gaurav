# Logical Components — Unit 5: Frontend Application + Auth/Isolation

## Backend

- `backend/src/auth/service.py` — `AuthService`. Lives in `auth/`, Unit 5's own package (per `project-structure.md`'s per-unit convention), not nested in `api/`.
- `backend/src/db/sqlalchemy_user_repository.py` — extended with `list_users`, `delete_session` (additive, per `domain-entities.md`).
- `backend/src/api/auth_router.py` — `GET /auth/users`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
- `backend/src/api/deps.py` — `get_auth_context()` (replaces `get_current_user`'s stub), `get_auth_service()`.
- `main.py` — `CORSMiddleware` registration, demo-user seeding in `lifespan` (alongside the existing worker startup).

## Frontend (`frontend/`, new — this unit creates the project)

```
frontend/
  index.html, vite.config.ts, tsconfig.json, tailwind.config.js, postcss.config.js, package.json
  src/
    main.tsx, App.tsx
    types.ts                    # hand-mirrored backend shapes
    api/
      client.ts                 # fetch wrapper: credentials:'include', central 401 -> redirect
      auth.ts, chat.ts, metrics.ts
    context/
      AuthContext.tsx, AuthContext.test.tsx
    hooks/
      useConversations.ts, useMessages.ts, useMetrics.ts, useChatStream.ts (+ .test.ts for useChatStream)
    pages/
      LoginPage.tsx (+.test.tsx), ChatPage.tsx, DashboardPage.tsx
    components/
      NavBar.tsx, ConversationList.tsx, ChatWindow.tsx (+.test.tsx), MessageBubble.tsx,
      ChatInput.tsx, CancelButton.tsx (+.test.tsx), MetricsSummary.tsx
```
