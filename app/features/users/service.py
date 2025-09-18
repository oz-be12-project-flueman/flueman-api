from __future__ import annotations

import uuid

from passlib.context import CryptContext

from app.features.users.models import User as UserModel
from app.features.users.repository import UsersRepository
from app.features.users.schemas import UserCreate, UserResponse, UserUpdate
from app.shared.errors import not_found

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


JSONScalar = str | int | float | bool | None


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
    # DI: 필요 시 테스트에서 FakeRepo로 갈아끼울 수 있음
    repo_cls: type[UsersRepository] = UsersRepository

    def __init__(self, repo: UsersRepository | None = None) -> None:
        # repo를 직접 주입하지 않으면 repo_cls로 생성
        self.repo = repo or self.repo_cls()

    async def list_users(self, page: int, page_size: int) -> tuple[list[UserResponse], int]:
        """
        User 목록과 total 반환. 이 메서드에서는 바로 Pydantic 스키마로 변환해 반환.
        (원한다면 라우터에서 변환하도록 변경해도 됨)
        """
        items, total = await self.repo.list_users(page, page_size)
        return ([_to_user_out(u) for u in items], total)

    async def get_user(self, user_uuid: str) -> UserResponse:
        user = await self.repo.get(user_uuid)
        if not user:
            not_found("user not found22")  # 예외 발생하여 흐름 중단
        # 정적 분석기 힌트
        assert user is not None
        return _to_user_out(user)

    # ─────────────────────────────────────────────────────────
    # Sign up
    # ─────────────────────────────────────────────────────────
    @classmethod
    async def create_user(cls, user: UserCreate) -> UserResponse:
        # ── (1) 유니크 제약 사전검사 ─────────────────────────────────────────
        if await UserModel.exists(email=user.email):
            raise ValueError("이미 가입된 email 입니다.")
        if await UserModel.exists(username=user.username):
            raise ValueError("이미 가입된 유저 아이디입니다.")

        # ── (2) ID 동기화 ───────────────────────────────────────────────────
        u = uuid.uuid4()
        id_uuid = str(u)
        id_hex32 = u.hex.lower()

        new_user = await UserModel.create(
            id=id_uuid,
            id_bin_hex=id_hex32,
            email=user.email,
            username=user.username,
            phone_number=user.phone_number,
            password_hash=pwd.hash(user.password),
            role=user.role,
            is_active=user.is_active,
        )

        return _to_user_out(new_user)

    async def update_user(self, user_uuid: str, user: UserUpdate) -> UserResponse:
        db_user = await self.repo.get(user_uuid)
        if not db_user:
            not_found("user not found")
        assert db_user is not None

        # 레포지토리의 TypedDict 제약에 맞춰 None 제거 후 전달
        fields: UsersRepository.UserUpdateFields = {}
        if user.phone_number is not None:
            fields["phone_number"] = user.phone_number
        if user.role is not None:
            fields["role"] = user.role
        if user.is_active is not None:
            fields["is_active"] = user.is_active

        # 필요 시 username/password 갱신 로직 추가 가능:
        # if user.username is not None:
        #     fields["username"] = user.username
        # if user.password is not None:
        #     fields["password_hash"] = pwd.hash(user.password)

        if fields:
            await self.repo.update_partial(db_user, **fields)

        return _to_user_out(db_user)
