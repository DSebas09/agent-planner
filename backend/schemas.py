from pydantic import BaseModel, Field, AwareDatetime

from models import Priority, EnergyLevel, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: Priority
    energy_required: EnergyLevel
    estimated_minutes: int = Field(gt=0)
    deadline: AwareDatetime | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    priority: Priority
    energy_required: EnergyLevel
    estimated_minutes: int
    actual_minutes: int | None
    deadline: AwareDatetime | None
    status: TaskStatus
    created_at: AwareDatetime

    model_config = {"from_attributes": True}


class PlanEntryResponse(BaseModel):
    position: int
    scheduled_start: AwareDatetime
    scheduled_end: AwareDatetime
    task: TaskResponse

    model_config = {"from_attributes": True}


class CompleteTaskRequest(BaseModel):
    actual_minutes: int = Field(gt=0)


class DelayRequest(BaseModel):
    extra_minutes: int = Field(gt=0)


class AgentLogResponse(BaseModel):
    id: int
    timestamp: AwareDatetime
    trigger: str
    message: str

    model_config = {"from_attributes": True}