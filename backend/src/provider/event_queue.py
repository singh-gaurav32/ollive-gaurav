"""EventQueue: Strategy interface for the log-event broker.

Unit 1 defines the interface only. InProcessEventQueue (the v1 concrete
implementation, backed by an in-process asyncio.Queue) is Unit 3's
deliverable - this unit's tests use a FakeEventQueue test double instead.
A future RedisStreamsEventQueue implementation swaps in behind this same
interface without touching InstrumentedProvider or IngestionWorker.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from .models import LogEvent


class EventQueue(ABC):
    @abstractmethod
    async def publish(self, event: LogEvent) -> None:
        """Non-blocking enqueue. Must not block the caller for longer than
        it takes to hand the event to the underlying transport."""

    @abstractmethod
    def consume(self) -> AsyncIterator[LogEvent]:
        """Async iterator yielding events as they arrive. Consumer-side;
        not exercised by this unit."""
