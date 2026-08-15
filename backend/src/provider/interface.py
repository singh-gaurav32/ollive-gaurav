"""LLMProvider: the Strategy/Adapter interface every concrete provider implements.

conversation_id/session_id are part of the interface itself (not bolted onto
InstrumentedProvider only) so every implementation honors the same contract -
GeminiProvider accepts and ignores them; InstrumentedProvider uses them to
populate LogEvent. Keeps the Decorator relationship strictly substitutable.

See aidlc-docs/inception/application-design/components.md for the design
rationale.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from uuid import UUID

from .models import Message, Token


class ProviderResponse:
    """Result of a non-streaming send() call."""

    def __init__(
        self,
        content: str,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        raw: dict | None = None,
    ) -> None:
        self.content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.raw = raw or {}


class ProviderError(Exception):
    """Normalized error raised by any LLMProvider implementation."""

    def __init__(self, message: str, *, provider: str, original: Exception | None = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.original = original


class LLMProvider(ABC):
    """Strategy interface abstracting a single LLM provider's call boundary."""

    @abstractmethod
    async def send(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> ProviderResponse:
        """Non-streaming completion. Raises ProviderError on failure."""

    @abstractmethod
    def stream(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> AsyncIterator[Token]:
        """Streaming completion - an async generator of Token. Raises ProviderError on failure."""
