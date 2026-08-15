# Domain Entities — Unit 2: Chatbot Spine

## Conversation lifecycle (State pattern)

Two states only — `"active"` and `"cancelled"` (per `db/models.py`'s `ConversationState`, already fixed in the shared contracts pass). "Resume" is the transition name for `cancelled → active`, not a third state.

```
        start_conversation
              |
              v
    +------------------+   cancel_conversation   +-----------+
    |      active      | ----------------------> | cancelled |
    +------------------+                          +-----------+
              ^                                        |
              +---------- resume_conversation ----------+
```

A conversation is never deleted or archived in this unit — only its `state` column changes. Multiple conversations per user can be `active` simultaneously (Q2 = A); starting a new conversation has no effect on any existing one.

## `ContextTruncationStrategy` (interface, unit-owned)

Lives in `chat/`, not a shared package — only `ChatService` ever calls it (see `project-structure.md`'s ownership rule).

| Method | Signature |
|---|---|
| `truncate` | `(history: list[ChatMessage]) -> list[ChatMessage]` |

### `WindowTruncationStrategy` (concrete, the only implementation for v1)

Keeps the most recent `window_turns` user/assistant pairs (default 10, i.e. 20 messages), drops everything older. No summarization, no token estimation — a turn is either fully kept or fully dropped.

## In-memory active-stream registry

Not a persisted entity — a runtime detail `ChatService` needs to make cancellation possible at all. A single-process dict, `conversation_id -> asyncio.Task`, tracking the task currently streaming a response for that conversation. Registered when `send_message` starts, removed in a `finally` block regardless of outcome. `cancel_conversation` looks up the task here (after verifying ownership via `ConversationRepository.get`) and calls `.cancel()` on it — this is what actually triggers the `CancelledError` that `InstrumentedProvider` (Unit 1) catches and logs.
