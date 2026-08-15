# Project Structure

**Supersedes** the code-organization sketch in `unit-of-work.md` — that sketch assumed one top-level package per unit and didn't account for contracts shared *between* units (discovered when `EventQueue` was initially, incorrectly, nested inside `provider/`). This is now the authoritative structure.

## Principle

A package under `backend/src/` is either:
- **Unit-owned**: built entirely by one unit, consumed by others only through that unit's service-layer entry points (e.g. Unit 5 never touches `chat/`'s repositories directly — it calls `ChatService`).
- **Shared**: a contract that more than one unit reads, writes, or implements directly. Shared packages are defined as interfaces/models up front (this pass), with concrete implementations still landing in whichever unit owns that slice.

## Full Tree

```
backend/
  pyproject.toml
  .python-version
  src/
    db/                           # SHARED - all persistence contracts
      __init__.py
      models.py                    # User, Conversation, ChatMessage, LogRecord, Session (pydantic)
      user_repository.py           # UserRepository (ABC) - impl: Unit 2 (seed-user stub), Unit 5 (full)
      conversation_repository.py   # ConversationRepository (ABC) - impl: Unit 2
      message_repository.py        # MessageRepository (ABC) - impl: Unit 2
      log_repository.py            # LogRepository (ABC) + MetricBucket - impl: Unit 3; read directly by Unit 4
    events/                        # SHARED - the Unit1-to-Unit3 event contract
      __init__.py
      log_event.py                  # LogEvent, truncate_preview (moved from provider/)
      event_queue.py                 # EventQueue (ABC) (moved from provider/) - impl: Unit 3
      in_process_event_queue.py     # Unit 3 adds this; not created yet
    provider/                      # Unit 1 - provider-call boundary only
      __init__.py
      models.py                     # Message, Token, Role (provider-call-specific only)
      interface.py                   # LLMProvider (ABC), ProviderResponse, ProviderError
      gemini_provider.py
      instrumented_provider.py
    chat/                          # Unit 2 - not yet implemented
      __init__.py
    ingestion/                     # Unit 3 - not yet implemented
      __init__.py
    analytics/                     # Unit 4 - not yet implemented
      __init__.py
    auth/                          # Unit 5 - not yet implemented
      __init__.py
    api/                           # Units 2-5 (routers, grown incrementally)
      __init__.py
  tests/
    db/
    events/
    provider/
    chat/ ingestion/ analytics/ auth/ api/     # populated as each unit lands
frontend/                          # Unit 5 - not yet created
docker-compose.yml                  # Unit 6 - not yet created
k8s/                                 # Unit 6 - not yet created
```

## Why `db/` exists as one package instead of per-unit

`LogRepository` is written by Unit 3 but read directly by Unit 4's `AnalyticsService` (per `component-dependency.md`) — not through an intermediary service, a direct dependency. `UserRepository` is needed in stub form by Unit 2 (the seeded demo user, per the schema-foresight decision in `unit-of-work.md`) before Unit 5 builds real auth against the same interface. Neither of these is "owned" by a single unit in the way `ChatService` is owned by Unit 2. Grouping every repository under `db/` — regardless of which unit implements which — reflects that persistence is a whole-system concern (`requirements.md` FR4 is stated at the system level, not per-unit), and prevents a repeat of the `EventQueue` situation for every other repository.

`ConversationRepository` and `MessageRepository` are also here even though only Unit 2 touches them directly today — consistency: every repository lives in `db/`, none nested in a unit's own directory, so no future unit has to guess or reach across a boundary.

## What's still unit-scoped

Anything that doesn't cross a unit boundary stays where it is: `provider/`'s `Message`/`Token`/`Role`/`LLMProvider`/`ProviderResponse`/`ProviderError` are only ever touched by Unit 1's own code (Unit 2's `ChatService` calls `InstrumentedProvider`, not these types directly at the boundary — it passes/receives `Message`/`Token` through the interface, which is normal interface usage, not a structural coupling). The concrete storage technology (SQLAlchemy, raw SQL, whatever) behind each `db/` repository interface remains that repository's implementing unit's own decision.
