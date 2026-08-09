from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class NewspaperDelivery(SQLModel, table=True):
    """Monthly newspaper subscription tracking."""

    __tablename__ = "newspaper_deliveries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=128)
    monthly_cost: float = Field(gt=0)
    month: str = Field(index=True, max_length=7)
    payment_status: str = Field(default="pending", max_length=16)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
