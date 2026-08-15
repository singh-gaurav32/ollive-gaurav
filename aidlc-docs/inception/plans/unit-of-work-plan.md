# Unit of Work Plan

**Input**: `requirements.md`, `stories.md`, `application-design/` artifacts

## Execution Checklist

- [x] Confirm backend process model (see Question 1) — A: single process
- [x] Confirm frontend delivery slicing (see Question 2) — A: one frontend unit, built last
- [x] Confirm unit-to-epic mapping (see Question 3) — A: 1:1 with the 6 story epics
- [x] Confirm code organization / directory structure (see Question 4) — A: backend/ + frontend/ split
- [ ] Generate `application-design/unit-of-work.md` — unit definitions, responsibilities, code organization
- [ ] Generate `application-design/unit-of-work-dependency.md` — dependency matrix between units
- [ ] Generate `application-design/unit-of-work-story-map.md` — story-to-unit mapping
- [ ] Validate: every story from `stories.md` assigned to exactly one unit

## Deferred Decision: Redis Streams Swap Testing

During Q1 discussion, the user asked whether choosing single-process (Q1=A) would block testing the actual Redis Streams swap before submission. Clarified: no — `EventQueue` is reached identically whether the caller is in-process or not, since Redis itself is out-of-process infrastructure reached over the network either way. The user explicitly decided **not** to expand v1 scope to include implementing/testing the Redis swap now; it remains a stretch goal to attempt opportunistically inside the Ingestion Pipeline unit, not a committed deliverable. `requirements.md` and US-3.3 are unchanged — only the swap-ready `EventQueue` interface is required for v1.

## Category Coverage Note

**Team Alignment** is intentionally not asked about as a question: `user-stories-assessment.md` already documents this as a solo build with no team-ownership boundaries to negotiate. Justification recorded here per the mandatory "don't skip without explicit justification" rule.

---

## Question 1: Backend process model
This has a real technical constraint attached. Requirements Analysis (Q6) chose an **in-process async queue** (e.g. `asyncio.Queue`) for the event broker. That data structure is only shareable within a single OS process — it cannot be shared across separate containers/processes without switching to something IPC-capable.

A) **Single process** — the FastAPI app runs `IngestionWorker` as a background asyncio task inside the same process. Consistent with the in-process queue decision already made; one backend container; simplest. *(Recommended — this is what "in-process queue" actually implies.)*

B) **Separate processes** — API and worker run as separate containers/entrypoints. This requires replacing the in-process queue with something IPC-capable now (effectively pulling forward the Redis Streams swap from Requirements Analysis Q6 rather than deferring it).

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2: Frontend delivery slicing
The confirmed delivery sequence (Requirements Analysis Q11) lists "frontend lifecycle" as its own late step. But some backend units are hard to verify without any UI at all.

A) **One frontend unit, built last** — full UI (chat, dashboard, lifecycle, auth) built together after all backend units are done. Matches the sequence as literally stated; backend units are verified via API calls/curl/SSE clients until then.

B) **Frontend built incrementally** — a minimal chat UI ships alongside the Chatbot Spine unit (so streaming is visually verified as it's built), a minimal dashboard view ships alongside the Dashboard unit, and the final frontend-focused unit only adds cancel/list/resume + auth UI on top of what already exists.

C) Other (please describe after [Answer]: tag below)

[Answer]: A — changed from initial B. Full UI built as one unit at the end (matches the delivery sequence as literally stated); backend units up through Dashboard are verified via API calls/curl/SSE clients, not a UI.

## Question 3: Unit-to-epic mapping
`stories.md` already groups stories into 6 epics matching the delivery sequence.

A) **Keep units 1:1 with the 6 story epics** (Provider Abstraction, Chatbot Spine, Ingestion Pipeline, Dashboard, Frontend Lifecycle, Deployment) — cleanest traceability from story → unit → code.

B) **Merge Provider Abstraction into Chatbot Spine** (5 units instead of 6) — they're built together in practice since Chatbot Spine can't function without the provider interface existing first.

C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4: Code organization (greenfield)
A) Single repo, two top-level directories: `backend/` (Python, src-layout, modular monolith with one module per unit) and `frontend/` (React app), plus `docker-compose.yml` and `k8s/` at the repo root

B) Single repo, `services/api/` and `services/frontend/` style layout

C) Other (please describe after [Answer]: tag below)

[Answer]: A
