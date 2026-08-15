# Application Design — Consolidated

This document consolidates `components.md`, `component-methods.md`, `services.md`, and `component-dependency.md` into a single reviewable view. See those files for full detail.

## Design Decisions (from `application-design-plan.md`)

| Decision | Choice | Rationale |
|---|---|---|
| Ingestion pipeline granularity | Separate component per stage (`PayloadValidator`, `MetadataExtractor`, `PIIRedactor`, `LogPersister`) | Independently testable, matches Chain of Responsibility cleanly |
| Auto-instrumentation mechanism | Decorator (`InstrumentedProvider`) | Only option that satisfies "no call-site changes" (US-1.2) — a context-manager approach can be forgotten at new call sites |
| Chat/Conversation service boundary | Single `ChatService` | Owns both orchestration and lifecycle state; kept as one service since they're tightly coupled (every chat turn can affect lifecycle state) |
| Messages vs. logs writes | Two independent paths — messages synchronous, logs asynchronous via `EventQueue` | Messages must be immediately queryable for resume; logs must never add latency to chat (US-3.1) |
| Auth/session mechanism | Server-side session store | Simplest correct option for a demo with a handful of seeded users; no statelessness requirement exists |

## Component Summary

**Provider Layer**: `LLMProvider` (interface) → `GeminiProvider` (v1 adapter) → `InstrumentedProvider` (Decorator, the auto-instrumentation boundary).

**Event/Queue Layer**: `EventQueue` (interface) → `InProcessEventQueue` (v1 implementation, swap-ready for Redis Streams).

**Chat Layer**: `ChatService` (orchestration + lifecycle state) backed by `ConversationRepository` and `MessageRepository`.

**Ingestion Layer**: `IngestionWorker` driving four sequential pipeline stages (`PayloadValidator` → `MetadataExtractor` → `PIIRedactor` → `LogPersister`) into `LogRepository`.

**Auth Layer**: `AuthService` + `UserRepository`, server-side sessions.

**Analytics Layer**: `AnalyticsService` reading `LogRepository` with time-bucketed queries.

**API Layer**: `ChatRouter`, `ConversationRouter`, `DashboardRouter`, `AuthRouter` (FastAPI).

**Frontend**: single React SPA — chat, conversation list/resume, dashboard, login.

## The One Structural Property Worth Highlighting

The chat path and the ingestion path touch at exactly one point — `InstrumentedProvider`'s non-blocking publish to `EventQueue` — and nowhere else. `ChatService` has zero awareness that logging exists. This is what makes the "auto-instrument" and "non-blocking ingestion" requirements structural guarantees rather than conventions someone has to remember to follow.

## Completeness Check

- Every FR in `requirements.md` (FR1–FR6) maps to at least one component above.
- Every story in `stories.md` maps to at least one service flow in `services.md`.
- No orphan components: every component listed appears in at least one service flow or is a direct dependency of one that does.
