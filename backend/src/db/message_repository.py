"""MessageRepository: shared persistence contract for chat messages.
Implemented by Unit 2.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .models import ChatMessage, MessageRole


class MessageRepository(ABC):
    @abstractmethod
    async def append(self, conversation_id: UUID, role: MessageRole, content: str) -> ChatMessage: ...

    @abstractmethod
    async def list_for_conversation(self, conversation_id: UUID) -> list[ChatMessage]: ...
