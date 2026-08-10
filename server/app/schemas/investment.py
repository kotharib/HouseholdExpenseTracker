from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel


def current_month() -> str:
    return date_type.today().strftime("%Y-%m")


class InvestmentBase(SQLModel):
    scheme_name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=64)
    amount: float = Field(gt=0)
    date: date_type
    month: str = Field(default_factory=current_month, max_length=7)
    expected_return: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None

    @field_validator("scheme_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str) -> str:
        return v.strip()


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(SQLModel):
    scheme_name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    category: Optional[str] = Field(default=None, min_length=1, max_length=64)
    amount: Optional[float] = Field(default=None, gt=0)
    date: Optional[date_type] = None
    month: Optional[str] = Field(default=None, max_length=7)
    expected_return: Optional[float] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None


class InvestmentRead(InvestmentBase):
    id: int
    created_at: Optional[datetime] = None


class AllocationItem(BaseModel):
    asset_class: str
    label: str
    percent: float
    amount: float


class AllocationResponse(BaseModel):
    profile: str
    description: str
    total: float
    items: list[AllocationItem]


class AdvisorRequest(BaseModel):
    amount: float = Field(gt=0)
    profile: str = Field(default="moderate", max_length=32)
    months: Optional[int] = Field(default=None, ge=1, le=600)


class AdvisorResponse(BaseModel):
    allocation: AllocationResponse
    schemes: list[dict]
    profiles: list[dict]
    disclaimer: str
