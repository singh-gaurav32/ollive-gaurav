"""Test doubles for the provider unit's tests."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from events.event_queue import EventQueue
from events.log_event import LogEvent
from provider.interface import LLMProvider, ProviderResponse
from provider.models import Message, Token


class FakeLLMProvider(LLMProvider):
    """Controllable double: scripted response, error, or a token sequence
    with optional mid-stream cancellation, for exercising InstrumentedProvider."""

    def __init__(self, model: str = "fake-model") -> None:
        self.model = model
        self._response: ProviderResponse | None = None
        self._error: Exception | None = None
        self._tokens: list[Token] = []
        self._cancel_after: int | None = None

    def will_return(self, response: ProviderResponse) -> None:
        self._response = response

    def will_raise(self, error: Exception) -> None:
        self._error = error

    def will_stream(self, tokens: list[Token], *, cancel_after: int | None = None) -> None:
        self._tokens = tokens
        self._cancel_after = cancel_after

    async def send(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> ProviderResponse:
        if self._error is not None:
            raise self._error
        assert self._response is not None, "FakeLLMProvider: call will_return() first"
        return self._response

    async def stream(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> AsyncIterator[Token]:
        for i, token in enumerate(self._tokens):
            if self._cancel_after is not None and i == self._cancel_after:
                raise asyncio.CancelledError()
            yield token
        if self._error is not None:
            raise self._error


class FakeEventQueue(EventQueue):
    """Records published events; can simulate a publish failure."""

    def __init__(self, *, fail_publish: bool = False) -> None:
        self.published: list[LogEvent] = []
        self._fail_publish = fail_publish

    async def publish(self, event: LogEvent) -> None:
        if self._fail_publish:
            raise RuntimeError("simulated publish failure")
        self.published.append(event)

    def consume(self):  # pragma: no cover - not exercised by this unit's tests
        raise NotImplementedError
