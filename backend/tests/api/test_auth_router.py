"""API-layer tests for the auth flow - login sets a cookie, /auth/me
reflects it, logout clears it. Uses a fake AuthService, no real DB."""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from db.models import Session, User
from fastapi.testclient import TestClient

from api import deps
from main import app


class _FakeAuthService:
    def __init__(self, users: list[User]) -> None:
        self._users = {u.username: u for u in users}
        self._sessions: dict[UUID, User] = {}

    async def list_demo_users(self):
        return list(self._users.values())

    async def login(self, username: str) -> Session:
        from auth.service import UserNotFoundError

        user = self._users.get(username)
        if user is None:
            raise UserNotFoundError(username)
        session = Session(user_id=user.id)
        self._sessions[session.id] = user
        return session

    async def validate_session(self, session_id: UUID):
        return self._sessions.get(session_id)

    async def logout(self, session_id: UUID) -> None:
        self._sessions.pop(session_id, None)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _cookies_over_plain_http(monkeypatch):
    # TestClient talks to http://testserver, not https - same situation as
    # local dev, which is why this is also how local dev opts out of the
    # Secure cookie attribute (see auth/cookies.py). Without this, the
    # client's cookie jar would - correctly - refuse to store or resend a
    # Secure cookie over a non-HTTPS connection, exactly as a real browser
    # would, and every login-then-authenticated-request test below would see
    # a 401 regardless of whether login actually worked.
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")


def test_login_sets_cookie_and_me_reflects_it():
    alice = User(username="alice")
    # A single shared instance, not "lambda: _FakeAuthService(...)" - that
    # would construct a fresh (session-less) instance on every dependency
    # resolution, so login's session would never be visible to /auth/me.
    fake_service = _FakeAuthService([alice])
    app.dependency_overrides[deps.get_auth_service] = lambda: fake_service
    client = TestClient(app)

    login_resp = client.post("/auth/login", json={"username": "alice"})
    assert login_resp.status_code == 200
    assert login_resp.json()["username"] == "alice"
    assert "session_id" in login_resp.cookies

    me_resp = client.get("/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "alice"


def test_login_cookie_is_secure_by_default(monkeypatch):
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)  # undo the autouse fixture above
    app.dependency_overrides[deps.get_auth_service] = lambda: _FakeAuthService([User(username="alice")])
    client = TestClient(app)

    login_resp = client.post("/auth/login", json={"username": "alice"})

    assert "secure" in login_resp.headers["set-cookie"].lower()


def test_login_cookie_omits_secure_when_explicitly_disabled():
    # SESSION_COOKIE_SECURE=false is set by the autouse fixture above -
    # same opt-out local dev/docker-compose use for plain-HTTP environments.
    app.dependency_overrides[deps.get_auth_service] = lambda: _FakeAuthService([User(username="alice")])
    client = TestClient(app)

    login_resp = client.post("/auth/login", json={"username": "alice"})

    assert "secure" not in login_resp.headers["set-cookie"].lower()


def test_login_with_unknown_username_returns_404():
    app.dependency_overrides[deps.get_auth_service] = lambda: _FakeAuthService([])
    client = TestClient(app)

    resp = client.post("/auth/login", json={"username": "nobody"})

    assert resp.status_code == 404


def test_me_without_a_session_returns_401():
    app.dependency_overrides[deps.get_auth_service] = lambda: _FakeAuthService([])
    client = TestClient(app)

    resp = client.get("/auth/me")

    assert resp.status_code == 401


def test_logout_invalidates_the_session():
    alice = User(username="alice")
    fake_service = _FakeAuthService([alice])
    app.dependency_overrides[deps.get_auth_service] = lambda: fake_service
    client = TestClient(app)
    client.post("/auth/login", json={"username": "alice"})

    # Prove the session was actually valid before logout - otherwise a
    # post-logout 401 would be true regardless of whether logout did
    # anything (see the same bug fixed in the test above this one).
    assert client.get("/auth/me").status_code == 200

    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200

    me_resp = client.get("/auth/me")
    assert me_resp.status_code == 401
