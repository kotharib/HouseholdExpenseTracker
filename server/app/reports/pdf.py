"""Monthly financial PDF generator built on ReportLab.

Produces a self-contained PDF with:
  - Title + period header
  - Key metrics cards (totals)
  - A bar chart of daily spending rendered with ReportLab graphics
  - An expenses table
  - Pending payments table
  - AI summary text block (when provided)

Also generates the monthly billing PDF:
  - Bill breakdown cards + table
  - Milk / newspaper delivery calendars
  - Daily milk quantity chart
  - AI-generated summary paragraph + savings suggestions
"""

from __future__ import annotations

import calendar
import io
from collections import defaultdict
from datetime import date
from typing import Optional

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.utils.helpers import month_name

# Helvetica is always available; try to register a common DejaVu font for
# broader unicode support but fall back gracefully.
try:
    pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    FONT = "DejaVu"
    FONT_BOLD = "DejaVu"
except Exception:
    FONT = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

# The Indian Rupee glyph (U+20B9) is only available in fonts that ship it;
# use a safe ASCII fallback in the base-14 Helvetica.
CURRENCY_SYMBOL = "₹" if FONT != "Helvetica" else "Rs "

PRIMARY = colors.HexColor("#2563eb")
LIGHT = colors.HexColor("#eff6ff")
PENDING = colors.HexColor("#f59e0b")
PAID = colors.HexColor("#16a34a")

h1 = ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=20, leading=24, textColor=colors.HexColor("#111827"))
h2 = ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=14, leading=18, textColor=PRIMARY, spaceAfter=6, spaceBefore=14)
body = ParagraphStyle("body", fontName=FONT, fontSize=10, leading=14, textColor=colors.HexColor("#374151"))
small = ParagraphStyle("small", fontName=FONT, fontSize=9, leading=12, textColor=colors.HexColor("#6b7280"))


def _bar_chart(data: list[dict], width=460, height=170) -> Drawing:
    """Simple horizontal-turned bar chart via ReportLab graphics."""
    drawing = Drawing(width, height)
    if not data:
        drawing.add(String(10, height / 2, "No expense data for this period", fontSize=10))
        return drawing

    labels = [d["date"] for d in data]
    values = [d["total"] for d in data]
    max_val = max(values) or 1.0
    n = len(values)
    plot_w = width - 70
    plot_h = height - 40
    bar_w = plot_w / max(n, 1) * 0.6
    gap = plot_w / max(n, 1)

    drawing.add(Rect(0, 0, width, height, fillColor=LIGHT, strokeColor=None, rx=6))
    for i, (label, value) in enumerate(zip(labels, values)):
        x = 50 + i * gap + (gap - bar_w) / 2
        bar_h = max(2, (value / max_val) * plot_h)
        y = 20
        drawing.add(Rect(x, y, bar_w, bar_h, fillColor=PRIMARY, strokeColor=None, rx=2))
        drawing.add(String(x + bar_w / 2, y + bar_h + 4, f"{value:,.0f}", fontSize=7, textAnchor="middle"))
        drawing.add(String(x + bar_w / 2, 8, label[-5:], fontSize=6, textAnchor="middle"))
    drawing.add(String(10, height - 12, "Daily spending", fontSize=9, fontName=FONT_BOLD))
    return drawing


def _metric_card(width: float, title: str, value: str, color=PRIMARY) -> Drawing:
    drawing = Drawing(width, 52)
    drawing.add(Rect(0, 0, width, 52, fillColor=LIGHT, strokeColor=None, rx=8))
    drawing.add(Rect(0, 0, 5, 52, fillColor=color, strokeColor=None))
    drawing.add(String(16, 30, title, fontSize=9, fontName=FONT_BOLD, fillColor=colors.HexColor("#6b7280")))
    drawing.add(String(16, 12, value, fontSize=15, fontName=FONT_BOLD, fillColor=colors.HexColor("#111827")))
    return drawing


