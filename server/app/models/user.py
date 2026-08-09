from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Application user accounts."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    password_hash: str = Field(max_length=256)
    role: str = Field(default="user", max_length=16)  # admin | user
