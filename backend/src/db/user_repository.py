"""UserRepository: shared persistence contract for demo users and sessions.
Unit 2 implements only get_or_create_seed_user() for its stand-in user;
Unit 5 completes the interface with real login/session validation. See
the cross-cutting schema decision in unit-of-work.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .models import Session, User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_or_create_seed_user(self) -> User:
        """Unit 2's stand-in for real auth - returns a single fixed demo
        user until Unit 5 wires in real login. Stays in the interface
        permanently; only callers change once Unit 5 ships."""

    @abstractmethod
    async def create_session(self, user_id: UUID) -> Session: ...

    @abstractmethod
    async def get_session(self, session_id: UUID) -> Session | None: ...
