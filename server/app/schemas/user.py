from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="user", max_length=16)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"admin", "user"}:
            raise ValueError("role must be 'admin' or 'user'")
        return v


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    id: int
    username: str
    role: str


TokenResponse.model_rebuild()
