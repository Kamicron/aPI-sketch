from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    # Email ou nom d'utilisateur
    login: str
    password: str


class RegisterRequest(BaseModel):
    code: str
    email: EmailStr
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_admin: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class InvitationCreate(BaseModel):
    email: EmailStr | None = None
    ttl_days: int | None = Field(default=None, ge=1, le=365)


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    email: str | None
    status: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None


class InvitationCheck(BaseModel):
    valid: bool
    email: str | None = None
