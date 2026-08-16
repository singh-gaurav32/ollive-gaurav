"""Tests for AnalyticsService - a thin delegation layer (BR4)."""
from __future__ import annotations

from datetime import datetime, timezone

from analytics.service import AnalyticsService
from db.log_repository import LogRepository, MetricBucket


class FakeLogRepository(LogRepository):
    def __init__(self, buckets: list[MetricBucket]) -> None:
        self._buckets = buckets
        self.last_call: tuple | None = None

    async def insert(self, record) -> None:
        raise NotImplementedError

    async def query_window(self, start_time, end_time, bucket_size_seconds) -> list[MetricBucket]:
        self.last_call = (start_time, end_time, bucket_size_seconds)
        return self._buckets


async def test_get_metrics_delegates_to_query_window_unchanged():
    now = datetime.now(timezone.utc)
    expected = [
        MetricBucket(bucket_start=now, bucket_end=now, request_count=5, error_count=1, p50_latency_ms=100.0)
    ]
    repo = FakeLogRepository(expected)
    service = AnalyticsService(repo)

    result = await service.get_metrics(now, now, 60)

    assert result == expected
    assert repo.last_call == (now, now, 60)
