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
