# app/shared/auth.py
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.features.auth.service import get_current_user
from app.features.users.models import User as UserModel
from app.features.users.models import UserRole


# ── 역할 가드(여러 역할 중 하나면 통과) ─────────────────────────────
def role_guard(*roles: UserRole) -> Callable[[UserModel], Awaitable[UserModel]]:
    async def _dep(user: Annotated[UserModel, Depends(get_current_user)]) -> UserModel:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="권한이 없습니다.",
            )
        return user

    return _dep


# 자주 쓰는 별칭
require_admin = role_guard(UserRole.admin)

# 타입 별칭(그대로 엔드포인트 파라미터에 사용)
AdminUser = Annotated[UserModel, Depends(require_admin)]
CurrentUser = Annotated[UserModel, Depends(get_current_user)]


# ── Admin 또는 본인(경로의 username 기준) ────────────────────────────
async def require_admin_or_self_by_username(
    username: str,
    current: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    if current.role is UserRole.admin or current.username == username:
        return current
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


AdminOrSelfByUsername = Annotated[UserModel, Depends(require_admin_or_self_by_username)]


# ── Admin 또는 본인(경로의 user_id 기준) ─────────────────────────────
async def require_admin_or_self_by_user_id(
    user_id: str,
    current: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    if current.role is UserRole.admin or str(current.id) == user_id:
        return current
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


AdminOrSelfByUserId = Annotated[UserModel, Depends(require_admin_or_self_by_user_id)]


# ── 조회 전용: Admin 또는 Manager 또는 본인 ───────────────────────────
async def require_viewer_admin_manager_or_self_by_username(
    username: str,
    current: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    if current.role in (UserRole.admin, UserRole.manager) or current.username == username:
        return current
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


ViewerAdminManagerOrSelfByUsername = Annotated[
    UserModel, Depends(require_viewer_admin_manager_or_self_by_username)
]
