# Logical Components — Unit 2: Chatbot Spine

## Session factory

A single module-level async `sessionmaker` (`async_sessionmaker[AsyncSession]`), bound to one async engine constructed from the `DATABASE_URL` environment variable at process startup. Every repository method that needs a session gets one from this factory via an `async with` block scoped to just that method — this is the mechanical realization of the session-per-operation pattern above.

## Repository implementations

`SqlAlchemyConversationRepository`, `SqlAlchemyMessageRepository`, `SqlAlchemyUserRepository` — concrete implementations of the `db/` interfaces already fixed in the shared-contracts pass. Each method opens its own session (see above), maps between the ORM row and the shared pydantic model (`Conversation`, `ChatMessage`, `User`, `Session`) before returning, so the ORM types never leak past the repository boundary into `ChatService` or any other unit.

## ORM models

SQLAlchemy `DeclarativeBase` table definitions living alongside the repositories in `db/` (e.g. `db/orm.py`) — distinct from `db/models.py`'s pydantic models, which remain the shared contract. This is the one deliberate duplication in the system: an ORM row shape and a pydantic domain shape for the same entity, kept separate on purpose so the ORM is swappable (per the tech-stack decision) without the shared contract ever changing shape.

## Alembic migration environment

Standard `alembic/` directory (`env.py`, `versions/`) at `backend/`'s root, configured to read `DATABASE_URL` from the same environment variable as the app. First migration creates `users`, `sessions`, `conversations`, `messages` — `logs` is Unit 3's migration to add later, kept as a separate revision so each unit's schema ownership stays visible in the migration history itself.

## Docker Compose (started this unit)

`docker-compose.yml` at the repo root: a `postgres` service (`pgvector/pgvector:pg16` image, named volume, `pg_isready` healthcheck) is all that exists yet. The `api` service (this unit's FastAPI app) depends on it via `condition: service_healthy`, per the resilience pattern above. Unit 6 adds `worker`/`frontend` services alongside these.
