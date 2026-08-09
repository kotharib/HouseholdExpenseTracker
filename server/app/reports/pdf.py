"""Monthly financial PDF generator built on ReportLab.

Produces a self-contained PDF with:
  - Title + period header
  - Key metrics cards (totals)
  - A bar chart of daily spending rendered with ReportLab graphics
  - An expenses table
  - Pending payments table
  - AI summary text block (when provided)
"""

from __future__ import annotations

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
