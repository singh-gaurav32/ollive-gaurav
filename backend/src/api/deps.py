"""FastAPI dependencies: a wired ChatService and a current-user stand-in.

get_chat_service is deliberately a cached singleton, not a per-request
instance - ChatService's active-stream registry (BR6) must be shared
across requests, since cancel_conversation runs as a *separate* request
from the one that started the stream. A fresh ChatService per request
would make cancellation permanently unable to find anything to cancel.
"""
from __future__ import annotations

import os
from functools import lru_cache

from chat.service import ChatService
from chat.truncation import WindowTruncationStrategy
from db.engine import session_factory
from db.models import User
from db.sqlalchemy_conversation_repository import SqlAlchemyConversationRepository
from db.sqlalchemy_message_repository import SqlAlchemyMessageRepository
from db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from events.noop_event_queue import NoOpEventQueue
from provider.gemini_provider import GeminiProvider
from provider.instrumented_provider import InstrumentedProvider


@lru_cache
def get_chat_service() -> ChatService:
    conversation_repo = SqlAlchemyConversationRepository(session_factory)
    message_repo = SqlAlchemyMessageRepository(session_factory)
    gemini = GeminiProvider(api_key=os.environ["GEMINI_API_KEY"])
    instrumented = InstrumentedProvider(gemini, NoOpEventQueue(), provider_name="gemini")
    return ChatService(
        instrumented_provider=instrumented,
        conversation_repository=conversation_repo,
        message_repository=message_repo,
        truncation_strategy=WindowTruncationStrategy(),
    )


@lru_cache
def _user_repository() -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session_factory)


async def get_current_user() -> User:
    """Temporary: always resolves to the seeded demo user until Unit 5
    wires in real session-based auth (Unit 2 Q4)."""
    return await _user_repository().get_or_create_seed_user()
