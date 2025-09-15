from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.users.schemas import UserCreate, UserOut, UserUpdate
from app.features.users.service import UsersService
from app.shared.deps import CurrentUser, get_current_user

router = APIRouter()

# DI 별칭 (B008 회피)
DbSess = Annotated[AsyncSession, Depends(get_session)]
CurUser = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("/")
async def list_users(
    session: DbSess,
    _: CurUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> tuple[list[UserOut], int]:
    svc = UsersService(session)
    items, total = await svc.list_users(page, page_size)
    # repo는 ORM 엔티티를 반환한다고 가정. 서비스에서 UserOut로 변환
    out: list[UserOut] = [
        UserOut(
            id=u.__getattribute__("id"),
            email=u.__getattribute__("email"),
            username=u.__getattribute__("username"),
            phone_number=u.__getattribute__("phone_number"),
            role=u.__getattribute__("role"),
            is_active=u.__getattribute__("is_active"),
        )
        for u in items
    ]
    return out, total


@router.get("/{username}", response_model=UserOut)
async def get_user(
    username: str,
    session: DbSess,
    _: CurUser,
) -> UserOut:
    svc = UsersService(session)
    return await svc.get_user(username)


@router.post("/", status_code=201)
async def create_user(
    payload: UserCreate,
    session: DbSess,
    _: CurUser,
):
    svc = UsersService(session)
    return await svc.create_user(**payload.model_dump())


@router.patch("/{username}")
async def update_user(
    username: str,
    payload: UserUpdate,
    session: DbSess,
    _: CurUser,
):
    svc = UsersService(session)
    return await svc.update_user(username, **payload.model_dump(exclude_none=True))
