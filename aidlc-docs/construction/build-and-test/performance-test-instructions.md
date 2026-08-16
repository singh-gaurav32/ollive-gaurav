# Performance Test Instructions

## Status: Not executed — out of scope for this project, by design

Ollive is a demo/portfolio project (single-VM, Always-Free-tier deployment, no autoscaling — see `aidlc-docs/construction/unit-06-packaging-deployment/nfr-requirements/nfr-requirements.md`), and no performance/load requirements were ever defined during Requirements Analysis or any unit's NFR Requirements stage. Formal load/stress testing (response-time SLAs, concurrent-user targets) would be testing against numbers nobody asked for. This file documents *how* to run one if that ever changes, rather than fabricating pass/fail results against undefined targets.

## What already exists instead

Unit 4's Observability Dashboard (`GET /metrics`) reports real p50/p95 latency, throughput, and error rate from actual traffic — the closest thing this project has to a performance signal, and it's live data, not a synthetic benchmark. During this session's verification, a single real request showed a 360ms p95 (backend-only path; the underlying Gemini call itself failed fast due to a dummy API key in this environment, so this number reflects the app's own overhead, not a representative LLM round-trip).

## If load testing becomes a requirement later

A minimal setup, using [k6](https://k6.io/) against the deployed instance:

```javascript
// smoke-test.js
import http from 'k6/http';
export default function () {
  http.get('https://YOUR-SUBDOMAIN.duckdns.org/health');
}
```
```bash
k6 run --vus 10 --duration 30s smoke-test.js
```

Before treating any result as meaningful, first get real requirements from the user (expected concurrent users, acceptable latency, acceptable error rate) — none currently exist for this project.
