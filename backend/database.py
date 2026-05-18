from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base

DATABASE_URL = "sqlite:///agent_planner.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
