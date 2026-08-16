"""SQLAlchemy implementation of LogRepository. insert() and query_window()
both live here - Unit 3 owns the logs table; Unit 4's AnalyticsService
reads query_window()'s result directly (see project-structure.md)."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from .log_repository import LogRepository, MetricBucket
from .models import LogRecord
from .orm import LogORM


class SqlAlchemyLogRepository(LogRepository):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def insert(self, record: LogRecord) -> None:
        async with self._session_factory() as session:
            row = LogORM(
                id=record.id,
                model=record.model,
                provider=record.provider,
                latency_ms=record.latency_ms,
                ttft_ms=record.ttft_ms,
                input_tokens=record.input_tokens,
                output_tokens=record.output_tokens,
                timestamp=record.timestamp,
                status=record.status,
                error_message=record.error_message,
                conversation_id=record.conversation_id,
                session_id=record.session_id,
                input_preview=record.input_preview,
                output_preview=record.output_preview,
                extra=record.extra,
            )
            session.add(row)
            await session.commit()

    async def query_window(
        self, start_time: datetime, end_time: datetime, bucket_size_seconds: int
    ) -> list[MetricBucket]:
        bucket_expr = func.to_timestamp(
            func.floor(func.extract("epoch", LogORM.timestamp) / bucket_size_seconds) * bucket_size_seconds
        ).label("bucket_start")

        stmt = (
            select(
                bucket_expr,
                func.count().label("request_count"),
                func.count().filter(LogORM.status == "error").label("error_count"),
                func.percentile_cont(0.5).within_group(LogORM.latency_ms).label("p50_latency_ms"),
                func.percentile_cont(0.95).within_group(LogORM.latency_ms).label("p95_latency_ms"),
            )
            .where(LogORM.timestamp >= start_time, LogORM.timestamp < end_time)
            .group_by(bucket_expr)
            .order_by(bucket_expr)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            rows = result.all()

        return [
            MetricBucket(
                bucket_start=row.bucket_start,
                bucket_end=row.bucket_start + timedelta(seconds=bucket_size_seconds),
                request_count=row.request_count,
                error_count=row.error_count,
                p50_latency_ms=row.p50_latency_ms,
                p95_latency_ms=row.p95_latency_ms,
            )
            for row in rows
        ]
