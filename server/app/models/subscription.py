from datetime import date as date_type
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DeliverySubscription(SQLModel, table=True):
    """Recurring delivery subscription that auto-generates daily rows."""

    __tablename__ = "delivery_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    delivery_type: str = Field(index=True, max_length=32)
    name: str = Field(index=True, max_length=128)
    start_date: date_type
    end_date: Optional[date_type] = Field(default=None)
    active: bool = Field(default=True)
    delivery_frequency: str = Field(default="daily", max_length=32)
    custom_pattern: Optional[str] = Field(default=None, max_length=256)
    rate_per_unit: Optional[float] = Field(default=None)
    monthly_cost: Optional[float] = Field(default=None)
    default_quantity: Optional[float] = Field(default=None)
    auto_generate: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CustomDelivery(SQLModel, table=True):
    """Daily rows for custom recurring delivery types."""

    __tablename__ = "custom_deliveries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=128)
    date: date_type = Field(index=True)
    month: str = Field(index=True, max_length=7)
    delivered: Optional[bool] = Field(default=None)
    subscription_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
