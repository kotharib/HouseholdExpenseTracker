from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.servant import Servant
from app.models.user import User
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.servant import ServantCreate, ServantRead, ServantUpdate

router = APIRouter(prefix="/servants", tags=["servants"])


def _get_or_404(session: Session, servant_id: int) -> Servant:
    servant = session.get(Servant, servant_id)
    if servant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servant not found")
    return servant


@router.get("", response_model=list[ServantRead])
def list_servants(
    role: str | None = None,
    payment_status: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    stmt = select(Servant)
    if role:
        stmt = stmt.where(Servant.role == role)
    if payment_status:
        stmt = stmt.where(Servant.payment_status == payment_status)
    return session.exec(stmt.order_by(Servant.id)).all()


@router.post("", response_model=ServantRead, status_code=status.HTTP_201_CREATED)
def create_servant(
    payload: ServantCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    servant = Servant(**payload.model_dump())
    session.add(servant)
    session.commit()
    session.refresh(servant)
    return servant


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_servants(
    payload: BulkDeleteRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if payload.all:
        rows = session.exec(select(Servant)).all()
    else:
        if not payload.ids:
            raise HTTPException(status_code=400, detail="Provide ids or set all=true")
        rows = session.exec(select(Servant).where(Servant.id.in_(payload.ids))).all()
    for row in rows:
        session.delete(row)
    session.commit()
    return BulkDeleteResponse(deleted=len(rows))


@router.put("/{servant_id}", response_model=ServantRead)
def update_servant(
    servant_id: int,
    payload: ServantUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    servant = _get_or_404(session, servant_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(servant, key, value)
    session.add(servant)
    session.commit()
    session.refresh(servant)
    return servant


@router.delete("/{servant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_servant(
    servant_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    servant = _get_or_404(session, servant_id)
    session.delete(servant)
    session.commit()
    return None
