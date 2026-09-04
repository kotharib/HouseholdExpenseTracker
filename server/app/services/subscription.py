"""Delivery subscription management and daily-row auto-generation.

This module only touches delivery subscriptions and the daily milk /
newspaper / custom delivery rows they generate. Users never create daily
rows themselves; those are produced here and later marked delivered or not.
"""

from __future__ import annotations

import calendar
import json
from datetime import date, datetime, timedelta
from typing import Iterable

from sqlmodel import Session, select

from app.models.milk import MilkDelivery
from app.models.newspaper import NewspaperDelivery
from app.models.subscription import CustomDelivery, DeliverySubscription
from app.utils.helpers import month_range, validate_month

WEEKDAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def encode_pattern(pattern: list[str] | None) -> str | None:
    if not pattern:
        return None
    return json.dumps([item.strip().lower() for item in pattern])


def decode_pattern(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(item) for item in data]
    except (ValueError, TypeError):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return None


def to_read_dict(sub: DeliverySubscription, generated_count: int = 0) -> dict:
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "delivery_type": sub.delivery_type,
        "name": sub.name,
        "start_date": sub.start_date,
        "end_date": sub.end_date,
        "active": sub.active,
        "delivery_frequency": sub.delivery_frequency,
        "custom_pattern": decode_pattern(sub.custom_pattern),
        "rate_per_unit": sub.rate_per_unit,
        "monthly_cost": sub.monthly_cost,
        "default_quantity": sub.default_quantity,
        "auto_generate": sub.auto_generate,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
        "generated_count": generated_count,
    }


def _month_start(month: str) -> date:
    year, month_num = int(month[:4]), int(month[5:7])
    return date(year, month_num, 1)


def _month_end(month: str) -> date:
    year, month_num = int(month[:4]), int(month[5:7])
    return date(year, month_num, calendar.monthrange(year, month_num)[1])


def _iter_months(start: date, end: date) -> list[str]:
    months: list[str] = []
    cursor = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cursor <= last:
        months.append(cursor.strftime("%Y-%m"))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return months


def generation_window(sub: DeliverySubscription, today: date | None = None) -> tuple[date, date] | None:
    """Return the inclusive date range that should have generated rows."""
    today = today or date.today()
    start = sub.start_date
    if sub.end_date:
        end = sub.end_date
    else:
        end = _month_end(today.strftime("%Y-%m"))
    if end < start:
        return None
    return start, end


def scheduled_dates(sub: DeliverySubscription, start: date, end: date) -> list[date]:
    """Dates that should receive a generated row for this subscription."""
    if end < start:
        return []
    frequency = (sub.delivery_frequency or "daily").lower()
    dates: list[date] = []
    if frequency == "daily":
        cursor = start
        while cursor <= end:
            dates.append(cursor)
            cursor += timedelta(days=1)
        return dates
    if frequency == "alternate":
        cursor = start
        while cursor <= end:
            dates.append(cursor)
            cursor += timedelta(days=2)
        return dates
    pattern = decode_pattern(sub.custom_pattern) or []
    weekdays = {WEEKDAY_ALIASES[item] for item in pattern if item in WEEKDAY_ALIASES}
    cursor = start
    while cursor <= end:
        if cursor.weekday() in weekdays:
            dates.append(cursor)
        cursor += timedelta(days=1)
    return dates


def _count_generated(session: Session, sub: DeliverySubscription) -> int:
    if sub.delivery_type == "milk":
        return len(session.exec(select(MilkDelivery).where(MilkDelivery.subscription_id == sub.id)).all())
    if sub.delivery_type == "newspaper":
        return len(
            session.exec(select(NewspaperDelivery).where(NewspaperDelivery.subscription_id == sub.id)).all()
        )
    return len(session.exec(select(CustomDelivery).where(CustomDelivery.subscription_id == sub.id)).all())


def existing_dates_for_subscription(session: Session, sub: DeliverySubscription) -> set[date]:
    if sub.delivery_type == "milk":
        rows = session.exec(select(MilkDelivery).where(MilkDelivery.subscription_id == sub.id)).all()
        return {r.date for r in rows}
    if sub.delivery_type == "newspaper":
        rows = session.exec(select(NewspaperDelivery).where(NewspaperDelivery.subscription_id == sub.id)).all()
        return {r.date for r in rows}
    rows = session.exec(select(CustomDelivery).where(CustomDelivery.subscription_id == sub.id)).all()
    return {r.date for r in rows}


