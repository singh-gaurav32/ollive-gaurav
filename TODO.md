# TODO — Before Submission

Picked up from a live deployment/review session on 2026-08-17. Ordered roughly by priority.

## 1. Required deliverable content — done (2026-08-17)

- [x] **Architecture Overview** section added to README
- [x] **Schema Design** section added to README
- [x] **Tradeoffs** section added to README
- [x] **"What I'd improve with more time"** section added to README
- [x] Standalone **Architecture Notes** written as `docs/architecture-notes.md` (ingestion flow, logging strategy, scaling considerations, failure handling assumptions)
- [x] As part of this, stopped tracking `aidlc-docs/` (the internal AI-DLC process trail — plans, per-stage approvals, incremental unit-by-unit build log) in git; it's gitignored now and `docs/` is the curated, evaluator-facing replacement. Note: this only affects commits going forward — `aidlc-docs/` is still visible in the repo's existing git history unless that's separately rewritten (not done, would need a force-push, wasn't asked for)

## 2. Small fixes identified during live deployment review

- [ ] **Dashboard bucket window isn't user-configurable in the UI.** The backend already supports `bucket_size_seconds`/`start`/`end` query params (`GET /metrics`), but the frontend hardcodes no params (always last-1h/60s) — `frontend/src/api/metrics.ts`. Add UI controls (bucket-size dropdown, time-range picker) and wire them through `useMetrics`.
- [ ] **No cap on Gemini output length or request rate.** `gemini_provider.py`'s calls pass no `max_output_tokens`/`generation_config` — Gemini's own model default applies, uncapped by our code. No rate limiting exists either. Options: add `max_output_tokens` to the provider call (bounds worst-case response length/cost), and/or set a spend cap directly in Google AI Studio's billing settings for the API key (authoritative, independent of app code).

## 3. Bonus opportunity: multi-provider support

7 of 8 bonus items from the problem statement are done (streaming, dashboards, Docker Compose, event-based architecture, PII redaction, self-hosted k8s deploy, frontend cancel/list/resume). The one gap: only `GeminiProvider` is implemented, even though `LLMProvider` (Unit 1) was deliberately built provider-agnostic for exactly this. Adding a second provider (OpenAI or Claude) shouldn't touch chat logic, ingestion, the dashboard, or the frontend — just a new `XProvider` class implementing `LLMProvider`, wired via a config choice in `api/deps.py`. Highest-leverage remaining bonus item.

## 4. Cleanup (not urgent, no cost)

- [ ] Terminate the unused `161.118.184.11` Oracle instance (wrong-shape first attempt from provisioning)
