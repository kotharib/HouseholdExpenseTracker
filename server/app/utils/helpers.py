"""Shared date/currency helpers."""
import calendar
import datetime
import re
from datetime import date

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def validate_month(value: str) -> str:
    """Validate and normalize a YYYY-MM string; raise ValueError otherwise."""
    value = (value or "").strip()
    if not MONTH_RE.match(value):
        raise ValueError("month must be in YYYY-MM format")
    return value


def month_range(month: str) -> tuple[date, date]:
    """Return (first_day, last_day) of the given YYYY-MM month."""
    year, month_num = int(month[:4]), int(month[5:7])
    return date(year, month_num, 1), date(year, month_num, calendar.monthrange(year, month_num)[1])


def last_month(month: str) -> str:
    """Return the month immediately preceding the given YYYY-MM month."""
    year, month_num = int(month[:4]), int(month[5:7])
    if month_num == 1:
        return f"{year - 1}-12"
    return f"{year}-{month_num - 1:02d}"


def format_money(value: float) -> str:
    """Format a number as INR with Indian digit grouping, e.g. Rs 1,23,456.78."""
    negative = value < 0
    value = abs(round(float(value), 2))
    whole, frac = f"{value:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts: list[str] = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if negative else "") + f"₹{whole}.{frac}"


def month_name(month: str) -> str:
    """Convert 'YYYY-MM' into a human readable 'Month YYYY' label."""
    year, month_num = int(month[:4]), int(month[5:7])
    return datetime.date(year, month_num, 1).strftime("%B %Y")
