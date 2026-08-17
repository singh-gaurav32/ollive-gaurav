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

## 3. Bonus: multi-provider support — done (2026-08-17)

- [x] **8 of 8 bonus items from the problem statement now done.** Added `OpenAIProvider` (`backend/src/provider/openai_provider.py`) implementing `LLMProvider`. `LLM_PROVIDER` env var selects `gemini` (default) or `openai` in `api/deps.py`'s `_build_provider()` — zero changes needed to `ChatService`, ingestion, the dashboard, or the frontend, confirming the provider-agnostic design (Unit 1) actually works as intended, not just in theory.
- [x] 59/59 backend tests pass (2 new mocked-client tests for `OpenAIProvider`, mirroring `test_gemini_provider.py`'s structure).
- [ ] **Not verified against the real OpenAI API** — no chargeable API key was available (user's explicit call). Every Gemini change in this session was confirmed live before deploying; this one only has mocked-unit-test coverage. Documented as a real gap in README's "What I'd Improve," not glossed over. If a key becomes available: run the same local-script verification pattern used for Gemini (`GeminiProvider` → `OpenAIProvider`, real message, check streamed output), then redeploy.

## 4. Cleanup (not urgent, no cost)

- [ ] Terminate the unused `161.118.184.11` Oracle instance (wrong-shape first attempt from provisioning)
