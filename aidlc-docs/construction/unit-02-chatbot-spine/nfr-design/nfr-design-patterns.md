# NFR Design Patterns — Unit 2: Chatbot Spine

## Resilience: fail-fast on startup, Compose sequencing owns the race

The app makes no special retry effort connecting to Postgres at startup. `docker-compose.yml`'s `api` service declares `depends_on: postgres: condition: service_healthy`, and the `postgres` service defines a `pg_isready`-based healthcheck — Compose won't start the app container until Postgres is actually accepting connections. Simpler than client-side retry logic, and sufficient since there's no requirement (yet) to survive Postgres restarting *after* the app is already up.

## Session-per-operation, not session-per-request

The core pattern for this unit: an `AsyncSession` is opened, used for exactly one logical DB operation, and closed — never held open across an `await` on something external (the LLM stream). Concretely, `send_message`'s flow (see `functional-design/business-logic-model.md`) opens and closes a session at each of: the initial conversation/history load, the user-message write, and the final assistant-message write. Nothing holds a session during the streaming loop itself.

**Why this matters concretely**: the streaming phase of a chat turn is the dominant share of its wall-clock time (multiple seconds, bound by Gemini's response time) but touches the database not at all. Session-per-request would check out a pool connection for that entire duration per concurrent chat; session-per-operation only checks one out for the few milliseconds an actual query takes. This directly serves the explicit goal of not growing the connection count — the pool's default size (5 + 10 overflow) can serve far more *concurrent chats* under this pattern than under session-per-request, because connections are only held during the brief moments they're actually doing something.

## Performance: default pool, unmodified

`pool_size=5`, `max_overflow=10` (SQLAlchemy's defaults) — not tuned, since there's no stated load target to tune against (NFR Requirements Q4) and the session-per-operation pattern above already minimizes how long each connection is held, which matters more than pool size at this project's scale.

## Security: inherited from the tech-stack choice, not a separate pattern

SQLAlchemy's query construction parameterizes values by default — this isn't a pattern applied on top, it's a property of using the ORM as intended (no raw string-interpolated SQL anywhere in this unit's repository implementations). Credentials via environment variable was already fixed in NFR Requirements.
