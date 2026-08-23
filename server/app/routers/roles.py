"""Role metadata and admin user-management endpoints.

Exposes the role catalog under ``/auth/roles`` and admin-only user
management (list users, assign roles) under ``/auth/users``.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import require_admin, viewer_allowed
from app.auth.roles import ROLE_ADMIN, ROLE_DESCRIPTIONS, VALID_ROLES
from app.database import get_session
from app.models.user import User
from app.schemas.user import RoleInfo, RoleUpdateRequest, RolesResponse, UserAdminResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/roles", response_model=RolesResponse)
def list_roles(_: User = Depends(viewer_allowed)):
    """Return the catalog of valid roles and their permissions."""
    return RolesResponse(
        roles=[RoleInfo(key=key, description=desc) for key, desc in ROLE_DESCRIPTIONS.items()]
    )


@router.get("/users", response_model=list[UserAdminResponse])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """List all users (admin only)."""
    return session.exec(select(User).order_by(User.id)).all()


@router.put("/users/{user_id}/role", response_model=UserAdminResponse)
def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    """Assign a role to a user (admin only).

    Guards against privilege escalation and lockout:
    - an admin cannot change their own role;
    - the last remaining admin cannot be demoted.
    """
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role")
    if user.role == ROLE_ADMIN and payload.role != ROLE_ADMIN:
        admins = session.exec(select(User).where(User.role == ROLE_ADMIN)).all()
        if len(admins) <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last admin")
    user.role = payload.role
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
