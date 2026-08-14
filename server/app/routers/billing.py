"""Monthly billing router: bill calculation, daily delivery data and PDF export."""

import asyncio
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session

from app.ai.agent import agent
from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.user import User
from app.reports.pdf import generate_billing_pdf
from app.schemas.billing import MonthlyBillResponse
from app.services import delivery as delivery_service
from app.services import insights as insight_service
from app.utils.helpers import validate_month

router = APIRouter(prefix="/billing", tags=["billing"])


def _month_label(month: str) -> str:
    from app.utils.helpers import month_name

    return month_name(month)


@router.get("/monthly/{year}/{month}", response_model=MonthlyBillResponse)
def monthly_bill(
    year: int,
    month: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    month_str = validate_month(f"{year}-{month:02d}")
    return MonthlyBillResponse(**delivery_service.monthly_bill(session, month_str))


@router.get("/monthly/{year}/{month}/pdf")
async def monthly_bill_pdf(
    year: int,
    month: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    month_str = validate_month(f"{year}-{month:02d}")
    bill = delivery_service.monthly_bill(session, month_str)
    milk_daily = delivery_service.milk_daily_summary(session, month_str)
    newspaper_daily = delivery_service.newspaper_daily_summary(session, month_str)
    insights = insight_service.compute_insights(session, month_str)
    ai_text = await asyncio.to_thread(agent.monthly_report, month_str)
    pdf_bytes = generate_billing_pdf(
        month_str,
        bill,
        milk_daily=milk_daily,
        newspaper_daily=newspaper_daily,
        ai_summary=ai_text,
        savings_hints=insights["savings_hints"],
    )
    headers = {
        "Content-Disposition": f'attachment; filename="monthly-bill-{month_str}.pdf"',
        "Content-Type": "application/pdf",
    }
    return Response(content=pdf_bytes, headers=headers, media_type="application/pdf")
