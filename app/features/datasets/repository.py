# app/features/datasets/repository.py
from __future__ import annotations

from typing import Any, TypedDict

from tortoise.expressions import Q

from app.features.datasets.models import Dataset


class DatasetsRepository:
    # ---------- 생성 ----------
    async def create(
        self,
        *,
        owner_id: str,
        name: str,
        version: str,
        storage_url: str,
        size_bytes: int | None,
        description: str | None,
        stats: dict[str, Any] | None,
    ) -> Dataset:
        return await Dataset.create(
            owner_id=owner_id,
            name=name,
            version=version,
            storage_url=storage_url,
            size_bytes=size_bytes,
            description=description,
            stats=stats or {},
        )

    # ---------- 조회 ----------
    async def get(self, dataset_id: str) -> Dataset | None:
        return await Dataset.get_or_none(id=dataset_id)

    async def list(
        self,
        *,
        name: str | None,
        owner_id: str | None,
        q: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Dataset], int]:
        qs = Dataset.all().order_by("-created_at")
        if name:
            qs = qs.filter(name=name)
        if owner_id:
            qs = qs.filter(owner_id=owner_id)
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(version__icontains=q) | Q(description__icontains=q)
            )
        total = await qs.count()
        items = await qs.offset((page - 1) * page_size).limit(page_size)
        return list(items), total

    # ---------- 부분 업데이트 ----------
    class UpdateFields(TypedDict, total=False):
        storage_url: str
        size_bytes: int
        description: str
        stats: dict[str, Any]

    async def update_partial(self, dataset_id: str, fields: UpdateFields) -> Dataset | None:
        ds = await self.get(dataset_id)
        if not ds:
            return None
        for k, v in fields.items():
            if v is not None and hasattr(ds, k):
                setattr(ds, k, v)
        await ds.save()
        return ds

    # ---------- 삭제 ----------
    async def delete(self, dataset_id: str) -> bool:
        ds = await self.get(dataset_id)
        if not ds:
            return False
        await ds.delete()
        return True
