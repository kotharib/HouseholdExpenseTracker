from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator, model_validator
from sqlmodel import SQLModel

VALID_DELIVERY_TYPES = {"milk", "newspaper", "custom"}
VALID_FREQUENCIES = {"daily", "alternate", "custom"}
WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


class SubscriptionBase(SQLModel):
    delivery_type: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    start_date: date_type
    end_date: Optional[date_type] = None
    active: bool = True
    delivery_frequency: str = Field(default="daily", max_length=32)
    custom_pattern: Optional[list[str]] = None
    rate_per_unit: Optional[float] = Field(default=None, gt=0)
    monthly_cost: Optional[float] = Field(default=None, gt=0)
    default_quantity: Optional[float] = Field(default=None, gt=0)
    auto_generate: bool = True

    @field_validator("delivery_type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_DELIVERY_TYPES:
            raise ValueError("delivery_type must be milk, newspaper, or custom")
        return v

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("delivery_frequency")
    @classmethod
    def normalize_frequency(cls, v: str) -> str:
        v = v.strip().lower().replace(" days", "").replace("-", " ")
        if v in {"alternate days", "every other day", "alternate day"}:
            v = "alternate"
        if v not in VALID_FREQUENCIES:
            raise ValueError("delivery_frequency must be daily, alternate, or custom")
        return v

    @field_validator("custom_pattern")
    @classmethod
    def normalize_pattern(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        cleaned = [item.strip().lower() for item in v if item and item.strip()]
        for item in cleaned:
            if item not in WEEKDAYS:
                raise ValueError(f"invalid weekday in custom_pattern: {item}")
        return cleaned

    @model_validator(mode="after")
    def validate_type_fields(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.delivery_frequency == "custom" and not self.custom_pattern:
            raise ValueError("custom_pattern is required when frequency is custom")
        if self.delivery_type == "milk":
            if self.rate_per_unit is None or self.default_quantity is None:
                raise ValueError("milk subscriptions require rate_per_unit and default_quantity")
        if self.delivery_type == "newspaper" and self.monthly_cost is None:
            raise ValueError("newspaper subscriptions require monthly_cost")
        return self


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SQLModel):
    delivery_type: Optional[str] = Field(default=None, min_length=1, max_length=32)
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None
    active: Optional[bool] = None
    delivery_frequency: Optional[str] = Field(default=None, max_length=32)
    custom_pattern: Optional[list[str]] = None
    rate_per_unit: Optional[float] = Field(default=None, gt=0)
    monthly_cost: Optional[float] = Field(default=None, gt=0)
    default_quantity: Optional[float] = Field(default=None, gt=0)
    auto_generate: Optional[bool] = None

    @field_validator("delivery_type")
    @classmethod
    def normalize_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in VALID_DELIVERY_TYPES:
            raise ValueError("delivery_type must be milk, newspaper, or custom")
        return v

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else v

    @field_validator("delivery_frequency")
    @classmethod
    def normalize_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower().replace(" days", "").replace("-", " ")
        if v in {"alternate days", "every other day", "alternate day"}:
            v = "alternate"
        if v not in VALID_FREQUENCIES:
            raise ValueError("delivery_frequency must be daily, alternate, or custom")
        return v

    @field_validator("custom_pattern")
    @classmethod
    def normalize_pattern(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        cleaned = [item.strip().lower() for item in v if item and item.strip()]
        for item in cleaned:
            if item not in WEEKDAYS:
                raise ValueError(f"invalid weekday in custom_pattern: {item}")
        return cleaned


class SubscriptionRead(SQLModel):
    id: int
    user_id: int
    delivery_type: str
    name: str
    start_date: date_type
    end_date: Optional[date_type] = None
    active: bool
    delivery_frequency: str
    custom_pattern: Optional[list[str]] = None
    rate_per_unit: Optional[float] = None
    monthly_cost: Optional[float] = None
    default_quantity: Optional[float] = None
    auto_generate: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    generated_count: int = 0


class DeliveryStatusUpdate(SQLModel):
    delivered: bool
    delivery_type: Optional[str] = None


class DeliveryDayRead(SQLModel):
    id: int
    date: str
    delivered: Optional[bool] = None
    name: str
    delivery_type: str
    quantity: Optional[float] = None
    rate: Optional[float] = None
    monthly_cost: Optional[float] = None
    subscription_id: Optional[int] = None
    month: str


class SubscriptionDeliveriesResponse(SQLModel):
    subscription_id: int
    year: int
    month: str
    delivery_type: str
    days: list[DeliveryDayRead]


class DeliveryStatusRead(SQLModel):
    id: int
    delivery_type: str
    delivered: Optional[bool] = None
    date: str
    name: str
    subscription_id: Optional[int] = None
