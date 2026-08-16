"""LogPersister: maps a (validated, extracted, redacted) LogEvent into a
LogRecord and persists it via LogRepository.
"""
from __future__ import annotations

from db.log_repository import LogRepository
from db.models import LogRecord
from events.log_event import LogEvent


class LogPersister:
    def __init__(self, log_repository: LogRepository) -> None:
        self._log_repository = log_repository

    async def persist(self, event: LogEvent) -> None:
        record = LogRecord(
            model=event.model,
            provider=event.provider,
            latency_ms=event.latency_ms,
            ttft_ms=event.ttft_ms,
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
            timestamp=event.timestamp,
            status=event.status,
            error_message=event.error_message,
            conversation_id=event.conversation_id,
            session_id=event.session_id,
            input_preview=event.input_preview,
            output_preview=event.output_preview,
            extra=event.extra,
        )
        await self._log_repository.insert(record)
