# app/features/auth/repository.py
from __future__ import annotations

from datetime import UTC, datetime
import uuid

from app.features.auth.models import ApiKey, RefreshToken, Session
from app.features.users.models import User
from app.features.users.repository import UsersRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AuthRepository:
    def __init__(self, users_repo: UsersRepository | None = None) -> None:
        self.users = users_repo or UsersRepository()

    # ---------- Users 위임 ----------
    async def get_user_by_uuid(self, user_uuid: str) -> User | None:
        return await self.users.get(user_uuid)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.users.get_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.users.get_by_email(email)

    # ---------- Session / ApiKey ----------
    @staticmethod
    async def create_session(
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

    @staticmethod
    async def revoke_session_by_jti(jti: str) -> None:
        await Session.filter(jti=jti, revoked_at=None).update(is_active=False, revoked_at=_utcnow())

    @staticmethod
    async def get_apikey_owner(key_hash: str) -> User | None:
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

    # ---------- RefreshToken ----------
    @staticmethod
    async def create_refresh_token_row(
        *,
        user_uuid: str,
        jti: str,
        token_hash: str,
        family_id: uuid.UUID,
        expires_at: datetime,
        ip: str | None,
        ua: str | None,
    ) -> str:
        await RefreshToken.create(
            user_id=user_uuid,
            family_id=family_id,
            jti=jti,
            token_hash=token_hash,
            is_active=True,
            expires_at=expires_at,
            revoked_at=None,
            ip_address=ip,
            user_agent=ua,
        )
        return jti

    @staticmethod
    async def get_refresh_by_hash(token_hash: str) -> RefreshToken | None:
        return await RefreshToken.filter(token_hash=token_hash).first()

    @staticmethod
    async def mark_refresh_used(refresh_id: uuid.UUID) -> None:
        await RefreshToken.filter(id=refresh_id).update(last_used_at=_utcnow())

    @staticmethod
    async def revoke_refresh_by_id(refresh_id: uuid.UUID) -> None:
        await RefreshToken.filter(id=refresh_id, revoked_at=None, is_active=True).update(
            is_active=False, revoked_at=_utcnow()
        )

    @staticmethod
    async def revoke_family(family_id: uuid.UUID) -> int:
        return await RefreshToken.filter(
            family_id=family_id, revoked_at=None, is_active=True
        ).update(is_active=False, revoked_at=_utcnow())

    @staticmethod
    async def is_refresh_active_and_valid(rt: RefreshToken) -> bool:
        if not rt.is_active:
            return False
        if rt.expires_at <= _utcnow():
            return False
        return True
