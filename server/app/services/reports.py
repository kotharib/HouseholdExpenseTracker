"""Monthly and yearly expense reporting.

Reuses existing billing logic (`delivery.monthly_bill`) so report totals
always match the monthly bill page. Graph payloads are cached in-memory.
"""
from __future__ import annotations

import time
from datetime import date

from sqlmodel import Session, select

from app.models.expense import Expense
from app.services import delivery as delivery_service
from app.services import insights as insight_service
from app.utils.helpers import format_money, last_month, validate_month

ALL_CATEGORIES = [
    "groceries",
    "utilities",
    "transport",
    "entertainment",
    "health",
    "medical",
    "education",
    "household",
    "dining",
    "shopping",
    "travel",
    "insurance",
    "internet",
    "subscriptions",
    "ott",
    "other",
]

MONTH_ABBREV = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_YEAR_CACHE: dict[tuple[str, int], tuple[float, dict]] = {}
_CACHE_TTL_SECONDS = 60.0


def _cache_get(kind: str, year: int) -> dict | None:
    hit = _YEAR_CACHE.get((kind, year))
    if not hit:
        return None
    stored_at, data = hit
    if time.monotonic() - stored_at >= _CACHE_TTL_SECONDS:
        return None
    return data


def _cache_set(kind: str, year: int, data: dict) -> dict:
    _YEAR_CACHE[(kind, year)] = (time.monotonic(), data)
    return data


def _known_categories(session: Session) -> list[str]:
    found = {row["category"] for row in insight_service.category_totals(session)}
    ordered = list(ALL_CATEGORIES)
    seen = set(ordered)
    for name in sorted(found):
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered


def _fill_categories(all_cats: list[str], totals: list[dict]) -> list[dict]:
    by_cat = {row["category"]: float(row["total"] or 0.0) for row in totals}
    return [{"category": name, "total": round(by_cat.get(name, 0.0), 2)} for name in all_cats]


def _month_str(year: int, month: int) -> str:
    return validate_month(f"{year}-{month:02d}")


def monthly_expense_report(session: Session, year: int, month: int) -> dict:
    month_key = _month_str(year, month)
    bill = delivery_service.monthly_bill(session, month_key)
    delivery = delivery_service.delivery_summary(session, month_key)
    categories = _fill_categories(
        _known_categories(session),
        insight_service.category_totals(session, month_key),
    )
    prev_bill = delivery_service.monthly_bill(session, last_month(month_key))
    delta = round(bill["grand_total"] - prev_bill["grand_total"], 2)
    saved = delta < 0
    if saved:
        message = f"Saved {format_money(abs(delta))} vs {prev_bill['month_label']}"
    elif delta > 0:
        message = f"Spent {format_money(delta)} more than {prev_bill['month_label']}"
    else:
        message = f"Household cost is level with {prev_bill['month_label']}"

    return {
        "year": year,
        "month": month_key,
        "month_label": bill["month_label"],
        "total_expenses": bill["expenses_total"],
        "category_totals": categories,
        "milk_bill": bill["milk_bill"],
        "newspaper_bill": bill["newspaper_bill"],
        "servant_salary_total": bill["servant_salary_total"],
        "grand_total": bill["grand_total"],
        "delivery_summary": delivery,
        "savings": {
            "previous_month_grand_total": prev_bill["grand_total"],
            "delta": delta,
            "saved": saved,
            "message": message,
        },
    }


def _year_months(session: Session, year: int) -> list[dict]:
    rows: list[dict] = []
    for month_num in range(1, 13):
        month_key = _month_str(year, month_num)
        bill = delivery_service.monthly_bill(session, month_key)
        delivery = delivery_service.delivery_summary(session, month_key)
        rows.append(
            {
                "month": month_key,
                "month_label": bill["month_label"],
                "month_abbrev": MONTH_ABBREV[month_num - 1],
                "expenses_total": bill["expenses_total"],
                "milk_bill": bill["milk_bill"],
                "newspaper_bill": bill["newspaper_bill"],
                "servant_salary_total": bill["servant_salary_total"],
                "grand_total": bill["grand_total"],
                "milk_delivered_days": delivery["milk_delivered_days"],
                "newspaper_delivered_days": delivery["newspaper_delivered_days"],
                "total_missed_deliveries": delivery["total_missed_deliveries"],
            }
        )
    return rows


def _yearly_category_totals(session: Session, year: int) -> list[dict]:
    start, end = date(year, 1, 1), date(year, 12, 31)
    rows = session.exec(select(Expense).where(Expense.date >= start, Expense.date <= end)).all()
    totals: dict[str, float] = {}
    for expense in rows:
        totals[expense.category] = totals.get(expense.category, 0.0) + expense.amount
    filled = _fill_categories(
        _known_categories(session),
        [{"category": name, "total": amount} for name, amount in totals.items()],
    )
    return filled


def yearly_expense_report(session: Session, year: int) -> dict:
    cached = _cache_get("yearly", year)
    if cached is not None:
        return cached

    months = _year_months(session, year)
    category_totals = _yearly_category_totals(session, year)
    data = {
        "year": year,
        "total_expenses": round(sum(row["expenses_total"] for row in months), 2),
        "category_totals": category_totals,
        "milk_bill": round(sum(row["milk_bill"] for row in months), 2),
        "newspaper_bill": round(sum(row["newspaper_bill"] for row in months), 2),
        "servant_salary_total": round(sum(row["servant_salary_total"] for row in months), 2),
        "grand_total": round(sum(row["grand_total"] for row in months), 2),
        "months": months,
    }
    return _cache_set("yearly", year, data)


def yearly_bill_summary(session: Session, year: int) -> dict:
    yearly = yearly_expense_report(session, year)
    return {
        "year": year,
        "milk_cost": yearly["milk_bill"],
        "newspaper_cost": yearly["newspaper_bill"],
        "servant_salary": yearly["servant_salary_total"],
        "expenses_total": yearly["total_expenses"],
        "household_cost": yearly["grand_total"],
        "milk_bill": yearly["milk_bill"],
        "newspaper_bill": yearly["newspaper_bill"],
        "servant_salary_total": yearly["servant_salary_total"],
        "grand_total": yearly["grand_total"],
    }


def yearly_graph_data(session: Session, year: int) -> dict:
    cached = _cache_get("graphs", year)
    if cached is not None:
        return cached

    yearly = yearly_expense_report(session, year)
    months = yearly["months"]
    data = {
        "year": year,
        "months": [row["month_abbrev"] for row in months],
        "monthly_expenses": [row["expenses_total"] for row in months],
        "milk_cost": [row["milk_bill"] for row in months],
        "newspaper_cost": [row["newspaper_bill"] for row in months],
        "servant_salary": [row["servant_salary_total"] for row in months],
        "grand_total": [row["grand_total"] for row in months],
        "category_totals": yearly["category_totals"],
        "milk_delivered_days": [row["milk_delivered_days"] for row in months],
        "newspaper_delivered_days": [row["newspaper_delivered_days"] for row in months],
    }
    return _cache_set("graphs", year, data)
