"""EventQueue: cross-unit transport contract. InstrumentedProvider (Unit 1)
publishes; IngestionWorker (Unit 3) implements and consumes. Lives here, not
nested in provider/ or ingestion/, because it's the seam between them - see
shared-contracts.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from .log_event import LogEvent


class EventQueue(ABC):
    @abstractmethod
    async def publish(self, event: LogEvent) -> None:
        """Non-blocking enqueue. Must not block the caller for longer than
        it takes to hand the event to the underlying transport."""

    @abstractmethod
    def consume(self) -> AsyncIterator[LogEvent]:
        """Async iterator yielding events as they arrive. Unit 3's concern."""
