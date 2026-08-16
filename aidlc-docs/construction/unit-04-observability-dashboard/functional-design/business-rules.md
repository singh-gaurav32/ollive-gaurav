# Business Rules — Unit 4: Observability Dashboard

**BR1 — Defaults apply when parameters are omitted.** `start` defaults to one hour before now, `end` defaults to now, `bucket_size_seconds` defaults to 60.

**BR2 — Invalid ranges are rejected at the API boundary, not silently coerced.** `start >= end` or `bucket_size_seconds <= 0` returns `400`, not an empty result set or a swapped range.

**BR3 — The endpoint returns aggregate data only, never per-user or per-conversation content.** `MetricBucket` structurally cannot carry conversation content (per `db/log_repository.py`'s already-fixed shape), so there is no separate access-scoping rule to enforce here beyond standard session auth (once Unit 5 lands) — the isolation concern that applies to conversations doesn't apply to this endpoint by construction, not by policy.

**BR4 — `AnalyticsService` adds no logic beyond delegation.** It exists as a named seam between the API layer and `LogRepository`, not because there's business logic to hide — matching `component-methods.md`'s original design intent even though the aggregation itself now lives entirely in Unit 3's `query_window`.
