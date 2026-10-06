import os
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool, NullPool
from app.config import settings
from app.core.logging import logger

Base = declarative_base()


def get_db_url() -> str:
    """Returns dynamic database connection URL checking environment overrides."""
    return os.getenv("TEST_DATABASE_URL") or settings.TEST_DATABASE_URL or settings.DATABASE_URL


def get_engine_args(url: str):
    """Determines engine arguments based on database URL scheme."""
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    if url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["poolclass"] = QueuePool
        engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 3600

    return engine_kwargs


# Default application engine and session factory
db_url = get_db_url()
engine_kwargs = get_engine_args(db_url)
engine = create_engine(db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db_tables():
    """Ensure models are imported and tables exist if using SQLite."""
    import app.db.models  # noqa: F401
    if get_db_url().startswith("sqlite"):
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            logger.warning(f"Could not auto-create SQLite tables: {exc}")


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a managed database session."""
    init_db_tables()
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connected(db_session: Optional[Session] = None) -> bool:
    """Executes a lightweight query (SELECT 1) to test database connectivity."""
    init_db_tables()
    close_after = False
    if db_session is None:
        try:
            db_session = SessionLocal()
            close_after = True
        except Exception:
            return False

    try:
        db_session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return False
    finally:
        if close_after and db_session is not None:
            db_session.close()
