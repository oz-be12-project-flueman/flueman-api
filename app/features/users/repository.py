from __future__ import annotations

from typing import TypedDict, Unpack
import uuid

from tortoise.expressions import Q

from app.features.users.models import User


class UsersRepository:
    # ---------- 조회 ----------
    async def get(self, user_uuid: str) -> User | None:
        """PK(문자열 UUID)로 조회"""
        return await User.get_or_none(id=user_uuid)

    async def get_by_id_hex(self, id_hex32: str) -> User | None:
        """32자리 HEX로 직접 조회 (가장 빠름: UNIQUE 인덱스)"""
        return await User.get_or_none(id_bin_hex=id_hex32.lower())

    async def get_by_username(self, username: str) -> User | None:
        return await User.get_or_none(username=username)

    async def get_by_email(self, email: str) -> User | None:
        return await User.get_or_none(email=email)

    async def get_by_phone(self, phone: str) -> User | None:
        return await User.get_or_none(phone_number=phone)

    async def list_users(self, page: int, page_size: int) -> tuple[list[User], int]:
        qs = User.all().order_by("-created_at")
        total = await qs.count()
        items = await qs.offset((page - 1) * page_size).limit(page_size)
        # items는 이미 list[User]로 materialize됨
        return list(items), total

    async def search(
        self, *, keyword: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        qs = User.filter(
            Q(username__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(phone_number__icontains=keyword)
        ).order_by("-created_at")
        total = await qs.count()
        items = await qs.offset((page - 1) * page_size).limit(page_size)
        return list(items), total

    # ---------- 부분 업데이트 ----------
    class UserUpdateFields(TypedDict, total=False):
        username: str
        phone_number: str
        role: str
        is_active: bool
        password_hash: str

    async def update_partial(self, user: User, **fields: Unpack[UserUpdateFields]) -> User:
        """
        id / id_bin / id_bin_hex는 불변 권장.
        (동기화 이슈 방지를 위해 별도 메서드로 처리)
        """
        for k, v in fields.items():
            if v is not None:
                setattr(user, k, v)
        await user.save()
        return user

    # ---------- ID 교체(필요할 때만) ----------
    async def replace_id(
        self,
        user: User,
        *,
        new_uuid: str | None = None,
        new_hex32: str | None = None,
    ) -> User:
        """
        정말 필요할 때만 사용. 둘 중 하나만 넘겨도 나머지 자동 동기화.
        UNIQUE(id_bin_hex) 충돌 시 예외 발생.
        """
        if new_uuid:
            u = uuid.UUID(new_uuid)
            new_hex32 = (new_hex32 or u.hex).lower()
        elif new_hex32:
            u = uuid.UUID(hex=new_hex32)
            new_hex32 = new_hex32.lower()
        else:
            raise ValueError("새 ID가 필요합니다(new_uuid | new_hex32 중 하나).")

        user.id = u
        user.id_bin_hex = new_hex32
        await user.save()
        return user

    # ---------- 삭제 ----------
    async def delete(self, user: User) -> None:
        await user.delete()
