"""Domain models for the provider layer: LogEvent, Message, Token.

See aidlc-docs/construction/unit-01-provider-abstraction/functional-design/
for the business rules (BR1-BR9) and domain entity spec these implement.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

PREVIEW_MAX_CHARS = 500


def truncate_preview(text: str, max_chars: int = PREVIEW_MAX_CHARS) -> str:
    """BR7: previews are raw (unredacted) and truncated to a fixed length."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: Role
    content: str


class Token(BaseModel):
    """A single streamed content fragment from a provider.

    input_tokens/output_tokens are populated only on the chunk(s) where the
    provider actually reports usage (typically the final chunk) - see
    InstrumentedProvider for how these are accumulated into a LogEvent (BR3).
    """

    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None


LogStatus = Literal["success", "error", "cancelled"]


class LogEvent(BaseModel):
    """Immutable snapshot of one provider call. Per BR1-BR9 and domain-entities.md."""

    model: str
    provider: str
    latency_ms: float
    ttft_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: LogStatus
    error_message: str | None = None
    conversation_id: UUID
    session_id: UUID
    input_preview: str
    output_preview: str
    extra: dict[str, Any] = Field(default_factory=dict)
