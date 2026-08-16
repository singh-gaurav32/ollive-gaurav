# Functional Design Plan — Unit 4: Observability Dashboard

## Execution Checklist

- [x] Confirm endpoint shape (see Question 1) — A: one unified endpoint
- [x] Confirm parameter defaults/validation (see Question 2) — A: last-1h/60s defaults + validation
- [x] Confirm access scope (see Question 3) — A: aggregate view, not per-user scoped
- [x] Generate `business-logic-model.md`
- [x] Generate `business-rules.md`
- [x] Generate `domain-entities.md`
- No `frontend-components.md` — no UI in this unit (dashboard UI is Unit 5)

---

## Question 1: Endpoint shape
`component-methods.md` originally sketched three separate endpoints (`GET /metrics/latency`, `/metrics/throughput`, `/metrics/errors`) — but `query_window` already returns one `MetricBucket` with all three (`request_count`, `error_count`, `p50_latency_ms`, `p95_latency_ms`) per bucket in a single query.

A) **One endpoint**, `GET /metrics?start=&end=&bucket_size_seconds=`, returning the full list of `MetricBucket`s — the frontend (Unit 5) picks whichever fields it wants to chart. Matches what the underlying query already produces; three endpoints would mean either three separate calls to the same `query_window` or artificially splitting one result into three response shapes.

B) **Three endpoints** as originally sketched, each still backed by the same `query_window` call, just re-shaping the response to expose only the relevant field(s) — matches the original component design exactly, more surface area for no functional gain

C) Other (please describe after [Answer]: tag below)

[Answer]: A — one unified endpoint.

## Question 2: Parameter defaults and validation
`query_window(start_time, end_time, bucket_size_seconds)` has no defaults — the router needs to supply sensible ones when the caller doesn't specify.

A) Default to the last 1 hour, 60-second buckets, if `start`/`end`/`bucket_size_seconds` are omitted; reject (400) if `start >= end` or `bucket_size_seconds <= 0`

B) Require all three parameters explicitly — no defaults, simpler router code, pushes the decision to the caller (the future dashboard UI)

C) Other (please describe after [Answer]: tag below)

[Answer]: A — default to last 1 hour / 60s buckets, reject start>=end or bucket_size_seconds<=0 with a 400.

## Question 3: Access scope
Per `personas.md`, the Operator/Analyst persona views *aggregated* metrics only, never another user's raw conversation content — `MetricBucket` already only contains aggregate numbers, no per-user data.

A) Confirm: the metrics endpoint(s) require the same session auth as everything else (once Unit 5 lands) but aren't scoped to "my own data" the way conversations are — an aggregate view is inherently cross-user by design, not a leak given it contains no conversation content

B) Something else — describe after [Answer]: tag below

[Answer]: A — confirmed.
