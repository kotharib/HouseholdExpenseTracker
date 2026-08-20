"""Custom LangChain tools exposed to the AI agent.

All tools are strictly read-only and data-grounded. The agent must never answer
from memory or assumptions: for any question about bills, deliveries or missed
deliveries it calls the dedicated tool below, and for ad-hoc data questions it
uses run_sql_query.
"""

from __future__ import annotations

from sqlmodel import Session

from app.database import engine
from app.services import delivery as delivery_service
from app.services import insights as insight_service
from app.utils.helpers import format_money


def _run_sql_query(sql: str) -> str:
    """Execute a read-only SQL query against SQLite and return results."""
    sql_lower = sql.strip().lower()
    if sql_lower and not any(sql_lower.startswith(k) for k in ("select", "pragma", "with")):
        raise ValueError("Only SELECT queries are allowed")
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        cols = list(result.keys())
        if not rows:
            return "No rows returned."
        header = " | ".join(cols)
        lines = [header, "-" * len(header)]
        for row in rows[:100]:
            lines.append(" | ".join(str(v) for v in row))
        if len(rows) > 100:
            lines.append(f"... ({len(rows) - 100} more rows truncated)")
        return "\n".join(lines)


def _financial_insights(month: str = "") -> str:
    """Return AI-readable financial insights for a month (default: current)."""
    with Session(engine) as session:
        data = insight_service.compute_insights(session, month or None)
        lines = [
            f"Month: {data['month_label']} ({data['month']})",
            f"Current month total: {format_money(data['current_month_total'])}",
            f"Previous month total: {format_money(data['previous_month_total'])}",
            f"Delta: {format_money(data['delta'])}",
            f"Expense count: {data['expense_count']}",
            "Top categories: "
            + ", ".join(f"{c['category']} ({format_money(c['total'])})" for c in data["category_totals"][:5]),
            f"Pending total: {format_money(data['pending']['total'])} "
            f"(servants {format_money(data['pending']['servant'])}, "
            f"milk {format_money(data['pending']['milk'])}, "
            f"newspaper {format_money(data['pending']['newspaper'])})",
        ]
        if data["overspending"]:
            lines.append(f"Overspending detected: {format_money(data['over_spent_by'])} above previous month.")
        for hint in data["savings_hints"]:
            lines.append(f"Savings hint: {hint}")
        return "\n".join(lines)


def _monthly_summary(month: str = "") -> str:
    """Generate a human-readable monthly financial summary."""
    with Session(engine) as session:
        data = insight_service.compute_insights(session, month or None)
        lines = [
            f"MONTHLY SUMMARY - {data['month_label']}",
            f"Total spent: {format_money(data['current_month_total'])} across {data['expense_count']} transactions.",
            f"Compared to last month ({format_money(data['previous_month_total'])}) you are {_trend_word(data['delta'])} by {format_money(abs(data['delta']))}.",
        ]
        if data["category_totals"]:
            lines.append("Breakdown by category:")
            for c in data["category_totals"]:
                lines.append(f"  - {c['category']}: {format_money(c['total'])}")
        lines.append(
            f"Pending payments: {format_money(data['pending']['total'])} "
            f"(servants {format_money(data['pending']['servant'])}, "
            f"milk {format_money(data['pending']['milk'])}, newspaper {format_money(data['pending']['newspaper'])})."
        )
        if data["savings_hints"]:
            lines.append("Suggestions:")
            for hint in data["savings_hints"]:
                lines.append(f"  - {hint}")
        return "\n".join(lines)


def _pdf_ready_text(month: str = "") -> str:
    """Generate PDF-ready summary blocks for a month."""
    with Session(engine) as session:
        data = insight_service.compute_insights(session, month or None)
        return (
            f"AI-generated summary for {data['month_label']}:\n"
            f"Total expenses were {format_money(data['current_month_total'])}. "
            f"{'Spending increased' if data['overspending'] else 'Spending was steady or reduced'} "
            f"relative to the previous month "
            f"({'+' if data['delta'] >= 0 else ''}{format_money(data['delta'])}). "
            f"Top spending category: {data['top_category'] or 'n/a'}. "
            f"Total pending payments: {format_money(data['pending']['total'])}."
        )


