"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from api.chat_router import router as chat_router

app = FastAPI(title="Ollive - LLM Inference Logging & Ingestion System")
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
