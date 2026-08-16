# NFR Requirements Plan — Unit 3: Ingestion Pipeline Hardening

## Category Coverage

- **Reliability** — Question 1 (worker crash recovery).
- **Performance / Schema** — Question 2 (logs table indexing, relevant to Unit 4's future queries).
- **Tech Stack Selection** — N/A, decided directly: no new dependency needed (`re` and `asyncio` are stdlib, `LogRepository`/`FailedLogEventRepository` reuse the SQLAlchemy stack already fixed in Unit 2).
- **Security** — N/A beyond what Functional Design already owns: redaction correctness is a functional-correctness question (tested), not a separate security pattern to layer on.
- **Scalability** — N/A, single-process monolith already fixed in Units Generation.
- **Availability** — N/A, Resiliency Baseline extension was declined in Requirements Analysis.

---

## Question 1: Worker crash recovery
`IngestionWorker._process` catches per-event failures (BR5), but if the outer `run()` loop itself dies unexpectedly (a bug outside the per-event try/except, or something equally unforeseen), what happens?

A) **Let it die** — the chat path is unaffected (ingestion is fully decoupled per Unit 1/2's design), but logging silently stops until the process restarts. Simplest; consistent with declining the Resiliency Baseline earlier. Worth logging loudly (e.g. a critical-level log line) so it's at least *discoverable*, even though nothing auto-recovers.

B) **Auto-restart with a supervisor loop** — wrap `run()` in an outer loop that catches anything escaping the per-event handler, logs it, and restarts the consume loop rather than letting the task die permanently. More resilient, more code, revisits the "no resiliency baseline" decision for this one specific case.

C) Other (please describe after [Answer]: tag below)

[Answer]: A — let it die, but log it loudly (critical-level) so it's at least discoverable rather than silently stopping.

## Question 2: `logs` table indexing ahead of Unit 4
Unit 4's `AnalyticsService.query_window(start_time, end_time, bucket_size)` will filter/aggregate by timestamp (and likely group by status for the error-rate view) — but Unit 4 hasn't been built yet.

A) **Index `timestamp` and `status` now**, in this unit's migration — avoids a schema-churning migration when Unit 4 lands, and the access pattern is already predictable from `LogRepository`'s interface signature (fixed in the shared-contracts pass), not a guess

B) **No indexes yet** — let Unit 4 add exactly what it needs when it writes the real queries, avoiding speculation about exact access patterns now

C) Other (please describe after [Answer]: tag below)

[Answer]: B — no indexes yet; Unit 4 adds exactly what it needs when it writes the real queries.
