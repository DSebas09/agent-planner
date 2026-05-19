from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from config import DATABASE_URL
from models import Base

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        # SQLite blocks cross-thread connection reuse by default. Disabling this is safe
        # because SQLAlchemy's connection pool can return a connection created in one thread
        # to another, that's expected behavior, not a concurrency hazard.
        _engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    assert _engine is not None
    return _engine


def init_db() -> None:
    Base.metadata.create_all(get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()