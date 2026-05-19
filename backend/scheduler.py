from datetime import datetime, timedelta, timezone

from config import INTERRUPTION_THRESHOLD, MINUTES_IN_DAY
from fuzzy_engine import compute_task_score
from models import DayPlanEntry, Task, TaskStatus, EnergyLevel

_ENERGY_LEVEL_ORDER = list(reversed(EnergyLevel))  # [LOW, MEDIUM, HIGH]


def build_plan(
    tasks: list[Task],
    now: datetime,
    urgent_task: Task | None = None,
) -> list[DayPlanEntry]:
    """Score and schedule all pending tasks into sequential time slots from now.

    If a task is in progress, it stays at the top unless urgent_task scores
    above it by at least INTERRUPTION_THRESHOLD points.
    """
    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    in_progress = next((t for t in tasks if t.status == TaskStatus.IN_PROGRESS), None)

    scored = _score_tasks(pending, now)

    if in_progress is None:
        ordered_tasks = [t for t, _ in scored]
    else:
        ordered_tasks = _resolve_order(in_progress, scored, now, urgent_task)

    return _assign_time_slots(ordered_tasks, now)


def _score_tasks(tasks: list[Task], now: datetime) -> list[tuple[Task, float]]:
    scored = []
    for task in tasks:
        minutes = _minutes_to_deadline(task, now)
        score = compute_task_score(minutes, task.priority, task.energy_required)
        scored.append((task, score))
    return sorted(
        scored,
        key=lambda x: (
            -x[1],
            x[0].deadline or datetime.max.replace(tzinfo=timezone.utc),
            _ENERGY_LEVEL_ORDER.index(x[0].energy_required),
        ),
    )


def _resolve_order(
    in_progress: Task,
    scored_pending: list[tuple[Task, float]],
    now: datetime,
    urgent_task: Task | None,
) -> list[Task]:
    if not scored_pending:
        return [in_progress]

    in_progress_score = compute_task_score(
        _minutes_to_deadline(in_progress, now),
        in_progress.priority,
        in_progress.energy_required,
    )

    top_task, top_score = scored_pending[0]
    should_interrupt = (
        urgent_task is not None
        and top_task.id == urgent_task.id
        and top_score >= in_progress_score + INTERRUPTION_THRESHOLD
    )

    pending_tasks = [t for t, _ in scored_pending]

    if should_interrupt:
        return [top_task, in_progress, *pending_tasks[1:]]

    return [in_progress, *pending_tasks]


def _assign_time_slots(tasks: list[Task], now: datetime) -> list[DayPlanEntry]:
    entries = []
    cursor = now

    for position, task in enumerate(tasks):
        start = cursor
        end = cursor + timedelta(minutes=task.estimated_minutes)
        entries.append(
            DayPlanEntry(
                task_id=task.id,
                position=position,
                scheduled_start=start,
                scheduled_end=end,
            )
        )
        cursor = end

    return entries


def _minutes_to_deadline(task: Task, now: datetime) -> float:
    if task.deadline is None:
        return float(MINUTES_IN_DAY)
    return max(0.0, (task.deadline - now).total_seconds() / 60)