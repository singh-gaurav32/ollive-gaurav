"""In-memory fakes for IngestionWorker's repository dependencies."""
from __future__ import annotations

from datetime import datetime

from db.failed_log_event_repository import FailedLogEventRepository
from db.log_repository import LogRepository, MetricBucket
from db.models import FailedLogEvent, LogRecord


class FakeLogRepository(LogRepository):
    def __init__(self) -> None:
        self.inserted: list[LogRecord] = []

    async def insert(self, record: LogRecord) -> None:
        self.inserted.append(record)

    async def query_window(
        self, start_time: datetime, end_time: datetime, bucket_size_seconds: int
    ) -> list[MetricBucket]:
        raise NotImplementedError("not exercised by Unit 3's own tests")


class FakeFailedLogEventRepository(FailedLogEventRepository):
    def __init__(self, *, fail_insert: bool = False) -> None:
        self.inserted: list[FailedLogEvent] = []
        self._fail_insert = fail_insert

    async def insert(self, record: FailedLogEvent) -> None:
        if self._fail_insert:
            raise RuntimeError("simulated dead-letter write failure")
        self.inserted.append(record)


class FailingPersister:
    """A persister that always fails, for exercising the worker's failure path."""

    async def persist(self, event) -> None:
        raise RuntimeError("db down")
