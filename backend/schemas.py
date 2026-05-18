from datetime import datetime
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: str = Field(pattern="^(high|medium|low)$")
    energy_required: str = Field(pattern="^(high|medium|low)$")
    estimated_minutes: int = Field(gt=0)
    deadline: datetime | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    priority: str
    energy_required: str
    estimated_minutes: int
    actual_minutes: int | None
    deadline: datetime | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanEntryResponse(BaseModel):
    position: int
    scheduled_start: datetime
    scheduled_end: datetime
    task: TaskResponse

    model_config = {"from_attributes": True}


class CompleteTaskRequest(BaseModel):
    actual_minutes: int = Field(gt=0)


class DelayRequest(BaseModel):
    extra_minutes: int = Field(gt=0)


class AgentLogResponse(BaseModel):
    id: int
    timestamp: datetime
    trigger: str
    message: str

    model_config = {"from_attributes": True}