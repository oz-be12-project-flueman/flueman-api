from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI 라우터: 인증/인가(Auth) 관련 엔드포인트 모음
# ──────────────────────────────────────────────────────────────────────────────
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.features.auth.schemas import (
    LoginIn,
    MeOut,
    RefreshIn,
    TokenOut,
)
from app.features.auth.service import AuthService, get_current_user
from app.features.auth.tokens import decode_jwt
from app.features.users.models import User as UserModel

router = APIRouter(prefix="/auth", tags=["auth"])

CurUser = Annotated[UserModel, Depends(get_current_user)]


# [POST] /auth/signin — 아이디/비밀번호 로그인 → 액세스·리프레시 발급 및 세션 기록(IP/UA 포함)
@router.post("/signin", response_model=TokenOut)
async def login(payload: LoginIn, request: Request) -> TokenOut:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    access, refresh, ttl = await AuthService.login_password(payload, ip, ua)
    return TokenOut(access_token=access, refresh_token=refresh, token_type="Bearer", expires_in=ttl)


# [POST] /auth/refresh — 리프레시 토큰 검증 후 액세스 토큰 재발급
@router.post("/refresh", response_model=TokenOut)
async def refresh(payload: RefreshIn) -> TokenOut:
    svc = AuthService()
    access, new_refresh, ttl = await svc.refresh(refresh_token=payload.refresh_token)
    return TokenOut(
        access_token=access, refresh_token=new_refresh, token_type="Bearer", expires_in=ttl
    )


# [POST] /auth/logout — Authorization 헤더의 액세스 토큰으로 현재 세션 무효화
@router.post("/logout")
async def logout(
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    svc = AuthService()
    await svc.logout(access_token=token)
    return {"status": "ok"}


# [POST] /auth/me — Authorization 헤더의 액세스 토큰으로 현재 세션 무효화
@router.get("/me", response_model=MeOut)
async def me(
    authorization: str | None = Header(default=None),
) -> MeOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]

    payload = decode_jwt(token)
    user_uuid_val = payload.get("sub")

    # 🔒 타입/값 검증: 빈 문자열 또는 비문자열 차단
    if not isinstance(user_uuid_val, str) or not user_uuid_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token subject",
        )

    svc = AuthService()
    return await svc.me(user_uuid=user_uuid_val)
