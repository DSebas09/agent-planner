from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_session
from models import Task


def get_db() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


DBSession = Annotated[Session, Depends(get_db)]


def get_task_or_404(task_id: int, session: DBSession) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task  # type: ignore


TaskDep = Annotated[Task, Depends(get_task_or_404)]