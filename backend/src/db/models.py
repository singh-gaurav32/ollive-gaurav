"""Shared persistence-layer domain models: User, Session, Conversation,
ChatMessage, LogRecord. These are the pydantic shapes every repository
interface in this package works with. Concrete storage technology
(SQLAlchemy, raw SQL, etc.) is each implementing unit's own decision - these
models are the stable contract other units read/write against.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


ConversationState = Literal["active", "cancelled"]


class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    state: ConversationState = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


MessageRole = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


LogStatus = Literal["success", "error", "cancelled"]


class LogRecord(BaseModel):
    """The persisted, post-redaction form of a LogEvent (see events/log_event.py
    for the in-flight, pre-redaction shape). Adds `id` since this is a stored
    row, not a transient message."""

    id: UUID = Field(default_factory=uuid4)
    model: str
    provider: str
    latency_ms: float
    ttft_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    timestamp: datetime
    status: LogStatus
    error_message: str | None = None
    conversation_id: UUID
    session_id: UUID
    input_preview: str
    output_preview: str
    extra: dict[str, Any] = Field(default_factory=dict)
