"""FastAPI dependencies for authentication and role-based authorization (RBAC)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth.roles import ROLE_ADMIN, ROLE_USER, ROLE_VIEWER, VALID_ROLES
from app.auth.security import decode_access_token
from app.database import get_session
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _forbidden() -> HTTPException:
    """Standard 403 response used across all RBAC checks."""
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_EXC
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise _CREDENTIALS_EXC
    username = payload.get("sub")
    if not username:
        raise _CREDENTIALS_EXC
    user = session.get(User, int(username)) if username.isdigit() else None
    if user is None:
        user = _find_by_username(session, username)
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def _find_by_username(session: Session, username: str) -> User | None:
    from sqlmodel import select

    return session.exec(select(User).where(User.username == username)).first()


def require_role(role: str):
    """Return a dependency that requires the exact given role.

    Rejects the request with 403 "Not authorized" when the current user's
    role does not match.
    """
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role!r}")

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise _forbidden()
        return user

    return dependency


def require_any_role(*roles: str):
    """Return a dependency that requires any of the given roles."""
    invalid = [r for r in roles if r not in VALID_ROLES]
    if invalid:
        raise ValueError(f"Invalid role(s): {invalid}")

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise _forbidden()
        return user

    return dependency


# Pre-built dependencies used across routers.
require_admin = require_role(ROLE_ADMIN)
user_required = require_any_role(ROLE_ADMIN, ROLE_USER)
viewer_allowed = require_any_role(ROLE_ADMIN, ROLE_USER, ROLE_VIEWER)
