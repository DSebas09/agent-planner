from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from agent import Agent
from dependencies import DBSession, TaskDep
from database import init_db
from models import AgentLog, DayPlanEntry, Task, TaskStatus
from schemas import (
    AgentLogResponse,
    CompleteTaskRequest,
    DelayRequest,
    PlanEntryResponse,
    TaskCreate,
    TaskResponse,
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Agent Planner", lifespan=lifespan)

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])
plan_router  = APIRouter(prefix="/plan",  tags=["plan"])
logs_router  = APIRouter(prefix="/logs",  tags=["logs"])


@tasks_router.post("", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate, session: DBSession) -> Task:
    task = Task(**payload.model_dump())
    session.add(task)
    session.flush()
    Agent(session).on_task_added(task)
    session.commit()
    session.refresh(task)
    return task

@tasks_router.get("", response_model=list[TaskResponse])
def list_tasks(session: DBSession) -> list[Task]:
    return list(
        session.execute(
            select(Task).where(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        ).scalars()
    )

@plan_router.get("", response_model=list[PlanEntryResponse])
def get_plan(session: DBSession) -> list[DayPlanEntry]:
    return _fetch_current_plan(session)


@tasks_router.post("/{task_id}/start", response_model=list[PlanEntryResponse])
def start_task(task_id: int, task: TaskDep, session: DBSession) -> list[DayPlanEntry]:
    Agent(session).on_task_started(task)
    return _fetch_current_plan(session)


@tasks_router.post("/{task_id}/complete", response_model=list[PlanEntryResponse])
def complete_task(task_id: int, task: TaskDep, payload: CompleteTaskRequest, session: DBSession) -> list[DayPlanEntry]:
    Agent(session).on_task_completed(task, payload.actual_minutes)
    return _fetch_current_plan(session)


@tasks_router.post("/{task_id}/delay", response_model=list[PlanEntryResponse])
def report_delay(task_id: int, task: TaskDep, payload: DelayRequest, session: DBSession) -> list[DayPlanEntry]:
    Agent(session).on_delay_reported(task, payload.extra_minutes)
    return _fetch_current_plan(session)


@logs_router.get("", response_model=list[AgentLogResponse])
def get_logs(session: DBSession) -> list[AgentLog]:
    return list(
        session.execute(
            select(AgentLog).order_by(AgentLog.timestamp.desc())
        ).scalars()
    )


def _fetch_current_plan(session: Session) -> list[DayPlanEntry]:
    result = session.execute(
        select(DayPlanEntry)
        .options(joinedload(DayPlanEntry.task))
        .order_by(DayPlanEntry.position)
    )
    return list(result.scalars())

app.include_router(tasks_router)
app.include_router(plan_router)
app.include_router(logs_router)
