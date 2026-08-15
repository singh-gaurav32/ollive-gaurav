# Unit of Work Dependencies

## Dependency Matrix

| Unit | Depends On | Why |
|---|---|---|
| 1. Provider Abstraction | — | Foundation; no dependencies |
| 2. Chatbot Spine | Unit 1 | Needs `InstrumentedProvider` as the call boundary |
| 3. Ingestion Pipeline | Unit 1, Unit 2 | Events originate in `InstrumentedProvider`; needs a real chat call (Unit 2) to generate one end-to-end |
| 4. Observability Dashboard | Unit 3 | Needs real log data to query |
| 5. Frontend + Auth | Unit 1, Unit 2, Unit 3, Unit 4 | Builds the UI for every prior unit's stories and wraps real auth around the stub user introduced in Unit 2 |
| 6. Packaging & Deployment | Unit 1, Unit 2, Unit 3, Unit 4, Unit 5 | Packages the complete system |

## Update Strategy

- **Sequence**: Strictly sequential — this is a single-process modular monolith (Q1), not independently deployable microservices, so there's no meaningful parallelization opportunity between units. Each unit's code also physically depends on the previous one's modules.
- **Critical Path**: Every unit is on the critical path; there is no branch of work that can run in parallel with another given the dependency chain above.
- **Coordination Points**: Unit 2 introduces the `user_id`-scoped schema that Units 3 and 5 both build on — get that schema right in Unit 2 since Units 3-6 assume it exists. Unit 3's `EventQueue` interface is the coordination point for the deferred Redis Streams swap (not built now, but the interface contract must not change shape later).
- **Testing Checkpoints**: Each unit ends with its own verification (unit tests for 1, integration test for 3, curl/Postman for 2 and 4, full end-to-end browser testing for 5, a clean-clone `docker compose up` for 6) before merging its branch to `main`, per the confirmed git workflow (one branch per unit).
- **Rollback Strategy**: Because units merge to `main` sequentially via separate branches, a problem discovered in unit N is isolated to that branch until merged — reverting a merge commit rolls back cleanly without affecting earlier units' already-merged work.