def _create_row(session: Session, sub: DeliverySubscription, day: date) -> None:
    month = day.strftime("%Y-%m")
    if sub.delivery_type == "milk":
        session.add(
            MilkDelivery(
                supplier=sub.name,
                quantity=sub.default_quantity or 1,
                rate=sub.rate_per_unit or 1,
                date=day,
                month=month,
                is_delivered=None,
                subscription_id=sub.id,
                payment_status="pending",
            )
        )
        return
    if sub.delivery_type == "newspaper":
        session.add(
            NewspaperDelivery(
                name=sub.name,
                monthly_cost=sub.monthly_cost or 1,
                date=day,
                month=month,
                delivery_status=None,
                subscription_id=sub.id,
                payment_status="pending",
            )
        )
        return
    session.add(
        CustomDelivery(
            name=sub.name,
            date=day,
            month=month,
            delivered=None,
            subscription_id=sub.id,
        )
    )


def generate_rows(
    session: Session,
    sub: DeliverySubscription,
    months: Iterable[str] | None = None,
) -> int:
    """Create missing daily rows for the subscription. Never duplicates existing dates.

    Historical delivered/missed marks are preserved because existing rows are skipped.
    Deactivated or auto_generate=false subscriptions do not generate new rows.
    """
    if not sub.active or not sub.auto_generate:
        return 0
    if months:
        ranges = []
        for month in months:
            month = validate_month(month)
            start, end = month_range(month)
            start = max(start, sub.start_date)
            if sub.end_date:
                end = min(end, sub.end_date)
            ranges.append((start, end))
    else:
        window = generation_window(sub)
        if window is None:
            return 0
        ranges = [window]

    existing = existing_dates_for_subscription(session, sub)
    created = 0
    for start, end in ranges:
        if end < start:
            continue
        for day in scheduled_dates(sub, start, end):
            if day in existing:
                continue
            _create_row(session, sub, day)
            existing.add(day)
            created += 1
    return created


def prune_unmarked_future_rows(
    session: Session,
    sub: DeliverySubscription,
    keep_dates: set[date],
) -> None:
    """Remove unmarked generated rows that are no longer scheduled.

    Rows the user already marked (delivered true/false) are kept as history.
    """
    today = date.today()

    def should_drop(day: date, marked: bool | None) -> bool:
        if marked is not None:
            return False
        if day <= today:
            return False
        return day not in keep_dates

    if sub.delivery_type == "milk":
        rows = session.exec(select(MilkDelivery).where(MilkDelivery.subscription_id == sub.id)).all()
        for row in rows:
            if should_drop(row.date, row.is_delivered):
                session.delete(row)
        return
    if sub.delivery_type == "newspaper":
        rows = session.exec(select(NewspaperDelivery).where(NewspaperDelivery.subscription_id == sub.id)).all()
        for row in rows:
            if should_drop(row.date, row.delivery_status):
                session.delete(row)
        return
    rows = session.exec(select(CustomDelivery).where(CustomDelivery.subscription_id == sub.id)).all()
    for row in rows:
        if should_drop(row.date, row.delivered):
            session.delete(row)


def regenerate(
    session: Session,
    sub: DeliverySubscription,
    affected_months: Iterable[str] | None = None,
) -> int:
    """Regenerate rows for affected months without duplicating existing ones."""
    window = generation_window(sub)
    keep: set[date] = set()
    if sub.active and sub.auto_generate and window is not None:
        start, end = window
        if affected_months:
            for month in affected_months:
                month = validate_month(month)
                m_start, m_end = month_range(month)
                keep.update(scheduled_dates(sub, max(start, m_start), min(end, m_end)))
        else:
            keep.update(scheduled_dates(sub, start, end))
        prune_unmarked_future_rows(session, sub, keep)
        created = generate_rows(session, sub, months=affected_months)
        _sync_unmarked_row_fields(session, sub)
        return created
    prune_unmarked_future_rows(session, sub, keep)
    return 0


def _sync_unmarked_row_fields(session: Session, sub: DeliverySubscription) -> None:
    """Keep unmarked generated rows aligned with the latest subscription fields."""
    if sub.delivery_type == "milk":
        rows = session.exec(select(MilkDelivery).where(MilkDelivery.subscription_id == sub.id)).all()
        for row in rows:
            if row.is_delivered is not None:
                continue
            row.supplier = sub.name
            if sub.default_quantity:
                row.quantity = sub.default_quantity
            if sub.rate_per_unit:
                row.rate = sub.rate_per_unit
            session.add(row)
        return
    if sub.delivery_type == "newspaper":
        rows = session.exec(
            select(NewspaperDelivery).where(NewspaperDelivery.subscription_id == sub.id)
        ).all()
        for row in rows:
            if row.delivery_status is not None:
                continue
            row.name = sub.name
            if sub.monthly_cost:
                row.monthly_cost = sub.monthly_cost
            session.add(row)
        return
    rows = session.exec(select(CustomDelivery).where(CustomDelivery.subscription_id == sub.id)).all()
    for row in rows:
        if row.delivered is not None:
            continue
        row.name = sub.name
        session.add(row)


