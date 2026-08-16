"""FastAPI application entrypoint."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.chat_router import router as chat_router
from api.deps import get_ingestion_worker

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


@asynccontextmanager
async def lifespan(app: FastAPI):
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
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
