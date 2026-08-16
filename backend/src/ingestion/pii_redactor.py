"""PIIRedactor: the pipeline stage that does real work in v1. Hardcoded
regex patterns + an optional constructor-supplied denylist (BR3).
Redacts only input_preview/output_preview - every other field passes
through unchanged (BR2).
"""
from __future__ import annotations

import re

from events.log_event import LogEvent

REDACTED = "[REDACTED]"

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

DEFAULT_PATTERNS = [EMAIL_PATTERN, PHONE_PATTERN, SSN_PATTERN, CREDIT_CARD_PATTERN]


class PIIRedactor:
    def __init__(self, denylist_patterns: list[str] | None = None) -> None:
        self._patterns = [*DEFAULT_PATTERNS, *(re.compile(p) for p in (denylist_patterns or []))]

    def redact(self, event: LogEvent) -> LogEvent:
        return event.model_copy(
            update={
                "input_preview": self._redact_text(event.input_preview),
                "output_preview": self._redact_text(event.output_preview),
            }
        )

    def _redact_text(self, text: str) -> str:
        for pattern in self._patterns:
            text = pattern.sub(REDACTED, text)
        return text
