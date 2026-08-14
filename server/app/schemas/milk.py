from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel

VALID_PAYMENT_STATUSES = {"pending", "paid"}


def current_month() -> str:
    return date.today().strftime("%Y-%m")


class MilkBase(SQLModel):
    supplier: str = Field(min_length=1, max_length=128)
    quantity: float = Field(gt=0)
    rate: float = Field(gt=0)
    date: date_type
    month: str = Field(default_factory=current_month, max_length=7)
    is_delivered: bool = Field(default=True)
    payment_status: str = Field(default="pending", max_length=16)

    @field_validator("supplier")
    @classmethod
    def strip_supplier(cls, v: str) -> str:
        return v.strip()

    @field_validator("month")
    @classmethod
    def normalize_month(cls, v: str) -> str:
        return v.strip()

    @field_validator("payment_status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_PAYMENT_STATUSES:
            raise ValueError("payment_status must be 'pending' or 'paid'")
        return v


class MilkCreate(MilkBase):
    pass


class MilkUpdate(SQLModel):
    supplier: Optional[str] = Field(default=None, min_length=1, max_length=128)
    quantity: Optional[float] = Field(default=None, gt=0)
    rate: Optional[float] = Field(default=None, gt=0)
    date: Optional[date_type] = None
    month: Optional[str] = Field(default=None, max_length=7)
    is_delivered: Optional[bool] = None
    payment_status: Optional[str] = Field(default=None, max_length=16)


class MilkRead(MilkBase):
    id: int
    total: float
    created_at: Optional[datetime] = None
