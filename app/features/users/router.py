from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.features.auth.service import get_current_user
from app.features.users.models import User as UserModel
from app.features.users.schemas import (
    UserCreate,
    UserResponse,
    UsersListResponse,
    UserUpdate,
)
from app.features.users.service import UsersService
from app.shared.auth import AdminOrSelfByUsername, AdminUser, ViewerAdminManagerOrSelfByUsername

router = APIRouter(prefix="/user", tags=["user"])

# 의존성 타입 별칭(선택)
CurUser = Annotated[UserModel, Depends(get_current_user)]


@router.post("/signup", status_code=201, response_model=UserResponse)
async def create_user(
    user: UserCreate,
) -> UserResponse:
    """
    회원가입
    """
    return await UsersService.create_user(user)


@router.get("/", response_model=UsersListResponse)
async def list_users(
    _: AdminUser,  # 관리자 가드 + 현재 사용자 객체
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> UsersListResponse:
    """
    admin만 전체 목록 조회 가능
    """
    svc = UsersService()
    items, total = await svc.list_users(page, page_size)
    return UsersListResponse(items=items, total=total)


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    _: ViewerAdminManagerOrSelfByUsername,  # ✅ admin/manager/본인만 통과
) -> UserResponse:
    """
    - admin: 아무나 조회 가능
    - manager: 아무나 '단일' 조회 가능(목록 X)
    - user: 자기 자신만 조회 가능
    """
    # username → 대상 유저 찾기
    target = await UserModel.get_or_none(username=username)
    if not target:
        raise HTTPException(status_code=404, detail="해당 유저의 검색 결과가 없습니다.")

    # 서비스는 UUID 기반이므로 변환해서 호출
    svc = UsersService()
    return await svc.get_user(user_uuid=str(target.id))


@router.patch("/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    payload: UserUpdate,
    _: AdminOrSelfByUsername,  # ✅ admin 또는 본인만 통과, manager는 차단
) -> UserResponse:
    """
    - admin: 아무나 수정 가능
    - user: 자기 자신만 수정 가능
    - manager: 수정 불가
    """
    svc = UsersService()

    # username → UUID 해석
    target = await UserModel.get_or_none(username=username)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await svc.update_user(str(target.id), payload)
    return updated
