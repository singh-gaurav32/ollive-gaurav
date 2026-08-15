"""API-layer tests using FastAPI's TestClient with dependency overrides -
no real DB, no real Gemini. Exercises routing, request/response shapes,
and that ownership checks apply at the HTTP layer too."""
from __future__ import annotations

from fastapi.testclient import TestClient

from api import deps
from chat.service import ChatService
from chat.truncation import WindowTruncationStrategy
from db.models import User
from main import app
from provider.instrumented_provider import InstrumentedProvider
from provider.models import Token

from ..chat.doubles import FakeConversationRepository, FakeMessageRepository
from ..provider.doubles import FakeEventQueue, FakeLLMProvider


def _override_app(fake_provider: FakeLLMProvider, user: User) -> None:
    instrumented = InstrumentedProvider(fake_provider, FakeEventQueue(), provider_name="fake")
    service = ChatService(
        instrumented_provider=instrumented,
        conversation_repository=FakeConversationRepository(),
        message_repository=FakeMessageRepository(),
        truncation_strategy=WindowTruncationStrategy(),
    )
    app.dependency_overrides[deps.get_chat_service] = lambda: service
    app.dependency_overrides[deps.get_current_user] = lambda: user


def test_start_list_and_resume_conversation():
    _override_app(FakeLLMProvider(), User(username="test-user"))
    client = TestClient(app)

    create_resp = client.post("/conversations")
    assert create_resp.status_code == 200
    conversation_id = create_resp.json()["id"]

    list_resp = client.get("/conversations")
    assert len(list_resp.json()) == 1

    resume_resp = client.post(f"/conversations/{conversation_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["conversation"]["id"] == conversation_id

    app.dependency_overrides.clear()


def test_actions_on_another_users_conversation_return_404():
    _override_app(FakeLLMProvider(), User(username="owner"))
    client = TestClient(app)
    conversation_id = client.post("/conversations").json()["id"]

    app.dependency_overrides[deps.get_current_user] = lambda: User(username="other")

    resp = client.post(f"/conversations/{conversation_id}/cancel")

    assert resp.status_code == 404
    app.dependency_overrides.clear()


def test_send_message_streams_tokens_as_sse():
    fake_provider = FakeLLMProvider()
    fake_provider.will_stream([Token(content="Hi")])
    _override_app(fake_provider, User(username="test-user"))
    client = TestClient(app)
    conversation_id = client.post("/conversations").json()["id"]

    resp = client.post(f"/conversations/{conversation_id}/messages", json={"content": "hello"})

    assert resp.status_code == 200
    assert "event: token" in resp.text
    assert "Hi" in resp.text
    assert "event: done" in resp.text
    app.dependency_overrides.clear()


def test_send_message_on_nonexistent_conversation_returns_404():
    _override_app(FakeLLMProvider(), User(username="test-user"))
    client = TestClient(app)

    resp = client.post("/conversations/00000000-0000-0000-0000-000000000000/messages", json={"content": "hi"})

    assert resp.status_code == 404
    app.dependency_overrides.clear()
