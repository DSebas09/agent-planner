from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import AgentLog, AgentTrigger, DayPlanEntry, Task, TaskStatus
from scheduler import build_plan
from schemas import TaskUpdate


class Agent:
    def __init__(self, session: Session) -> None:
        self._session = session

    def on_task_added(self, new_task: Task) -> list[DayPlanEntry]:
        return self._replan(
            trigger=AgentTrigger.TASK_ADDED,
            message_fn=lambda plan: self._message_task_added(new_task, plan),
            urgent_task=new_task,
        )

    def on_task_started(self, task: Task) -> list[DayPlanEntry]:
        self._reset_current_in_progress(exclude_id=task.id)
        task.status = TaskStatus.IN_PROGRESS
        # flush before _replan so _perceive() reads the updated status
        self._session.flush()
        return self._replan(
            trigger=AgentTrigger.TASK_STARTED,
            message_fn=lambda _: f"Iniciaste '{task.title}'. Ajusté el plan a partir de ahora.",
        )

    def on_task_completed(self, task: Task, actual_minutes: int) -> list[DayPlanEntry]:
        task.status = TaskStatus.COMPLETED
        task.actual_minutes = actual_minutes
        self._session.flush()
        return self._replan(
            trigger=AgentTrigger.TASK_COMPLETED,
            message_fn=lambda plan: self._message_task_completed(task, actual_minutes, self._resolve_next_task(plan)),
        )

    def on_task_updated(self, task: Task, payload: TaskUpdate) -> list[DayPlanEntry]:
        for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(task, field, value)
        if "deadline" in payload.model_fields_set and payload.deadline is None:
            task.deadline = None
        self._session.flush()
        return self._replan(
            trigger=AgentTrigger.TASK_UPDATED,
            message_fn=lambda _: f"Actualizaste '{task.title}'. Reorganicé el plan.",
        )

    def on_task_deleted(self, task: Task) -> list[DayPlanEntry]:
        title = task.title
        self._session.execute(delete(DayPlanEntry).where(DayPlanEntry.task_id == task.id))
        self._session.delete(task)
        self._session.flush()
        return self._replan(
            trigger=AgentTrigger.TASK_DELETED,
            message_fn=lambda _: f"Eliminaste '{title}'. Reorganicé el plan.",
        )

    def on_delay_reported(self, task: Task, extra_minutes: int) -> list[DayPlanEntry]:
        shifted_now = datetime.now(timezone.utc) + timedelta(minutes=extra_minutes)
        return self._replan(
            trigger=AgentTrigger.DELAY_REPORTED,
            message_fn=lambda plan: self._message_delay_reported(task, extra_minutes, self._resolve_next_task(plan)),
            now=shifted_now,
        )

    # Cognition

    def _perceive(self) -> list[Task]:
        return list(
            self._session.execute(
                select(Task).where(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            ).scalars()
        )

    # Execution

    def _replan(
        self,
        trigger: AgentTrigger,
        message_fn: Callable[[list[DayPlanEntry]], str],
        now: datetime | None = None,
        urgent_task: Task | None = None,
    ) -> list[DayPlanEntry]:
        effective_now = now or datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, effective_now, urgent_task=urgent_task)
        self._apply_plan(plan)
        self._log(trigger=trigger, message=message_fn(plan))
        self._session.flush()
        return plan

    def _apply_plan(self, plan: list[DayPlanEntry]) -> None:
        self._session.execute(delete(DayPlanEntry))
        self._session.add_all(plan)
        self._session.flush()

    def _reset_current_in_progress(self, exclude_id: int) -> None:
        current = self._session.execute(
            select(Task).where(
                Task.status == TaskStatus.IN_PROGRESS,
                Task.id != exclude_id,
            )
        ).scalar_one_or_none()

        if current is not None:
            current.status = TaskStatus.PENDING

    def _log(self, trigger: AgentTrigger, message: str) -> None:
        self._session.add(AgentLog(trigger=trigger, message=message))

    def _resolve_next_task(self, plan: list[DayPlanEntry]) -> Task | None:
        next_entry = plan[0] if plan else None
        return self._session.get(Task, next_entry.task_id) if next_entry else None  # type: ignore

    # Natural language templates

    def _message_task_added(self, task: Task, plan: list[DayPlanEntry]) -> str:
        entry = next((e for e in plan if e.task_id == task.id), None)
        position: int | None = entry.position + 1 if entry else None
        minutes = self._minutes_to_deadline_str(task)
        if position == 1:
            return (
                f"Agregaste '{task.title}' con deadline en {minutes}. "
                f"La inserté en posición 1 porque su urgencia supera la tarea actual."
            )
        return (
            f"Agregaste '{task.title}' con deadline en {minutes}. "
            f"La inserté en posición {position or '?'} según su prioridad y deadline."
        )

    def _message_task_completed(self, task: Task, actual_minutes: int, next_task: Task | None) -> str:
        delta = actual_minutes - task.estimated_minutes
        deviation = f"+{delta} min" if delta > 0 else f"{delta} min"
        base = (
            f"Completaste '{task.title}' en {actual_minutes} min "
            f"(estimado: {task.estimated_minutes} min, {deviation}). "
        )
        if next_task:
            return base + f"Reorganicé el plan — siguiente tarea: '{next_task.title}'."
        return base + "No quedan tareas pendientes por hoy."

    def _message_delay_reported(self, task: Task, extra_minutes: int, next_task: Task | None) -> str:
        base = (
            f"Reportaste {extra_minutes} min extra en '{task.title}'. "
            f"Reorganicé el plan desplazando todos los slots siguientes."
        )
        if next_task:
            return base + f" Siguiente tarea: '{next_task.title}'."
        return base

    def _minutes_to_deadline_str(self, task: Task) -> str:
        if task.deadline is None:
            return "sin deadline"
        minutes = max(0, int((task.deadline - datetime.now(timezone.utc)).total_seconds() / 60))
        if minutes < 60:
            return f"{minutes} min"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h {minutes % 60}min"
        days = hours // 24
        remaining_hours = hours % 24
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        return f"{days}d"
