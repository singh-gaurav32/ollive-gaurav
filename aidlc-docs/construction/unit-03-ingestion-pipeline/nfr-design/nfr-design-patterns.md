# NFR Design Patterns — Unit 3: Ingestion Pipeline Hardening

No question round this time: NFR Requirements' one real decision (let the worker die, but log it loudly) already resolved the only genuine choice for this unit. What follows is that decision's technical realization, not a new open question.

## Resilience: making "let it die, loudly" actually loud

`asyncio.create_task()` does **not** surface an exception raised inside the task automatically — by default, an unhandled exception in a task is only reported (via `asyncio`'s default exception handler) when the task object is garbage collected, which can be arbitrarily delayed and is easy to miss entirely. Silence-by-default is the opposite of what NFR Requirements asked for.

The pattern: attach a `done_callback` to the worker task at creation time. The callback checks `task.exception()` — if the task ended via an exception (not cancellation, not a clean return), it's logged immediately at `CRITICAL` level with the full traceback, at the moment the task actually dies, not whenever the garbage collector happens to run.

## Performance: no pattern needed

NFR Requirements already decided no indexing and no new dependencies for this unit. Nothing further to design.

## Security: no pattern needed

Redaction correctness is functional-design territory (already specified, will be verified by tests in Code Generation), not a separate security pattern layered on top.

## Scalability: no pattern needed

Single-process monolith, unchanged from Units Generation.
