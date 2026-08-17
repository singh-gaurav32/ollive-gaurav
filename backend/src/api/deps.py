"""FastAPI dependencies: a wired ChatService, an IngestionWorker, and the
auth context (Unit 5, replaces Unit 2's get_current_user stub).

get_chat_service and get_ingestion_worker are deliberately cached
singletons, not per-request instances - ChatService's active-stream
registry (BR6, Unit 2) must be shared across requests, and get_event_queue
must return the *same* InProcessEventQueue instance to both the producer
side (InstrumentedProvider, via get_chat_service) and the consumer side
(IngestionWorker, started in main.py's lifespan) - otherwise the worker
would be draining a different queue than the one events are published to.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

from fastapi import Depends, HTTPException, Request

from analytics.service import AnalyticsService
from auth import SESSION_COOKIE_NAME, AuthService
from chat.service import ChatService
from chat.truncation import WindowTruncationStrategy
from db.engine import session_factory
from db.models import User
from db.sqlalchemy_conversation_repository import SqlAlchemyConversationRepository
from db.sqlalchemy_failed_log_event_repository import SqlAlchemyFailedLogEventRepository
from db.sqlalchemy_log_repository import SqlAlchemyLogRepository
from db.sqlalchemy_message_repository import SqlAlchemyMessageRepository
from db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from events.in_process_event_queue import InProcessEventQueue
from ingestion.log_persister import LogPersister
from ingestion.metadata_extractor import MetadataExtractor
from ingestion.payload_validator import PayloadValidator
from ingestion.pii_redactor import PIIRedactor
from ingestion.worker import IngestionWorker
from provider.gemini_provider import GeminiProvider
from provider.instrumented_provider import InstrumentedProvider


@lru_cache
def get_event_queue() -> InProcessEventQueue:
    return InProcessEventQueue()


@lru_cache
def get_chat_service() -> ChatService:
    conversation_repo = SqlAlchemyConversationRepository(session_factory)
    message_repo = SqlAlchemyMessageRepository(session_factory)
    gemini = GeminiProvider(
        api_key=os.environ["GEMINI_API_KEY"],
        max_output_tokens=int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "2048")),
    )
    instrumented = InstrumentedProvider(gemini, get_event_queue(), provider_name="gemini")
    return ChatService(
        instrumented_provider=instrumented,
        conversation_repository=conversation_repo,
        message_repository=message_repo,
        truncation_strategy=WindowTruncationStrategy(),
    )


@lru_cache
def get_ingestion_worker() -> IngestionWorker:
    log_repo = SqlAlchemyLogRepository(session_factory)
    failed_repo = SqlAlchemyFailedLogEventRepository(session_factory)
    return IngestionWorker(
        queue=get_event_queue(),
        validator=PayloadValidator(),
        extractor=MetadataExtractor(),
        redactor=PIIRedactor(),
        persister=LogPersister(log_repo),
        failed_log_event_repository=failed_repo,
    )


@lru_cache
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(SqlAlchemyLogRepository(session_factory))


@lru_cache
def get_user_repository() -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session_factory)


@lru_cache
def get_auth_service() -> AuthService:
    return AuthService(get_user_repository())


@dataclass
class AuthContext:
    """Carries both the current User and the real session id - replaces
    Unit 2's user.id-as-session_id placeholder (BR4)."""

    user: User
    session_id: UUID


async def get_auth_context(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
) -> AuthContext:
    raw_session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_session_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        session_id = UUID(raw_session_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await auth_service.validate_session(session_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return AuthContext(user=user, session_id=session_id)
