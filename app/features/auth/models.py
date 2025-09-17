from __future__ import annotations

import uuid

from tortoise import fields, models

from app.features.users.models import User


class Session(models.Model):
    """
    액세스 세션(JWT jti 기준 추적)
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # User PK(UUID, CHAR(36))를 FK로 참조 (to_field="id" 필요 없음: PK가 기본)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="sessions", on_delete=fields.CASCADE
    )

    jti = fields.CharField(max_length=36, null=False)
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=255, null=True)

    expires_at = fields.DatetimeField(null=False)
    revoked_at = fields.DatetimeField(null=True)
    is_active = fields.BooleanField(null=False, default=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "session"
        unique_together = (("jti",),)  # jti가 중복되지 않도록(필요 시)


class ApiKey(models.Model):
    """
    API 키 보관(해시 저장)
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="api_keys", on_delete=fields.CASCADE
    )

    key_hash = fields.CharField(max_length=64, null=False)
    scopes: list[str] = fields.JSONField(null=False, default=list)
    expires_at = fields.DatetimeField(null=True)
    is_revoked = fields.BooleanField(null=False, default=False)
    last_used_at = fields.DatetimeField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "api_keys"
        indexes = (("key_hash",),)