def _trend_word(delta: float) -> str:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"


def _resolve_tool_month(year: str, month: str) -> str:
    """Resolve a YYYY-MM month from optional year/month tool arguments.

    LangChain Tool wraps functions so the LLM typically sends a single string
    (the JSON args or a "YYYY-MM" value), which lands in the first parameter.
    Accepts: "2026-07", '{"year":"2026","month":"07"}', "2026 07", month names
    like "July", or falls back to the current month.
    """
    import calendar as _calendar
    import json
    import re as _re
    from datetime import date

    today = date.today()
    year = (year or "").strip()
    month = (month or "").strip()
    combined = year or month

    if combined.startswith("{"):
        try:
            data = json.loads(combined)
            year = str(data.get("year", "") or "").strip()
            month = str(data.get("month", "") or "").strip()
        except (ValueError, TypeError):
            pass
    else:
        match = _re.match(r"^(\d{4})[\s,/-]+(\d{1,2})$", combined)
        if match:
            year, month = match.group(1), match.group(2)

    if len(year) == 4 and year.isdigit() and month.isdigit() and 1 <= int(month) <= 12:
        return f"{year}-{int(month):02d}"
    if len(month) == 7 and month[:4].isdigit() and month[5:7].isdigit():
        return month

    lowered = combined.lower()
    for idx, name in enumerate(_calendar.month_name[1:], start=1):
        if name.lower() in lowered:
            return f"{today.year}-{idx:02d}"
    return today.strftime("%Y-%m")


def _get_monthly_bill(year: str = "", month: str = "") -> str:
    """Return the full monthly bill breakdown for a given year/month."""
    target = _resolve_tool_month(year, month)
    with Session(engine) as session:
        data = delivery_service.monthly_bill(session, target)
        lines = [
            f"MONTHLY BILL - {data['month_label']}",
            f"Milk bill: {format_money(data['milk_bill'])}",
            f"Newspaper bill: {format_money(data['newspaper_bill'])}",
            f"Servant salary total: {format_money(data['servant_salary_total'])}",
            f"Expenses total: {format_money(data['expenses_total'])}",
            f"GRAND TOTAL: {format_money(data['grand_total'])}",
        ]
        lines.append("Milk details:")
        for d in data["milk_details"]:
            lines.append(
                f"  - {d['date']}: {d['supplier']} {d['quantity']}L x {format_money(d['rate'])} "
                f"= {format_money(d['total'])}"
            )
        lines.append("Newspaper details:")
        for d in data["newspaper_details"]:
            lines.append(
                f"  - {d['name']}: {format_money(d['monthly_cost'])} x {d['days_delivered']} days "
                f"= {format_money(d['total'])}"
            )
        lines.append("Servant details:")
        for d in data["servant_details"]:
            lines.append(f"  - {d['name']} ({d['role']}): {format_money(d['monthly_salary'])}")
        return "\n".join(lines)


def _get_delivery_summary(year: str = "", month: str = "") -> str:
    """Return a daily delivery status summary for a given year/month."""
    target = _resolve_tool_month(year, month)
    with Session(engine) as session:
        milk = delivery_service.milk_daily_summary(session, target)
        papers = delivery_service.newspaper_daily_summary(session, target)
        lines = [
            f"DELIVERY SUMMARY - {milk['month_label']}",
            f"Milk: {milk['delivered_days']} delivered / {len(milk['days'])} recorded "
            f"({milk['missed_days']} missed).",
        ]
        for d in milk["days"]:
            lines.append(
                f"  - {d['date']}: {'delivered' if d['delivered'] else 'MISSED'} "
                f"({d['supplier']} {d['quantity']}L)"
            )
        for group in papers["newspapers"]:
            lines.append(
                f"{group['name']}: {group['days_delivered']}/{group['days_total']} days delivered."
            )
        return "\n".join(lines)


def _get_missing_deliveries(year: str = "", month: str = "") -> str:
    """Return the list of days where milk or newspaper was not delivered."""
    target = _resolve_tool_month(year, month)
    with Session(engine) as session:
        missed = delivery_service.missing_deliveries(session, target)
        if not missed:
            return f"No missed deliveries for {target}."
        lines = [f"MISSED DELIVERIES - {target} ({len(missed)} total):"]
        for item in missed:
            lines.append(f"  - {item['date']} ({item['type']}): {item['detail']}")
        return "\n".join(lines)


