"""Tests for PIIRedactor - the pipeline stage that does real work."""
from __future__ import annotations

from uuid import uuid4

from events.log_event import LogEvent
from ingestion.pii_redactor import PIIRedactor


def _event(input_preview: str, output_preview: str) -> LogEvent:
    return LogEvent(
        model="m",
        provider="p",
        latency_ms=1.0,
        status="success",
        conversation_id=uuid4(),
        session_id=uuid4(),
        input_preview=input_preview,
        output_preview=output_preview,
    )


def test_redacts_email():
    redactor = PIIRedactor()
    redacted = redactor.redact(_event("contact me at jane.doe@example.com please", "ok"))
    assert "jane.doe@example.com" not in redacted.input_preview
    assert "[REDACTED]" in redacted.input_preview


def test_redacts_phone_number():
    redactor = PIIRedactor()
    redacted = redactor.redact(_event("call 555-123-4567", "ok"))
    assert "555-123-4567" not in redacted.input_preview


def test_redacts_ssn():
    redactor = PIIRedactor()
    redacted = redactor.redact(_event("my ssn is 123-45-6789", "ok"))
    assert "123-45-6789" not in redacted.input_preview


def test_redacts_credit_card():
    redactor = PIIRedactor()
    redacted = redactor.redact(_event("card 4111111111111111", "ok"))
    assert "4111111111111111" not in redacted.input_preview


def test_redacts_output_preview_too():
    redactor = PIIRedactor()
    redacted = redactor.redact(_event("hi", "email me at test@example.com"))
    assert "test@example.com" not in redacted.output_preview


def test_applies_constructor_denylist():
    redactor = PIIRedactor(denylist_patterns=[r"PROJECT-\w+"])
    redacted = redactor.redact(_event("about PROJECT-PHOENIX status", "ok"))
    assert "PROJECT-PHOENIX" not in redacted.input_preview


def test_leaves_non_preview_fields_untouched():
    redactor = PIIRedactor()
    event = _event("hi jane.doe@example.com", "ok")
    redacted = redactor.redact(event)
    assert redacted.model == event.model
    assert redacted.status == event.status
    assert redacted.conversation_id == event.conversation_id
    assert redacted.session_id == event.session_id
