"""InProcessEventQueue: the v1 concrete EventQueue implementation.
Bounded, and uses put_nowait (not blocking put) to honor EventQueue's
non-blocking contract even under backpressure (BR6, Unit 3).
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .event_queue import EventQueue
from .log_event import LogEvent

DEFAULT_MAXSIZE = 1000


class InProcessEventQueue(EventQueue):
    def __init__(self, maxsize: int = DEFAULT_MAXSIZE) -> None:
        self._queue: asyncio.Queue[LogEvent] = asyncio.Queue(maxsize=maxsize)

    async def publish(self, event: LogEvent) -> None:
        self._queue.put_nowait(event)

    async def consume(self) -> AsyncIterator[LogEvent]:
        while True:
            yield await self._queue.get()
