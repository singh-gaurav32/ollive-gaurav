# Ollive — LLM Inference Logging & Ingestion System

Built incrementally via AI-DLC. See `aidlc-docs/` for the full requirements, design, and decision trail behind every choice below.

## Getting Started (Backend)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
cd backend
uv sync
uv run pytest -v
```

Environment variables (create `backend/.env`, not committed):

```
GEMINI_API_KEY=your-key-here
```

## Status

This README grows as each unit of work lands.

- **Unit 1 — Provider Abstraction & Auto-Instrumentation** (done): `backend/src/provider/` — the `LLMProvider` interface, `GeminiProvider` adapter, and the `InstrumentedProvider` auto-instrumentation decorator. See `aidlc-docs/construction/unit-01-provider-abstraction/`.

More sections (architecture overview, schema design, tradeoffs, frontend setup, Docker Compose, deployment) will be added as later units land — the final polished README is a deliverable of its own, assembled once the system is complete.
