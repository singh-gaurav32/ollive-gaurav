"""Tests for ChatService - the core business-logic coverage for Unit 2.
Uses in-memory fakes throughout; no real DB, no real Gemini."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from chat.service import ChatService, ConversationNotFoundError
from chat.truncation import WindowTruncationStrategy
from provider.instrumented_provider import InstrumentedProvider
from provider.models import Token

from ..provider.doubles import FakeEventQueue, FakeLLMProvider
from .doubles import FakeConversationRepository, FakeMessageRepository


def _make_service(fake_provider: FakeLLMProvider) -> tuple[ChatService, FakeConversationRepository, FakeMessageRepository]:
    conversation_repo = FakeConversationRepository()
    message_repo = FakeMessageRepository()
    instrumented = InstrumentedProvider(fake_provider, FakeEventQueue(), provider_name="fake")
    service = ChatService(
        instrumented_provider=instrumented,
        conversation_repository=conversation_repo,
        message_repository=message_repo,
        truncation_strategy=WindowTruncationStrategy(),
    )
    return service, conversation_repo, message_repo


async def _consume(stream) -> list[str]:
    return [token.content async for token in stream]


async def test_send_message_persists_user_and_assistant_messages_on_success():
    fake_provider = FakeLLMProvider()
    fake_provider.will_stream([Token(content="Hi"), Token(content=" there")])
    service, _, messages = _make_service(fake_provider)
    user_id = uuid4()
    conversation = await service.start_conversation(user_id)

    collected = await _consume(
        service.send_message(conversation.id, user_id, "hello", session_id=user_id)
    )

    assert collected == ["Hi", " there"]
    history = await messages.list_for_conversation(conversation.id)
    assert [m.role for m in history] == ["user", "assistant"]
    assert history[0].content == "hello"
    assert history[1].content == "Hi there"


async def test_send_message_rejects_wrong_owner():
    fake_provider = FakeLLMProvider()
    service, _, _ = _make_service(fake_provider)
    owner_id = uuid4()
    other_user_id = uuid4()
    conversation = await service.start_conversation(owner_id)

    with pytest.raises(ConversationNotFoundError):
        await _consume(
            service.send_message(conversation.id, other_user_id, "hi", session_id=other_user_id)
        )


async def test_send_message_persists_user_message_even_when_provider_fails():
    fake_provider = FakeLLMProvider()
    fake_provider.will_stream([Token(content="partial")])
    fake_provider.will_raise(RuntimeError("boom"))
    service, _, messages = _make_service(fake_provider)
    user_id = uuid4()
    conversation = await service.start_conversation(user_id)

    with pytest.raises(RuntimeError):
        await _consume(
            service.send_message(conversation.id, user_id, "hello", session_id=user_id)
        )

    history = await messages.list_for_conversation(conversation.id)
    # user message persisted; no assistant message, since the provider call
    # failed after yielding partial content (BR4 - error case).
    assert [m.role for m in history] == ["user"]


async def test_cancel_rejects_wrong_owner():
    fake_provider = FakeLLMProvider()
    service, _, _ = _make_service(fake_provider)
    owner_id = uuid4()
    other_user_id = uuid4()
    conversation = await service.start_conversation(owner_id)

    with pytest.raises(ConversationNotFoundError):
        await service.cancel_conversation(conversation.id, other_user_id)


async def test_cancel_is_a_no_op_when_nothing_is_running():
    fake_provider = FakeLLMProvider()
    service, _, _ = _make_service(fake_provider)
    user_id = uuid4()
    conversation = await service.start_conversation(user_id)

    await service.cancel_conversation(conversation.id, user_id)  # should not raise


async def test_cancel_finds_and_cancels_the_correct_running_task():
    """Deterministic (event-synchronized) test of the registry mechanism
    itself - cancel_conversation is called from a separate task while
    send_message's stream is genuinely still in progress, not just
    simulated via a scripted cancellation inside the fake provider."""

    class SlowFakeProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__()
            self.first_token_yielded = asyncio.Event()
            self.may_continue = asyncio.Event()

        async def stream(self, messages, *, conversation_id, session_id):
            yield Token(content="Hel")
            self.first_token_yielded.set()
            await self.may_continue.wait()
            yield Token(content="lo")  # pragma: no cover - never reached once cancelled

    fake_provider = SlowFakeProvider()
    service, conversations, messages = _make_service(fake_provider)
    user_id = uuid4()
    conversation = await service.start_conversation(user_id)

    collected: list[str] = []

    async def consume() -> None:
        async for token in service.send_message(conversation.id, user_id, "hi", session_id=user_id):
            collected.append(token.content)

    consumer_task = asyncio.create_task(consume())
    await fake_provider.first_token_yielded.wait()

    await service.cancel_conversation(conversation.id, user_id)

    with pytest.raises(asyncio.CancelledError):
        await consumer_task

    assert collected == ["Hel"]
    history = await messages.list_for_conversation(conversation.id)
    assert history[-1].role == "assistant"
    assert history[-1].content == "Hel"
    updated = await conversations.get(conversation.id, user_id)
    assert updated.state == "cancelled"


async def test_resume_transitions_cancelled_to_active_and_returns_history():
    fake_provider = FakeLLMProvider()
    service, conversations, messages = _make_service(fake_provider)
    user_id = uuid4()
    conversation = await service.start_conversation(user_id)
    await conversations.update_state(conversation.id, "cancelled")
    await messages.append(conversation.id, role="user", content="hi")

    detail = await service.resume_conversation(conversation.id, user_id)

    assert detail.conversation.state == "active"
    assert len(detail.messages) == 1


async def test_list_conversations_is_scoped_to_user():
    fake_provider = FakeLLMProvider()
    service, _, _ = _make_service(fake_provider)
    user_a = uuid4()
    user_b = uuid4()
    await service.start_conversation(user_a)
    await service.start_conversation(user_b)

    conversations = await service.list_conversations(user_a)

    assert len(conversations) == 1
    assert conversations[0].user_id == user_a
