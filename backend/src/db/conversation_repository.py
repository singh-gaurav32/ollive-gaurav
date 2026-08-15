"""ConversationRepository: shared persistence contract for conversations.
Implemented by Unit 2. Later units reach this only through ChatService,
never by importing the repository directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .models import Conversation, ConversationState


class ConversationRepository(ABC):
    @abstractmethod
    async def create(self, user_id: UUID) -> Conversation: ...

    @abstractmethod
    async def get(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        """User-scoped: returns None (never another user's conversation) if
        the conversation belongs to someone else - this is the isolation
        guarantee behind US-5.4, not a policy layered on top of it."""

    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[Conversation]: ...

    @abstractmethod
    async def update_state(self, conversation_id: UUID, new_state: ConversationState) -> None: ...
