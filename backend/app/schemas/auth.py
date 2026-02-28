"""Pydantic v2 schemas for authentication endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ── Request schemas ───────────────────────────────────────────
class UserRegister(BaseModel):
    """POST /auth/register body."""

    name: str
    email: EmailStr
    password: str
    role: Literal["customer", "agent", "admin"] = "customer"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    """POST /auth/login body."""

    email: EmailStr
    password: str


# ── Response schemas ──────────────────────────────────────────
class UserResponse(BaseModel):
    """User profile returned from API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token response after login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
