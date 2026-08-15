"""ContextTruncationStrategy: Strategy interface + WindowTruncationStrategy,
the sole implementation for v1. Unit-owned - lives here, not in a shared
package, because only ChatService ever calls it (see project-structure.md's
ownership rule)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from db.models import ChatMessage

DEFAULT_WINDOW_TURNS = 10


class ContextTruncationStrategy(ABC):
    @abstractmethod
    def truncate(self, history: list[ChatMessage]) -> list[ChatMessage]: ...


class WindowTruncationStrategy(ContextTruncationStrategy):
    """Keeps the most recent `window_turns` user/assistant pairs, drops the
    rest outright - no summarization, no token estimation (BR2)."""

    def __init__(self, window_turns: int = DEFAULT_WINDOW_TURNS) -> None:
        self._max_messages = window_turns * 2

    def truncate(self, history: list[ChatMessage]) -> list[ChatMessage]:
        if len(history) <= self._max_messages:
            return history
        return history[-self._max_messages :]
