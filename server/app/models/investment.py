from datetime import date as date_type
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Investment(SQLModel, table=True):
    """Investment tracking record (mutual funds, PPF, NPS, etc.)."""

    __tablename__ = "investments"

    id: Optional[int] = Field(default=None, primary_key=True)
    scheme_name: str = Field(index=True, max_length=160)
    category: str = Field(index=True, max_length=64)
    amount: float = Field(gt=0)
    date: date_type = Field(index=True)
    month: str = Field(index=True, max_length=7)
    expected_return: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
