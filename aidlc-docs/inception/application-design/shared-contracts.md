# Shared Contracts

Every interface and domain model that crosses a unit boundary, defined now so no later unit discovers a structural surprise. Concrete implementations still land in whichever unit owns that slice — this document (and the corresponding code in `db/` and `events/`) fixes only the *shape*.

## `events/` — the Unit 1 → Unit 3 contract

### `LogEvent` (pydantic model)
Unchanged from Unit 1's `domain-entities.md` — relocated, not redesigned. In-flight, pre-redaction snapshot of one provider call. Published by `InstrumentedProvider` (Unit 1), consumed by `IngestionWorker` (Unit 3).

### `EventQueue` (ABC)
Unchanged from Unit 1 — `publish(event) -> None`, `consume() -> AsyncIterator[LogEvent]`. Implemented by `InProcessEventQueue` (Unit 3).

## `db/` — the whole-system persistence contract

### `User`
| Field | Type |
|---|---|
| `id` | UUID |
| `username` | str |
| `created_at` | datetime |

### `Session`
| Field | Type |
|---|---|
| `id` | UUID |
| `user_id` | UUID |
| `created_at` | datetime |

### `Conversation`
| Field | Type |
|---|---|
| `id` | UUID |
| `user_id` | UUID |
| `state` | `"active"` \| `"cancelled"` (default `"active"`) |
| `created_at`, `updated_at` | datetime |

Note: "resume" is a transition (`cancelled` → `active`), not a third state — matches the State-pattern design from `component-methods.md` (`ChatService.resume_conversation` sets state back to `active`).

### `ChatMessage`
| Field | Type |
|---|---|
| `id` | UUID |
| `conversation_id` | UUID |
| `role` | `"user"` \| `"assistant"` |
| `content` | str |
| `created_at` | datetime |

### `LogRecord`
The persisted, **post-redaction** counterpart to `LogEvent` — same shape, but `input_preview`/`output_preview` have been through `PIIRedactor` (Unit 3) before this is ever constructed. Adds an `id` (UUID) that `LogEvent` doesn't have, since `LogEvent` is a transient message, not a stored row.

### `UserRepository` (ABC)
- `get_by_username(username) -> User | None`
- `get_or_create_seed_user() -> User` — Unit 2's stand-in for real auth until Unit 5 lands. The method stays in the interface permanently (harmless once unused); only callers change when Unit 5 ships.
- `create_session(user_id) -> Session`
- `get_session(session_id) -> Session | None`

**Implemented by**: Unit 2 (seed-user path only), completed by Unit 5 (real login).

### `ConversationRepository` (ABC)
- `create(user_id) -> Conversation`
- `get(conversation_id, user_id) -> Conversation | None` — user-scoped; returns `None` rather than another user's data if the conversation belongs to someone else. This *is* the isolation guarantee behind US-5.4, not a policy layered on top of it.
- `list_for_user(user_id) -> list[Conversation]`
- `update_state(conversation_id, new_state) -> None`

**Implemented by**: Unit 2. Read only through `ChatService`, never imported directly by later units.

### `MessageRepository` (ABC)
- `append(conversation_id, role, content) -> ChatMessage`
- `list_for_conversation(conversation_id) -> list[ChatMessage]`

**Implemented by**: Unit 2.

### `LogRepository` (ABC) + `MetricBucket`
- `insert(record: LogRecord) -> None`
- `query_window(start_time, end_time, bucket_size_seconds) -> list[MetricBucket]`
- `MetricBucket`: `bucket_start`, `bucket_end`, `request_count`, `error_count`, `p50_latency_ms`, `p95_latency_ms`

**Implemented by**: Unit 3 (`insert`, and `query_window` since it's the natural owner of the `logs` table). **Read directly by**: Unit 4's `AnalyticsService` — this is the one repository with a genuine cross-unit *direct* dependency (not mediated through a service), which is exactly why it lives in `db/` rather than nested in `ingestion/`.

## Refinement vs. `application-design/component-methods.md`

`AuthService.validate_session` was originally specified as returning a `UserContext`. This pass collapses that into returning `User | None` directly — no separate context type earns its keep at this project's scope. Noted here rather than silently diverging from the approved Application Design.
