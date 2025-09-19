# app/features/datasets/schemas.py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=50)
    storage_url: str = Field(min_length=1, max_length=512)
    size_bytes: int | None = None
    description: str | None = None
    stats: dict[str, Any] = Field(default_factory=dict)


class DatasetUpdate(BaseModel):
    storage_url: str | None = Field(default=None, max_length=512)
    size_bytes: int | None = None
    description: str | None = None
    stats: dict[str, Any] | None = None


class DatasetOut(BaseModel):
    id: str
    owner_id: str
    name: str
    version: str
    storage_url: str
    size_bytes: int | None
    description: str | None
    stats: dict[str, Any]
    created_at: object
    updated_at: object


class DatasetsListResponse(BaseModel):
    items: list[DatasetOut]
    total: int
