from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def make_engine(url: str | None = None):
    url = url or settings.database_url
    if not url.startswith("sqlite"):
        return create_engine(url)
    # SQLite is the dev/soak database. Workers run in threads, so: WAL for concurrent readers,
    # a generous busy timeout instead of "database is locked". Production is Postgres.
    eng = create_engine(url, connect_args={"check_same_thread": False, "timeout": 60})

    @event.listens_for(eng, "connect")
    def _pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=60000")
        cur.close()

    return eng


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency."""
    with session_scope() as s:
        yield s
