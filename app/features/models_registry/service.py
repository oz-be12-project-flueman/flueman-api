from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.features.models_registry.models import ModelRecord, ModelStatus
from app.features.models_registry.repository import ModelsRepository
from app.features.models_registry.schemas import ModelCreate, ModelOut


def _to_out(m: ModelRecord) -> ModelOut:
    # ✅ Tortoise 모델의 *_id는 타입 힌트가 없어 getattr로 안전 접근
    owner_id_val: Any = getattr(m, "owner_id", None)
    owner_id_str: str | None
    if owner_id_val is None:
        owner_id_str = None
    else:
        owner_id_str = str(owner_id_val)

    return ModelOut(
        id=str(m.id),
        name=m.name,
        version=m.version,
        artifact_url=m.artifact_url,
        status=m.status,  # Pydantic이 문자열로 직렬화
        owner_id=owner_id_str,
        description=m.description,
        tags=m.tags or {},
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class ModelsService:
    repo_cls = ModelsRepository

    def __init__(self) -> None:
        self.repo = self.repo_cls()

    async def create_model(self, *, payload: ModelCreate, owner_id: str | None) -> ModelOut:
        try:
            m = await self.repo.create(
                name=payload.name,
                version=payload.version,
                artifact_url=payload.artifact_url,
                status=payload.status,  # ✅ models.ModelStatus
                owner_id=owner_id,
                description=payload.description,
                tags=payload.tags,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="name+version already exists"
            ) from None
        return _to_out(m)

    async def list_models(
        self, *, name: str | None, status_val: ModelStatus | None, page: int, page_size: int
    ) -> tuple[list[ModelOut], int]:
        items, total = await self.repo.list(
            name=name, status=status_val, page=page, page_size=page_size
        )
        return ([_to_out(m) for m in items], total)

    async def get_active(self, *, name: str) -> ModelOut:
        m = await self.repo.get_active_by_name(name)
        if not m:
            raise HTTPException(status_code=404, detail="active model not found")
        return _to_out(m)

    async def activate(self, *, target_id: str) -> tuple[str, str]:
        try:
            name, activated_id = await self.repo.activate(target_id=target_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="model not found") from None
        return name, activated_id