def affected_months_for_update(old: DeliverySubscription, new: DeliverySubscription) -> list[str]:
    window_old = generation_window(old)
    window_new = generation_window(new)
    starts: list[date] = []
    ends: list[date] = []
    for window in (window_old, window_new):
        if window:
            starts.append(window[0])
            ends.append(window[1])
    if not starts:
        today = date.today()
        return [today.strftime("%Y-%m")]
    return _iter_months(min(starts), max(ends))


def list_subscription_deliveries(session: Session, sub: DeliverySubscription, year: int, month: int) -> list[dict]:
    month_str = validate_month(f"{year}-{month:02d}")
    if sub.delivery_type == "milk":
        rows = session.exec(
            select(MilkDelivery)
            .where(MilkDelivery.subscription_id == sub.id, MilkDelivery.month == month_str)
            .order_by(MilkDelivery.date)
        ).all()
        return [
            {
                "id": r.id,
                "date": r.date.isoformat(),
                "delivered": r.is_delivered,
                "name": r.supplier,
                "delivery_type": "milk",
                "quantity": r.quantity,
                "rate": r.rate,
                "monthly_cost": None,
                "subscription_id": r.subscription_id,
                "month": r.month,
            }
            for r in rows
        ]
    if sub.delivery_type == "newspaper":
        rows = session.exec(
            select(NewspaperDelivery)
            .where(NewspaperDelivery.subscription_id == sub.id, NewspaperDelivery.month == month_str)
            .order_by(NewspaperDelivery.date)
        ).all()
        return [
            {
                "id": r.id,
                "date": r.date.isoformat(),
                "delivered": r.delivery_status,
                "name": r.name,
                "delivery_type": "newspaper",
                "quantity": None,
                "rate": None,
                "monthly_cost": r.monthly_cost,
                "subscription_id": r.subscription_id,
                "month": r.month,
            }
            for r in rows
        ]
    rows = session.exec(
        select(CustomDelivery)
        .where(CustomDelivery.subscription_id == sub.id, CustomDelivery.month == month_str)
        .order_by(CustomDelivery.date)
    ).all()
    return [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "delivered": r.delivered,
            "name": r.name,
            "delivery_type": "custom",
            "quantity": None,
            "rate": None,
            "monthly_cost": None,
            "subscription_id": r.subscription_id,
            "month": r.month,
        }
        for r in rows
    ]


def set_delivery_status(
    session: Session,
    delivery_id: int,
    delivered: bool,
    delivery_type: str | None = None,
) -> dict:
    """Mark a generated daily row as delivered or missed."""
    candidates: list[tuple[str, object, str]] = []
    if delivery_type in (None, "milk"):
        row = session.get(MilkDelivery, delivery_id)
        if row is not None:
            candidates.append(("milk", row, "is_delivered"))
    if delivery_type in (None, "newspaper"):
        row = session.get(NewspaperDelivery, delivery_id)
        if row is not None:
            candidates.append(("newspaper", row, "delivery_status"))
    if delivery_type in (None, "custom"):
        row = session.get(CustomDelivery, delivery_id)
        if row is not None:
            candidates.append(("custom", row, "delivered"))
    if not candidates:
        raise KeyError("delivery not found")
    dtype, row, field = candidates[0]
    setattr(row, field, delivered)
    if hasattr(row, "updated_at"):
        row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    name = getattr(row, "supplier", None) or getattr(row, "name")
    return {
        "id": row.id,
        "delivery_type": dtype,
        "delivered": delivered,
        "date": row.date.isoformat(),
        "name": name,
        "subscription_id": getattr(row, "subscription_id", None),
    }


def apply_payload(sub: DeliverySubscription, data: dict) -> DeliverySubscription:
    if "custom_pattern" in data:
        sub.custom_pattern = encode_pattern(data.pop("custom_pattern"))
    for key, value in data.items():
        setattr(sub, key, value)
    sub.updated_at = datetime.utcnow()
    return sub


def create_from_payload(user_id: int, payload: dict) -> DeliverySubscription:
    pattern = payload.pop("custom_pattern", None)
    return DeliverySubscription(
        user_id=user_id,
        custom_pattern=encode_pattern(pattern),
        **payload,
    )


def counted_read(session: Session, sub: DeliverySubscription) -> dict:
    return to_read_dict(sub, generated_count=_count_generated(session, sub))


def ensure_month_rows(session: Session, month: str, delivery_type: str | None = None) -> int:
    """Generate missing rows for active subscriptions covering a YYYY-MM month."""
    month = validate_month(month)
    stmt = select(DeliverySubscription).where(
        DeliverySubscription.active == True,  # noqa: E712
        DeliverySubscription.auto_generate == True,  # noqa: E712
    )
    if delivery_type:
        stmt = stmt.where(DeliverySubscription.delivery_type == delivery_type)
    created = 0
    for sub in session.exec(stmt).all():
        created += generate_rows(session, sub, months=[month])
    if created:
        session.commit()
    return created
