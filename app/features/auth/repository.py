# app/features/auth/repository.py
from __future__ import annotations

from datetime import UTC, datetime

from app.features.auth.models import ApiKey, Session
from app.features.users.models import User
from app.features.users.repository import UsersRepository  # ✅ 의존


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuthRepository:
    def __init__(self, users_repo: UsersRepository | None = None) -> None:
        self.users = users_repo or UsersRepository()

    # Users 관련은 모두 위임
    async def get_user_by_uuid(self, user_uuid: str) -> User | None:
        """PK(문자열 UUID)로 조회"""
        return await self.users.get(user_uuid)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.users.get_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.users.get_by_email(email)

    # Session / ApiKey 로직만 보유
    async def create_session(
        self,
        *,
        user_uuid: str,
        jti: str,
        expires_at: datetime,
        ip: str | None,
        ua: str | None,
    ) -> str:
        await Session.create(
            user_id=user_uuid,
            jti=jti,
            ip_address=ip,
            user_agent=ua,
            expires_at=expires_at,
            revoked_at=None,
            is_active=True,
        )
        return jti

    async def revoke_session_by_jti(self, jti: str) -> None:
        await Session.filter(jti=jti, revoked_at=None).update(is_active=False, revoked_at=_utcnow())

    async def get_apikey_owner(self, key_hash: str) -> User | None:
        api = await (
            ApiKey.filter(key_hash=key_hash, is_revoked=False).select_related("user").first()
        )
        if not api:
            return None
        if api.expires_at and api.expires_at <= _utcnow():
            return None
        if not api.user.is_active:
            return None
        return api.user
