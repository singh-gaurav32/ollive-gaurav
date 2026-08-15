# Functional Design Plan — Unit 2: Chatbot Spine (Streaming Chat + Memory)

## Execution Checklist

- [x] Confirm context truncation strategy (see Question 1) — Strategy pattern, WindowTruncationStrategy default
- [x] Confirm concurrent-conversation policy (see Question 2) — A: multiple independently-active conversations
- [x] Confirm message persistence timing (see Question 3) — A: once, after stream ends (success or cancellation)
- [x] Confirm seed-user policy for pre-auth isolation testing (see Question 4) — A: single fixed seed user
- [x] Confirm chat-turn error handling (see Question 5) — A: propagate, discard partial assistant content
- [x] Generate `business-logic-model.md`
- [x] Generate `business-rules.md`
- [x] Generate `domain-entities.md` (conversation lifecycle state machine)
- No `frontend-components.md` — no UI in this unit (frontend is Unit 5, per Q2 of Units Generation)

---

## Question 1: Context truncation strategy
US-2.3 requires the assistant to keep responding sensibly once a conversation exceeds the model's context window.

A) **Fixed turn-count window** — keep only the most recent N message pairs (e.g. last 10 user/assistant turns), drop everything older. Simple, predictable, no extra LLM calls.

B) **Token-budget window** — keep as many of the most recent messages as fit under a token budget (e.g. 80% of the model's context window), computed by estimating tokens per message. More accurate use of the window, more moving parts.

C) **Summarization** — once history exceeds a threshold, replace the oldest turns with an LLM-generated summary message. Best continuity, costs an extra LLM call and adds real complexity for a take-home.

D) Other (please describe after [Answer]: tag below)

[Answer]: Strategy pattern — define a `ContextTruncationStrategy` interface (unit-owned, lives in `chat/`, not a shared package, since only `ChatService` ever calls it) with `WindowTruncationStrategy` (fixed turn-count, i.e. option A) as the sole concrete implementation for now. `ChatService` depends on the interface, so token-budget (B) or summarization (C) truncation can be added later as a new class without touching `ChatService`. Default window: last 10 user/assistant turn-pairs, configurable via the strategy's constructor.

## Question 2: Concurrent-conversation policy
Can a user have more than one conversation active at once, or does starting a new one affect existing ones?

A) A user can have any number of conversations, all independently active — starting a new one doesn't touch existing ones. "Active" just means "not cancelled," not "the only one in progress."

B) A user has at most one active conversation at a time — starting a new one auto-cancels or archives whatever was active

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3: Message persistence timing
When does the assistant's response get written to `MessageRepository`?

A) Once, after the stream completes (or is cancelled) — one write with the full (or partial) accumulated content. Matches Unit 1's precedent of accumulating output during streaming and acting once at the end.

B) Incrementally, appending partial content as tokens arrive, then finalizing — more resilient to a server crash mid-stream, meaningfully more complexity for a take-home's likelihood of that failure mode.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: Seed-user policy
Unit 5 hasn't landed yet, so there's no real login. `UserRepository.get_or_create_seed_user()` exists for this.

A) A single fixed seed user for all of Unit 2 — isolation itself isn't testable until Unit 5, and that's fine; Unit 2's job is just to prove the `user_id` column is populated correctly, not to prove isolation end-to-end.

B) Seed 2-3 demo users now, and write an isolation test in Unit 2 itself (call `ConversationRepository.get()` with the wrong user's ID and assert `None`) — proves the isolation guarantee (US-5.4's foundation) earlier, before it's wired to real auth.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5: Chat-turn error handling
If the provider call fails mid-turn (network error, API error — surfaced by `InstrumentedProvider` re-raising per BR5), what does `ChatService` do?

A) Let the exception propagate to the API layer as-is; whatever partial assistant content existed (if any) is discarded, not persisted. The API layer is responsible for turning it into an HTTP error response.

B) Catch it in `ChatService`, persist a message noting the failure (e.g. role=assistant, content="[error: ...]"), then re-raise — so the conversation history shows something happened, not just a gap

C) Other (please describe after [Answer]: tag below)

[Answer]: A
