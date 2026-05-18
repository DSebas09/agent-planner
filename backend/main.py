from fastapi import FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from agent import Agent
from database import get_session, init_db
from models import AgentLog, DayPlanEntry, Task, TaskStatus
from schemas import (
    AgentLogResponse,
    CompleteTaskRequest,
    DelayRequest,
    PlanEntryResponse,
    TaskCreate,
    TaskResponse,
)

app = FastAPI(title="Agent Planner")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate) -> Task:
    with get_session() as session:
        task = Task(**payload.model_dump())
        session.add(task)
        session.flush()
        Agent(session).on_task_added(task)
        session.commit()
        session.refresh(task)
        return task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks() -> list[Task]:
    with get_session() as session:
        return list(
            session.execute(
                select(Task).where(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            ).scalars()
        )


@app.get("/plan", response_model=list[PlanEntryResponse])
def get_plan() -> list[DayPlanEntry]:
    with get_session() as session:
        return list(
            session.execute(
                select(DayPlanEntry)
                .options(joinedload(DayPlanEntry.task))
                .order_by(DayPlanEntry.position)
            ).scalars()
        )


@app.post("/tasks/{task_id}/start", response_model=list[PlanEntryResponse])
def start_task(task_id: int) -> list[DayPlanEntry]:
    with get_session() as session:
        task = _get_task_or_404(session, task_id)
        Agent(session).on_task_started(task)
        session.commit()
        return session.execute(
            select(DayPlanEntry)
            .options(joinedload(DayPlanEntry.task))
            .order_by(DayPlanEntry.position)
        ).scalars().all()


@app.post("/tasks/{task_id}/complete", response_model=list[PlanEntryResponse])
def complete_task(task_id: int, payload: CompleteTaskRequest) -> list[DayPlanEntry]:
    with get_session() as session:
        task = _get_task_or_404(session, task_id)
        Agent(session).on_task_completed(task, payload.actual_minutes)
        session.commit()
        return session.execute(
            select(DayPlanEntry)
            .options(joinedload(DayPlanEntry.task))
            .order_by(DayPlanEntry.position)
        ).scalars().all()


@app.post("/tasks/{task_id}/delay", response_model=list[PlanEntryResponse])
def report_delay(task_id: int, payload: DelayRequest) -> list[DayPlanEntry]:
    with get_session() as session:
        task = _get_task_or_404(session, task_id)
        Agent(session).on_delay_reported(task, payload.extra_minutes)
        session.commit()
        return session.execute(
            select(DayPlanEntry)
            .options(joinedload(DayPlanEntry.task))
            .order_by(DayPlanEntry.position)
        ).scalars().all()


@app.get("/logs", response_model=list[AgentLogResponse])
def get_logs() -> list[AgentLog]:
    with get_session() as session:
        return list(
            session.execute(
                select(AgentLog).order_by(AgentLog.timestamp.desc())
            ).scalars()
        )


def _get_task_or_404(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task