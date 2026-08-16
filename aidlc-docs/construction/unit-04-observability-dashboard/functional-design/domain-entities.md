# Domain Entities — Unit 4: Observability Dashboard

No new domain entities. `MetricBucket` (already defined in `db/log_repository.py` during the shared-contracts pass) is the only shape this unit produces — a thin wrapper around what Unit 3's `query_window` already returns.

## `AnalyticsService`

The one new component. Owns no state, no persistence of its own — a pass-through orchestration layer between the API router and `LogRepository.query_window`.

| Method | Signature |
|---|---|
| `get_metrics` | `(start_time: datetime, end_time: datetime, bucket_size_seconds: int) -> list[MetricBucket]` |

## Endpoint

`GET /metrics?start=&end=&bucket_size_seconds=` — one endpoint, all three query params optional (defaults per BR1), returns `list[MetricBucket]`.
