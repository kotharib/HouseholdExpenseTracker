from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.milk import MilkDelivery
from app.models.user import User
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.milk import MilkCreate, MilkRead, MilkUpdate
from app.utils.helpers import validate_month

router = APIRouter(prefix="/milk", tags=["milk"])


def _get_or_404(session: Session, milk_id: int) -> MilkDelivery:
    delivery = session.get(MilkDelivery, milk_id)
    if delivery is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milk delivery not found")
    return delivery


@router.get("", response_model=list[MilkRead])
def list_milk(
    month: str | None = None,
    supplier: str | None = None,
    payment_status: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if month:
        validate_month(month)
    stmt = select(MilkDelivery)
    if month:
        stmt = stmt.where(MilkDelivery.month == month)
    if supplier:
        stmt = stmt.where(MilkDelivery.supplier == supplier)
    if payment_status:
        stmt = stmt.where(MilkDelivery.payment_status == payment_status)
    return session.exec(stmt.order_by(MilkDelivery.date.desc())).all()


@router.post("", response_model=MilkRead, status_code=status.HTTP_201_CREATED)
def create_milk(
    payload: MilkCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    delivery = MilkDelivery(**payload.model_dump())
    session.add(delivery)
    session.commit()
    session.refresh(delivery)
    return delivery


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_milk(
    payload: BulkDeleteRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if payload.all:
        rows = session.exec(select(MilkDelivery)).all()
    else:
        if not payload.ids:
            raise HTTPException(status_code=400, detail="Provide ids or set all=true")
        rows = session.exec(select(MilkDelivery).where(MilkDelivery.id.in_(payload.ids))).all()
    for row in rows:
        session.delete(row)
    session.commit()
    return BulkDeleteResponse(deleted=len(rows))


@router.put("/{milk_id}", response_model=MilkRead)
def update_milk(
    milk_id: int,
    payload: MilkUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    delivery = _get_or_404(session, milk_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(delivery, key, value)
    session.add(delivery)
    session.commit()
    session.refresh(delivery)
    return delivery


@router.delete("/{milk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milk(
    milk_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    delivery = _get_or_404(session, milk_id)
    session.delete(delivery)
    session.commit()
    return None
