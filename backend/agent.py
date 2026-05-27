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
        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, now, urgent_task=new_task)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.TASK_ADDED,
            message=self._message_task_added(new_task, plan),
        )
        self._session.flush()
        return plan

    def on_task_started(self, task: Task) -> list[DayPlanEntry]:
        self._reset_current_in_progress(exclude_id=task.id)
        task.status = TaskStatus.IN_PROGRESS
        # flush here stays. it's needed before _perceive() reads updated state
        self._session.flush()

        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, now)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.TASK_STARTED,
            message=f"Iniciaste '{task.title}'. Ajusté el plan a partir de ahora.",
        )
        self._session.flush()
        return plan

    def on_task_completed(self, task: Task, actual_minutes: int) -> list[DayPlanEntry]:
        task.status = TaskStatus.COMPLETED
        task.actual_minutes = actual_minutes
        self._session.flush()

        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, now)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.TASK_COMPLETED,
            message=self._message_task_completed(task, actual_minutes, self._resolve_next_task(plan)),
        )
        self._session.flush()
        return plan

    def on_task_updated(self, task: Task, payload: TaskUpdate) -> list[DayPlanEntry]:
        for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(task, field, value)
        if "deadline" in payload.model_fields_set and payload.deadline is None:
            task.deadline = None
        self._session.flush()

        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, now)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.TASK_UPDATED,
            message=f"Actualizaste '{task.title}'. Reorganicé el plan.",
        )
        self._session.flush()
        return plan

    def on_task_deleted(self, task: Task) -> list[DayPlanEntry]:
        title = task.title
        self._session.execute(delete(DayPlanEntry).where(DayPlanEntry.task_id == task.id))
        self._session.delete(task)
        self._session.flush()

        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, now)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.TASK_DELETED,
            message=f"Eliminaste '{title}'. Reorganicé el plan.",
        )
        self._session.flush()
        return plan

    def on_delay_reported(self, task: Task, extra_minutes: int) -> list[DayPlanEntry]:
        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        # No state mutation here. We shift the temporal perception forward
        # so the scheduler treats the delay as already consumed time.
        shifted_now = now + timedelta(minutes=extra_minutes)
        plan = build_plan(tasks, shifted_now)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.DELAY_REPORTED,
            message=self._message_delay_reported(task, extra_minutes, self._resolve_next_task(plan)),
        )
        self._session.flush()
        return plan

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