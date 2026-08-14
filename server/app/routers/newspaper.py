import calendar
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.newspaper import NewspaperDelivery
from app.models.user import User
from app.schemas.billing import NewspaperDailyResponse
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.newspaper import NewspaperCreate, NewspaperRead, NewspaperUpdate
from app.services import delivery as delivery_service
from app.utils.helpers import validate_month

router = APIRouter(prefix="/newspaper", tags=["newspaper"])


def _get_or_404(session: Session, paper_id: int) -> NewspaperDelivery:
    paper = session.get(NewspaperDelivery, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Newspaper delivery not found")
    return paper


@router.get("/deliveries/{year}/{month}", response_model=NewspaperDailyResponse)
def daily_newspaper_deliveries(
    year: int,
    month: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    month_str = validate_month(f"{year}-{month:02d}")
    return NewspaperDailyResponse(**delivery_service.newspaper_daily_summary(session, month_str))


@router.get("", response_model=list[NewspaperRead])
def list_newspaper(
    month: str | None = None,
    payment_status: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if month:
        validate_month(month)
    stmt = select(NewspaperDelivery)
    if month:
        stmt = stmt.where(NewspaperDelivery.month == month)
    if payment_status:
        stmt = stmt.where(NewspaperDelivery.payment_status == payment_status)
    return session.exec(stmt.order_by(NewspaperDelivery.date)).all()


def _generate_month_records(payload: NewspaperCreate, session: Session) -> list[NewspaperDelivery]:
    """Expand a monthly newspaper subscription into one daily record per day.

    When a newspaper is added without an explicit date it is treated as a
    full-month subscription: a record is created for every day of the month
    with delivery_status defaulting to true so the daily calendar and billing
    work out of the box.
    """
    month = validate_month(payload.month)
    year, month_num = int(month[:4]), int(month[5:7])
    days_in_month = calendar.monthrange(year, month_num)[1]
    created: list[NewspaperDelivery] = []
    for day_num in range(1, days_in_month + 1):
        record = NewspaperDelivery(
            name=payload.name,
            monthly_cost=payload.monthly_cost,
            date=date(year, month_num, day_num),
            month=month,
            delivery_status=payload.delivery_status,
            payment_status=payload.payment_status,
        )
        session.add(record)
        created.append(record)
    return created


@router.post("", response_model=NewspaperRead, status_code=status.HTTP_201_CREATED)
def create_newspaper(
    payload: NewspaperCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    if "date" in data:
        created = [NewspaperDelivery(**data)]
        session.add(created[0])
    else:
        created = _generate_month_records(payload, session)
    session.commit()
    for record in created:
        session.refresh(record)
    return created[0]


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_newspaper(
    payload: BulkDeleteRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if payload.all:
        rows = session.exec(select(NewspaperDelivery)).all()
    else:
        if not payload.ids:
            raise HTTPException(status_code=400, detail="Provide ids or set all=true")
        rows = session.exec(select(NewspaperDelivery).where(NewspaperDelivery.id.in_(payload.ids))).all()
    for row in rows:
        session.delete(row)
    session.commit()
    return BulkDeleteResponse(deleted=len(rows))


@router.put("/{paper_id}", response_model=NewspaperRead)
def update_newspaper(
    paper_id: int,
    payload: NewspaperUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    paper = _get_or_404(session, paper_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(paper, key, value)
    session.add(paper)
    session.commit()
    session.refresh(paper)
    return paper


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_newspaper(
    paper_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    paper = _get_or_404(session, paper_id)
    session.delete(paper)
    session.commit()
    return None
