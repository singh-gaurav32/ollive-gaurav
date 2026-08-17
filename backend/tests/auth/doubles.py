"""In-memory fake for AuthService's UserRepository dependency."""
from __future__ import annotations

from uuid import UUID

from db.models import Session, User
from db.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}
        self.sessions: dict[UUID, Session] = {}

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self.users.values() if u.username == username), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def create_user(self, username: str) -> User:
        user = User(username=username)
        self.users[user.id] = user
        return user

    async def list_users(self) -> list[User]:
        return list(self.users.values())

    async def create_session(self, user_id: UUID) -> Session:
        session = Session(user_id=user_id)
        self.sessions[session.id] = session
        return session

    async def get_session(self, session_id: UUID) -> Session | None:
        return self.sessions.get(session_id)

    async def delete_session(self, session_id: UUID) -> None:
        self.sessions.pop(session_id, None)
