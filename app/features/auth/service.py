import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.features.auth.repository import AuthRepository
from app.features.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    is_refresh,
)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuthRepository(session)
        self.session = session

    # ---- 이메일/비밀번호 로그인 ----
    async def login_password(
        self,
        *,
        email: str,
        password: str,
        ip: str | None,
        ua: str | None,
    ) -> tuple[str, str, int]:
        user = await self.repo.get_user_by_email(email)
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

        # 토큰 생성
        access, access_jti, access_ttl = create_access_token(username=str(uuid.UUID(bytes=user.id)))
        refresh, refresh_jti, _ = create_refresh_token(username=str(uuid.UUID(bytes=user.id)))

        # 세션 기록(access jti 기준) 및 만료
        access_exp = _utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        await self.repo.create_session(
            user_uuid=str(uuid.UUID(bytes=user.id)),
            jti=access_jti,
            expires_at=access_exp,
            ip=ip,
            ua=ua,
        )
        await self.session.commit()
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
    async def logout(self, *, access_token: str):
        payload = decode_jwt(access_token)
        jti = payload.get("jti")
        if jti:
            await self.repo.revoke_session_by_jti(jti)
            await self.session.commit()

    # ---- API 키 해시로 사용자 확인(백오피스/게이트웨이) ----
    async def get_user_by_apikey_hash(self, *, key_hash: str):
        user = await self.repo.get_apikey_owner(key_hash)
        if not user:
            raise HTTPException(status_code=401, detail="invalid api key")
        return {
            "id": str(uuid.UUID(bytes=user.id)),
            "email": user.email,
            "username": user.username,
            "role": user.role,
        }

    # ---- me 정보 ----
    async def me(self, *, user_uuid: str):
        user = await self.repo.get_user_by_uuid(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        return {
            "id": str(uuid.UUID(bytes=user.id)),
            "email": user.email,
            "username": user.username,
            "role": user.role,
        }
