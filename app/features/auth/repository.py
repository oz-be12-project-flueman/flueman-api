# app/features/auth/repository.py
from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import ScalarResult, insert, select, update
from sqlalchemy.dialects.mysql import BINARY, BOOLEAN, CHAR, JSON, VARCHAR
from sqlalchemy.engine import Result  # ★ 제네릭 Result 사용
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.shared.utils.uuid import uuid_to_bin


# ---- 테이블 매핑 (필요 컬럼만 정의) ----
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True)
    username: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    email: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    role: Mapped[str] = mapped_column(VARCHAR(16), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, default=True)


class Session(Base):
    __tablename__ = "session"
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True)
    username: Mapped[bytes] = mapped_column(BINARY(16), nullable=False)
    jti: Mapped[str] = mapped_column(CHAR(36), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(VARCHAR(45))
    user_agent: Mapped[str | None] = mapped_column(VARCHAR(255))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    is_active: Mapped[bool]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True)
    username: Mapped[bytes]
    key_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    scopes: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON
    expires_at: Mapped[datetime | None]
    is_revoked: Mapped[bool]
    last_used_at: Mapped[datetime | None]
    created_at: Mapped[datetime]


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---- Users ----
    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.is_active)  # noqa: E712
        res: ScalarResult[User] = await self.session.scalars(stmt)  # ★ scalars() 사용
        return res.one_or_none()

    async def get_user_by_uuid(self, user_uuid: str) -> User | None:
        stmt = select(User).where(User.id == uuid_to_bin(user_uuid))
        res: ScalarResult[User] = await self.session.scalars(stmt)  # ★ scalars() 사용
        return res.one_or_none()

    # ---- Session ----
    async def create_session(
        self,
        *,
        user_uuid: str,
        jti: str,
        expires_at: datetime,
        ip: str | None,
        ua: str | None,
    ) -> str:
        import uuid as _uuid

        sid = _uuid.uuid4()
        await self.session.execute(
            insert(Session).values(
                id=sid.bytes,
                username=uuid_to_bin(user_uuid),
                jti=jti,
                ip_address=ip,
                user_agent=ua,
                expires_at=expires_at,
                revoked_at=None,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        )
        return str(sid)

    async def revoke_session_by_jti(self, jti: str) -> None:
        await self.session.execute(
            update(Session)
            .where(Session.jti == jti, Session.revoked_at.is_(None))
            .values(
                is_active=False,
                revoked_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        )

    # ---- API Key ----
    async def get_apikey_owner(self, key_hash: str) -> User | None:
        # JOIN 결과 타입을 명시적으로 지정: (ApiKey, User)
        stmt = (
            select(ApiKey, User)
            .join(User, User.id == ApiKey.username)
            .where(
                ApiKey.key_hash == key_hash,
                ApiKey.is_revoked == False,  # noqa: E712
            )
        )
        res: Result[tuple[ApiKey, User]] = await self.session.execute(stmt)  # ★ 타입 명시
        row = res.first()
        if row is None:
            return None
        _, user = row
        return cast(User, user)  # ★ Any → User
