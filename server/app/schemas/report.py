from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: float


class AutoReportResponse(BaseModel):
    month: str
    title: str
    sections: list[str]
    ai_summary: str
    pending: list[dict]
    totals: dict
    expense_count: int = 0
    previous_month_total: float = 0.0
    delta: float = 0.0
    category_totals: list[CategoryTotal] = []
    generated_at: str
    milk_bill: float = 0.0
    newspaper_bill: float = 0.0
    servant_salary_total: float = 0.0
    grand_total: float = 0.0
    missed_deliveries: int = 0


class DeliverySummaryLite(BaseModel):
    milk_total_days: int
    milk_delivered_days: int
    milk_missed_days: int
    newspaper_delivered_days: int
    newspaper_missed_days: int
    total_missed_deliveries: int


class SavingsIndicator(BaseModel):
    previous_month_grand_total: float
    delta: float
    saved: bool
    message: str


class MonthlyExpenseReport(BaseModel):
    year: int
    month: str
    month_label: str
    total_expenses: float
    category_totals: list[CategoryTotal]
    milk_bill: float
    newspaper_bill: float
    servant_salary_total: float
    grand_total: float
    delivery_summary: DeliverySummaryLite
    savings: SavingsIndicator


class YearMonthBreakdown(BaseModel):
    month: str
    month_label: str
    month_abbrev: str
    expenses_total: float
    milk_bill: float
    newspaper_bill: float
    servant_salary_total: float
    grand_total: float
    milk_delivered_days: int
    newspaper_delivered_days: int
    total_missed_deliveries: int


class YearlyExpenseReport(BaseModel):
    year: int
    total_expenses: float
    category_totals: list[CategoryTotal]
    milk_bill: float
    newspaper_bill: float
    servant_salary_total: float
    grand_total: float
    months: list[YearMonthBreakdown]


class YearlyGraphData(BaseModel):
    year: int
    months: list[str]
    monthly_expenses: list[float]
    milk_cost: list[float]
    newspaper_cost: list[float]
    servant_salary: list[float]
    grand_total: list[float]
    category_totals: list[CategoryTotal] = []
    milk_delivered_days: list[int] = []
    newspaper_delivered_days: list[int] = []
