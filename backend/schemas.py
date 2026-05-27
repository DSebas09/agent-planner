from pydantic import BaseModel, Field, AwareDatetime, ConfigDict

from models import Priority, EnergyLevel, TaskStatus


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    priority: Priority
    energy_required: EnergyLevel
    estimated_minutes: int = Field(gt=0)
    deadline: AwareDatetime | None = None


class TaskResponse(OrmBase):
    id: int
    title: str
    priority: Priority
    energy_required: EnergyLevel
    estimated_minutes: int
    actual_minutes: int | None
    deadline: AwareDatetime | None
    status: TaskStatus
    created_at: AwareDatetime


class PlanEntryResponse(OrmBase):
    position: int
    scheduled_start: AwareDatetime
    scheduled_end: AwareDatetime
    task: TaskResponse


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    priority: Priority | None = None
    energy_required: EnergyLevel | None = None
    estimated_minutes: int | None = Field(default=None, gt=0)
    deadline: AwareDatetime | None = None


class CompleteTaskRequest(BaseModel):
    actual_minutes: int = Field(gt=0)


class DelayRequest(BaseModel):
    extra_minutes: int = Field(gt=0)


class AgentLogResponse(OrmBase):
    id: int
    timestamp: AwareDatetime
    trigger: str
    message: str
