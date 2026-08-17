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

- [x] **Dashboard bucket window is now user-configurable in the UI** (2026-08-17). Added bucket-size (30s/1m/5m/15m/1h) and range (1h/6h/24h) dropdowns to `DashboardPage.tsx`, wired through `useMetrics`/`api/metrics.ts` to the backend's existing `bucket_size_seconds`/`start`/`end` params. Also fixed the "Requests (last 1h)" summary label to reflect whatever range is actually selected. Verified locally and live.
- [x] **Gemini output length now capped** (2026-08-17). `GeminiProvider` passes `GenerateContentConfig(max_output_tokens=...)` on every call, default 2048, overridable via `GEMINI_MAX_OUTPUT_TOKENS`. Found via real-API testing that `gemini-3-flash-preview`'s internal "thinking" tokens count against this same budget — a cap set too low (~20) can starve visible output entirely; 2048 confirmed to leave real headroom. Verified locally against the real API before redeploying. **Still open**: no request-rate limiting exists — that's a separate concern (Google AI Studio's own billing/spend cap is the authoritative guard for that, independent of app code).

## 3. Bonus opportunity: multi-provider support

7 of 8 bonus items from the problem statement are done (streaming, dashboards, Docker Compose, event-based architecture, PII redaction, self-hosted k8s deploy, frontend cancel/list/resume). The one gap: only `GeminiProvider` is implemented, even though `LLMProvider` (Unit 1) was deliberately built provider-agnostic for exactly this. Adding a second provider (OpenAI or Claude) shouldn't touch chat logic, ingestion, the dashboard, or the frontend — just a new `XProvider` class implementing `LLMProvider`, wired via a config choice in `api/deps.py`. Highest-leverage remaining bonus item.

## 4. Cleanup (not urgent, no cost)

- [ ] Terminate the unused `161.118.184.11` Oracle instance (wrong-shape first attempt from provisioning)
