# Business Rules — Unit 2: Chatbot Spine

**BR1 — A user may have any number of independently active conversations.** Starting a new conversation never affects the state of any other conversation (Q2).

**BR2 — Truncation is delegated to a swappable strategy, never inlined in `ChatService`.** The default `WindowTruncationStrategy` keeps the most recent 10 turn-pairs (20 messages) and drops the rest outright — no summarization, no token estimation in v1 (Q1).

**BR3 — The user's message is persisted immediately, independent of what happens to the assistant's turn.** The user already said it; a later provider failure must never cause it to be lost.

**BR4 — The assistant's message is persisted exactly once, after the stream ends — but only on success or cancellation, never on error.**
- Success: persist the full accumulated content.
- Cancellation: persist whatever partial content had accumulated at the point of cancellation (Q3), and transition the conversation to `"cancelled"` via `ConversationRepository.update_state`.
- Any other exception (provider error, network failure): **nothing is persisted for the assistant's turn** — the exception propagates to the API layer as-is (Q5). The user sees no trace of a failed attempt in conversation history; this is deliberately different from cancellation, where partial content is kept.

**BR5 — Ownership is checked before any state-changing action, not just before reads.** `cancel_conversation` and `resume_conversation` both call `ConversationRepository.get(conversation_id, user_id)` first — if it returns `None` (wrong owner, or doesn't exist), the action is rejected before it touches the active-stream registry or the state column. This is the isolation guarantee (US-5.4's foundation) applied to writes, not just to reads.

**BR6 — Cancellation works by cancelling the actual asyncio task, not a flag the streaming loop polls.** `send_message` registers its task in the in-memory active-stream registry on start and deregisters it in a `finally` block. `cancel_conversation` looks up that task and calls `.cancel()` on it directly — this is what produces the `CancelledError` that `InstrumentedProvider` (Unit 1, BR8) observes and logs.

**BR7 — Isolation is enforced by all of Unit 2's own code today, even though only one seed user exists to test it against.** `ConversationRepository`'s interface (fixed in the shared-contracts pass) is already user-scoped; Unit 2 uses it that way from the start rather than adding scoping later when Unit 5 introduces real multiple users (Q4).
