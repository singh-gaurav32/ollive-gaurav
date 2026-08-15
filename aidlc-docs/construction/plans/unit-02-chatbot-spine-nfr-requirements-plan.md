# NFR Requirements Plan — Unit 2: Chatbot Spine

## Category Coverage

- **Tech Stack Selection** — Questions 1-3 below. This is the main point of this stage: `db/`'s repository interfaces were fixed without committing to a storage technology.
- **Performance** — Question 4.
- **Security** — N/A for this unit beyond standard credential hygiene (DB connection string via env var, never hardcoded) — real auth/session security is Unit 5's concern; PII handling is Unit 3's.
- **Availability / Scalability** — N/A at this project's scale; Resiliency Baseline extension was declined in Requirements Analysis.
- **Maintainability** — covered implicitly by the tech-stack questions (migration tooling).
- **Usability** — N/A, no UI in this unit.

---

## Question 1: DB access technology
`db/`'s repository interfaces (`ConversationRepository`, `MessageRepository`, `UserRepository`) need a concrete implementation. Postgres + pgvector was already fixed in Requirements Analysis; this is about how Python talks to it.

A) **SQLAlchemy 2.0 (async, with `asyncpg` driver)** — mature ORM, async-native since 2.0, pairs with Alembic for migrations, most familiar to most reviewers

B) **Raw `asyncpg` with hand-written SQL** — lightest weight, full control, no ORM abstraction to fight, more boilerplate per repository method

C) **SQLModel** (Pydantic + SQLAlchemy combined) — nice DX since your `db/models.py` pydantic models could become the ORM models directly, less battle-tested than plain SQLAlchemy, built by the FastAPI author so it's a natural pairing

D) Other (please describe after [Answer]: tag below)

[Answer]: A — SQLAlchemy 2.0 (async, asyncpg driver). Note: pinning to `sqlalchemy>=2.0` rather than a specific "2.2" — the current stable line is 2.0.x; there is no 2.2 release. uv will resolve the latest compatible 2.0.x release.

## Question 2: Migration tooling
A) **Alembic** — the standard companion to SQLAlchemy/SQLModel, versioned migration scripts, real production practice, worth demonstrating for a Senior-level submission

B) **`create_all()` on startup** — no migration history, tables just get (re)created from the current model definitions; simplest, but doesn't demonstrate schema evolution and would need replacing before this could be called production-grade

C) Other (please describe after [Answer]: tag below)

[Answer]: A — Alembic.

## Question 3: Local Postgres for development
Docker Compose (Unit 6) doesn't exist yet, but Unit 2's tests need a real Postgres to run against — pgvector rules out SQLite as a substitute.

A) A single `docker run postgres` command, documented in the README now, formalized into `docker-compose.yml` when Unit 6 lands

B) Testcontainers — tests spin up an ephemeral Postgres container automatically, no manual step, heavier dependency

C) Other (please describe after [Answer]: tag below)

[Answer]: C — write `docker-compose.yml` now with a Postgres (+pgvector) service, rather than a bare `docker run` command, since it's going to exist anyway once Unit 6 lands. Unit 6 extends this file (api/worker/frontend services) rather than creating it from scratch.

## Question 4: Message-write latency budget
Per Unit 2's functional design (BR3), the user's message is written to `MessageRepository` before the provider call starts — a slow write here directly delays time-to-first-token.

A) No hard SLA — standard practices only (indexed foreign keys, connection pooling, async I/O throughout), revisit only if it's actually observed to be slow

B) A stated target (e.g. p95 < 20ms for the write) — worth defining now so a regression would be noticeable

C) Other (please describe after [Answer]: tag below)

[Answer]: A — no hard SLA, standard practices only.
