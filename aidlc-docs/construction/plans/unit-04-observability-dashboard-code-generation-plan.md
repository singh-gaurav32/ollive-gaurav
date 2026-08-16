# Code Generation Plan — Unit 4: Observability Dashboard

**Stories**: US-4.1
**Dependencies**: Unit 3 (`LogRepository.query_window`, real log data)
**Code location**: `backend/src/analytics/`, `backend/src/api/`, `backend/alembic/`

## Steps

### Step 1: Project Structure
- [x] `backend/alembic/versions/0003_index_logs_timestamp.py` — single-column index on `logs.timestamp`

### Step 2: Business Logic Generation
- [x] `backend/src/analytics/service.py` — `AnalyticsService` (thin delegation, BR4)

### Step 3: Business Logic Unit Testing
- [x] `backend/tests/analytics/test_service.py` — delegates to `LogRepository.query_window` with a fake repository, returns whatever it returns unchanged

### Step 4: API Layer Generation
- [x] `backend/src/api/dashboard_router.py` — `GET /metrics`: defaults (BR1), range validation (BR2), bucket-count cap (NFR)
- [x] Wire into `backend/src/main.py`, `backend/src/api/deps.py` (`get_analytics_service()`)

### Step 5: API Layer Testing
- [x] `backend/tests/api/test_dashboard_router.py` — defaults applied when omitted, `400` on invalid range, `400` on bucket-count-cap violation, happy path returns the fake repository's buckets

### Step 6: Repository Layer Testing
- [x] No new repository code this unit (`SqlAlchemyLogRepository.query_window` already tested in Unit 3) — but add one real-Postgres test confirming the new index actually gets created (`\d logs` / a catalog query), since a migration that doesn't apply cleanly is worse than no migration

### Step 7: Documentation
- [x] `aidlc-docs/construction/unit-04-observability-dashboard/code/summary.md`
- [x] Update root `README.md`

## Verification Plan — all executed
1. `make migrate` — `0003` applied cleanly
2. `make test` (47/47) / `make test-db` (8/8, including the new index-existence check)
3. Rebuilt and restarted the live stack; `GET /metrics` with defaults returned real aggregated data from Unit 3's verification-pass rows (7 requests, 3 errors, real p50/p95); a deliberately wide range correctly triggered the bucket-count cap with the exact expected error message against the live system
