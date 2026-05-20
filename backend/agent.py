from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import AgentLog, AgentTrigger, DayPlanEntry, Task, TaskStatus
from scheduler import build_plan


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
        return plan

    def on_task_started(self, task: Task) -> list[DayPlanEntry]:
        self._reset_current_in_progress(exclude_id=task.id)
        task.status = TaskStatus.IN_PROGRESS
        self._session.flush()

        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        plan = build_plan(tasks, now)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.TASK_STARTED,
            message=f"Iniciaste '{task.title}'. Ajusté el plan a partir de ahora.",
        )
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
            message=self._message_task_completed(task, actual_minutes, plan),
        )
        return plan

    def on_delay_reported(self, task: Task, extra_minutes: int) -> list[DayPlanEntry]:
        now = datetime.now(timezone.utc)
        tasks = self._perceive()
        now_shifted = now + timedelta(minutes=extra_minutes)
        plan = build_plan(tasks, now_shifted)
        self._apply_plan(plan)
        self._log(
            trigger=AgentTrigger.DELAY_REPORTED,
            message=self._message_delay_reported(task, extra_minutes, plan),
        )
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
        self._session.flush()

    # Natural language templates

    def _message_task_added(self, task: Task, plan: list[DayPlanEntry]) -> str:
        entry = next((e for e in plan if e.task_id == task.id), None)
        position = entry.position + 1 if entry else "?"
        minutes = self._minutes_to_deadline_str(task)
        if entry and entry.position == 0:
            return (
                f"Agregaste '{task.title}' con deadline en {minutes}. "
                f"La inserté en posición 1 porque su urgencia supera la tarea actual."
            )
        return (
            f"Agregaste '{task.title}' con deadline en {minutes}. "
            f"La inserté en posición {position} según su prioridad y deadline."
        )

    def _message_task_completed(
        self, task: Task, actual_minutes: int, plan: list[DayPlanEntry]
    ) -> str:
        delta = actual_minutes - task.estimated_minutes
        next_entry = plan[0] if plan else None
        next_task = (
            self._session.get(Task, next_entry.task_id) if next_entry else None
        )
        deviation = f"+{delta} min" if delta > 0 else f"{delta} min"
        base = (
            f"Completaste '{task.title}' en {actual_minutes} min "
            f"(estimado: {task.estimated_minutes} min, {deviation}). "
        )
        if next_task:
            return base + f"Reorganicé el plan — siguiente tarea: '{next_task.title}'."
        return base + "No quedan tareas pendientes por hoy."

    def _message_delay_reported(
        self, task: Task, extra_minutes: int, plan: list[DayPlanEntry]
    ) -> str:
        return (
            f"Reportaste {extra_minutes} min extra en '{task.title}'. "
            f"Reorganicé el plan desplazando todos los slots siguientes."
        )

    def _minutes_to_deadline_str(self, task: Task) -> str:
        if task.deadline is None:
            return "sin deadline"
        minutes = max(0, int((task.deadline - datetime.now(timezone.utc)).total_seconds() / 60))
        if minutes < 60:
            return f"{minutes} min"
        return f"{minutes // 60}h {minutes % 60}min"