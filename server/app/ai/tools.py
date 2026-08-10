"""Custom LangChain tools exposed to the AI agent."""

from __future__ import annotations

from sqlmodel import Session

from app.database import engine
from app.services import insights as insight_service
from app.services import investment_advisor
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


def _investment_advice(amount: str = "0", profile: str = "moderate") -> str:
    """Return a suggested asset-allocation for a lump sum based on risk profile."""
    try:
        amount = float(amount or 0)
    except ValueError:
        amount = 0.0
    allocation = investment_advisor.build_allocation(amount, profile)
    lines = [
        f"Suggested allocation for {format_money(allocation['total'])} "
        f"({allocation['profile']} profile):",
    ]
    for item in allocation["items"]:
        lines.append(f"- {item['label']}: {item['percent']:.0f}% ({format_money(item['amount'])})")
    lines.append("")
    lines.append("Representative schemes:")
    for opt in investment_advisor.suggested_schemes(allocation, limit=5):
        lines.append(
            f"- {opt['name']} (risk: {opt['risk']}, ~{opt['expected_return']:.1f}% expected): {opt['description']}"
        )
    lines.append("")
    lines.append("Note: educational information, not SEBI-registered financial advice.")
    return "\n".join(lines)


def build_langchain_tools() -> list:
    """Build the list of LangChain Tool objects for the SQL agent."""
    from langchain.tools import Tool

    sql_tool = Tool.from_function(
        name="sql_query_tool",
        func=_run_sql_query,
        description=(
            "Execute a read-only SQL SELECT query on the SQLite database. Tables: "
            "expenses(id, category, amount, date, notes, payment_mode, tags), "
            "servants(id, name, role, monthly_salary, payment_status, attendance_count), "
            "milk_deliveries(id, supplier, quantity, rate, date, month, payment_status), "
            "newspaper_deliveries(id, name, monthly_cost, month, payment_status), "
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
    investment_tool = Tool.from_function(
        name="investment_advisor",
        func=_investment_advice,
        description=(
            "Suggest an asset allocation and Indian investment schemes (PPF, NPS, ELSS, "
            "Sukanya Samriddhi, FDs, mutual funds) for an amount and a risk profile "
            "(conservative/moderate/aggressive). Pass amount as a string number."
        ),
    )
    return [sql_tool, insights_tool, summary_tool, pdf_tool, investment_tool]
