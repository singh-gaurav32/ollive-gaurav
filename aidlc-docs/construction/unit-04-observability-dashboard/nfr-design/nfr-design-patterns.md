# NFR Design Patterns — Unit 4: Observability Dashboard

No question round this time: both NFR Requirements decisions (timestamp index, bucket-count cap) are mechanical to realize, with no genuine pattern choice left open.

## Performance: index as a new migration, cap as a boundary check

The `logs.timestamp` index is added via a new Alembic revision (`0003_index_logs_timestamp`), not folded into the existing `0002` migration — keeping each unit's schema changes in their own revision preserves the migration history as a readable record of which unit changed what, matching the same reasoning already applied when `logs`/`failed_log_events` got their own revision separate from `0001`.

The bucket-count cap is a pure validation check at the API boundary: `ceil((end - start).total_seconds() / bucket_size_seconds) > 10_000` → `400`, computed before `AnalyticsService.get_metrics` is ever called — the expensive query is never issued for a rejected request, not caught and discarded after the fact.

## Everything else: no pattern needed

Security, Scalability, Availability, Reliability: unchanged from earlier units, nothing new to design.
