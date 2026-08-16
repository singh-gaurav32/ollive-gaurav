# Logical Components — Unit 4: Observability Dashboard

## `AnalyticsService`

`backend/src/analytics/service.py` — the thin delegation layer (BR4).

## `dashboard_router.py`

`backend/src/api/dashboard_router.py` — the single `GET /metrics` endpoint: parses query params, applies defaults (BR1), validates range and bucket-count cap (BR2, NFR), then calls `AnalyticsService.get_metrics`.

## Migration

`backend/alembic/versions/0003_index_logs_timestamp.py` — adds the single-column index on `logs.timestamp`, its own revision separate from `0002`.
