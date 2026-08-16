"""SQLAlchemy implementation of FailedLogEventRepository."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker

from .failed_log_event_repository import FailedLogEventRepository
from .models import FailedLogEvent
from .orm import FailedLogEventORM


class SqlAlchemyFailedLogEventRepository(FailedLogEventRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def insert(self, record: FailedLogEvent) -> None:
        async with self._session_factory() as session:
            row = FailedLogEventORM(
                id=record.id,
                model=record.model,
                provider=record.provider,
                conversation_id=record.conversation_id,
                session_id=record.session_id,
                timestamp=record.timestamp,
                failure_stage=record.failure_stage,
                failure_reason=record.failure_reason,
            )
            session.add(row)
            await session.commit()
