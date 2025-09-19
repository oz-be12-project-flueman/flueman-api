# app/features/datasets/models.py
from __future__ import annotations

from typing import Any
import uuid

from tortoise import fields, models

from app.features.users.models import User


class Dataset(models.Model):
    """
    데이터셋 카탈로그(버전/스토리지/통계)
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)

    # 소유자
    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="datasets", on_delete=fields.CASCADE
    )

    # 식별
    name = fields.CharField(max_length=120, null=False)
    version = fields.CharField(max_length=50, null=False)

    # 저장소/메타
    storage_url = fields.CharField(max_length=512, null=False)
    size_bytes = fields.BigIntField(null=True)
    description = fields.TextField(null=True)
    stats: dict[str, Any] = fields.JSONField(null=False, default=dict)

    # 생성/수정 시각
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "datasets"
        unique_together = (("name", "version"),)
        indexes = (("owner_id", "created_at"), ("name", "created_at"))

    def __str__(self) -> str:
        return f"{self.name}:{self.version}"
