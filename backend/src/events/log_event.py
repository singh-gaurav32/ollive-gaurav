"""LogEvent: the cross-unit event contract. Published by InstrumentedProvider
(Unit 1), consumed by Unit 3's ingestion pipeline. Lives in its own package
because neither unit owns it exclusively - see
aidlc-docs/inception/application-design/shared-contracts.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

PREVIEW_MAX_CHARS = 500


def truncate_preview(text: str, max_chars: int = PREVIEW_MAX_CHARS) -> str:
    """BR7 (Unit 1 functional design): previews are raw and truncated, not redacted."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


LogStatus = Literal["success", "error", "cancelled"]


class LogEvent(BaseModel):
    """Immutable, in-flight, pre-redaction snapshot of one provider call.
    See db/models.py LogRecord for the persisted, post-redaction shape."""

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
