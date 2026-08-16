"""API-layer tests for GET /metrics - defaults, validation, and the
bucket-count cap, all with a fake AnalyticsService (no real DB)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from api import deps
from api.deps import AuthContext
from db.log_repository import MetricBucket
from db.models import User
from main import app


class _FakeAnalyticsService:
    def __init__(self, buckets=None) -> None:
        self._buckets = buckets or []
        self.last_call = None

    async def get_metrics(self, start_time, end_time, bucket_size_seconds):
        self.last_call = (start_time, end_time, bucket_size_seconds)
        return self._buckets


def _override(service) -> None:
    app.dependency_overrides[deps.get_analytics_service] = lambda: service
    app.dependency_overrides[deps.get_auth_context] = lambda: AuthContext(
        user=User(username="test-user"), session_id=uuid4()
    )


def test_defaults_applied_when_omitted():
    service = _FakeAnalyticsService()
    _override(service)
    client = TestClient(app)

    resp = client.get("/metrics")

    assert resp.status_code == 200
    start, end, bucket_size = service.last_call
    assert bucket_size == 60
    assert (end - start) == timedelta(hours=1)
    app.dependency_overrides.clear()


def test_rejects_start_after_end():
    _override(_FakeAnalyticsService())
    client = TestClient(app)
    end = datetime.now(timezone.utc)
    start = end + timedelta(hours=1)

    resp = client.get("/metrics", params={"start": start.isoformat(), "end": end.isoformat()})

    assert resp.status_code == 400
    app.dependency_overrides.clear()


def test_rejects_non_positive_bucket_size():
    _override(_FakeAnalyticsService())
    client = TestClient(app)

    resp = client.get("/metrics", params={"bucket_size_seconds": 0})

    assert resp.status_code == 400
    app.dependency_overrides.clear()


def test_rejects_when_implied_bucket_count_exceeds_cap():
    _override(_FakeAnalyticsService())
    client = TestClient(app)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)

    resp = client.get(
        "/metrics", params={"start": start.isoformat(), "end": end.isoformat(), "bucket_size_seconds": 1}
    )

    assert resp.status_code == 400
    assert "exceeding" in resp.json()["detail"]
    app.dependency_overrides.clear()


def test_happy_path_returns_buckets_from_service():
    now = datetime.now(timezone.utc)
    buckets = [
        MetricBucket(bucket_start=now, bucket_end=now, request_count=3, error_count=1, p50_latency_ms=42.0)
    ]
    _override(_FakeAnalyticsService(buckets))
    client = TestClient(app)

    resp = client.get("/metrics")

    assert resp.status_code == 200
    assert resp.json()[0]["request_count"] == 3
    app.dependency_overrides.clear()
