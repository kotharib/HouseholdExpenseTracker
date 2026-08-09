from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Servant(SQLModel, table=True):
    """Household servant / helper salary tracking."""

    __tablename__ = "servants"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=128)
    role: str = Field(default="home cleaning", max_length=64)
    monthly_salary: float = Field(gt=0)
    payment_status: str = Field(default="pending", max_length=16)
    attendance_count: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
