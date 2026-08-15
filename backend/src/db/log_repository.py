"""LogRepository: shared persistence contract for inference logs.
insert() and query_window() are both implemented by Unit 3 (the natural
owner of the `logs` table), but query_window() is read directly by Unit 4's
AnalyticsService - a genuine cross-unit dependency, and exactly why this
interface lives in db/ rather than nested inside ingestion/.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel

from .models import LogRecord


class MetricBucket(BaseModel):
    bucket_start: datetime
    bucket_end: datetime
    request_count: int
    error_count: int
    p50_latency_ms: float | None = None
    p95_latency_ms: float | None = None


class LogRepository(ABC):
    @abstractmethod
    async def insert(self, record: LogRecord) -> None: ...

    @abstractmethod
    async def query_window(
        self, start_time: datetime, end_time: datetime, bucket_size_seconds: int
    ) -> list[MetricBucket]: ...
