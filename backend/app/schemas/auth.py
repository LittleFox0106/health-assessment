"""
认证相关 Pydantic Schema
"""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: str
    email: str
    session_token: str
    is_anonymous: bool


class UserProfile(BaseModel):
    user_id: str
    email: str | None
    is_anonymous: bool
    has_subscription: bool
