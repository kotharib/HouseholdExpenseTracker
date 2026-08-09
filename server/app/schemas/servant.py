from typing import Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel

VALID_PAYMENT_STATUSES = {"pending", "paid"}


class ServantBase(SQLModel):
    name: str = Field(min_length=1, max_length=128)
    role: str = Field(default="home cleaning", max_length=64)
    monthly_salary: float = Field(gt=0)
    payment_status: str = Field(default="pending", max_length=16)
    attendance_count: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("payment_status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_PAYMENT_STATUSES:
            raise ValueError("payment_status must be 'pending' or 'paid'")
        return v


class ServantCreate(ServantBase):
    pass


class ServantUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    role: Optional[str] = Field(default=None, max_length=64)
    monthly_salary: Optional[float] = Field(default=None, gt=0)
    payment_status: Optional[str] = Field(default=None, max_length=16)
    attendance_count: Optional[int] = Field(default=None, ge=0)


class ServantRead(ServantBase):
    id: int
