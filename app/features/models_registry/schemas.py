from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ✅ 단일 소스의 Enum 사용
from app.features.models_registry.models import ModelStatus


class ModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    artifact_url: str = Field(min_length=1, max_length=512)
    status: ModelStatus = ModelStatus.inactive
    description: str | None = None
    tags: dict[str, Any] = Field(default_factory=dict)


class ModelOut(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    name: str
    version: str
    artifact_url: str
    status: ModelStatus
    owner_id: str | None
    description: str | None
    tags: dict[str, Any]
    created_at: object
    updated_at: object


class ActivateOut(BaseModel):
    name: str
    activated_model_id: str
