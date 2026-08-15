"""SQLAlchemy implementation of ConversationRepository. Session-per-operation:
each method opens and closes its own session (NFR design)."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from .conversation_repository import ConversationRepository
from .models import Conversation, ConversationState
from .orm import ConversationORM


class SqlAlchemyConversationRepository(ConversationRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(row: ConversationORM) -> Conversation:
        return Conversation(
            id=row.id,
            user_id=row.user_id,
            state=row.state,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, user_id: UUID) -> Conversation:
        async with self._session_factory() as session:
            row = ConversationORM(user_id=user_id)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_domain(row)

    async def get(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ConversationORM).where(
                    ConversationORM.id == conversation_id,
                    ConversationORM.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            return self._to_domain(row) if row is not None else None

    async def list_for_user(self, user_id: UUID) -> list[Conversation]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ConversationORM)
                .where(ConversationORM.user_id == user_id)
                .order_by(ConversationORM.updated_at.desc())
            )
            return [self._to_domain(row) for row in result.scalars().all()]

    async def update_state(self, conversation_id: UUID, new_state: ConversationState) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ConversationORM).where(ConversationORM.id == conversation_id)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                row.state = new_state
                await session.commit()
