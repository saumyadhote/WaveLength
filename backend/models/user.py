from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


# ── DB document shape ─────────────────────────────────────────────────────────

class UserInDB(BaseModel):
    """Represents the user document stored in MongoDB."""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    email: EmailStr
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ── Request / response shapes ─────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class UserPublic(BaseModel):
    """Safe user shape returned in responses — no password."""
    id: str
    email: EmailStr
    username: str
    created_at: datetime
