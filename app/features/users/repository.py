from collections.abc import Sequence
from typing import TypedDict, Unpack

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import BINARY, BOOLEAN, VARCHAR
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.shared.utils.uuid import uuid_to_bin


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


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_uuid: str) -> User | None:
        stmt = select(User).where(User.id == uuid_to_bin(user_uuid))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(self, page: int, page_size: int) -> tuple[Sequence[User], int]:
        stmt = select(User).offset((page - 1) * page_size).limit(page_size)
        items = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(select(func.count()).select_from(User))).scalar_one()
        return items, int(total)

    async def create(
        self,
        *,
        id_bytes: bytes,
        email: str,
        username: str,
        phone_number: str,
        password_hash: str,
        role: str,
        is_active: bool,
    ) -> User:
        user = User(
            id=id_bytes,
            email=email,
            username=username,
            phone_number=phone_number,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    # 부분 업데이트 가능한 필드만 허용(정적 타입)
    class UserUpdateFields(TypedDict, total=False):
        phone_number: str
        role: str
        is_active: bool

    async def update_partial(self, user: User, **fields: Unpack[UserUpdateFields]) -> User:
        for k, v in fields.items():
            if v is not None and hasattr(user, k):
                setattr(user, k, v)
        await self.session.flush()
        return user
