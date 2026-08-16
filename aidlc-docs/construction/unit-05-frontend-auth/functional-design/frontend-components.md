# Frontend Components — Unit 5

## Component Hierarchy

```
App
  AuthProvider (AuthContext)
    Router
      LoginPage                          [/login]
      ProtectedLayout                    (route guard, redirects to /login if unauthenticated)
        ChatPage                         [/chat, /chat/:conversationId]
          ConversationList (sidebar)
          ChatWindow
            MessageBubble (x N)
            ChatInput
            CancelButton (visible only while streaming)
        DashboardPage                    [/dashboard]
          MetricsSummary (latency/throughput/error stat tiles)
          MetricsTable or simple chart (bucketed over time)
        NavBar (user's name, logout button, links to /chat and /dashboard)
```

## Pages

### `LoginPage`
- **State**: `demoUsers: User[]` (loaded via `GET /auth/users` on mount), `isLoggingIn: boolean`.
- **Interaction**: click a username → `POST /auth/login` → on success, `AuthContext.login(user)` → redirect to `/chat`.

### `ChatPage`
- **State**: `activeConversationId` (from the route param, or `null`), conversation list and message history both owned by TanStack Query hooks (`useConversations`, `useMessages`), not local `useState`.
- **Interaction flows**: "New conversation" button → `POST /conversations` → navigate to `/chat/:newId`. Selecting a conversation in the sidebar → navigate to `/chat/:id`, which triggers `resume` (`POST /conversations/:id/resume`) to load full history and flip a cancelled conversation back to active.

### `DashboardPage`
- **State**: `useMetrics()` hook (TanStack Query, `GET /metrics`), no client-side params exposed in v1 — always requests the backend's defaults (last 1h, 60s buckets); a time-range picker is a natural future enhancement, not built here.

## Key Components

### `ChatWindow`
- **Props**: `conversationId: string`.
- **State**: `streamingContent: string` (the in-progress assistant message, appended to as tokens arrive), `isStreaming: boolean`, `abortController: AbortController | null`.
- **API integration**: owns the `fetch` + `ReadableStream` loop from `business-logic-model.md`. On stream completion, invalidates the TanStack Query cache for this conversation's messages so the final persisted version (from the backend) replaces the locally-accumulated streaming text.

### `CancelButton`
- **Props**: `onCancel: () => void`, rendered only when `isStreaming` is true.
- **Behavior**: per BR6 — calls both `abortController.abort()` and the cancel endpoint.

### `ConversationList`
- **Props**: none (reads from `useConversations()` directly).
- **Behavior**: highlights the active conversation (from the route param), shows cancelled conversations with a visual marker (still clickable — clicking resumes them, per US-5.3).

## Form Validation

The only form in this unit is the chat input (`ChatInput`): disallow submitting empty/whitespace-only content, disable the send control while a stream is already in progress for that conversation (prevents overlapping `send_message` calls to the same conversation, which `ChatService`'s active-stream registry would otherwise just silently overwrite — see Unit 2's known simplification).

## API Integration Points

| Component | Endpoint(s) |
|---|---|
| `LoginPage` | `GET /auth/users`, `POST /auth/login` |
| `NavBar` | `POST /auth/logout` |
| `ConversationList` | `GET /conversations` |
| `ChatWindow` | `POST /conversations`, `POST /conversations/:id/messages` (streaming), `POST /conversations/:id/resume` |
| `CancelButton` | `POST /conversations/:id/cancel` |
| `DashboardPage` | `GET /metrics` |
