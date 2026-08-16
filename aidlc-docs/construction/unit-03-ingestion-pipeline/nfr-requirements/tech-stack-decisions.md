# Tech Stack Decisions — Unit 3: Ingestion Pipeline Hardening

No new tech stack decisions for this unit. `PIIRedactor` uses stdlib `re`; `InProcessEventQueue` uses stdlib `asyncio.Queue`; `SqlAlchemyLogRepository` and `SqlAlchemyFailedLogEventRepository` reuse the SQLAlchemy 2.0 async + Alembic stack already decided in Unit 2's NFR Requirements. Recorded here for completeness rather than left implicit.
