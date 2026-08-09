"""Financial analysis helpers shared by the AI agent and dashboards."""
from collections import defaultdict

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.expense import Expense
from app.models.milk import MilkDelivery
from app.models.newspaper import NewspaperDelivery
from app.models.servant import Servant
from app.utils.helpers import last_month, month_range, validate_month


def expenses_in_month(session: Session, month: str) -> list[Expense]:
    """All expenses whose date falls inside the given YYYY-MM month."""
    start, end = month_range(validate_month(month))
    return session.exec(select(Expense).where(Expense.date >= start, Expense.date <= end)).all()


def monthly_expense_total(session: Session, month: str) -> float:
    return sum(e.amount for e in expenses_in_month(session, month))


def total_expenses(session: Session) -> float:
    total = session.exec(select(func.coalesce(func.sum(Expense.amount), 0.0))).one()
    return float(total or 0.0)


def expense_count(session: Session) -> int:
    return len(session.exec(select(Expense.id)).all())


def category_totals(session: Session, month: str | None = None) -> list[dict]:
    stmt = select(Expense.category, func.sum(Expense.amount)).group_by(Expense.category)
    if month:
        start, end = month_range(month)
        stmt = stmt.where(Expense.date >= start, Expense.date <= end)
    rows = session.exec(stmt).all()
    return [{"category": cat, "total": float(t or 0.0)} for cat, t in rows]


def monthly_trend(session: Session, limit: int = 12) -> list[dict]:
    month_expr = func.strftime("%Y-%m", Expense.date)
    rows = session.exec(
        select(month_expr, func.sum(Expense.amount)).group_by(month_expr).order_by(month_expr)
    ).all()
    trend = rows[-limit:]
    return [{"month": m, "total": float(t or 0.0)} for m, t in trend]


def pending_servants(session: Session) -> list[dict]:
    rows = session.exec(select(Servant).where(Servant.payment_status == "pending")).all()
    return [
        {
            "type": "servant",
            "name": s.name,
            "amount": s.monthly_salary,
            "month": "",
        }
        for s in rows
    ]


def pending_milk(session: Session) -> list[dict]:
    rows = session.exec(select(MilkDelivery).where(MilkDelivery.payment_status == "pending")).all()
    return [
        {
            "type": "milk",
            "name": f"{m.supplier} ({m.quantity}L x {m.rate})",
            "amount": round(m.quantity * m.rate, 2),
            "month": m.month,
        }
        for m in rows
    ]


def pending_newspaper(session: Session) -> list[dict]:
    rows = session.exec(
        select(NewspaperDelivery).where(NewspaperDelivery.payment_status == "pending")
    ).all()
    return [
        {
            "type": "newspaper",
            "name": n.name,
            "amount": n.monthly_cost,
            "month": n.month,
        }
        for n in rows
    ]


def all_pending(session: Session) -> list[dict]:
    return pending_servants(session) + pending_milk(session) + pending_newspaper(session)


def pending_totals(session: Session) -> dict[str, float]:
    return {
        "servant": sum(p["amount"] for p in pending_servants(session)),
        "milk": sum(p["amount"] for p in pending_milk(session)),
        "newspaper": sum(p["amount"] for p in pending_newspaper(session)),
    }


def compute_insights(session: Session, month: str | None = None) -> dict:
    """Aggregate all metrics needed for insights/reports in one pass."""
    current = validate_month(month) if month else _current_month()
    previous = last_month(current)

    expenses = expenses_in_month(session, current) + expenses_in_month(session, previous)
    expenses.sort(key=lambda e: e.date)

    current_total = sum(e.amount for e in expenses_in_month(session, current))
    previous_total = sum(e.amount for e in expenses_in_month(session, previous))

    by_category: dict[str, float] = defaultdict(float)
    for e in expenses_in_month(session, current):
        by_category[e.category] += e.amount

    pend = pending_totals(session)

    return {
        "month": current,
        "month_label": _month_name(current),
        "current_month_total": round(current_total, 2),
        "previous_month_total": round(previous_total, 2),
        "delta": round(current_total - previous_total, 2),
        "expense_count": len([e for e in expenses if e.month == current]),
        "category_totals": sorted(
            [{"category": k, "total": round(v, 2)} for k, v in by_category.items()],
            key=lambda x: x["total"],
            reverse=True,
        ),
        "pending": {
            "servant": round(pend["servant"], 2),
            "milk": round(pend["milk"], 2),
            "newspaper": round(pend["newspaper"], 2),
            "total": round(pend["servant"] + pend["milk"] + pend["newspaper"], 2),
        },
        "top_category": max(by_category, key=by_category.get) if by_category else None,
        "overspending": current_total > previous_total > 0,
        "over_spent_by": round(current_total - previous_total, 2) if current_total > previous_total > 0 else 0.0,
        "savings_hints": _savings_hints(by_category, current_total),
    }


def _current_month() -> str:
    from datetime import date

    return date.today().strftime("%Y-%m")


def _month_name(month: str) -> str:
    from app.utils.helpers import month_name

    return month_name(month)


def _savings_hints(by_category: dict[str, float], total: float) -> list[str]:
    hints: list[str] = []
    if not by_category or total <= 0:
        return hints
    for cat, amt in sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:3]:
        pct = amt / total * 100
        if pct >= 20:
            hints.append(f"{cat} is {pct:.0f}% of spending — review if it can be reduced.")
    return hints
