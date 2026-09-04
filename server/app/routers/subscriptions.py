"""Delivery subscription endpoints and daily-row status updates."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import require_admin, user_required, viewer_allowed
from app.database import get_session
from app.models.subscription import DeliverySubscription
from app.models.user import User
from app.schemas.subscription import (
    DeliveryStatusRead,
    DeliveryStatusUpdate,
    SubscriptionCreate,
    SubscriptionDeliveriesResponse,
    SubscriptionRead,
    SubscriptionUpdate,
)
from app.services import subscription as subscription_service

router = APIRouter(tags=["subscriptions"])


def _get_owned_or_404(session: Session, subscription_id: int, user: User) -> DeliverySubscription:
    sub = session.get(DeliverySubscription, subscription_id)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if user.role != "admin" and sub.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.post("/subscriptions", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    session: Session = Depends(get_session),
    user: User = Depends(user_required),
):
    sub = subscription_service.create_from_payload(user.id, payload.model_dump())
    session.add(sub)
    session.commit()
    session.refresh(sub)
    generated = subscription_service.generate_rows(session, sub)
    session.commit()
    session.refresh(sub)
    result = subscription_service.counted_read(session, sub)
    result["generated_count"] = generated
    return result


@router.get("/subscriptions", response_model=list[SubscriptionRead])
def list_subscriptions(
    delivery_type: str | None = None,
    active: bool | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(viewer_allowed),
):
    stmt = select(DeliverySubscription)
    if user.role != "admin":
        stmt = stmt.where(DeliverySubscription.user_id == user.id)
    if delivery_type:
        stmt = stmt.where(DeliverySubscription.delivery_type == delivery_type.strip().lower())
    if active is not None:
        stmt = stmt.where(DeliverySubscription.active == active)
    rows = session.exec(stmt.order_by(DeliverySubscription.id.desc())).all()
    return [subscription_service.counted_read(session, row) for row in rows]


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionRead)
def get_subscription(
    subscription_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(viewer_allowed),
):
    sub = _get_owned_or_404(session, subscription_id, user)
    return subscription_service.counted_read(session, sub)


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionRead)
def update_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(user_required),
):
    sub = _get_owned_or_404(session, subscription_id, user)
    old = DeliverySubscription(**sub.model_dump())
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return subscription_service.counted_read(session, sub)
    if "end_date" in data and data["end_date"] and sub.start_date and data["end_date"] < sub.start_date:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    if data.get("start_date") and sub.end_date and data["start_date"] > sub.end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")
    subscription_service.apply_payload(sub, data)
    session.add(sub)
    session.commit()
    session.refresh(sub)
    months = subscription_service.affected_months_for_update(old, sub)
    generated = subscription_service.regenerate(session, sub, affected_months=months)
    session.commit()
    session.refresh(sub)
    result = subscription_service.counted_read(session, sub)
    result["generated_count"] = generated
    return result


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_admin),
):
    sub = _get_owned_or_404(session, subscription_id, user)
    sub.active = False
    sub.auto_generate = False
    sub.updated_at = datetime.utcnow()
    session.add(sub)
    subscription_service.regenerate(session, sub)
    session.commit()
    return None


@router.get(
    "/subscriptions/{subscription_id}/deliveries/{year}/{month}",
    response_model=SubscriptionDeliveriesResponse,
)
def subscription_deliveries(
    subscription_id: int,
    year: int,
    month: int,
    session: Session = Depends(get_session),
    user: User = Depends(viewer_allowed),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    sub = _get_owned_or_404(session, subscription_id, user)
    month_str = f"{year}-{month:02d}"
    if sub.active and sub.auto_generate:
        subscription_service.generate_rows(session, sub, months=[month_str])
        session.commit()
    days = subscription_service.list_subscription_deliveries(session, sub, year, month)
    return {
        "subscription_id": sub.id,
        "year": year,
        "month": f"{year}-{month:02d}",
        "delivery_type": sub.delivery_type,
        "days": days,
    }


@router.patch("/deliveries/{delivery_id}/status", response_model=DeliveryStatusRead)
def patch_delivery_status(
    delivery_id: int,
    payload: DeliveryStatusUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(user_required),
):
    try:
        return subscription_service.set_delivery_status(
            session, delivery_id, payload.delivered, payload.delivery_type
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
