"""PayloadValidator: pass-through for v1 (BR1, Unit 3). Extension point
for future business-level checks pydantic's type validation doesn't
cover (e.g. latency_ms >= 0).
"""
from __future__ import annotations

from events.log_event import LogEvent


class PayloadValidator:
    def validate(self, event: LogEvent) -> LogEvent:
        return event
