# NFR Design Plan — Unit 2: Chatbot Spine

## Category Coverage

- **Resilience Patterns** — Question 1.
- **Logical Components** — Question 2 (session lifecycle — the one genuinely ambiguous design point given async SQLAlchemy + a long-lived SSE request).
- **Scalability Patterns** — N/A, decided directly, not asked: single-process monolith (fixed in Units Generation), no stated load requirement to design against. Nothing to choose between.
- **Performance Patterns** — N/A, decided directly: SQLAlchemy's default async connection pool (`pool_size=5`, `max_overflow=10`) is used as-is — no stated SLA (per NFR Requirements Q4) to tune against, and guessing a pool size without a load target would be premature optimization.
- **Security Patterns** — N/A, decided directly: SQLAlchemy's parameterized queries close off SQL injection by construction (not a pattern chosen, a consequence of the ORM choice already made); DB credentials via env var was already decided in NFR Requirements.

---

## Question 1: Database startup resilience
Docker Compose brings up the app and Postgres together — the app container could start before Postgres is ready to accept connections.

A) **Retry with backoff on startup** — the app retries its first DB connection a few times with exponential backoff (e.g. up to ~10s total) before giving up, tolerating the race without relying on orchestration timing

B) **Fail fast, rely on Compose sequencing** — `depends_on` with a Postgres healthcheck (`pg_isready`) ensures Postgres is ready before the app container starts at all; the app makes no special effort itself

C) Other (please describe after [Answer]: tag below)

[Answer]: B — rely on Compose's `depends_on` + `pg_isready` healthcheck for now.

## Question 2: DB session lifecycle
Async SQLAlchemy sessions aren't meant to be long-lived or shared across concurrent operations. Unit 2's chat flow has one request (the SSE stream) that can stay open for the full duration of a streamed response, but does several *separate* DB operations within it (load conversation, load history, persist user message, persist assistant message at the end).

A) **A fresh, short-lived session per DB operation** — `send_message` opens and closes a session for the initial load, another for the user-message write, another for the final assistant-message write; never one session held open across the whole streaming duration

B) **One session for the whole request** — opened when the SSE request starts, closed when it ends, reused for every DB operation within that turn

C) Other (please describe after [Answer]: tag below)

[Answer]: A — short-lived session per DB operation, never held open across the streaming duration. Explicitly to keep connection usage minimal per concurrent chat.
