"""InstrumentedProvider: the Decorator that auto-instruments any LLMProvider.

Implements the logic model and business rules (BR1-BR9) from
aidlc-docs/construction/unit-01-provider-abstraction/functional-design/.

Key invariant: instrumentation failures (can't publish to the queue) are
always swallowed and never visible to the caller; provider call failures
(including cancellation) are always observed as a LogEvent AND re-raised.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from uuid import UUID

from events.event_queue import EventQueue
from events.log_event import LogEvent, truncate_preview

from .interface import LLMProvider, ProviderResponse
from .models import Message, Token

logger = logging.getLogger(__name__)


class InstrumentedProvider(LLMProvider):
    """Wraps any LLMProvider, transparently capturing a LogEvent per call."""

    def __init__(self, wrapped: LLMProvider, event_queue: EventQueue, provider_name: str) -> None:
        self._wrapped = wrapped
        self._event_queue = event_queue
        self._provider_name = provider_name

    async def _publish(self, event: LogEvent) -> None:
        # BR5/BR9: instrumentation failures are swallowed and logged locally,
        # never propagated to the caller. Nothing to dead-letter here - the
        # event never entered the queue in the first place.
        try:
            await self._event_queue.publish(event)
        except Exception:  # noqa: BLE001 - intentionally broad, see BR5
            logger.warning("Failed to publish LogEvent; dropping.", exc_info=True)

    def _messages_preview(self, messages: list[Message]) -> str:
        return truncate_preview(" ".join(m.content for m in messages))

    async def send(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> ProviderResponse:
        start = time.monotonic()
        try:
            response = await self._wrapped.send(
                messages, conversation_id=conversation_id, session_id=session_id
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            await self._publish(
                LogEvent(
                    model=getattr(self._wrapped, "model", "unknown"),
                    provider=self._provider_name,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=str(exc),
                    conversation_id=conversation_id,
                    session_id=session_id,
                    input_preview=self._messages_preview(messages),
                    output_preview="",
                )
            )
            raise  # BR5: provider failures are always re-raised

        latency_ms = (time.monotonic() - start) * 1000
        await self._publish(
            LogEvent(
                model=getattr(self._wrapped, "model", "unknown"),
                provider=self._provider_name,
                latency_ms=latency_ms,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                status="success",
                conversation_id=conversation_id,
                session_id=session_id,
                input_preview=self._messages_preview(messages),
                output_preview=truncate_preview(response.content),
                extra=dict(response.raw),
            )
        )
        return response

    async def stream(
        self, messages: list[Message], *, conversation_id: UUID, session_id: UUID
    ) -> AsyncIterator[Token]:
        start = time.monotonic()
        first_token_time: float | None = None
        output_chunks: list[str] = []
        input_tokens: int | None = None
        output_tokens: int | None = None

        async def emit(status: str, error_message: str | None = None) -> None:
            latency_ms = (time.monotonic() - start) * 1000
            ttft_ms = (first_token_time - start) * 1000 if first_token_time is not None else None
            await self._publish(
                LogEvent(
                    model=getattr(self._wrapped, "model", "unknown"),
                    provider=self._provider_name,
                    latency_ms=latency_ms,
                    ttft_ms=ttft_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    status=status,
                    error_message=error_message,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    input_preview=self._messages_preview(messages),
                    output_preview=truncate_preview("".join(output_chunks)),
                )
            )

        try:
            async for token in self._wrapped.stream(
                messages, conversation_id=conversation_id, session_id=session_id
            ):
                if first_token_time is None:
                    first_token_time = time.monotonic()
                output_chunks.append(token.content)
                if token.input_tokens is not None:
                    input_tokens = token.input_tokens
                if token.output_tokens is not None:
                    output_tokens = token.output_tokens
                yield token
        except asyncio.CancelledError:
            await emit("cancelled")  # BR8: partial output/tokens captured above
            raise
        except Exception as exc:
            await emit("error", str(exc))
            raise  # BR5: provider failures are always re-raised
        else:
            await emit("success")
