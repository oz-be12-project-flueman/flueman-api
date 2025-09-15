from __future__ import annotations

import uuid

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.repository import UsersRepository
from app.features.users.schemas import UserOut
from app.shared.errors import conflict, not_found
from app.shared.utils.uuid import bin_to_uuid

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UsersService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UsersRepository(session)
        self.session = session

    async def list_users(self, page: int, page_size: int) -> tuple[list[dict], int]:
        items, total = await self.repo.list(page, page_size)
        return (
            [
                {
                    "id": bin_to_uuid(u.id),
                    "email": u.email,
                    "username": u.username,
                    "phone_number": u.phone_number,
                    "role": u.role,
                    "is_active": u.is_active,
                }
                for u in items
            ],
            total,
        )

    async def get_user(self, user_uuid: str) -> UserOut:
        user = await self.repo.get(user_uuid)
        if not user:
            not_found("user not found")

        return UserOut(
            id=bin_to_uuid(user.id),
            email=user.email,
            username=user.username,
            phone_number=user.phone_number,
            role=user.role,
            is_active=user.is_active,
        )

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        username: str,
        phone_number: str,
        role: str,
        is_active: bool,
    ) -> dict:
        dup = await self.repo.get_by_email(email)
        if dup:
            conflict("email already exists")

        uid = uuid.uuid4()
        await self.repo.create(
            id_bytes=uid.bytes,
            email=email,
            username=username,
            phone_number=phone_number,
            password_hash=pwd.hash(password),
            role=role,
            is_active=is_active,
        )
        await self.session.commit()
        return {"id": str(uid)}

    async def update_user(
        self,
        user_uuid: str,
        *,
        phone_number: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        user = await self.repo.get(user_uuid)
        if not user:
            not_found("user not found")

        # 레포지토리의 TypedDict 제약에 맞춰 None 제거 후 전달
        fields: UsersRepository.UserUpdateFields = {}
        if phone_number is not None:
            fields["phone_number"] = phone_number
        if role is not None:
            fields["role"] = role
        if is_active is not None:
            fields["is_active"] = is_active

        if fields:
            await self.repo.update_partial(user, **fields)
            await self.session.commit()

        return {"id": user_uuid, "role": user.role, "is_active": user.is_active}
