from typing import Optional

from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: float


class MonthlyTotal(BaseModel):
    month: str
    total: float


class PendingPayment(BaseModel):
    type: str
    name: str
    amount: float
    month: str


class DashboardSummary(BaseModel):
    current_month: str
    current_month_total: float
    previous_month_total: float
    total_expenses: float
    expense_count: int
    servant_pending: float
    milk_pending: float
    newspaper_pending: float
    total_pending: float
    category_totals: list[CategoryTotal]
    monthly_trend: list[MonthlyTotal]
    pending_payments: list[PendingPayment]


class MonthlyExpensesResponse(BaseModel):
    month: str
    total: float
    items: list[dict]


class PendingPaymentsResponse(BaseModel):
    items: list[PendingPayment]
    total: float
