from datetime import date

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    DeliverySummary,
    MonthlyExpensesResponse,
    MonthlyTotal,
    PendingPayment,
    PendingPaymentsResponse,
)
from app.services import delivery as delivery_service
from app.services import insights
from app.utils.helpers import validate_month

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    current_month = date.today().strftime("%Y-%m")
    from app.utils.helpers import last_month

    prev = last_month(current_month)

    current_total = insights.monthly_expense_total(session, current_month)
    previous_total = insights.monthly_expense_total(session, prev)

    pend = insights.pending_totals(session)
    pending_payments = [
        PendingPayment(**item)
        for item in sorted(insights.all_pending(session), key=lambda x: x["amount"], reverse=True)
    ]

    return DashboardSummary(
        current_month=current_month,
        current_month_total=round(current_total, 2),
        previous_month_total=round(previous_total, 2),
        total_expenses=round(insights.total_expenses(session), 2),
        expense_count=insights.expense_count(session),
        servant_pending=pend["servant"],
        milk_pending=pend["milk"],
        newspaper_pending=pend["newspaper"],
        total_pending=round(pend["servant"] + pend["milk"] + pend["newspaper"], 2),
        category_totals=insights.category_totals(session, current_month),
        monthly_trend=[MonthlyTotal(**t) for t in insights.monthly_trend(session)],
        pending_payments=pending_payments,
        delivery_summary=DeliverySummary(**delivery_service.delivery_summary(session, current_month)),
    )


@router.get("/monthly-expenses", response_model=MonthlyExpensesResponse)
def monthly_expenses(
    month: str,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    month = validate_month(month)
    from app.models.expense import Expense
    from sqlmodel import select
    from app.utils.helpers import month_range

    start, end = month_range(month)
    rows = session.exec(
        select(Expense).where(Expense.date >= start, Expense.date <= end).order_by(Expense.date.desc())
    ).all()
    return MonthlyExpensesResponse(
        month=month,
        total=round(sum(e.amount for e in rows), 2),
        items=[
            {
                "id": e.id,
                "category": e.category,
                "amount": e.amount,
                "date": e.date.isoformat(),
                "notes": e.notes,
                "payment_mode": e.payment_mode,
                "tags": e.tags,
            }
            for e in rows
        ],
    )


@router.get("/pending-payments", response_model=PendingPaymentsResponse)
def pending_payments(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    items = insights.all_pending(session)
    return PendingPaymentsResponse(
        items=[PendingPayment(**i) for i in items],
        total=round(sum(i["amount"] for i in items), 2),
    )
