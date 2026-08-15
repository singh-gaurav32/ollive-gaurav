# Code Generation Plan — Unit 1: Provider Abstraction & Auto-Instrumentation

**Stories**: US-1.1, US-1.2
**Dependencies**: None — this is the foundation unit
**Workspace root**: `/Users/gauravsingh/developer/workspace/study/companies/ollive`
**Code location** (per `unit-of-work.md`): `backend/src/provider/`, `backend/tests/provider/`

## Scope Note
This unit is pure business logic — no HTTP surface, no persistence, no UI, no infrastructure. API Layer, Repository Layer, Frontend Components, Database Migrations, and Deployment Artifacts steps are all **N/A** and omitted below; they belong to later units (2, 2, 5, 6 respectively).

**Tooling choice**: Python 3.12, managed with `uv` (consistent with how you set up the alarm-clock AIDLC project). `google-genai` as the Gemini SDK. `pytest` + `pytest-asyncio` for testing. Flagging this now — if you'd rather use plain pip/poetry, say so before I generate.

## Steps

### Step 1: Project Structure Setup (greenfield — first unit, initializes the backend project)
- [x] `backend/pyproject.toml` — project metadata, dependencies (`google-genai`, `pydantic`), dev dependencies (`pytest`, `pytest-asyncio`)
- [x] `backend/.python-version` — pin to 3.12
- [x] `backend/src/provider/__init__.py`
- [x] `backend/tests/provider/__init__.py`
- [x] Root `README.md` — starts a "Getting Started" section with backend setup/test-run instructions; will grow with each subsequent unit rather than being rewritten

### Step 2: Business Logic Generation
- [x] `backend/src/provider/models.py` — `LogEvent` (per `domain-entities.md`), `Message`, `Token` types
- [x] `backend/src/provider/interface.py` — `LLMProvider` abstract interface (`send`, `stream`)
- [x] `backend/src/provider/event_queue.py` — `EventQueue` abstract interface (`publish`, `consume`) — interface only; `InProcessEventQueue` is Unit 3's deliverable
- [x] `backend/src/provider/gemini_provider.py` — `GeminiProvider` implementing `LLMProvider` against `google-genai`
- [x] `backend/src/provider/instrumented_provider.py` — `InstrumentedProvider` decorator, implementing the logic model exactly (BR1-BR9)

**Story mapping**: `interface.py` + `gemini_provider.py` → US-1.1 [x]. `instrumented_provider.py` → US-1.2 [x].

### Step 3: Business Logic Unit Testing
- [x] `backend/tests/provider/doubles.py` — `FakeLLMProvider` (controllable success/error/cancel behavior) and `FakeEventQueue` (records published events, can simulate publish failure) test doubles
- [x] `backend/tests/provider/test_instrumented_provider.py` — covers: success path populates all `LogEvent` fields correctly (BR1-BR4, BR6, BR7); provider error is re-raised AND logged with `status="error"` (BR5); publish failure is swallowed and never surfaces to the caller (BR5, BR9); `stream()` measures `ttft_ms` correctly; cancellation mid-stream produces a `status="cancelled"` event with partial tokens and re-raises `CancelledError` (BR8)
- [x] `backend/tests/provider/test_gemini_provider.py` — adapter shape test against a mocked `google-genai` client (no real API calls in unit tests)
- [x] Verified: `uv sync` + `uv run pytest -v` → 7/7 passed

**Story mapping**: Both test files → US-1.1, US-1.2 acceptance criteria.

### Step 4: Business Logic Summary
- [x] `aidlc-docs/construction/unit-01-provider-abstraction/code/summary.md` — what was built, how it maps to the functional design, how to run the tests

## Explicitly Skipped for This Unit
- API Layer Generation — no endpoints in this unit
- Repository Layer Generation — no persistence in this unit
- Frontend Components Generation — backend-only unit
- Database Migration Scripts — no data models persisted here
- Deployment Artifacts Generation — belongs to Unit 6
