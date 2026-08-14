from datetime import date as date_type
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class MilkDelivery(SQLModel, table=True):
    """Daily milk delivery tracking."""

    __tablename__ = "milk_deliveries"

    id: Optional[int] = Field(default=None, primary_key=True)
    supplier: str = Field(index=True, max_length=128)
    quantity: float = Field(gt=0)
    rate: float = Field(gt=0)
    date: date_type = Field(index=True)
    month: str = Field(index=True, max_length=7)
    is_delivered: bool = Field(default=True)
    payment_status: str = Field(default="pending", max_length=16)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total(self) -> float:
        return round(self.quantity * self.rate, 2)
