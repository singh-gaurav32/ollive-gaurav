"""In-memory fakes for ChatService's repository dependencies, so its
business logic can be tested without a real database."""
from __future__ import annotations

from uuid import UUID

from db.conversation_repository import ConversationRepository
from db.message_repository import MessageRepository
from db.models import ChatMessage, Conversation, ConversationState, MessageRole


class FakeConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._conversations: dict[UUID, Conversation] = {}

    async def create(self, user_id: UUID) -> Conversation:
        conversation = Conversation(user_id=user_id)
        self._conversations[conversation.id] = conversation
        return conversation

    async def get(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return None
        return conversation

    async def list_for_user(self, user_id: UUID) -> list[Conversation]:
        return [c for c in self._conversations.values() if c.user_id == user_id]

    async def update_state(self, conversation_id: UUID, new_state: ConversationState) -> None:
        conversation = self._conversations.get(conversation_id)
        if conversation is not None:
            self._conversations[conversation_id] = conversation.model_copy(update={"state": new_state})


class FakeMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self._messages: dict[UUID, list[ChatMessage]] = {}

    async def append(self, conversation_id: UUID, role: MessageRole, content: str) -> ChatMessage:
        message = ChatMessage(conversation_id=conversation_id, role=role, content=content)
        self._messages.setdefault(conversation_id, []).append(message)
        return message

    async def list_for_conversation(self, conversation_id: UUID) -> list[ChatMessage]:
        return list(self._messages.get(conversation_id, []))
