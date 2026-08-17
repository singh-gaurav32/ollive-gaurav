"""UserRepository: shared persistence contract for demo users and sessions.
See the cross-cutting schema decision in unit-of-work.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .models import Session, User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Unit 5: resolves a Session's user_id back into a User for
        validate_session."""

    @abstractmethod
    async def create_user(self, username: str) -> User:
        """Unit 5: used by demo-user seeding at startup."""

    @abstractmethod
    async def list_users(self) -> list[User]:
        """Unit 5: powers the login picker."""

    @abstractmethod
    async def create_session(self, user_id: UUID) -> Session: ...

    @abstractmethod
    async def get_session(self, session_id: UUID) -> Session | None: ...

    @abstractmethod
    async def delete_session(self, session_id: UUID) -> None:
        """Unit 5: logout."""
