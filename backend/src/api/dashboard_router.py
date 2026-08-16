"""Dashboard endpoint - one unified GET /metrics (Unit 4, Functional Design
Q1). Defaults (BR1), range validation (BR2), and the bucket-count cap
(NFR Requirements) all happen here, before AnalyticsService is called.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from analytics.service import AnalyticsService

from .deps import AuthContext, get_analytics_service, get_auth_context

router = APIRouter(tags=["dashboard"])

DEFAULT_WINDOW = timedelta(hours=1)
DEFAULT_BUCKET_SIZE_SECONDS = 60
MAX_BUCKET_COUNT = 10_000


@router.get("/metrics")
async def get_metrics(
    start: datetime | None = None,
    end: datetime | None = None,
    bucket_size_seconds: int = DEFAULT_BUCKET_SIZE_SECONDS,
    auth: AuthContext = Depends(get_auth_context),  # BR3: same session auth as everything else
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    end_time = end or datetime.now(timezone.utc)
    start_time = start or (end_time - DEFAULT_WINDOW)

    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start must be before end")
    if bucket_size_seconds <= 0:
        raise HTTPException(status_code=400, detail="bucket_size_seconds must be positive")

    implied_buckets = math.ceil((end_time - start_time).total_seconds() / bucket_size_seconds)
    if implied_buckets > MAX_BUCKET_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"requested range/bucket_size implies {implied_buckets} buckets, exceeding the {MAX_BUCKET_COUNT} cap",
        )

    return await analytics_service.get_metrics(start_time, end_time, bucket_size_seconds)
