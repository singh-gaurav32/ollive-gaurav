"""Async engine + session factory. Session-per-operation pattern (NFR
design): callers open a session via `async with session_factory() as
session:` scoped to exactly one operation, never held across an external
call (e.g. the LLM streaming phase).

Not imported by db/__init__.py on purpose - reading DATABASE_URL happens
only when something actually needs a real connection (main.py, the
repository integration tests), not on every `from db.models import X`.
"""
from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL)
session_factory = async_sessionmaker(engine, expire_on_commit=False)
