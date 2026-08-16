# Business Logic Model — Unit 4: Observability Dashboard

## `AnalyticsService.get_metrics(start_time, end_time, bucket_size_seconds)`
1. `return await self._log_repository.query_window(start_time, end_time, bucket_size_seconds)` — no transformation, no filtering beyond what Unit 3's implementation already does (BR4).

## `GET /metrics` (router)
1. Parse `start`, `end`, `bucket_size_seconds` from query params.
2. Apply defaults where omitted (BR1): `end = now()`, `start = end - 1h`, `bucket_size_seconds = 60`.
3. Validate (BR2): if `start >= end` or `bucket_size_seconds <= 0`, return `400`.
4. `return await analytics_service.get_metrics(start, end, bucket_size_seconds)`.

## Key Point

There is deliberately very little logic in this unit. The interesting engineering — the windowed aggregation query itself — was already built in Unit 3, because `LogRepository` (the interface *and* its implementation) was fixed there as the natural owner of the `logs` table. This unit's job is narrower than its name suggests: give that already-working query an HTTP front door with sensible defaults.
