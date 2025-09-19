# app/features/datasets/service.py
from __future__ import annotations

from fastapi import HTTPException, status

from app.features.datasets.models import Dataset
from app.features.datasets.repository import DatasetsRepository
from app.features.datasets.schemas import DatasetCreate, DatasetOut, DatasetUpdate


def _to_out(d: Dataset) -> DatasetOut:
    return DatasetOut(
        id=str(d.id),
        owner_id=str(d.owner.id),
        name=d.name,
        version=d.version,
        storage_url=d.storage_url,
        size_bytes=d.size_bytes,
        description=d.description,
        stats=d.stats or {},
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


class DatasetsService:
    repo_cls = DatasetsRepository

    def __init__(self) -> None:
        self.repo = self.repo_cls()

    async def create(self, *, owner_id: str, payload: DatasetCreate) -> DatasetOut:
        try:
            ds = await self.repo.create(
                owner_id=owner_id,
                name=payload.name,
                version=payload.version,
                storage_url=payload.storage_url,
                size_bytes=payload.size_bytes,
                description=payload.description,
                stats=payload.stats,
            )
        except Exception:
            # unique(name, version) 위반 등
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="dataset already exists"
            ) from None
        return _to_out(ds)

    async def get(self, dataset_id: str) -> DatasetOut:
        ds = await self.repo.get(dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="dataset not found")
        return _to_out(ds)

    async def list(
        self, *, name: str | None, owner_id: str | None, q: str | None, page: int, page_size: int
    ) -> tuple[list[DatasetOut], int]:
        items, total = await self.repo.list(
            name=name, owner_id=owner_id, q=q, page=page, page_size=page_size
        )
        return ([_to_out(d) for d in items], total)

    async def update(self, dataset_id: str, payload: DatasetUpdate) -> DatasetOut:
        fields: DatasetsRepository.UpdateFields = {}
        if payload.storage_url is not None:
            fields["storage_url"] = payload.storage_url
        if payload.size_bytes is not None:
            fields["size_bytes"] = payload.size_bytes
        if payload.description is not None:
            fields["description"] = payload.description
        if payload.stats is not None:
            fields["stats"] = payload.stats

        ds = await self.repo.update_partial(dataset_id, fields)
        if not ds:
            raise HTTPException(status_code=404, detail="dataset not found")
        return _to_out(ds)

    async def delete(self, dataset_id: str) -> None:
        ok = await self.repo.delete(dataset_id)
        if not ok:
            raise HTTPException(status_code=404, detail="dataset not found")
