from pydantic import BaseModel


class AutoReportResponse(BaseModel):
    month: str
    title: str
    sections: list[str]
    ai_summary: str
    pending: list[dict]
    totals: dict
    generated_at: str