def _suggest_mutual_funds(limit: str = "6") -> str:
    """Return mutual fund suggestions based on the current market value (live NAV)."""
    from app.services.market_data import MarketDataUnavailable, market_text_summary

    try:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 6
        return market_text_summary(limit=limit)
    except MarketDataUnavailable:
        return "I could not fetch live market data right now. Please try again later."


def build_langchain_tools() -> list:
    """Build the list of LangChain Tool objects for the SQL agent."""
    from langchain.tools import Tool

    sql_tool = Tool.from_function(
        name="run_sql_query",
        func=_run_sql_query,
        description=(
            "Execute a read-only SQL SELECT query on the SQLite database. Tables: "
            "expenses(id, category, amount, date, notes, payment_mode, tags), "
            "servants(id, name, role, monthly_salary, payment_status, attendance_count), "
            "milk_deliveries(id, supplier, quantity, rate, date, month, is_delivered, payment_status), "
            "newspaper_deliveries(id, name, monthly_cost, date, month, delivery_status, payment_status), "
            "users(id, username, password_hash, role). Use month LIKE 'YYYY-MM' filters."
        ),
    )
    insights_tool = Tool.from_function(
        name="financial_insights",
        func=_financial_insights,
        description=(
            "Compute financial insights and metrics for a month (format YYYY-MM) or current "
            "month if empty. Returns totals, category breakdown, pending payments and savings hints."
        ),
    )
    summary_tool = Tool.from_function(
        name="generate_monthly_summary",
        func=_monthly_summary,
        description="Generate a natural-language monthly financial summary for a month (YYYY-MM).",
    )
    pdf_tool = Tool.from_function(
        name="generate_pdf_ready_text",
        func=_pdf_ready_text,
        description="Generate a PDF-ready text block summarizing a month (YYYY-MM) for reports.",
    )
    delivery_bill_tool = Tool.from_function(
        name="get_monthly_bill",
        func=_get_monthly_bill,
        description=(
            "Compute the full monthly bill breakdown for a month. Pass a single month "
            "string in YYYY-MM format (e.g. '2026-07') or a JSON object with year and month "
            "fields. FORMULAS: Milk Bill = SUM(quantity x rate for delivered days only); "
            "Newspaper Bill = monthly_cost x days_delivered; Grand Total = milk + newspaper + "
            "servant salaries + expenses. Returns milk bill, newspaper bill, servant salary "
            "total, expenses total and grand total with details."
        ),
    )
    delivery_summary_tool = Tool.from_function(
        name="get_delivery_summary",
        func=_get_delivery_summary,
        description=(
            "Return the daily delivery status for a month. Pass a single month string in "
            "YYYY-MM format (e.g. '2026-07') or a JSON object with year and month fields. "
            "Includes delivered vs missed milk days and per-paper delivered days."
        ),
    )
    missing_deliveries_tool = Tool.from_function(
        name="get_missing_deliveries",
        func=_get_missing_deliveries,
        description=(
            "Return the list of days where milk or newspaper was NOT delivered for a month. "
            "Pass a single month string in YYYY-MM format (e.g. '2026-07') or a JSON object "
            "with year and month fields."
        ),
    )
    mf_tool = Tool.from_function(
        name="suggest_mutual_funds",
        func=_suggest_mutual_funds,
        description=(
            "Suggest good mutual funds to invest in based on the CURRENT MARKET VALUE. "
            "Fetches live NAV data from mfapi.in, computes 1M/3M/6M/1Y returns and returns "
            "the top performers with their current NAV. Optional first argument is the "
            "number of suggestions (default 6). Use this for questions about best/top "
            "mutual funds, market-based fund recommendations, or current NAV."
        ),
    )
    return [
        sql_tool,
        insights_tool,
        summary_tool,
        pdf_tool,
        delivery_bill_tool,
        delivery_summary_tool,
        missing_deliveries_tool,
        mf_tool,
    ]
