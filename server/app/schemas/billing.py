"""Pydantic schemas for daily delivery tracking and monthly billing."""
from datetime import date as date_type
from typing import Optional

from pydantic import BaseModel


class MilkDay(BaseModel):
    id: Optional[int] = None
    date: str
    supplier: str
    quantity: float
    rate: float
    total: float
    delivered: bool
    payment_status: str


class MilkDailyResponse(BaseModel):
    year: int
    month: str
    month_label: str
    days: list[MilkDay]
    delivered_days: int
    missed_days: int


class NewspaperDay(BaseModel):
    id: Optional[int] = None
    date: str
    delivered: bool


class NewspaperGroup(BaseModel):
    name: str
    monthly_cost: float
    days_delivered: int
    days_total: int
    total: float
    days: list[NewspaperDay]


class NewspaperDailyResponse(BaseModel):
    year: int
    month: str
    month_label: str
    newspapers: list[NewspaperGroup]
    total_delivered: int
    missed_days: int


class MilkBillDetail(BaseModel):
    date: str
    supplier: str
    quantity: float
    rate: float
    total: float
    delivered: bool
    payment_status: str


class NewspaperBillDetail(BaseModel):
    name: str
    monthly_cost: float
    days_delivered: int
    total: float


class ServantBillDetail(BaseModel):
    name: str
    role: str
    monthly_salary: float


class ExpenseBillDetail(BaseModel):
    id: int
    category: str
    amount: float
    date: str
    notes: Optional[str] = None
    payment_mode: Optional[str] = None


class MonthlyBillResponse(BaseModel):
    month: str
    month_label: str
    milk_bill: float
    newspaper_bill: float
    servant_salary_total: float
    expenses_total: float
    grand_total: float
    milk_details: list[MilkBillDetail]
    newspaper_details: list[NewspaperBillDetail]
    servant_details: list[ServantBillDetail]
    expense_details: list[ExpenseBillDetail]


class DeliverySummary(BaseModel):
    milk_total_days: int
    milk_delivered_days: int
    milk_missed_days: int
    newspaper_delivered_days: int
    newspaper_missed_days: int
    total_missed_deliveries: int
