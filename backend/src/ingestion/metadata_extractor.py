"""MetadataExtractor: pass-through for v1 (BR1, Unit 3). Extension point
for normalizing provider-specific `extra` fields into first-class
columns later, if Unit 4's dashboard ends up needing one.
"""
from __future__ import annotations

from events.log_event import LogEvent


class MetadataExtractor:
    def extract(self, event: LogEvent) -> LogEvent:
        return event