def generate_monthly_pdf(
    month: str,
    expenses: list[dict],
    pending: list[dict],
    ai_summary: Optional[str] = None,
    currency: Optional[str] = None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Monthly Financial Report {month}",
    )

    currency = currency or CURRENCY_SYMBOL
    total = sum(e["amount"] for e in expenses)
    daily = defaultdict(float)
    for e in expenses:
        daily[e["date"]] += e["amount"]

    story: list = []
    story.append(Paragraph(f"Household Financial Report", h1))
    story.append(Paragraph(month_name(month), ParagraphStyle("sub", fontName=FONT, fontSize=12, leading=16, textColor=colors.HexColor("#6b7280"))))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", small))
    story.append(Spacer(1, 14))

    # Metric cards
    pending_total = sum(p["amount"] for p in pending)
    paid_total = total - pending_total if pending_total else total
    metrics = Table(
        [[_metric_card(130, "Total Spending", f"{currency}{total:,.2f}"),
          _metric_card(130, "Paid", f"{currency}{paid_total:,.2f}"),
          _metric_card(130, "Pending", f"{currency}{pending_total:,.2f}", PENDING),
          _metric_card(130, "Transactions", str(len(expenses)))]],
        colWidths=[130, 130, 130, 130],
    )
    metrics.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(metrics)

    story.append(Paragraph("Spending Trend", h2))
    trend = [{"date": d, "total": v} for d, v in sorted(daily.items())]
    story.append(_bar_chart(trend))

    story.append(Paragraph("Expense Breakdown", h2))
    exp_table_data = [["#", "Date", "Category", "Notes", "Payment", "Amount"]]
    for idx, e in enumerate(expenses, start=1):
        exp_table_data.append(
            [str(idx), e["date"], e["category"], e.get("notes") or "-", e.get("payment_mode") or "-", f"{currency}{e['amount']:,.2f}"]
        )
    exp_table_data.append(["", "", "", "TOTAL", "", f"{currency}{total:,.2f}"])
    exp_table = Table(exp_table_data, colWidths=[24, 64, 90, 150, 60, 72])
    exp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9fafb")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(exp_table)

    if pending:
        story.append(Paragraph("Pending Payments", h2))
        pend_table_data = [["Type", "Name", "Month", "Amount"]]
        for p in pending:
            pend_table_data.append([p["type"], p["name"], p.get("month") or "-", f"{currency}{p['amount']:,.2f}"])
        pend_table_data.append(["", "", "TOTAL", f"{currency}{pending_total:,.2f}"])
        pend_table = Table(pend_table_data, colWidths=[90, 180, 90, 80])
        pend_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PENDING),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ]))
        story.append(pend_table)

    if ai_summary:
        story.append(Paragraph("AI Insights", h2))
        for block in ai_summary.split("\n"):
            if block.strip():
                story.append(Paragraph(block.strip(), body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Generated by Household Finance Manager AI report generator.", small))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Monthly billing PDF
# ---------------------------------------------------------------------------

CAL_HEADER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
OK_BG = colors.HexColor("#d1fae5")
MISSED_BG = colors.HexColor("#fee2e2")
NEUTRAL_BG = colors.HexColor("#f9fafb")


def _quantity_chart(data: list[dict], width=460, height=170, title="Daily milk quantity") -> Drawing:
    """Bar chart of milk quantity per day."""
    drawing = Drawing(width, height)
    if not data:
        drawing.add(String(10, height / 2, "No milk delivery data for this period", fontSize=10))
        return drawing

    labels = [d["date"] for d in data]
    values = [d["quantity"] for d in data]
    max_val = max(values) or 1.0
    n = len(values)
    plot_w = width - 70
    plot_h = height - 40
    bar_w = plot_w / max(n, 1) * 0.6
    gap = plot_w / max(n, 1)

    drawing.add(Rect(0, 0, width, height, fillColor=LIGHT, strokeColor=None, rx=6))
    for i, (label, value) in enumerate(zip(labels, values)):
        x = 50 + i * gap + (gap - bar_w) / 2
        bar_h = max(2, (value / max_val) * plot_h)
        y = 20
        drawing.add(Rect(x, y, bar_w, bar_h, fillColor=colors.HexColor("#0d9488"), strokeColor=None, rx=2))
        drawing.add(String(x + bar_w / 2, y + bar_h + 4, f"{value:g}", fontSize=7, textAnchor="middle"))
        drawing.add(String(x + bar_w / 2, 8, label[-5:], fontSize=6, textAnchor="middle"))
    drawing.add(String(10, height - 12, title, fontSize=9, fontName=FONT_BOLD))
    return drawing


def _month_calendar(delivered_map: dict[int, bool], month: str, show_qty: dict[int, float] | None = None) -> Table:
    """Build a month calendar grid where each day cell is coloured by delivery status."""
    year, month_num = int(month[:4]), int(month[5:7])
    days_in_month = calendar.monthrange(year, month_num)[1]
    first_weekday = calendar.weekday(year, month_num, 1)  # Monday = 0

    day_cell = ParagraphStyle(
        "daycell",
        fontName=FONT,
        fontSize=9,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#111827"),
    )

    rows: list[list[int | None]] = []
    row = [None] * first_weekday
    for day_num in range(1, days_in_month + 1):
        row.append(day_num)
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        row.extend([None] * (7 - len(row)))
        rows.append(row)

    header = [Paragraph(h, ParagraphStyle("calhdr", fontName=FONT_BOLD, fontSize=8, alignment=1)) for h in CAL_HEADER]
    data_rows = [header]
    status_by_cell: dict[tuple[int, int], str] = {}
    for r, week_row in enumerate(rows):
        built = []
        for c, d in enumerate(week_row):
            if d is None:
                built.append("")
                continue
            status = delivered_map.get(d)
            status_by_cell[(r, c)] = "ok" if status is True else "missed" if status is False else "neutral"
            qty = (show_qty or {}).get(d)
            if qty is not None:
                built.append(Paragraph(f"<b>{d}</b><br/><font size=6 color='#6b7280'>{qty:g} L</font>", day_cell))
            else:
                built.append(Paragraph(f"<b>{d}</b>", day_cell))
        data_rows.append(built)

    table = Table(data_rows, colWidths=[66] * 7)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]
    for (r, c), status in status_by_cell.items():
        bg = OK_BG if status == "ok" else MISSED_BG if status == "missed" else NEUTRAL_BG
        style_commands.append(("BACKGROUND", (c, r + 1), (c, r + 1), bg))
    table.setStyle(TableStyle(style_commands))
    return table


def _delivered_map_from_days(days: list[dict], month: str) -> dict[int, bool]:
    """Map day-number -> delivered for calendar rendering."""
    result: dict[int, bool] = {}
    for d in days:
        try:
            result[int(d["date"][-2:])] = bool(d["delivered"])
        except (ValueError, TypeError):
            continue
    return result


def generate_billing_pdf(
    month: str,
    bill: dict,
    milk_daily: dict | None = None,
    newspaper_daily: dict | None = None,
    ai_summary: Optional[str] = None,
    savings_hints: Optional[list[str]] = None,
    currency: Optional[str] = None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Monthly Bill {month}",
    )

    currency = currency or CURRENCY_SYMBOL
    story: list = []
    story.append(Paragraph("Monthly Household Bill", h1))
    story.append(Paragraph(month_name(month), ParagraphStyle("sub", fontName=FONT, fontSize=12, leading=16, textColor=colors.HexColor("#6b7280"))))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", small))
    story.append(Spacer(1, 14))

    # ---- Bill metric cards
    metrics = Table(
        [
            [
                _metric_card(120, "Milk Bill", f"{currency}{bill.get('milk_bill', 0):,.2f}", colors.HexColor("#0d9488")),
                _metric_card(120, "Newspaper Bill", f"{currency}{bill.get('newspaper_bill', 0):,.2f}", colors.HexColor("#7c3aed")),
                _metric_card(120, "Servant Salaries", f"{currency}{bill.get('servant_salary_total', 0):,.2f}", colors.HexColor("#0891b2")),
                _metric_card(120, "Grand Total", f"{currency}{bill.get('grand_total', 0):,.2f}", PRIMARY),
            ]
        ],
        colWidths=[120, 120, 120, 120],
    )
    metrics.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(metrics)

    # ---- Bill breakdown table
    story.append(Paragraph("Monthly Bill Breakdown", h2))
    breakdown = [
        ["Component", "Amount"],
        ["Milk bill (delivered days)", f"{currency}{bill.get('milk_bill', 0):,.2f}"],
        ["Newspaper bill", f"{currency}{bill.get('newspaper_bill', 0):,.2f}"],
        ["Servant salaries", f"{currency}{bill.get('servant_salary_total', 0):,.2f}"],
        ["Expenses", f"{currency}{bill.get('expenses_total', 0):,.2f}"],
        ["GRAND TOTAL", f"{currency}{bill.get('grand_total', 0):,.2f}"],
    ]
    breakdown_table = Table(breakdown, colWidths=[260, 140])
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9fafb")]),
    ]))
    story.append(breakdown_table)

    # ---- Expense details table
    expense_details = bill.get("expense_details") or []
    if expense_details:
        story.append(Paragraph("Expenses", h2))
        exp_rows = [["Date", "Category", "Notes", "Amount"]]
        for e in expense_details:
            exp_rows.append([e["date"], e["category"], e.get("notes") or "-", f"{currency}{e['amount']:,.2f}"])
        exp_rows.append(["", "", "TOTAL", f"{currency}{bill.get('expenses_total', 0):,.2f}"])
        exp_table = Table(exp_rows, colWidths=[64, 90, 180, 66])
        exp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9fafb")]),
        ]))
        story.append(exp_table)

    # ---- Servant details
    servant_details = bill.get("servant_details") or []
    if servant_details:
        story.append(Paragraph("Servant Salaries", h2))
        sv_rows = [["Name", "Role", "Monthly Salary"]]
        for s in servant_details:
            sv_rows.append([s["name"], s["role"], f"{currency}{s['monthly_salary']:,.2f}"])
        sv_rows.append(["", "TOTAL", f"{currency}{bill.get('servant_salary_total', 0):,.2f}"])
        sv_table = Table(sv_rows, colWidths=[160, 180, 80])
        sv_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0891b2")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ]))
        story.append(sv_table)

    # ---- Milk delivery calendar + quantity chart
    story.append(Paragraph("Milk Delivery Calendar", h2))
    milk_days = (milk_daily or {}).get("days") or []
    milk_map = _delivered_map_from_days(milk_days, month)
    qty_by_day: dict[int, float] = {}
    for d in milk_days:
        try:
            day_num = int(d["date"][-2:])
            qty_by_day[day_num] = qty_by_day.get(day_num, 0.0) + float(d.get("quantity") or 0)
        except (ValueError, TypeError):
            continue
    story.append(_month_calendar(milk_map, month, show_qty=qty_by_day))
    story.append(Spacer(1, 8))

    milk_chart_data = [{"date": d["date"], "quantity": qty_by_day.get(int(d["date"][-2:]), 0)} for d in milk_days]
    if milk_chart_data:
        story.append(Paragraph("Daily Milk Quantity", h2))
        story.append(_quantity_chart(milk_chart_data))

    # ---- Newspaper delivery calendar(s)
    newspaper_groups = (newspaper_daily or {}).get("newspapers") or []
    if newspaper_groups:
        story.append(Paragraph("Newspaper Delivery Calendar", h2))
        for group in newspaper_groups:
            story.append(
                Paragraph(
                    f"{group['name']} — {group['days_delivered']}/{group['days_total']} days delivered",
                    ParagraphStyle("papsub", fontName=FONT_BOLD, fontSize=10, leading=14, textColor=colors.HexColor("#374151"), spaceBefore=4, spaceAfter=4),
                )
            )
            paper_map = _delivered_map_from_days(group["days"], month)
            story.append(_month_calendar(paper_map, month))
            story.append(Spacer(1, 6))

    # ---- Newspaper detail table
    newspaper_details = bill.get("newspaper_details") or []
    if newspaper_details:
        story.append(Paragraph("Newspaper Bill Details", h2))
        np_rows = [["Newspaper", "Monthly Cost", "Days Delivered", "Bill"]]
        for nd in newspaper_details:
            np_rows.append([nd["name"], f"{currency}{nd['monthly_cost']:,.2f}", str(nd["days_delivered"]), f"{currency}{nd['total']:,.2f}"])
        np_table = Table(np_rows, colWidths=[160, 100, 100, 80])
        np_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ]))
        story.append(np_table)

    # ---- AI summary + savings suggestions
    if ai_summary:
        story.append(Paragraph("AI Summary", h2))
        for block in ai_summary.split("\n"):
            if block.strip():
                story.append(Paragraph(block.strip(), body))

    if savings_hints:
        story.append(Paragraph("Savings Suggestions", h2))
        for hint in savings_hints:
            story.append(Paragraph(f"• {hint}", body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Generated by Household Finance Manager AI report generator.", small))

    doc.build(story)
    return buf.getvalue()
