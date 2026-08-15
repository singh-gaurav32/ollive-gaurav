"""Tests for the db/ shared contract itself, independent of any unit's
concrete repository implementation."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from db.models import ChatMessage, Conversation, LogRecord, Session, User


def test_conversation_defaults_to_active_state():
    conversation = Conversation(user_id=uuid4())
    assert conversation.state == "active"


def test_chat_message_requires_role_and_content():
    message = ChatMessage(conversation_id=uuid4(), role="user", content="hi")
    assert message.role == "user"


def test_user_and_session_round_trip_ids():
    user = User(username="demo")
    session = Session(user_id=user.id)
    assert session.user_id == user.id


def test_log_record_has_id_that_log_event_does_not():
    record = LogRecord(
        model="gemini-2.0-flash",
        provider="gemini",
        latency_ms=100.0,
        timestamp=datetime.now(timezone.utc),
        status="success",
        conversation_id=uuid4(),
        session_id=uuid4(),
        input_preview="hi",
        output_preview="hello",
    )
    assert record.id is not None
