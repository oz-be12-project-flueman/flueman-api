from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.auth.service import get_current_user
from app.features.users.models import User as UserModel
from app.features.users.models import UserRole
from app.features.users.schemas import (
    UserCreate,
    UserResponse,
    UsersListResponse,
    UserUpdate,
)
from app.features.users.service import UsersService

router = APIRouter(prefix="/user", tags=["user"])

# 의존성 타입 별칭(선택)
CurUser = Annotated[UserModel, Depends(get_current_user)]


def _require_admin(user: UserModel) -> None:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin 권한만 가능합니다."
        )


def _require_admin_or_self(current: UserModel, target_username: str) -> None:
    if current.role == UserRole.admin:
        return
    if current.username == target_username:
        return
    # manager는 단일 조회만 허용, 수정은 안 됨
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


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
    current_user: CurUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> UsersListResponse:
    """
    admin만 전체 목록 조회 가능
    """
    _require_admin(current_user)

    svc = UsersService()
    items, total = await svc.list_users(page, page_size)
    return UsersListResponse(items=items, total=total)


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: CurUser,
) -> UserResponse:
    """
    - admin: 아무나 조회 가능
    - manager: 아무나 '단일' 조회 가능(목록 X)
    - user: 자기 자신만 조회 가능
    """
    svc = UsersService()
    role = str(current_user.role)

    if role == UserRole.user and current_user.username != username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    u = await svc.get_user(user_uuid=str(current_user.id))
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="해당 유저의 검색 결과가 없습니다."
        )
    return u


@router.patch("/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    user: UserUpdate,
    current_user: CurUser,
) -> UserResponse:
    """
    - admin: 아무나 수정 가능
    - user: 자기 자신만 수정 가능
    - manager: 수정 불가
    """
    _require_admin_or_self(current_user, username)

    svc = UsersService()
    user_uuid = str(current_user.id)
    updated = await svc.update_user(user_uuid, user)

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated
