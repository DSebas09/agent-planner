# CLAUDE.md — Agent Planner

> This file is the source of truth for how code is written in this project.
> Every decision here has a reason. Read it before writing a single line.

---

## Project Overview

A FastAPI + SQLAlchemy agent that plans a user's day by scoring and scheduling tasks
using a two-layer fuzzy logic engine. The agent reacts to task lifecycle events
(added, started, completed, delayed) and continuously re-plans.

### Module Map

| File | Responsibility |
|---|---|
| `main.py` | HTTP routing only — no business logic |
| `agent.py` | Agent cognition: perceive → plan → log |
| `scheduler.py` | Build ordered `DayPlanEntry` list from tasks |
| `fuzzy_engine.py` | Two-layer fuzzy scoring (urgency × priority × energy) |
| `models.py` | SQLAlchemy ORM models and domain enums |
| `schemas.py` | Pydantic request/response shapes |
| `dependencies.py` | FastAPI `Depends` factories (`DBSession`, `TaskDep`) |
| `database.py` | Engine, session context manager, `init_db` |
| `db_types.py` | Custom SQLAlchemy type decorators (e.g. `UTCDateTime`) |
| `config.py` | All constants and env vars — single source of truth |

---

## Non-Negotiable Rules

These apply to every file, every PR, no exceptions.

### 1. Type everything
- All function signatures have input and return type annotations
- No `Any` in Python unless unavoidable — document why with a comment
- SQLAlchemy models use `Mapped[T]` — never bare `Column()`

### 2. Functions do one thing
- Maximum 20 lines per function
- Maximum 3 levels of nesting — extract a named function instead
- If you need to write a comment explaining what a block does, extract it

### 3. Comments explain why, not what
```python
# BAD
task.status = TaskStatus.IN_PROGRESS  # set status to in progress

# GOOD
# flush before _perceive() so the updated status is visible in the same session
self._session.flush()
```

### 4. No dead code
- No commented-out blocks
- No unused imports or variables
- No TODO comments — open a ticket or fix it now

### 5. Fail fast
- Validate inputs at the boundary (Pydantic schemas, `get_task_or_404`)
- Never let invalid data propagate into the domain layer
- Use specific exception types — never bare `except:`

### 6. Naming
- Functions → verbs: `build_plan()`, `compute_task_score()`, `re_plan_day()`
- Booleans → predicates: `is_overdue`, `has_deadline`, `can_fit`
- Constants → `UPPER_SNAKE_CASE`
- Private module helpers → `_snake_case` prefix

---

## FastAPI Conventions

### Endpoints are thin
Endpoints do exactly three things: receive input, call domain logic, return output.
No SQL queries, no business logic, no `if/else` chains inside endpoint bodies.

```python
# GOOD
@tasks_router.post("/{task_id}/complete", response_model=list[PlanEntryResponse])
def complete_task(task_id: int, task: TaskDep, payload: CompleteTaskRequest, session: DBSession) -> list[DayPlanEntry]:
    Agent(session).on_task_completed(task, payload.actual_minutes)
    return _fetch_current_plan(session)

# BAD — business logic leaking into the router
@tasks_router.post("/{task_id}/complete", response_model=list[PlanEntryResponse])
def complete_task(task_id: int, ...):
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(...)
    task.status = TaskStatus.COMPLETED
    ...
```

### Dependencies via `Annotated` + `Depends`
- `DBSession` — injects a SQLAlchemy session with automatic commit/rollback
- `TaskDep` — resolves `task_id` from path and returns the ORM object or 404
- New shared dependencies go in `dependencies.py`, never inline in `main.py`

### Path parameters must appear in endpoint signature
Even if consumed by a `Depends`, declare `task_id: int` explicitly in the endpoint
to avoid FastAPI routing warnings:
```python
def start_task(task_id: int, task: TaskDep, session: DBSession) -> ...:
```

### Routers by domain
- `tasks_router` — all `/tasks` and `/tasks/{id}/*` routes
- `plan_router` — `/plan`
- `logs_router` — `/logs`
- New domains get a new `APIRouter` — never add routes directly to `app`

### HTTP semantics
- `POST` creates or triggers state transitions — never `GET` for mutations
- `201` for resource creation, `200` for state transitions, `422` for validation errors
- Always declare `response_model` — no raw dicts from endpoints

---

## SQLAlchemy Conventions

### Session lifecycle
The session is managed by `get_session()` in `database.py` via a context manager.
- `get_session()` commits on clean exit, rolls back on exception
- `session.flush()` is used inside `Agent` methods to make state visible within
  the same session before re-querying
- `session.commit()` inside endpoints is only allowed when `session.refresh()` is
  needed immediately after (e.g. `create_task`)
- Never open a `with get_session()` block inside an endpoint — use `DBSession`

### DateTime fields
All datetime columns use `UTCDateTime` from `db_types.py`, not `DateTime(timezone=True)`.
`UTCDateTime` normalizes to UTC on write and reattaches UTC on read from SQLite.

```python
# CORRECT
created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=lambda: datetime.now(timezone.utc))

# WRONG
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
```

### No raw `DateTime(timezone=True)` in models
SQLite silently strips timezone info. `UTCDateTime` is the only safe option for
datetime columns in this project.

---

## Pydantic Conventions

### Response schemas inherit `OrmBase`
Any schema serialized from a SQLAlchemy object inherits from `OrmBase`:
```python
class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```
Request schemas (`*Create`, `*Request`) use plain `BaseModel` — they never touch ORM objects.

### Use domain enums, not `str`
```python
# CORRECT
priority: Priority
energy_required: EnergyLevel
status: TaskStatus

# WRONG
priority: str = Field(pattern="^(high|medium|low)$")
```

### Use `AwareDatetime` for all datetime fields
Never use bare `datetime` in schemas — it accepts naive datetimes that will
fail at the DB layer.
```python
deadline: AwareDatetime | None = None   # CORRECT
deadline: datetime | None = None        # WRONG
```

### Strip whitespace on string input schemas
Any schema with user-provided string fields includes:
```python
model_config = ConfigDict(str_strip_whitespace=True)
```

---

## Agent Conventions

The `Agent` class is the only entry point for state mutations that trigger re-planning.
Direct ORM mutations from outside `Agent` (except in tests) are a code smell.

### Perceive → Plan → Apply → Log
Every `on_*` method follows this pattern:
1. Mutate task state if needed, then `flush()`
2. `_perceive()` — read active tasks from DB
3. `build_plan()` — pure function, returns new plan
4. `_apply_plan()` — delete old plan, insert new one
5. `_log()` — append an `AgentLog` entry
6. Final `flush()`

### `flush()` vs `commit()`
- `flush()` inside Agent — makes changes visible within the session for subsequent queries
- `commit()` is handled by `get_session()` when the context manager exits
- Never call `session.commit()` inside `Agent` methods

---

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agent): add postpone task support
fix(models): reattach UTC timezone to datetimes read from SQLite
refactor(main): inject database session via FastAPI Depends
chore(deps): add scikit-fuzzy dependency
```

Scopes map to module names: `main`, `agent`, `scheduler`, `fuzzy_engine`,
`models`, `schemas`, `dependencies`, `database`, `db_types`, `config`.

---

## What To Never Do

- Never query the DB directly from `main.py` — use `Agent` or private helpers
- Never use `DateTime(timezone=True)` in models — use `UTCDateTime`
- Never use `str` for enum fields in schemas — use the domain enum
- Never add business logic to endpoints — endpoints are routers, not services
- Never silently catch exceptions — log or re-raise with context
- Never commit to `main` with broken tests or linting errors
- Never hardcode values that belong in `config.py`
- Never use `session.commit()` inside `Agent` methods
