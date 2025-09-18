from __future__ import annotations

from tortoise.transactions import in_transaction

from app.features.models_registry.models import ModelRecord, ModelStatus


class ModelsRepository:
    async def create(
        self,
        *,
        name: str,
        version: str,
        artifact_url: str,
        status: ModelStatus,
        owner_id: str | None,
        description: str | None,
        tags: dict,
    ) -> ModelRecord:
        return await ModelRecord.create(
            name=name,
            version=version,
            artifact_url=artifact_url,
            status=status,
            owner_id=owner_id,  # Tortoise가 *_id 수용
            description=description,
            tags=tags or {},
        )

    async def get_by_id(self, model_id: str) -> ModelRecord | None:
        return await ModelRecord.get_or_none(id=model_id)

    async def get_active_by_name(self, name: str) -> ModelRecord | None:
        return await ModelRecord.get_or_none(name=name, status=ModelStatus.active)

    async def list(
        self,
        *,
        name: str | None = None,
        status: ModelStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ModelRecord], int]:
        qs = ModelRecord.all().order_by("-created_at")
        if name:
            qs = qs.filter(name=name)
        if status:
            qs = qs.filter(status=status)
        total = await qs.count()
        items = await qs.offset((page - 1) * page_size).limit(page_size)
        return list(items), total

    async def activate(self, *, target_id: str) -> tuple[str, str]:
        target = await ModelRecord.get_or_none(id=target_id)
        if not target:
            raise ValueError("model_not_found")
        async with in_transaction():
            await ModelRecord.filter(name=target.name, status=ModelStatus.active).update(
                status=ModelStatus.inactive
            )
            await ModelRecord.filter(id=target.id).update(status=ModelStatus.active)
        return target.name, str(target.id)
