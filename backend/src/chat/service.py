"""ChatService: owns both LLM call orchestration and conversation lifecycle
(single service, per Application Design Q3). Implements the flow in
aidlc-docs/construction/unit-02-chatbot-spine/functional-design/
business-logic-model.md.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from uuid import UUID

from db.conversation_repository import ConversationRepository
from db.message_repository import MessageRepository
from db.models import ChatMessage, Conversation
from provider.instrumented_provider import InstrumentedProvider
from provider.models import Message, Role, Token
from pydantic import BaseModel

from .truncation import ContextTruncationStrategy

# BR6 (horizontal-scaling fix): how often _run() checks the DB for a
# cancellation requested by a *different* pod, where this pod's
# _active_streams has no matching Task to have been cancelled directly.
# Wall-clock throttled rather than per-token, so a fast token stream doesn't
# turn into a DB query per token.
_CANCELLATION_POLL_INTERVAL_SECONDS = 0.5


class ConversationNotFoundError(Exception):
    """Raised when a conversation doesn't exist or isn't owned by the caller."""


class ConversationDetail(BaseModel):
    conversation: Conversation
    messages: list[ChatMessage]


class ChatService:
    def __init__(
        self,
        instrumented_provider: InstrumentedProvider,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        truncation_strategy: ContextTruncationStrategy,
        cancellation_poll_interval_seconds: float = _CANCELLATION_POLL_INTERVAL_SECONDS,
    ) -> None:
        self._provider = instrumented_provider
        self._conversations = conversation_repository
        self._messages = message_repository
        self._truncation = truncation_strategy
        self._cancellation_poll_interval = cancellation_poll_interval_seconds
        # BR6: in-memory registry of the task currently streaming a response
        # for a given conversation, so a same-pod cancel_conversation call
        # can reach it directly and instantly. Still process-local by nature
        # (an asyncio.Task can't be reached across processes at all) - the
        # cross-pod case is handled separately, by _run()'s DB poll below,
        # not by making this registry itself distributed.
        self._active_streams: dict[UUID, asyncio.Task] = {}

    async def start_conversation(self, user_id: UUID) -> Conversation:
        return await self._conversations.create(user_id)

    async def list_conversations(self, user_id: UUID) -> list[Conversation]:
        return await self._conversations.list_for_user(user_id)

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Conversation:
        conversation = await self._conversations.get(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    async def resume_conversation(self, conversation_id: UUID, user_id: UUID) -> ConversationDetail:
        conversation = await self.get_conversation(conversation_id, user_id)  # BR5
        if conversation.state == "cancelled":
            await self._conversations.update_state(conversation_id, "active")
            conversation = conversation.model_copy(update={"state": "active"})
        history = await self._messages.list_for_conversation(conversation_id)
        return ConversationDetail(conversation=conversation, messages=history)

    async def cancel_conversation(self, conversation_id: UUID, user_id: UUID) -> None:
        await self.get_conversation(conversation_id, user_id)  # BR5 - reject before touching the registry
        # Cross-pod-visible signal, written unconditionally (BR6): a
        # different pod's _run() can never be reached through this pod's
        # in-memory _active_streams, so the DB write - not the registry - is
        # the mechanism that reaches it, via the poll in _run() below.
        await self._conversations.update_state(conversation_id, "cancelled")
        task = self._active_streams.get(conversation_id)
        if task is not None:
            task.cancel()  # same-pod fast path: near-instant, doesn't wait on a poll
        # No running stream *in this pod's registry* is not an error - the
        # response may have already finished, may never have started, or may
        # be running on a different pod and will pick up the state write
        # above on its own next poll.

    @staticmethod
    def _to_provider_messages(history: list[ChatMessage], new_content: str) -> list[Message]:
        role_map = {"user": Role.USER, "assistant": Role.ASSISTANT}
        messages = [Message(role=role_map[m.role], content=m.content) for m in history]
        messages.append(Message(role=Role.USER, content=new_content))
        return messages

    async def send_message(
        self, conversation_id: UUID, user_id: UUID, content: str, session_id: UUID
    ) -> AsyncIterator[Token]:
        await self.get_conversation(conversation_id, user_id)  # BR5

        await self._messages.append(conversation_id, role="user", content=content)  # BR3
        history = await self._messages.list_for_conversation(conversation_id)
        truncated = self._truncation.truncate(history[:-1])  # exclude the message just appended
        provider_messages = self._to_provider_messages(truncated, content)

        # Task+queue bridge: send_message itself is an async generator, but
        # cancel_conversation is invoked from a *separate* request/coroutine
        # and needs a real asyncio.Task to call .cancel() on (BR6). A plain
        # async generator has no such handle - so the actual provider call
        # runs in an explicit background task, and this generator relays
        # tokens from it via a queue.
        queue: asyncio.Queue = asyncio.Queue()

        async def _run() -> None:
            accumulated: list[str] = []
            last_poll = time.monotonic()
            try:
                async for token in self._provider.stream(
                    provider_messages, conversation_id=conversation_id, session_id=session_id
                ):
                    accumulated.append(token.content)
                    await queue.put(token)

                    # BR6 (horizontal-scaling fix): pick up a cancellation
                    # requested on a different pod, where _active_streams
                    # never had a Task to reach directly. Self-cancelling
                    # (rather than just breaking this loop) raises
                    # CancelledError at the next await point below, so it
                    # flows through InstrumentedProvider.stream's own
                    # cancellation handling exactly like an external
                    # task.cancel() would - not a separate code path.
                    now = time.monotonic()
                    if now - last_poll >= self._cancellation_poll_interval:
                        last_poll = now
                        conversation = await self._conversations.get(conversation_id, user_id)
                        if conversation is not None and conversation.state == "cancelled":
                            asyncio.current_task().cancel()
            except asyncio.CancelledError:
                # BR4 (cancellation case): partial content is kept.
                await self._messages.append(
                    conversation_id, role="assistant", content="".join(accumulated)
                )
                await self._conversations.update_state(conversation_id, "cancelled")
                await queue.put(None)
                raise
            except Exception as exc:
                # BR4 (error case): nothing persisted for the assistant turn.
                await queue.put(exc)
            else:
                # BR4 (success case): persist the full accumulated content.
                await self._messages.append(
                    conversation_id, role="assistant", content="".join(accumulated)
                )
                await queue.put(None)

        task = asyncio.create_task(_run())
        self._active_streams[conversation_id] = task
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
            await task  # re-raises CancelledError if that's how _run ended
        finally:
            self._active_streams.pop(conversation_id, None)  # BR6: always deregistered
