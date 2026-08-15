"""SQLAlchemy implementation of MessageRepository. Session-per-operation,
same as the conversation repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from .message_repository import MessageRepository
from .models import ChatMessage, MessageRole
from .orm import MessageORM


class SqlAlchemyMessageRepository(MessageRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: MessageORM) -> ChatMessage:
        return ChatMessage(
            id=row.id,
            conversation_id=row.conversation_id,
            role=row.role,
            content=row.content,
            created_at=row.created_at,
        )

    async def append(self, conversation_id: UUID, role: MessageRole, content: str) -> ChatMessage:
        async with self._session_factory() as session:
            row = MessageORM(conversation_id=conversation_id, role=role, content=content)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_domain(row)

    async def list_for_conversation(self, conversation_id: UUID) -> list[ChatMessage]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MessageORM)
                .where(MessageORM.conversation_id == conversation_id)
                .order_by(MessageORM.created_at.asc())
            )
            return [self._to_domain(row) for row in result.scalars().all()]
