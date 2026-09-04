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
    _ensure_delivery_subscription_schema()


def _ensure_delivery_subscription_schema() -> None:
    """Add subscription columns to an existing SQLite database if missing."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        if "milk_deliveries" in tables:
            milk_cols = {c["name"] for c in inspector.get_columns("milk_deliveries")}
            if "subscription_id" not in milk_cols:
                conn.execute(text("ALTER TABLE milk_deliveries ADD COLUMN subscription_id INTEGER"))
        if "newspaper_deliveries" in tables:
            paper_cols = {c["name"] for c in inspector.get_columns("newspaper_deliveries")}
            if "subscription_id" not in paper_cols:
                conn.execute(text("ALTER TABLE newspaper_deliveries ADD COLUMN subscription_id INTEGER"))


def get_session():
    with Session(engine) as session:
        yield session
