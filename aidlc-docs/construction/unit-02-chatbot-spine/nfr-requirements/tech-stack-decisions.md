# Tech Stack Decisions — Unit 2: Chatbot Spine

## SQLAlchemy 2.0 (async) + asyncpg

Chosen over raw `asyncpg` (more boilerplate per repository method) and SQLModel (less battle-tested, and `db/models.py`'s existing pydantic models stay decoupled from the ORM layer this way — a repository maps between them explicitly, which is a small amount of extra code in exchange for the ORM never leaking into the shared contract other units already depend on).

Dependency: `sqlalchemy[asyncio]>=2.0` — pinning the 2.0.x line generically rather than a specific patch version; there is no "2.2" release of SQLAlchemy to pin to.

## Alembic for migrations

Versioned migrations from the first table, not `create_all()`. Real practice, and directly supports the "schema design decisions" the problem statement's README deliverable asks for — a migration history is evidence of the schema's evolution, not just its final shape.

## `docker-compose.yml` started now, not deferred to Unit 6

Originally planned as purely Unit 6's deliverable. Brought forward because Unit 2's own tests need a real Postgres (pgvector rules out SQLite as a stand-in), and the file exists either way. Starts with a single `postgres` service (image `pgvector/pgvector:pg16` or equivalent, exposing 5432, a named volume for data, health check). Unit 6 adds the `api`, `worker`, and `frontend` services alongside it — this file is extended, not recreated.

## No hard latency SLA

Standard practices (indexed FKs, pooled async connections) without a pre-guessed number. Consistent with the Resiliency Baseline being declined earlier — this project states failure/performance assumptions pragmatically in the README rather than against a formal target.
