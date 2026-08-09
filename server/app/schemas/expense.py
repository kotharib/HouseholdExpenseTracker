from datetime import date as date_type
from typing import Optional

from pydantic import Field, field_validator
from sqlmodel import SQLModel


class ExpenseBase(SQLModel):
    category: str = Field(min_length=1, max_length=64)
    amount: float = Field(gt=0)
    date: date_type
    notes: Optional[str] = Field(default=None, max_length=512)
    payment_mode: Optional[str] = Field(default="cash", max_length=32)
    tags: Optional[str] = Field(default=None, max_length=256)

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str) -> str:
        return v.strip()

    @field_validator("payment_mode")
    @classmethod
    def normalize_mode(cls, v: Optional[str]) -> str:
        return (v or "cash").strip().lower()


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(SQLModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=64)
    amount: Optional[float] = Field(default=None, gt=0)
    date: Optional[date_type] = None
    notes: Optional[str] = Field(default=None, max_length=512)
    payment_mode: Optional[str] = Field(default=None, max_length=32)
    tags: Optional[str] = Field(default=None, max_length=256)


class ExpenseRead(ExpenseBase):
    id: int
    month: str
