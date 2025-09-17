# app/features/auth/service.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import HTTPException, Request, status
import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.features.auth.repository import AuthRepository  # Tortoise 기반 레포
from app.features.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    is_refresh,
)
from app.features.users.models import User  # Tortoise 모델

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_uuid_from_sub(sub: str) -> uuid.UUID:
    # 32자리 HEX면 uuid.UUID(hex=...)로, 아니면 일반 문자열로 파싱
    if isinstance(sub, str) and len(sub) == 32 and all(c in "0123456789abcdefABCDEF" for c in sub):
        return uuid.UUID(hex=sub)
    return uuid.UUID(str(sub))  # 하이픈 포함(36자) 등 일반 형태


class AuthService:
    def __init__(self) -> None:
        self.repo = AuthRepository()

    # ---- 아이디/비밀번호 로그인 ----
    async def login_password(
        self,
        *,
        username: str,
        password: str,
        ip: str | None,
        ua: str | None,
    ) -> tuple[str, str, int]:
        user = await self.repo.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid credentials",
            )

        # 패스워드 검증
        if not pwd.verify(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid credentials",
            )

        # 토큰 생성 (sub = UUID 문자열)
        u: uuid.UUID = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))
        sub = str(u)

        access, access_jti, access_ttl = create_access_token(username=sub)
        refresh, refresh_jti, _ = create_refresh_token(username=sub)

        # 세션 기록(access jti 기준) 및 만료
        access_exp = _utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRES_MIN)
        await self.repo.create_session(
            user_uuid=sub,
            jti=access_jti,
            expires_at=access_exp,
            ip=ip,
            ua=ua,
        )
        return access, refresh, access_ttl

    # ---- 리프레시 토큰으로 액세스 재발급 ----
    async def refresh(self, *, refresh_token: str) -> tuple[str, int]:
        payload = decode_jwt(refresh_token)
        if not is_refresh(payload):
            raise HTTPException(status_code=400, detail="not a refresh token")
        user_uuid = payload["sub"]
        access, _, access_ttl = create_access_token(username=user_uuid)
        return access, access_ttl

    # ---- 로그아웃(현재 세션 철회) ----
    async def logout(self, *, access_token: str) -> None:
        payload = decode_jwt(access_token)
        jti = payload.get("jti")
        if jti:
            await self.repo.revoke_session_by_jti(jti)

    # ---- API 키 해시로 사용자 확인(백오피스/게이트웨이) ----
    async def get_user_by_apikey_hash(self, *, key_hash: str) -> dict:
        user = await self.repo.get_apikey_owner(key_hash)
        if not user:
            raise HTTPException(status_code=401, detail="invalid api key")
        u: uuid.UUID = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))
        return {
            "id": str(u),
            "email": user.email,
            "username": user.username,
            "role": str(user.role),
        }

    # ---- me 정보 ----
    async def me(self, *, user_uuid: str) -> dict:
        user = await self.repo.get_user_by_uuid(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        u: uuid.UUID = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))
        return {
            "id": str(u),
            "email": user.email,
            "username": user.username,
            "role": str(user.role),
        }


# --------- 의존성: 현재 사용자 ---------
async def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # 쿠키에 "Bearer <jwt>" 형태로 들어오는 경우 대비
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # sub → uuid.UUID 객체로 변환
    try:
        u = _to_uuid_from_sub(sub)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from None

    # 1차: PK(UUID)로 조회
    user = await User.get_or_none(id=u)
    # 2차: 보조키(hex32)로 조회(필요 시)
    if not user:
        user = await User.get_or_none(id_bin_hex=u.hex)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user
