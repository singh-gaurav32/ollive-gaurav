# NFR Requirements — Unit 4: Observability Dashboard

## Performance / Schema

- **Index `logs.timestamp`** (single-column, not composite) — a new Alembic migration adds it. Serves both the `WHERE` range filter and the `GROUP BY` bucket expression in `query_window`, which is where the real cost lives on a growing table. The `status` filter stays unindexed — it runs per-row inside an aggregate over an already-narrowed set once the timestamp range is indexed, and a composite index's write overhead isn't justified without real cardinality data.
- **Cap requested bucket count at 10,000.** `(end - start) / bucket_size_seconds` is checked at the API boundary; exceeding the cap returns `400` rather than running a potentially enormous aggregation.

## Tech Stack Selection

N/A — no new dependency.

## Security

N/A — covered functionally (BR3: aggregate-only response, no conversation content, no per-user scoping needed).

## Scalability / Availability / Reliability

N/A — unchanged from earlier units; no new decisions this unit.
