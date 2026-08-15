"""ChatService: owns both LLM call orchestration and conversation lifecycle
(single service, per Application Design Q3). Implements the flow in
aidlc-docs/construction/unit-02-chatbot-spine/functional-design/
business-logic-model.md.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from db.conversation_repository import ConversationRepository
from db.message_repository import MessageRepository
from db.models import ChatMessage, Conversation
from provider.instrumented_provider import InstrumentedProvider
from provider.models import Message, Role, Token
from pydantic import BaseModel

from .truncation import ContextTruncationStrategy


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
    ) -> None:
        self._provider = instrumented_provider
        self._conversations = conversation_repository
        self._messages = message_repository
        self._truncation = truncation_strategy
        # BR6: in-memory registry of the task currently streaming a response
        # for a given conversation, so cancel_conversation can reach it.
        # Single-process only (Units Generation Q1) - correct for this
        # architecture, would need to move to something shared if the
        # worker ever ran as a separate process.
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
        task = self._active_streams.get(conversation_id)
        if task is not None:
            task.cancel()
        # No running stream is not an error - the response may have already
        # finished, or never started; cancel is a best-effort action.

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
            try:
                async for token in self._provider.stream(
                    provider_messages, conversation_id=conversation_id, session_id=session_id
                ):
                    accumulated.append(token.content)
                    await queue.put(token)
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
