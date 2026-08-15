# Unit → Story Map

| Unit | Stories (backend/logic) | Stories (frontend/UI, if deferred to Unit 5) |
|---|---|---|
| 1. Provider Abstraction | US-1.1, US-1.2 | — |
| 2. Chatbot Spine | US-2.1, US-2.2, US-2.3 (backend + persistence) | US-2.1, US-2.2, US-2.3 (chat UI completed in Unit 5) |
| 3. Ingestion Pipeline | US-3.1, US-3.2, US-3.3 | — (no UI surface) |
| 4. Observability Dashboard | US-4.1 (query endpoints) | US-4.1 (dashboard UI completed in Unit 5) |
| 5. Frontend + Auth | US-5.1, US-5.2, US-5.3, US-5.4 (new) | Full frontend for all of the above, plus its own stories |
| 6. Packaging & Deployment | US-6.1, US-6.2 | — |

## Notes

- US-2.1, US-2.2, US-2.3, and US-4.1 appear in two units deliberately: their acceptance criteria describe user-visible behavior ("I want to see...", "tokens appear incrementally in the UI"), which can't be fully satisfied until a UI exists. Unit 2 and Unit 4 build and verify the backend logic those criteria depend on; Unit 5 is where the criteria become fully demonstrable end-to-end. A story is not "done" in the shippable sense until its UI half lands in Unit 5, even though its logic is correct earlier.
- Every story in `stories.md` (US-1.1 through US-6.2, 13 total) appears in exactly one "home" unit above — no orphans.
