from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    phone_number: str
    role: str
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str
    phone_number: str
    role: str = "user"
    is_active: bool = True


class UserUpdate(BaseModel):
    phone_number: str | None = None
    role: str | None = None
    is_active: bool | None = None
