"""Tests for AuthService - login, session validation, logout."""
from __future__ import annotations

from uuid import uuid4

import pytest

from auth.service import AuthService, UserNotFoundError

from .doubles import FakeUserRepository


async def test_login_creates_a_session_for_a_known_user():
    users = FakeUserRepository()
    await users.create_user("alice")
    service = AuthService(users)

    session = await service.login("alice")

    assert session.user_id in [u.id for u in users.users.values()]


async def test_login_rejects_unknown_username():
    service = AuthService(FakeUserRepository())

    with pytest.raises(UserNotFoundError):
        await service.login("nobody")


async def test_validate_session_round_trips_to_the_correct_user():
    users = FakeUserRepository()
    alice = await users.create_user("alice")
    service = AuthService(users)
    session = await service.login("alice")

    validated = await service.validate_session(session.id)

    assert validated is not None
    assert validated.id == alice.id


async def test_validate_session_returns_none_for_unknown_session():
    service = AuthService(FakeUserRepository())

    result = await service.validate_session(uuid4())

    assert result is None


async def test_logout_invalidates_the_session():
    users = FakeUserRepository()
    await users.create_user("alice")
    service = AuthService(users)
    session = await service.login("alice")

    await service.logout(session.id)

    assert await service.validate_session(session.id) is None


async def test_list_demo_users_returns_seeded_users():
    users = FakeUserRepository()
    await users.create_user("alice")
    await users.create_user("bob")
    service = AuthService(users)

    result = await service.list_demo_users()

    assert {u.username for u in result} == {"alice", "bob"}
