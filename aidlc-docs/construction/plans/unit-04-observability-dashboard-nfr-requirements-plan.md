# NFR Requirements Plan — Unit 4: Observability Dashboard

## Category Coverage

- **Performance / Schema** — Questions 1 and 2.
- **Tech Stack Selection** — N/A, no new dependency.
- **Security** — N/A, covered functionally (BR3 — aggregate-only response, no conversation content).
- **Scalability / Availability / Reliability** — N/A, unchanged from earlier units.

---

## Question 1: `logs` table indexing (deferred from Unit 3, lands here)
`query_window`'s actual shape is now concrete: `WHERE timestamp >= ? AND timestamp < ?`, `GROUP BY` a timestamp-derived bucket expression, plus a `FILTER (WHERE status = 'error')` inside the aggregate.

A) **Index `timestamp` only** — directly serves the `WHERE` range filter and the `GROUP BY`, which is where the real cost lives for a table that will keep growing. The `status` filter runs per-row inside an aggregate over an already-narrowed set (cheap once the range is indexed); a composite index would add write overhead for a benefit that doesn't show up without real cardinality data.

B) **Composite index on `(timestamp, status)`** — lets Postgres potentially serve more of the query from the index directly, unclear benefit without knowing the real ratio of error to success rows

C) Still no index — continue deferring until there's real production-scale data to profile against

[Answer]: A — timestamp index only.

## Question 2: Cap on requested range / bucket granularity
Nothing currently stops a caller from requesting, say, a 1-year range with 1-second buckets — an enormous, expensive result set.

A) **Reject if the implied bucket count exceeds a fixed ceiling** (e.g. 10,000 buckets) with a `400` — cheap to check (`(end - start) / bucket_size_seconds`), protects against an accidental or malicious expensive query

B) No cap — matches the "no hard SLA, standard practices only" precedent from earlier units; add this only if it's ever actually observed to be a problem

C) Other (please describe after [Answer]: tag below)

[Answer]: A — reject if the implied bucket count exceeds a fixed ceiling (10,000).
