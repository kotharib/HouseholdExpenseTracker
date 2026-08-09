from datetime import date as date_type
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Expense(SQLModel, table=True):
    """Daily expense record."""

    __tablename__ = "expenses"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(index=True, max_length=64)
    amount: float = Field(gt=0)
    date: date_type = Field(index=True)
    notes: Optional[str] = Field(default=None, max_length=512)
    payment_mode: Optional[str] = Field(default="cash", max_length=32)
    tags: Optional[str] = Field(default=None, max_length=256)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def month(self) -> str:
        return self.date.strftime("%Y-%m")
