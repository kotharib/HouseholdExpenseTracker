from datetime import date
from typing import Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel

VALID_PAYMENT_STATUSES = {"pending", "paid"}


def current_month() -> str:
    return date.today().strftime("%Y-%m")


class NewspaperBase(SQLModel):
    name: str = Field(min_length=1, max_length=128)
    monthly_cost: float = Field(gt=0)
    month: str = Field(default_factory=current_month, max_length=7)
    payment_status: str = Field(default="pending", max_length=16)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
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


class NewspaperCreate(NewspaperBase):
    pass


class NewspaperUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    monthly_cost: Optional[float] = Field(default=None, gt=0)
    month: Optional[str] = Field(default=None, max_length=7)
    payment_status: Optional[str] = Field(default=None, max_length=16)


class NewspaperRead(NewspaperBase):
    id: int
