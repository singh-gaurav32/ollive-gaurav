"""FastAPI application entrypoint."""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth_router import router as auth_router
from api.chat_router import router as chat_router
from api.dashboard_router import router as dashboard_router
from api.deps import get_ingestion_worker, get_user_repository
from auth import DEMO_USERNAMES

logger = logging.getLogger(__name__)


def _log_if_crashed(task: asyncio.Task) -> None:
    """asyncio doesn't surface a task's unhandled exception until the task
    is garbage collected, which is arbitrarily delayed and easy to miss -
    this makes a worker crash loud and immediate instead (NFR design)."""
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.critical("IngestionWorker crashed", exc_info=exc)


async def _seed_demo_users() -> None:
    """Idempotent, same idiom as Unit 2's single seed user (BR2)."""
    user_repo = get_user_repository()
    for username in DEMO_USERNAMES:
        existing = await user_repo.get_by_username(username)
        if existing is None:
            await user_repo.create_user(username)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _seed_demo_users()

    worker = get_ingestion_worker()
    worker_task = asyncio.create_task(worker.run())
    worker_task.add_done_callback(_log_if_crashed)
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Ollive - LLM Inference Logging & Ingestion System", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
