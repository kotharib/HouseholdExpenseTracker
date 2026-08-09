"""Database engine, session management and table initialization."""
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Create all tables if they do not already exist.

    Alembic is used for schema versioning; this is a bootstrap helper so the
    application can start without manually running migrations first.
    """
    from app import models  # noqa: F401  (imports all table models)

    SQLModel.metadata.create_all(bind=engine)


def get_session():
    with Session(engine) as session:
        yield session
