"""Temporary stand-in for EventQueue until Unit 3's InProcessEventQueue
lands. publish() is a no-op - safe because InstrumentedProvider (Unit 1,
BR5/BR9) already treats publish failures as swallow-and-log, never
something that can affect the chat response. Used only to wire Unit 2's
API layer so InstrumentedProvider has something to publish to; Unit 3
replaces the instance passed to it in api/deps.py, nothing else changes.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from .event_queue import EventQueue
from .log_event import LogEvent


class NoOpEventQueue(EventQueue):
    async def publish(self, event: LogEvent) -> None:
        return None

    async def consume(self) -> AsyncIterator[LogEvent]:
        return
        yield  # pragma: no cover - never reached; makes this an async generator
