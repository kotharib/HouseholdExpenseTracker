from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.investment import Investment
from app.models.user import User
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.investment import (
    AdvisorRequest,
    AdvisorResponse,
    InvestmentCreate,
    InvestmentRead,
    InvestmentUpdate,
)
from app.services import investment_advisor
from app.utils.helpers import validate_month

router = APIRouter(prefix="/investments", tags=["investments"])

DISCLAIMER = (
    "This is educational information, not SEBI-registered financial advice. "
    "Rates are indicative and may change. Please consult a qualified advisor before investing."
)


def _get_or_404(session: Session, investment_id: int) -> Investment:
    investment = session.get(Investment, investment_id)
    if investment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")
    return investment


@router.get("", response_model=list[InvestmentRead])
def list_investments(
    month: str | None = None,
    category: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if month:
        validate_month(month)
    stmt = select(Investment)
    if month:
        stmt = stmt.where(Investment.month == month)
    if category:
        stmt = stmt.where(Investment.category == category)
    return session.exec(stmt.order_by(Investment.date.desc())).all()


@router.post("", response_model=InvestmentRead, status_code=status.HTTP_201_CREATED)
def create_investment(
    payload: InvestmentCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    investment = Investment(**payload.model_dump())
    session.add(investment)
    session.commit()
    session.refresh(investment)
    return investment


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
def bulk_delete_investments(
    payload: BulkDeleteRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    if payload.all:
        rows = session.exec(select(Investment)).all()
    else:
        if not payload.ids:
            raise HTTPException(status_code=400, detail="Provide ids or set all=true")
        rows = session.exec(select(Investment).where(Investment.id.in_(payload.ids))).all()
    for row in rows:
        session.delete(row)
    session.commit()
    return BulkDeleteResponse(deleted=len(rows))


@router.get("/options", response_model=list[dict])
def investment_options(_: User = Depends(get_current_user)):
    return investment_advisor.investment_catalog()


@router.get("/profiles", response_model=list[dict])
def risk_profiles(_: User = Depends(get_current_user)):
    return investment_advisor.risk_profiles()


@router.post("/advisor", response_model=AdvisorResponse)
def get_advisor(
    payload: AdvisorRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    allocation = investment_advisor.build_allocation(payload.amount, payload.profile)
    schemes = investment_advisor.suggested_schemes(allocation, limit=6)
    return AdvisorResponse(
        allocation=allocation,
        schemes=schemes,
        profiles=investment_advisor.risk_profiles(),
        disclaimer=DISCLAIMER,
    )


@router.get("/summary")
def investment_summary(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    rows = session.exec(select(Investment)).all()
    total = round(sum(r.amount for r in rows), 2)
    by_category: dict[str, float] = {}
    for r in rows:
        by_category[r.category] = by_category.get(r.category, 0.0) + r.amount
    return {
        "count": len(rows),
        "total": total,
        "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: x[1], reverse=True)},
    }


@router.put("/{investment_id}", response_model=InvestmentRead)
def update_investment(
    investment_id: int,
    payload: InvestmentUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    investment = _get_or_404(session, investment_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(investment, key, value)
    session.add(investment)
    session.commit()
    session.refresh(investment)
    return investment


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    investment = _get_or_404(session, investment_id)
    session.delete(investment)
    session.commit()
    return None
