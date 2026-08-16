"""Tests for InProcessEventQueue - the concrete EventQueue implementation."""
from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from events.in_process_event_queue import InProcessEventQueue
from events.log_event import LogEvent


def _event() -> LogEvent:
    return LogEvent(
        model="m",
        provider="p",
        latency_ms=1.0,
        status="success",
        conversation_id=uuid4(),
        session_id=uuid4(),
        input_preview="hi",
        output_preview="hello",
    )


async def test_publish_then_consume_round_trips():
    queue = InProcessEventQueue()
    event = _event()
    await queue.publish(event)

    received = await queue.consume().__anext__()

    assert received == event


async def test_publish_is_non_blocking_and_raises_queuefull_when_full():
    queue = InProcessEventQueue(maxsize=1)
    await queue.publish(_event())

    with pytest.raises(asyncio.QueueFull):
        await queue.publish(_event())
