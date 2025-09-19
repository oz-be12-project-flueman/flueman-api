# app/features/datasets/router.py
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.features.datasets.schemas import (
    DatasetCreate,
    DatasetOut,
    DatasetsListResponse,
    DatasetUpdate,
)
from app.features.datasets.service import DatasetsService
from app.features.users.models import UserRole
from app.shared.auth import CurrentUser

router = APIRouter(prefix="/datasets", tags=["datasets"])

# B008 회피: Annotated + Query 메타만 부여
NameQ = Annotated[str | None, Query(min_length=1)]
OwnerQ = Annotated[str | None, Query(min_length=1)]
SearchQ = Annotated[str | None, Query(min_length=1)]
PageQ = Annotated[int, Query(ge=1)]
PageSizeQ = Annotated[int, Query(ge=1, le=200)]


@router.post("", response_model=DatasetOut)
async def create_dataset(payload: DatasetCreate, current: CurrentUser) -> DatasetOut:
    """
    데이터셋 생성(로그인 사용자 소유)
    """
    svc = DatasetsService()
    return await svc.create(owner_id=str(current.id), payload=payload)


@router.get("", response_model=DatasetsListResponse)
async def list_datasets(
    current: CurrentUser,
    name: NameQ = None,
    owner_id: OwnerQ = None,
    q: SearchQ = None,  # 부분 검색(name/version/description)
    page: PageQ = 1,
    page_size: PageSizeQ = 20,
) -> DatasetsListResponse:
    """
    데이터셋 목록(필터/검색/페이지네이션)
    """
    svc = DatasetsService()
    items, total = await svc.list(name=name, owner_id=owner_id, q=q, page=page, page_size=page_size)
    return DatasetsListResponse(items=items, total=total)


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(dataset_id: str, _: CurrentUser) -> DatasetOut:
    """
    데이터셋 단건 조회(로그인 필요)
    """
    svc = DatasetsService()
    return await svc.get(dataset_id)


@router.patch("/{dataset_id}", response_model=DatasetOut)
async def update_dataset(
    dataset_id: str, payload: DatasetUpdate, current: CurrentUser
) -> DatasetOut:
    """
    데이터셋 수정(소유자 또는 관리자)
    """
    svc = DatasetsService()
    ds = await svc.get(dataset_id)
    if (ds.owner_id != str(current.id)) and (current.role is not UserRole.admin):
        raise HTTPException(status_code=403, detail="Forbidden")
    return await svc.update(dataset_id, payload)


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, current: CurrentUser):
    """
    데이터셋 삭제(소유자 또는 관리자)
    """
    svc = DatasetsService()
    ds = await svc.get(dataset_id)
    if (ds.owner_id != str(current.id)) and (current.role is not UserRole.admin):
        raise HTTPException(status_code=403, detail="Forbidden")
    await svc.delete(dataset_id)
    return {"status": "ok"}
