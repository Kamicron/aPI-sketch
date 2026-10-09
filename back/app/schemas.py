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


class ComedianCreate(BaseModel):
    channel_url: str = Field(max_length=300)
    min_duration_s: int = Field(default=120, ge=0, le=86400)
    max_duration_s: int = Field(default=1800, ge=1, le=86400)


class ComedianUpdate(BaseModel):
    subscribed: bool | None = None
    min_duration_s: int | None = Field(default=None, ge=0, le=86400)
    max_duration_s: int | None = Field(default=None, ge=1, le=86400)


class ComedianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    youtube_channel_id: str
    channel_url: str
    subscribed: bool
    min_duration_s: int
    max_duration_s: int
    last_synced_at: datetime | None
    sketch_count: int = 0


class SketchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comedian_id: int
    youtube_id: str
    title: str
    duration_s: int | None
    published_at: datetime
    thumbnail_url: str | None


class SyncOut(BaseModel):
    discovered: int
    filtered: int
