# NFR Requirements — Unit 3: Ingestion Pipeline Hardening

## Reliability

If `IngestionWorker.run()`'s outer loop dies unexpectedly (something escaping the per-event try/except), it is allowed to die — no auto-restart supervisor. The chat path is unaffected either way (ingestion is fully decoupled, per Unit 1/2's design), and adding a supervisor loop would revisit the "no Resiliency Baseline" decision made in Requirements Analysis for this one specific case, which wasn't asked for. The one requirement: this failure must be **loud** — a critical-level log line, not a silent stop, so it's discoverable rather than only noticed when the dashboard's data goes stale.

## Performance / Schema

No indexes added to the `logs` table in this unit beyond the primary key. Deferred to Unit 4, which will write the actual `query_window` implementation and knows its real access pattern at that point rather than guessing now.

## Tech Stack Selection

N/A — no new dependency. `re` and `asyncio` are stdlib; persistence reuses the SQLAlchemy stack already fixed in Unit 2.

## Security

N/A beyond what Functional Design already owns — redaction correctness is verified by tests, not a separate NFR pattern layered on top.

## Scalability / Availability

N/A — single-process monolith already fixed in Units Generation; Resiliency Baseline was declined in Requirements Analysis.
