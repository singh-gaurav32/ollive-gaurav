"""Tests for IngestionWorker - pipeline sequencing, failure isolation,
failure-stage tracking, and the PII-safe dead-letter guarantee (BR-PII)."""
from __future__ import annotations

import logging
from uuid import uuid4

from events.log_event import LogEvent
from ingestion.log_persister import LogPersister
from ingestion.metadata_extractor import MetadataExtractor
from ingestion.payload_validator import PayloadValidator
from ingestion.pii_redactor import PIIRedactor
from ingestion.worker import IngestionWorker

from .doubles import FailingPersister, FakeFailedLogEventRepository, FakeLogRepository


def _event(input_preview: str = "hi jane@example.com", output_preview: str = "hello") -> LogEvent:
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


def _make_worker(log_repo, failed_repo, *, persister=None) -> IngestionWorker:
    return IngestionWorker(
        queue=None,  # not exercised - tests call _process directly
        validator=PayloadValidator(),
        extractor=MetadataExtractor(),
        redactor=PIIRedactor(),
        persister=persister or LogPersister(log_repo),
        failed_log_event_repository=failed_repo,
    )


async def test_successful_event_is_redacted_and_persisted():
    log_repo = FakeLogRepository()
    failed_repo = FakeFailedLogEventRepository()
    worker = _make_worker(log_repo, failed_repo)

    await worker._process(_event())

    assert len(log_repo.inserted) == 1
    assert "jane@example.com" not in log_repo.inserted[0].input_preview
    assert failed_repo.inserted == []


async def test_persist_failure_is_dead_lettered_without_preview_text():
    log_repo = FakeLogRepository()
    failed_repo = FakeFailedLogEventRepository()
    worker = _make_worker(log_repo, failed_repo, persister=FailingPersister())

    await worker._process(_event(input_preview="secret jane@example.com"))

    assert log_repo.inserted == []
    assert len(failed_repo.inserted) == 1
    failed = failed_repo.inserted[0]
    assert failed.failure_stage == "persist"
    assert "jane@example.com" not in failed.failure_reason
    assert not hasattr(failed, "input_preview")  # BR-PII: no preview field on the model at all


async def test_one_events_failure_does_not_affect_the_next():
    log_repo = FakeLogRepository()
    failed_repo = FakeFailedLogEventRepository()
    failing_worker = _make_worker(log_repo, failed_repo, persister=FailingPersister())
    ok_worker = _make_worker(log_repo, failed_repo)

    await failing_worker._process(_event())
    await ok_worker._process(_event())

    assert len(failed_repo.inserted) == 1
    assert len(log_repo.inserted) == 1


async def test_dead_letter_write_failure_falls_back_to_logging_not_a_crash(caplog):
    caplog.set_level(logging.CRITICAL, logger="ingestion.worker")
    log_repo = FakeLogRepository()
    failed_repo = FakeFailedLogEventRepository(fail_insert=True)
    worker = _make_worker(log_repo, failed_repo, persister=FailingPersister())

    await worker._process(_event())  # must not raise

    assert "Failed to dead-letter" in caplog.text
    # The last-resort log must carry the *original* failure context (which
    # stage, which event, why) - not just the fact that the dead-letter
    # write itself also failed, which is all exc_info=True alone would give.
    assert "stage=persist" in caplog.text
    assert "model=m" in caplog.text
    assert "provider=p" in caplog.text
    assert "db down" in caplog.text  # the original persist() exception, not the dead-letter one
