"""FastAPI dependencies for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth.security import decode_access_token
from app.database import get_session
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


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


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
