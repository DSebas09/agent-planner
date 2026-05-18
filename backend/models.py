from datetime import datetime, timezone, date
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.config import TASK_STATUS_MAX_LENGTH, ENERGY_LEVEL_MAX_LENGTH, PRIORITY_MAX_LENGTH, TASK_TITLE_MAX_LENGTH, \
    AGENT_LOG_TRIGGER_MAX_LENGTH, AGENT_LOG_MESSAGE_MAX_LENGTH


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EnergyLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    POSTPONED = "postponed"

class AgentTrigger(str, Enum):
    RE_PLAN = "re_plan"
    TASK_ADDED = "task_added"
    TASK_COMPLETED = "task_completed"
    MANUAL = "manual"


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(TASK_TITLE_MAX_LENGTH))
    priority: Mapped[Priority] = mapped_column(String(PRIORITY_MAX_LENGTH))
    energy_required: Mapped[EnergyLevel] = mapped_column(String(ENERGY_LEVEL_MAX_LENGTH))
    estimated_minutes: Mapped[int] = mapped_column()
    actual_minutes: Mapped[int | None] = mapped_column()
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[TaskStatus] = mapped_column(String(TASK_STATUS_MAX_LENGTH), default=TaskStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    plan_entry: Mapped["DayPlanEntry | None"] = relationship(back_populates="task")


class DayPlanEntry(Base):
    __tablename__ = "day_plan_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    position: Mapped[int] = mapped_column()
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    task: Mapped["Task"] = relationship(back_populates="plan_entry")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    trigger: Mapped[AgentTrigger] = mapped_column(String(AGENT_LOG_TRIGGER_MAX_LENGTH))
    message: Mapped[str] = mapped_column(String(AGENT_LOG_MESSAGE_MAX_LENGTH))