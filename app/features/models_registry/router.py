# app/features/models_registry/router.py
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.features.models_registry.models import ModelStatus
from app.features.models_registry.schemas import ActivateOut, ModelCreate, ModelOut
from app.features.models_registry.service import ModelsService
from app.shared.auth import AdminUser

router = APIRouter(prefix="/models", tags=["models"])

# ---- Query 파라미터 타입 메타 (B008 회피) ----
NameQ = Annotated[str | None, Query(min_length=1)]
StatusQ = Annotated[ModelStatus | None, Query()]
PageQ = Annotated[int, Query(ge=1)]
PageSizeQ = Annotated[int, Query(ge=1, le=100)]


@router.post("", response_model=ModelOut)
async def create_model(payload: ModelCreate, current: AdminUser) -> ModelOut:
    """관리자만 모델 등록 가능"""
    svc = ModelsService()
    return await svc.create_model(payload=payload, owner_id=str(current.id))


@router.get("", response_model=list[ModelOut])
async def list_models(
    name: NameQ = None,
    status: StatusQ = None,
    page: PageQ = 1,
    page_size: PageSizeQ = 20,
) -> list[ModelOut]:
    """모델 목록 조회(필터/페이지네이션)"""
    svc = ModelsService()
    items, _ = await svc.list_models(name=name, status_val=status, page=page, page_size=page_size)
    return items


@router.get("/active", response_model=ModelOut)
async def get_active_model(name: Annotated[str, Query(min_length=1)]) -> ModelOut:
    """특정 name의 활성 모델 단건 조회"""
    svc = ModelsService()
    return await svc.get_active(name=name)


@router.patch("/{model_id}/activate", response_model=ActivateOut)
async def activate_model(model_id: str, current: AdminUser) -> ActivateOut:
    """관리자만 활성 전환 가능(같은 name은 하나만 active 유지)"""
    svc = ModelsService()
    name, activated_id = await svc.activate(target_id=model_id)
    return ActivateOut(name=name, activated_model_id=activated_id)
