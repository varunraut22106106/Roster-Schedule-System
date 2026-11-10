
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.models.enums import UserRole


# ---------------- ACCOUNT CREATION ----------------

class UserAccountCreate(BaseModel):
    employee_id: UUID
    password: str = Field(min_length=8)
    role: UserRole


# ---------------- LOGIN ----------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------------- TOKEN RESPONSE ----------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------- USER ACCOUNT RESPONSE ----------------

class UserAccountResponse(BaseModel):
    user_id: UUID
    employee_id: UUID
    role: UserRole
    is_active: bool
    last_login: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
