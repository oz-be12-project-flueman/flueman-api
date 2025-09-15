from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.auth.schemas import (
    AccessOnlyOut,
    LoginIn,
    MeOut,
    RefreshIn,
    TokenOut,
)
from app.features.auth.service import AuthService
from app.features.auth.tokens import decode_jwt
from app.shared.deps import CurrentUser, get_current_user

router = APIRouter()

# 타입 별칭: Annotated를 써서 B008 회피 (기본값에 함수 호출 X)
DbSess = Annotated[AsyncSession, Depends(get_session)]
CurUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request, session: DbSess) -> TokenOut:
    svc = AuthService(session)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    access, refresh, ttl = await svc.login_password(
        email=payload.email,
        password=payload.password,
        ip=ip,
        ua=ua,
    )
    return TokenOut(access_token=access, refresh_token=refresh, token_type="Bearer", expires_in=ttl)


@router.post("/refresh", response_model=AccessOnlyOut)
async def refresh(payload: RefreshIn, session: DbSess) -> AccessOnlyOut:
    svc = AuthService(session)
    access, ttl = await svc.refresh(refresh_token=payload.refresh_token)
    return AccessOnlyOut(access_token=access, token_type="Bearer", expires_in=ttl)


@router.post("/logout")
async def logout(
    session: DbSess,  # Annotated 사용 시 기본값은 필요 없음; 명시만 유지
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    svc = AuthService(session)
    await svc.logout(access_token=token)
    return {"status": "ok"}


@router.get("/me", response_model=MeOut)
async def me(
    session: DbSess,
    authorization: str | None = Header(default=None),
) -> MeOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]

    payload = decode_jwt(token)
    user_uuid_val = payload.get("sub")

    # 🔒 타입/값 검증으로 mypy가 이후를 str로 인식
    if not isinstance(user_uuid_val, str) or not user_uuid_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token subject",
        )

    svc = AuthService(session)
    return MeOut(**(await svc.me(user_uuid=user_uuid_val)))
