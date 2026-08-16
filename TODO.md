# TODO — Before Submission

Picked up from a live deployment/review session on 2026-08-17. Ordered roughly by priority.

## 1. Required deliverable content (not bonus — do this first)

The problem statement requires the README to include an architecture overview, schema design decisions, tradeoffs, and "what you'd improve with more time." Currently it doesn't — `README.md`'s Status section literally says this is still pending assembly. All the underlying material already exists scattered across `aidlc-docs/` (requirements, functional design, NFR design per unit) — this is a consolidation task, not new research.

- [ ] Add an **Architecture Overview** section to README: the 6-unit shape (provider abstraction → chat spine → ingestion pipeline → dashboard → frontend/auth → packaging/deployment), how they connect, and a simple diagram if time allows
- [ ] Add a **Schema Design** section: `logs`, `failed_log_events`, `conversations`, `chat_messages`, `users` — what each stores and why (source material: `aidlc-docs/construction/*/functional-design/domain-entities.md` per unit)
- [ ] Add a **Tradeoffs** section: notable ones already documented per-unit, e.g. in-process event queue vs. a real broker, window-based context truncation (no summarization), hand-mirrored TS types vs. codegen, no secrets manager, single-node k3s no HA
- [ ] Add/consolidate a **"What I'd improve with more time"** section — each unit's code summary (`aidlc-docs/construction/*/code/summary.md`) already has one of these, pull the highlights together

Separately, the problem statement asks for standalone **Architecture Notes** (can be a section in README or a separate `ARCHITECTURE.md`) covering:
- [ ] Ingestion flow (event → validate → extract → redact → persist, with the dead-letter path for failures)
- [ ] Logging strategy (auto-instrumentation via `InstrumentedProvider`, no manual call-site logging)
- [ ] Scaling considerations (current single-node/in-process limits, what would need to change for real scale — e.g. in-process event queue → real broker, single Postgres → read replicas)
- [ ] Failure handling assumptions (provider errors surfaced to the user gracefully, ingestion failures dead-lettered not dropped, worker crash logged loudly per `main.py`'s `_log_if_crashed`)

## 2. Small fixes identified during live deployment review

- [ ] **Dashboard bucket window isn't user-configurable in the UI.** The backend already supports `bucket_size_seconds`/`start`/`end` query params (`GET /metrics`), but the frontend hardcodes no params (always last-1h/60s) — `frontend/src/api/metrics.ts`. Add UI controls (bucket-size dropdown, time-range picker) and wire them through `useMetrics`.
- [ ] **No cap on Gemini output length or request rate.** `gemini_provider.py`'s calls pass no `max_output_tokens`/`generation_config` — Gemini's own model default applies, uncapped by our code. No rate limiting exists either. Options: add `max_output_tokens` to the provider call (bounds worst-case response length/cost), and/or set a spend cap directly in Google AI Studio's billing settings for the API key (authoritative, independent of app code).

## 3. Bonus opportunity: multi-provider support

7 of 8 bonus items from the problem statement are done (streaming, dashboards, Docker Compose, event-based architecture, PII redaction, self-hosted k8s deploy, frontend cancel/list/resume). The one gap: only `GeminiProvider` is implemented, even though `LLMProvider` (Unit 1) was deliberately built provider-agnostic for exactly this. Adding a second provider (OpenAI or Claude) shouldn't touch chat logic, ingestion, the dashboard, or the frontend — just a new `XProvider` class implementing `LLMProvider`, wired via a config choice in `api/deps.py`. Highest-leverage remaining bonus item.

## 4. Cleanup (not urgent, no cost)

- [ ] Terminate the unused `161.118.184.11` Oracle instance (wrong-shape first attempt from provisioning)
