# NFR Requirements — Unit 2: Chatbot Spine

## Tech Stack Selection

- **DB access**: SQLAlchemy 2.0, async, `asyncpg` driver.
- **Migrations**: Alembic, versioned migration scripts from the start — not `create_all()`.
- **Local Postgres**: `docker-compose.yml` created now (this unit), with a Postgres + pgvector service — not deferred to Unit 6, since it exists anyway once Unit 6 lands. Unit 6 extends this file rather than creating it.

## Performance

- No hard SLA on the user-message write latency. Standard practices apply (indexed foreign keys, connection pooling, async I/O throughout the repository layer) — revisit only if actually observed to be slow, not pre-optimized against a guessed number.

## Security

N/A beyond standard credential hygiene — DB connection string comes from an environment variable, never hardcoded or committed. Real auth/session security is Unit 5's scope; PII handling in stored data is Unit 3's scope (`PIIRedactor`).

## Availability / Scalability

N/A at this project's scale. Resiliency Baseline extension was declined in Requirements Analysis — no formal availability targets apply.

## Maintainability

Covered by the tech-stack choices above: Alembic gives the project real migration history from its first table, which is the maintainability-relevant decision here.

## Usability

N/A — no UI in this unit (frontend is Unit 5).
