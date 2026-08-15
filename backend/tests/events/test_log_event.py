"""Tests for the events/ shared contract itself, independent of any unit's
implementation - LogEvent construction and the truncate_preview helper."""
from __future__ import annotations

from uuid import uuid4

from events.log_event import LogEvent, truncate_preview


def test_truncate_preview_leaves_short_text_untouched():
    assert truncate_preview("hello") == "hello"


def test_truncate_preview_truncates_long_text():
    text = "x" * 600
    result = truncate_preview(text, max_chars=500)
    assert len(result) == 501  # 500 chars + the ellipsis marker
    assert result.endswith("…")


def test_log_event_requires_status_and_ids():
    event = LogEvent(
        model="gemini-2.0-flash",
        provider="gemini",
        latency_ms=120.5,
        status="success",
        conversation_id=uuid4(),
        session_id=uuid4(),
        input_preview="hi",
        output_preview="hello",
    )
    assert event.status == "success"
    assert event.extra == {}
    assert event.error_message is None
