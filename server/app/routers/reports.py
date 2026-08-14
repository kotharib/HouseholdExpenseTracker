from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlmodel import Session, select

from app.ai.agent import agent
from app.auth.dependencies import get_current_user
from app.database import engine, get_session
from app.models.expense import Expense
from app.models.user import User
from app.reports.pdf import generate_monthly_pdf
from app.schemas.report import AutoReportResponse
from app.services import delivery as delivery_service
from app.services import insights
from app.utils.helpers import format_money, month_name, validate_month

router = APIRouter(prefix="/reports", tags=["reports"])


def _month_expenses(session: Session, month: str) -> list[dict]:
    from app.utils.helpers import month_range

    start, end = month_range(month)
    rows = session.exec(
        select(Expense).where(Expense.date >= start, Expense.date <= end)
    ).all()
    return [
        {
            "id": e.id,
            "date": e.date.isoformat(),
            "category": e.category,
            "amount": round(e.amount, 2),
            "notes": e.notes,
            "payment_mode": e.payment_mode,
            "tags": e.tags,
        }
        for e in rows
    ]


@router.get("/monthly/pdf")
async def monthly_pdf(
    month: str,
    _: User = Depends(get_current_user),
):
    month = validate_month(month)
    with Session(engine) as session:
        expenses = _month_expenses(session, month)
        pending = insights.all_pending(session)
        ai_text = await _run_agent_monthly(month)
        pdf_bytes = generate_monthly_pdf(month, expenses, pending, ai_text)
    headers = {
        "Content-Disposition": f'attachment; filename="household-report-{month}.pdf"',
        "Content-Type": "application/pdf",
    }
    return Response(content=pdf_bytes, headers=headers, media_type="application/pdf")


@router.get("/auto", response_model=AutoReportResponse)
async def auto_report(
    month: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    target = validate_month(month) if month else date.today().strftime("%Y-%m")
    data = insights.compute_insights(session, target)
    pending = insights.all_pending(session)
    bill = delivery_service.monthly_bill(session, target)
    ai_text = await _run_agent_monthly(target)

    sections = [
        f"Total expenses in {month_name(target)}: {format_money(data['current_month_total'])} "
        f"across {data['expense_count']} transactions.",
        f"Previous month total: {format_money(data['previous_month_total'])} "
        f"({'+' if data['delta'] >= 0 else ''}{format_money(data['delta'])} change).",
    ]
    if data["category_totals"]:
        sections.append(
            "Category breakdown: "
            + "; ".join(f"{c['category']} {format_money(c['total'])}" for c in data["category_totals"])
        )
    sections.append(
        f"Pending payments: {format_money(data['pending']['total'])} "
        f"(servants {format_money(data['pending']['servant'])}, milk {format_money(data['pending']['milk'])}, "
        f"newspaper {format_money(data['pending']['newspaper'])})."
    )
    sections.append(
        f"Monthly bill breakdown: milk {format_money(bill['milk_bill'])}, "
        f"newspaper {format_money(bill['newspaper_bill'])}, "
        f"servant salaries {format_money(bill['servant_salary_total'])}, "
        f"expenses {format_money(bill['expenses_total'])}, "
        f"grand total {format_money(bill['grand_total'])}."
    )
    missed = delivery_service.missing_deliveries(session, target)
    sections.append(
        f"Deliveries: {len(missed)} missed "
        f"({'none' if not missed else '; '.join(m['date'] for m in missed[:5])})."
    )
    sections.append("AI insights: " + ai_text.replace("\n", " "))

    return AutoReportResponse(
        month=target,
        title=f"Auto Report — {month_name(target)}",
        sections=sections,
        ai_summary=ai_text,
        pending=pending,
        totals={
            "total_expenses": round(data["current_month_total"], 2),
            "pending": round(data["pending"]["total"], 2),
        },
        expense_count=data["expense_count"],
        previous_month_total=round(data["previous_month_total"], 2),
        delta=round(data["delta"], 2),
        category_totals=data["category_totals"],
        generated_at=date.today().isoformat(),
        milk_bill=round(bill["milk_bill"], 2),
        newspaper_bill=round(bill["newspaper_bill"], 2),
        servant_salary_total=round(bill["servant_salary_total"], 2),
        grand_total=round(bill["grand_total"], 2),
        missed_deliveries=len(missed),
    )


async def _run_agent_monthly(month: str) -> str:
    import asyncio

    return await asyncio.to_thread(agent.monthly_report, month)
