from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.newspaper import NewspaperDelivery
from app.models.user import User
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.newspaper import NewspaperCreate, NewspaperRead, NewspaperUpdate
from app.utils.helpers import validate_month

router = APIRouter(prefix="/newspaper", tags=["newspaper"])


def _get_or_404(session: Session, paper_id: int) -> NewspaperDelivery:
    paper = session.get(NewspaperDelivery, paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Newspaper delivery not found")
    return paper


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
    return session.exec(stmt.order_by(NewspaperDelivery.name)).all()


@router.post("", response_model=NewspaperRead, status_code=status.HTTP_201_CREATED)
def create_newspaper(
    payload: NewspaperCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    paper = NewspaperDelivery(**payload.model_dump())
    session.add(paper)
    session.commit()
    session.refresh(paper)
    return paper


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
