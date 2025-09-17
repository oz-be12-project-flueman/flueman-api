from __future__ import annotations

from enum import Enum
import uuid

from tortoise import fields
from tortoise.models import Model


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class User(Model):
    class Meta:
        table = "users"
        indexes = ("created_at",)  # idx_유저_created

    # PK: UUID 문자열(CHAR(36))
    # 예: "xxxxxxxx-....-xxxx"
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    # 보조키: 32자리 HEX 문자열 (인덱스/UNIQUE 가능, 조인/조회에 사용)
    # 예: "f47ac10b58cc4372a5670e02b2c3d479"
    id_bin_hex = fields.CharField(max_length=32, null=False, unique=True)

    username = fields.CharField(max_length=50, null=False)
    email = fields.CharField(max_length=255, null=False)
    phone_number = fields.CharField(max_length=20, null=False)
    password_hash = fields.CharField(max_length=255, null=False)

    role = fields.CharEnumField(UserRole, null=False, default=UserRole.user.value)
    is_active = fields.BooleanField(null=False, default=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self) -> str:
        return f"<User {self.username} ({self.role})>"

    # 편의 변환
    @staticmethod
    def uuid_to_bytes(u: str) -> bytes:
        return uuid.UUID(u).bytes

    @staticmethod
    def uuid_to_hex(u: str) -> str:
        return uuid.UUID(u).hex  # 32자리, 하이픈 없음

    @staticmethod
    def bytes_to_uuid(b: bytes) -> str:
        return str(uuid.UUID(bytes=b))

    @staticmethod
    def bytes_to_hex(b: bytes) -> str:
        return b.hex()  # 32자리 소문자
