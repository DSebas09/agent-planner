from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config import DATABASE_URL
from models import Base

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()