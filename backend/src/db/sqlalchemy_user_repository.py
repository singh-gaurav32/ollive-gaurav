"""SQLAlchemy implementation of UserRepository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from .models import Session, User
from .orm import SessionORM, UserORM
from .user_repository import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def get_by_username(self, username: str) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(select(UserORM).where(UserORM.username == username))
            row = result.scalar_one_or_none()
            return User(id=row.id, username=row.username, created_at=row.created_at) if row else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(select(UserORM).where(UserORM.id == user_id))
            row = result.scalar_one_or_none()
            return User(id=row.id, username=row.username, created_at=row.created_at) if row else None

    async def create_user(self, username: str) -> User:
        async with self._session_factory() as session:
            row = UserORM(username=username)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return User(id=row.id, username=row.username, created_at=row.created_at)

    async def list_users(self) -> list[User]:
        async with self._session_factory() as session:
            result = await session.execute(select(UserORM).order_by(UserORM.username))
            return [User(id=row.id, username=row.username, created_at=row.created_at) for row in result.scalars().all()]

    async def create_session(self, user_id: UUID) -> Session:
        async with self._session_factory() as session:
            row = SessionORM(user_id=user_id)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return Session(id=row.id, user_id=row.user_id, created_at=row.created_at)

    async def get_session(self, session_id: UUID) -> Session | None:
        async with self._session_factory() as session:
            result = await session.execute(select(SessionORM).where(SessionORM.id == session_id))
            row = result.scalar_one_or_none()
            return Session(id=row.id, user_id=row.user_id, created_at=row.created_at) if row else None

    async def delete_session(self, session_id: UUID) -> None:
        async with self._session_factory() as session:
            await session.execute(delete(SessionORM).where(SessionORM.id == session_id))
            await session.commit()
