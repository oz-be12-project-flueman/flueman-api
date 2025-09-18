from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.features.users.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    phone_number: str
    role: UserRole = UserRole.user
    is_active: bool = True


class UserUpdate(BaseModel):
    phone_number: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True


class UsersListResponse(BaseModel):
    items: list[UserResponse]
    total: int
