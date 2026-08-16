"""Integration tests for the SQLAlchemy repository implementations against
a real Postgres. Requires:

    docker compose up -d postgres
    cd backend && DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive uv run alembic upgrade head
    RUN_DB_TESTS=1 DATABASE_URL=postgresql+asyncpg://ollive:ollive@localhost:5432/ollive uv run pytest tests/db/test_sqlalchemy_repositories.py

Gated on RUN_DB_TESTS specifically, not just DATABASE_URL's presence -
conftest.py sets a dummy DATABASE_URL fallback so other tests can import
api/deps.py without a real database, which would otherwise make this
skip condition always false and try to connect to a database that
doesn't exist.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1", reason="requires a running Postgres - see module docstring"
)


@pytest.fixture
async def factory():
    # A fresh engine per test, not db.engine's module-level singleton -
    # pytest-asyncio gives each test its own event loop by default, and an
    # asyncpg connection pool bound to one loop breaks when reused from
    # another ("another operation is in progress"). Production code (one
    # process, one long-running loop) doesn't hit this; only the test
    # harness's per-function loop churn does.
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"])
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    yield session_maker
    await engine.dispose()


@pytest.fixture
def conversation_repo(factory):
    from db.sqlalchemy_conversation_repository import SqlAlchemyConversationRepository

    return SqlAlchemyConversationRepository(factory)


@pytest.fixture
def message_repo(factory):
    from db.sqlalchemy_message_repository import SqlAlchemyMessageRepository

    return SqlAlchemyMessageRepository(factory)


@pytest.fixture
def user_repo(factory):
    from db.sqlalchemy_user_repository import SqlAlchemyUserRepository

    return SqlAlchemyUserRepository(factory)


@pytest.fixture
def log_repo(factory):
    from db.sqlalchemy_log_repository import SqlAlchemyLogRepository

    return SqlAlchemyLogRepository(factory)


@pytest.fixture
def failed_log_repo(factory):
    from db.sqlalchemy_failed_log_event_repository import SqlAlchemyFailedLogEventRepository

    return SqlAlchemyFailedLogEventRepository(factory)


async def test_create_and_get_conversation(user_repo, conversation_repo):
    user = await user_repo.get_or_create_seed_user()
    conversation = await conversation_repo.create(user.id)

    fetched = await conversation_repo.get(conversation.id, user.id)

    assert fetched is not None
    assert fetched.id == conversation.id
    assert fetched.state == "active"


async def test_get_is_scoped_to_owner(user_repo, conversation_repo):
    user = await user_repo.get_or_create_seed_user()
    other_user_id = uuid4()
    conversation = await conversation_repo.create(user.id)

    result = await conversation_repo.get(conversation.id, other_user_id)

    assert result is None


async def test_update_state_persists(user_repo, conversation_repo):
    user = await user_repo.get_or_create_seed_user()
    conversation = await conversation_repo.create(user.id)

    await conversation_repo.update_state(conversation.id, "cancelled")
    fetched = await conversation_repo.get(conversation.id, user.id)

    assert fetched is not None
    assert fetched.state == "cancelled"


async def test_message_append_and_list_in_order(user_repo, conversation_repo, message_repo):
    user = await user_repo.get_or_create_seed_user()
    conversation = await conversation_repo.create(user.id)

    await message_repo.append(conversation.id, "user", "hi")
    await message_repo.append(conversation.id, "assistant", "hello")

    messages = await message_repo.list_for_conversation(conversation.id)

    assert [m.role for m in messages] == ["user", "assistant"]
    assert [m.content for m in messages] == ["hi", "hello"]


async def test_seed_user_is_idempotent(user_repo):
    first = await user_repo.get_or_create_seed_user()
    second = await user_repo.get_or_create_seed_user()

    assert first.id == second.id


async def test_log_insert_and_query_window_aggregates_correctly(log_repo):
    from db.models import LogRecord

    base = datetime.now(timezone.utc).replace(microsecond=0)
    conversation_id = uuid4()
    session_id = uuid4()

    for i, (latency, status) in enumerate([(100.0, "success"), (200.0, "success"), (50.0, "error")]):
        await log_repo.insert(
            LogRecord(
                model="m",
                provider="p",
                latency_ms=latency,
                status=status,
                timestamp=base + timedelta(seconds=i),
                conversation_id=conversation_id,
                session_id=session_id,
                input_preview="hi",
                output_preview="ok",
            )
        )

    buckets = await log_repo.query_window(
        base - timedelta(seconds=5), base + timedelta(seconds=30), bucket_size_seconds=60
    )

    matching = [b for b in buckets if b.request_count >= 3]
    assert matching, f"expected a bucket with our 3 inserted rows, got {buckets}"
    bucket = matching[0]
    assert bucket.request_count == 3
    assert bucket.error_count == 1
    assert bucket.p50_latency_ms is not None
    assert bucket.p95_latency_ms is not None


async def test_failed_log_event_insert_does_not_raise(failed_log_repo):
    from db.models import FailedLogEvent

    record = FailedLogEvent(
        model="m",
        provider="p",
        conversation_id=uuid4(),
        session_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        failure_stage="persist",
        failure_reason="db down",
    )

    await failed_log_repo.insert(record)


async def test_logs_timestamp_index_exists(factory):
    from sqlalchemy import text

    async with factory() as session:
        result = await session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = 'logs' AND indexname = 'ix_logs_timestamp'")
        )
        assert result.scalar_one_or_none() == "ix_logs_timestamp"
