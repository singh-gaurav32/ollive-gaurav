"""Tests for InstrumentedProvider - verifies BR1-BR9 from the functional design
(aidlc-docs/construction/unit-01-provider-abstraction/functional-design/)."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from provider.instrumented_provider import InstrumentedProvider
from provider.interface import ProviderResponse
from provider.models import Message, Role, Token

from .doubles import FakeEventQueue, FakeLLMProvider


def _messages() -> list[Message]:
    return [Message(role=Role.USER, content="hello")]


async def test_send_success_publishes_log_event_with_expected_fields():
    fake_provider = FakeLLMProvider()
    fake_provider.will_return(ProviderResponse(content="hi there", input_tokens=3, output_tokens=2))
    queue = FakeEventQueue()
    instrumented = InstrumentedProvider(fake_provider, queue, provider_name="fake")

    response = await instrumented.send(_messages(), conversation_id=uuid4(), session_id=uuid4())

    assert response.content == "hi there"
    assert len(queue.published) == 1
    event = queue.published[0]
    assert event.status == "success"
    assert event.input_tokens == 3
    assert event.output_tokens == 2
    assert event.latency_ms >= 0
    assert event.output_preview == "hi there"
    assert event.error_message is None


async def test_send_provider_error_is_reraised_and_logged():
    fake_provider = FakeLLMProvider()
    fake_provider.will_raise(RuntimeError("boom"))
    queue = FakeEventQueue()
    instrumented = InstrumentedProvider(fake_provider, queue, provider_name="fake")

    with pytest.raises(RuntimeError, match="boom"):
        await instrumented.send(_messages(), conversation_id=uuid4(), session_id=uuid4())

    assert len(queue.published) == 1
    event = queue.published[0]
    assert event.status == "error"
    assert event.error_message is not None and "boom" in event.error_message


async def test_publish_failure_is_swallowed_not_raised():
    fake_provider = FakeLLMProvider()
    fake_provider.will_return(ProviderResponse(content="hi", input_tokens=1, output_tokens=1))
    queue = FakeEventQueue(fail_publish=True)
    instrumented = InstrumentedProvider(fake_provider, queue, provider_name="fake")

    # Should not raise despite the queue always failing to publish (BR5/BR9).
    response = await instrumented.send(_messages(), conversation_id=uuid4(), session_id=uuid4())

    assert response.content == "hi"
    assert queue.published == []


async def test_stream_measures_ttft_and_accumulates_provider_reported_tokens():
    fake_provider = FakeLLMProvider()
    fake_provider.will_stream(
        [
            Token(content="Hel"),
            Token(content="lo", input_tokens=5, output_tokens=2),
        ]
    )
    queue = FakeEventQueue()
    instrumented = InstrumentedProvider(fake_provider, queue, provider_name="fake")

    collected = [
        token.content
        async for token in instrumented.stream(_messages(), conversation_id=uuid4(), session_id=uuid4())
    ]

    assert "".join(collected) == "Hello"
    assert len(queue.published) == 1
    event = queue.published[0]
    assert event.status == "success"
    assert event.ttft_ms is not None
    assert event.input_tokens == 5
    assert event.output_tokens == 2
    assert event.output_preview == "Hello"


async def test_stream_cancellation_publishes_cancelled_status_with_partial_output():
    fake_provider = FakeLLMProvider()
    fake_provider.will_stream(
        [Token(content="Hel"), Token(content="lo"), Token(content=" there")],
        cancel_after=1,
    )
    queue = FakeEventQueue()
    instrumented = InstrumentedProvider(fake_provider, queue, provider_name="fake")

    with pytest.raises(asyncio.CancelledError):
        async for _ in instrumented.stream(_messages(), conversation_id=uuid4(), session_id=uuid4()):
            pass

    assert len(queue.published) == 1
    event = queue.published[0]
    assert event.status == "cancelled"
    assert event.output_preview == "Hel"
