"""Ensures modules that read DATABASE_URL/GEMINI_API_KEY at import time
(api/deps.py -> db/engine.py) are importable in tests that never actually
connect - they override the dependency instead. Real Postgres integration
tests (tests/db/test_sqlalchemy_repositories.py) are gated separately by
RUN_DB_TESTS, not by DATABASE_URL's mere presence, so this fallback can't
accidentally make them run against a database that doesn't exist.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
