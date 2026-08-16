"""AnalyticsService: a thin delegation layer over LogRepository.query_window
(BR4) - the aggregation logic itself was already built in Unit 3.
"""
from __future__ import annotations

from datetime import datetime

from db.log_repository import LogRepository, MetricBucket


class AnalyticsService:
    def __init__(self, log_repository: LogRepository) -> None:
        self._log_repository = log_repository

    async def get_metrics(
        self, start_time: datetime, end_time: datetime, bucket_size_seconds: int
    ) -> list[MetricBucket]:
        return await self._log_repository.query_window(start_time, end_time, bucket_size_seconds)
