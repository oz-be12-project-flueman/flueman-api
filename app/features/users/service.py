# app/features/users/service.py
from __future__ import annotations

import uuid

from passlib.context import CryptContext

from app.features.users.models import User as UserModel
from app.features.users.repository import UsersRepository
from app.features.users.schemas import UserCreate, UserResponse, UserUpdate
from app.shared.errors import conflict, not_found

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _to_user_out(u: UserModel) -> UserResponse:
    # Tortoise 모델 → Pydantic 응답 스키마
    return UserResponse(
        id=str(u.id),
        username=u.username,
        created_at=u.created_at,
        updated_at=u.updated_at,
        is_active=bool(u.is_active),
    )


class UsersService:
    def __init__(self) -> None:
        # Tortoise ORM: 세션 개념이 없으므로 인자 불필요
        self.repo = UsersRepository()

    async def list_users(self, page: int, page_size: int) -> tuple[list[UserResponse], int]:
        """
        Tortoise 모델(User) 리스트와 total을 그대로 반환.
        라우터에서 Pydantic 스키마로 변환해 응답하는 패턴 권장.
        """
        items, total = await self.repo.list_users(page, page_size)
        return ([_to_user_out(u) for u in items], total)

    async def get_user(self, user_uuid: str) -> UserResponse:
        user = await self.repo.get(user_uuid)
        if not user:
            not_found("user not found")

        return _to_user_out(user)

    # ─────────────────────────────────────────────────────────
    # Sign up
    # ─────────────────────────────────────────────────────────
    async def create_user(self, user: UserCreate) -> UserResponse:
        dup = await self.repo.get_by_email(user.email)
        if dup:
            conflict("이미 존재하는 email 입니다.")

        u = uuid.uuid4()
        new_user = await self.repo.create(
            id_uuid=str(u),  # repo가 UUID/str/bytes 모두 처리
            email=user.email,
            username=user.username,
            phone_number=user.phone_number,
            password_hash=pwd.hash(user.password),
            role=user.role,
            is_active=user.is_active,
        )

        # Tortoise는 별도 commit() 불필요
        return _to_user_out(new_user)

    async def update_user(self, user_uuid: str, user: UserUpdate) -> UserResponse:
        get_user = await self.repo.get(user_uuid)
        if not get_user:
            not_found("user not found")

        # 레포지토리의 TypedDict 제약에 맞춰 None 제거 후 전달
        fields: UsersRepository.UserUpdateFields = {}
        if user.phone_number is not None:
            fields["phone_number"] = user.phone_number
        if user.role is not None:
            fields["role"] = user.role
        if user.is_active is not None:
            fields["is_active"] = user.is_active

        if fields:
            await self.repo.update_partial(get_user, **fields)

        return _to_user_out(get_user)
