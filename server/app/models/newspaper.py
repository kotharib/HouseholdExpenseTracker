from datetime import date as date_type
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class NewspaperDelivery(SQLModel, table=True):
    """Daily newspaper delivery tracking (extended from monthly-only tracking)."""

    __tablename__ = "newspaper_deliveries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=128)
    monthly_cost: float = Field(gt=0)
    date: date_type = Field(index=True, default_factory=date_type.today)
    month: str = Field(index=True, max_length=7)
    delivery_status: bool = Field(default=True)
    payment_status: str = Field(default="pending", max_length=16)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
