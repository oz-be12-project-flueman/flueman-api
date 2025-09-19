from __future__ import annotations

from enum import Enum
from typing import Any
import uuid

from tortoise import fields, models

from app.features.users.models import User


class ModelStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    shadow = "shadow"


class ModelRecord(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    name = fields.CharField(max_length=100, null=False)
    version = fields.CharField(max_length=50, null=False)
    artifact_url = fields.CharField(max_length=512, null=False)

    status: ModelStatus = fields.CharEnumField(
        ModelStatus, default=ModelStatus.inactive, null=False
    )

    # ✅ nullable FK → ForeignKeyNullableRelation 로 타입 지정
    owner: fields.ForeignKeyNullableRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="owned_models", on_delete=fields.SET_NULL, null=True
    )

    description = fields.TextField(null=True)
    tags: dict[str, Any] = fields.JSONField(null=False, default=dict)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "models"
        unique_together = (("name", "version"),)
        indexes = (("name", "status"),)

    def __str__(self) -> str:
        return f"{self.name}:{self.version}({self.status})"
