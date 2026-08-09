from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.expense import Expense
from app.models.user import User
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.utils.helpers import month_range, validate_month

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _get_or_404(session: Session, expense_id: int) -> Expense:
    expense = session.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.get("", response_model=list[ExpenseRead])
def list_expenses(
    month: str | None = None,
    category: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    stmt = select(Expense)
    if month:
        start, end = month_range(validate_month(month))
        stmt = stmt.where(Expense.date >= start, Expense.date <= end)
    if category:
        stmt = stmt.where(Expense.category == category)
    stmt = stmt.order_by(Expense.date.desc())
    return session.exec(stmt).all()


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    expense = Expense(**payload.model_dump())
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_expenses(
    payload: BulkDeleteRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if payload.all:
        rows = session.exec(select(Expense)).all()
    else:
        if not payload.ids:
            raise HTTPException(status_code=400, detail="Provide ids or set all=true")
        rows = session.exec(select(Expense).where(Expense.id.in_(payload.ids))).all()
    for row in rows:
        session.delete(row)
    session.commit()
    return BulkDeleteResponse(deleted=len(rows))


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    expense = _get_or_404(session, expense_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    expense = _get_or_404(session, expense_id)
    session.delete(expense)
    session.commit()
    return None
