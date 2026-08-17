"""IngestionWorker: consumes InProcessEventQueue, runs each event through
the 4-stage pipeline, tracks which stage a failure occurred at, and
dead-letters (metadata only - BR-PII) on failure without stopping the
consume loop (BR5).
"""
from __future__ import annotations

import logging

from db.failed_log_event_repository import FailedLogEventRepository
from db.models import FailedLogEvent
from events.event_queue import EventQueue
from events.log_event import LogEvent

from .log_persister import LogPersister
from .metadata_extractor import MetadataExtractor
from .payload_validator import PayloadValidator
from .pii_redactor import PIIRedactor

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(
        self,
        queue: EventQueue,
        validator: PayloadValidator,
        extractor: MetadataExtractor,
        redactor: PIIRedactor,
        persister: LogPersister,
        failed_log_event_repository: FailedLogEventRepository,
    ) -> None:
        self._queue = queue
        self._validator = validator
        self._extractor = extractor
        self._redactor = redactor
        self._persister = persister
        self._failed_repo = failed_log_event_repository

    async def run(self) -> None:
        async for event in self._queue.consume():
            await self._process(event)

    async def _process(self, event: LogEvent) -> None:
        stage = "validate"
        try:
            event = self._validator.validate(event)
            stage = "extract"
            event = self._extractor.extract(event)
            stage = "redact"
            event = self._redactor.redact(event)
            stage = "persist"
            await self._persister.persist(event)
        except Exception as exc:  # noqa: BLE001 - BR5: one event's failure must not stop the loop
            await self._record_failure(event, stage, exc)

    async def _record_failure(self, event: LogEvent, stage: str, exc: Exception) -> None:
        failed = FailedLogEvent(
            model=event.model,
            provider=event.provider,
            conversation_id=event.conversation_id,
            session_id=event.session_id,
            timestamp=event.timestamp,
            failure_stage=stage,
            failure_reason=str(exc),
        )
        try:
            await self._failed_repo.insert(failed)
        except Exception:  # noqa: BLE001 - last-resort fallback, business-logic-model step 5
            # exc_info=True here would only capture *this* insert's failure -
            # the original pipeline-stage exception (why _record_failure was
            # called at all) has to be logged explicitly or it's lost.
            logger.critical(
                "Failed to dead-letter event and failed to record failure: "
                "stage=%s model=%s provider=%s conversation_id=%s session_id=%s "
                "original_failure_reason=%s",
                stage,
                event.model,
                event.provider,
                event.conversation_id,
                event.session_id,
                exc,
                exc_info=True,
            )
