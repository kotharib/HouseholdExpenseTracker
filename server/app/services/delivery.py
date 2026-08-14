"""Delivery tracking and monthly billing helpers.

Shared by the FastAPI routers, the AI agent tools and the PDF generator.
Everything in this module only touches the delivery modules (milk, newspaper)
and the monthly bill aggregation (which reads expenses + servants read-only).
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date

from sqlmodel import Session, select

from app.models.expense import Expense
from app.models.milk import MilkDelivery
from app.models.newspaper import NewspaperDelivery
from app.models.servant import Servant
from app.utils.helpers import month_name, month_range, validate_month


def _current_month() -> str:
    return date.today().strftime("%Y-%m")


def _days_in_month(month: str) -> int:
    year, month_num = int(month[:4]), int(month[5:7])
    return calendar.monthrange(year, month_num)[1]


def milk_rows(session: Session, month: str) -> list[MilkDelivery]:
    """All milk delivery records for a YYYY-MM month."""
    month = validate_month(month)
    return session.exec(
        select(MilkDelivery).where(MilkDelivery.month == month).order_by(MilkDelivery.date)
    ).all()


def newspaper_rows(session: Session, month: str) -> list[NewspaperDelivery]:
    """All newspaper delivery records for a YYYY-MM month."""
    month = validate_month(month)
    return session.exec(
        select(NewspaperDelivery)
        .where(NewspaperDelivery.month == month)
        .order_by(NewspaperDelivery.date)
    ).all()


def milk_daily_summary(session: Session, month: str) -> dict:
    """Daily milk delivery data for a month."""
    month = validate_month(month)
    rows = milk_rows(session, month)
    days = [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "supplier": r.supplier,
            "quantity": r.quantity,
            "rate": r.rate,
            "total": round(r.quantity * r.rate, 2),
            "delivered": bool(r.is_delivered),
            "payment_status": r.payment_status,
        }
        for r in rows
    ]
    delivered = sum(1 for d in days if d["delivered"])
    return {
        "year": int(month[:4]),
        "month": month,
        "month_label": month_name(month),
        "days": days,
        "delivered_days": delivered,
        "missed_days": len(days) - delivered,
    }


def newspaper_daily_summary(session: Session, month: str) -> dict:
    """Daily newspaper delivery data grouped by newspaper, expanded into a
    full month calendar. Each calendar day is `delivered` when a daily record
    exists with delivery_status true.
    """
    month = validate_month(month)
    rows = newspaper_rows(session, month)
    by_name: dict[str, list[NewspaperDelivery]] = defaultdict(list)
    for r in rows:
        by_name[r.name].append(r)

    year, month_num = int(month[:4]), int(month[5:7])
    days_in_month = calendar.monthrange(year, month_num)[1]

    groups: list[dict] = []
    for name, records in sorted(by_name.items()):
        record_map = {r.date.day: r for r in records}
        days: list[dict] = []
        delivered_count = 0
        for day_num in range(1, days_in_month + 1):
            record = record_map.get(day_num)
            delivered = bool(record.delivery_status) if record else False
            days.append(
                {
                    "id": record.id if record else None,
                    "date": f"{month}-{day_num:02d}",
                    "delivered": delivered,
                }
            )
            if delivered:
                delivered_count += 1
        monthly_cost = records[0].monthly_cost
        groups.append(
            {
                "name": name,
                "monthly_cost": monthly_cost,
                "days_delivered": delivered_count,
                "days_total": days_in_month,
                "total": round(monthly_cost * delivered_count, 2),
                "days": days,
            }
        )

    total_delivered = sum(g["days_delivered"] for g in groups)
    return {
        "year": year,
        "month": month,
        "month_label": month_name(month),
        "newspapers": groups,
        "total_delivered": total_delivered,
        "missed_days": sum((g["days_total"] - g["days_delivered"]) for g in groups),
    }


def monthly_bill(session: Session, month: str) -> dict:
    """Aggregate the full monthly bill for a YYYY-MM month.

    Milk Bill      = SUM(quantity * rate for delivered days)
    Newspaper Bill = SUM(monthly_cost * days_delivered)
    Servant Salary = SUM(monthly_salary)
    Expenses       = SUM(amount)
    Grand Total    = sum of the above
    """
    month = validate_month(month)

    milk_rows_list = milk_rows(session, month)
    milk_details = [
        {
            "date": r.date.isoformat(),
            "supplier": r.supplier,
            "quantity": r.quantity,
            "rate": r.rate,
            "total": round(r.quantity * r.rate, 2),
            "delivered": bool(r.is_delivered),
            "payment_status": r.payment_status,
        }
        for r in milk_rows_list
        if r.is_delivered
    ]
    milk_bill = round(sum(d["total"] for d in milk_details), 2)

    paper_rows_list = newspaper_rows(session, month)
    by_name: dict[str, list[NewspaperDelivery]] = defaultdict(list)
    for r in paper_rows_list:
        by_name[r.name].append(r)
    newspaper_details: list[dict] = []
    newspaper_bill = 0.0
    for name, records in sorted(by_name.items()):
        days_delivered = sum(1 for r in records if r.delivery_status)
        monthly_cost = records[0].monthly_cost
        total = round(monthly_cost * days_delivered, 2)
        newspaper_details.append(
            {
                "name": name,
                "monthly_cost": monthly_cost,
                "days_delivered": days_delivered,
                "total": total,
            }
        )
        newspaper_bill += total
    newspaper_bill = round(newspaper_bill, 2)

    servant_rows = session.exec(select(Servant)).all()
    servant_details = [
        {"name": s.name, "role": s.role, "monthly_salary": s.monthly_salary}
        for s in servant_rows
    ]
    servant_salary_total = round(sum(s.monthly_salary for s in servant_rows), 2)

    start, end = month_range(month)
    expense_rows = session.exec(
        select(Expense).where(Expense.date >= start, Expense.date <= end).order_by(Expense.date)
    ).all()
    expense_details = [
        {
            "id": e.id,
            "category": e.category,
            "amount": e.amount,
            "date": e.date.isoformat(),
            "notes": e.notes,
            "payment_mode": e.payment_mode,
        }
        for e in expense_rows
    ]
    expenses_total = round(sum(e.amount for e in expense_rows), 2)

    grand_total = round(milk_bill + newspaper_bill + servant_salary_total + expenses_total, 2)

    return {
        "month": month,
        "month_label": month_name(month),
        "milk_bill": milk_bill,
        "newspaper_bill": newspaper_bill,
        "servant_salary_total": servant_salary_total,
        "expenses_total": expenses_total,
        "grand_total": grand_total,
        "milk_details": milk_details,
        "newspaper_details": newspaper_details,
        "servant_details": servant_details,
        "expense_details": expense_details,
    }


def missing_deliveries(session: Session, month: str) -> list[dict]:
    """List of days where milk and/or newspaper was not delivered."""
    month = validate_month(month)
    missed: list[dict] = []

    milk_rows_list = milk_rows(session, month)
    for r in milk_rows_list:
        if not r.is_delivered:
            missed.append(
                {
                    "type": "milk",
                    "date": r.date.isoformat(),
                    "name": r.supplier,
                    "detail": f"{r.supplier} not delivered",
                }
            )

    paper_rows_list = newspaper_rows(session, month)
    for r in paper_rows_list:
        if not r.delivery_status:
            missed.append(
                {
                    "type": "newspaper",
                    "date": r.date.isoformat(),
                    "name": r.name,
                    "detail": f"{r.name} not delivered",
                }
            )

    return sorted(missed, key=lambda x: x["date"])


def delivery_summary(session: Session, month: str | None = None) -> dict:
    """Compact delivery counts used by the dashboard widget.

    Reuses the daily summaries so the counts match the daily views and the
    monthly bill page.
    """
    month = validate_month(month) if month else _current_month()

    milk = milk_daily_summary(session, month)
    papers = newspaper_daily_summary(session, month)

    milk_missed = milk["missed_days"]
    newspaper_missed = papers["missed_days"]

    return {
        "milk_total_days": len(milk["days"]),
        "milk_delivered_days": milk["delivered_days"],
        "milk_missed_days": milk_missed,
        "newspaper_delivered_days": papers["total_delivered"],
        "newspaper_missed_days": newspaper_missed,
        "total_missed_deliveries": milk_missed + newspaper_missed,
    }
