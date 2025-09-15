from pydantic import BaseModel, EmailStr, Field


# ----------- 입력 스키마 -----------
class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    # 옵션: 클라이언트가 jti 명시하거나, 현재 세션 전부 무효화 등 정책에 맞게 확장
    refresh_token: str | None = None


# ----------- 출력 스키마 -----------
class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # access_token TTL(sec)


class AccessOnlyOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class MeOut(BaseModel):
    id: str
    email: EmailStr
    username: str
    role: str


# ----------- 공통 에러 페이로드 예시 -----------
class ErrorOut(BaseModel):
    error: str
    message: str
    code: str
