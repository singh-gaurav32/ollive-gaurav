"""Tests for WindowTruncationStrategy."""
from __future__ import annotations

from uuid import uuid4

from chat.truncation import WindowTruncationStrategy
from db.models import ChatMessage


def _messages(n: int) -> list[ChatMessage]:
    conversation_id = uuid4()
    return [
        ChatMessage(
            conversation_id=conversation_id,
            role="user" if i % 2 == 0 else "assistant",
            content=str(i),
        )
        for i in range(n)
    ]


def test_keeps_everything_under_the_window():
    strategy = WindowTruncationStrategy(window_turns=10)
    history = _messages(10)
    assert strategy.truncate(history) == history


def test_drops_oldest_messages_beyond_the_window():
    strategy = WindowTruncationStrategy(window_turns=2)
    history = _messages(10)
    truncated = strategy.truncate(history)
    assert len(truncated) == 4
    assert truncated == history[-4:]
