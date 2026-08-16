"""AuthService: pick-a-user login (no password, BR1), completing the
interface sketched in application-design/component-methods.md.
"""
from __future__ import annotations

from uuid import UUID

from db.models import Session, User
from db.user_repository import UserRepository

DEMO_USERNAMES = ["alice", "bob", "carol"]


class UserNotFoundError(Exception):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def list_demo_users(self) -> list[User]:
        return await self._users.list_users()

    async def login(self, username: str) -> Session:
        user = await self._users.get_by_username(username)
        if user is None:
            raise UserNotFoundError(username)
        return await self._users.create_session(user.id)

    async def validate_session(self, session_id: UUID) -> User | None:
        session = await self._users.get_session(session_id)
        if session is None:
            return None
        return await self._users.get_by_id(session.user_id)

    async def logout(self, session_id: UUID) -> None:
        await self._users.delete_session(session_id)
