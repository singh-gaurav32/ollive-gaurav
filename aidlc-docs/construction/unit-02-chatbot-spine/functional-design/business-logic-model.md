# Business Logic Model — Unit 2: Chatbot Spine

## `ChatService.start_conversation(user_id)`
1. `ConversationRepository.create(user_id)`. Returns the new `Conversation` (state `"active"`).

## `ChatService.send_message(conversation_id, user_id, content)` — the core flow

1. `conversation = ConversationRepository.get(conversation_id, user_id)`. If `None`, raise — not found or not owned (BR5).
2. `MessageRepository.append(conversation_id, role="user", content=content)` — persisted immediately (BR3), before anything provider-related happens.
3. `history = MessageRepository.list_for_conversation(conversation_id)`.
4. `truncated = truncation_strategy.truncate(history)` (BR2).
5. Convert `truncated` (`ChatMessage`s) + the new user message into `provider.Message` objects (role mapping: `"user"→Role.USER`, `"assistant"→Role.ASSISTANT`).
6. Create the streaming task, register it in the active-stream registry under `conversation_id` (BR6).
7. `async for token in instrumented_provider.stream(messages, conversation_id=conversation_id, session_id=session_id):` — accumulate `token.content`; `yield token` to the caller (API layer), transparent pass-through.
8. **On normal completion**: `MessageRepository.append(conversation_id, role="assistant", content=accumulated)` (BR4, success case).
9. **On `asyncio.CancelledError`**: `MessageRepository.append(conversation_id, role="assistant", content=accumulated_so_far)` (BR4, cancellation case — partial content kept), then `ConversationRepository.update_state(conversation_id, "cancelled")`, then re-raise `CancelledError`.
10. **On any other exception**: do not persist an assistant message (BR4, error case). Re-raise.
11. **Always** (`finally`): deregister the task from the active-stream registry (BR6), regardless of which of steps 8-10 ran.

## `ChatService.cancel_conversation(conversation_id, user_id)`
1. `conversation = ConversationRepository.get(conversation_id, user_id)`. If `None`, reject (BR5) — never reveal whether a conversation exists for another user.
2. Look up the task in the active-stream registry for `conversation_id`. If none is running (nothing to cancel — the stream already finished or was never started), this is a no-op, not an error.
3. `task.cancel()` — this is what triggers the `CancelledError` path in `send_message` (step 9 above) and, one layer further down, in `InstrumentedProvider.stream` (Unit 1, BR8).

## `ChatService.resume_conversation(conversation_id, user_id)`
1. `conversation = ConversationRepository.get(conversation_id, user_id)`. If `None`, reject (BR5).
2. If `conversation.state == "cancelled"`: `ConversationRepository.update_state(conversation_id, "active")`.
3. Return the conversation plus `MessageRepository.list_for_conversation(conversation_id)` (full history, untruncated — truncation only applies to what's sent to the provider, never to what's shown to the user).

## `ChatService.list_conversations(user_id)`
1. `ConversationRepository.list_for_user(user_id)` — already user-scoped by the repository itself.

## Key Invariant

Every state-changing method (`send_message`, `cancel_conversation`, `resume_conversation`) starts with the same ownership check (`ConversationRepository.get(conversation_id, user_id)` returning non-`None`) before doing anything else. There is no code path in this unit that mutates conversation or message state without that check happening first.
