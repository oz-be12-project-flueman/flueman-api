# app/features/auth/service.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
import uuid

from fastapi import HTTPException, Request, status
import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.security import hash_refresh_token
from app.features.auth.repository import AuthRepository  # Tortoise 기반 레포
from app.features.auth.schemas import LoginIn, MeOut
from app.features.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    is_refresh,
)
from app.features.users.models import User  # Tortoise 모델

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────────────────────
# 공용 유틸
def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_uuid_from_sub(sub: str) -> uuid.UUID:
    # 32자리 HEX면 uuid.UUID(hex=...)로, 아니면 일반 문자열로 파싱
    if isinstance(sub, str) and len(sub) == 32 and all(c in "0123456789abcdefABCDEF" for c in sub):
        return uuid.UUID(hex=sub)
    return uuid.UUID(str(sub))  # 하이픈 포함(36자) 등 일반 형태


# ─────────────────────────────────────────────────────────
# 헬퍼: 토큰 추출(헤더 우선, 없으면 쿠키)
def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    token = request.cookies.get("access_token")
    if token:
        return token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


# 헬퍼: 액세스 토큰 디코드/기본 검증
def _decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = cast(
            dict[str, Any],
            jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]),
        )
        return payload  # ← Dict[str, Any] 보장
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None


# 헬퍼: sub → UUID 파싱 후 활성 유저 조회
async def _load_active_user_from_sub(sub: str) -> User:
    try:
        u = _to_uuid_from_sub(sub)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from None

    # 1차: PK(UUID)로 조회
    user = await User.get_or_none(id=u)
    # 2차: 보조키(hex32)로 조회(필요 시)
    if not user:
        user = await User.get_or_none(id_bin_hex=u.hex)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user


# --------- 의존성: 현재 사용자 ---------
async def get_current_user(request: Request) -> User:
    """
    현재 요청의 액세스 토큰을 검증하고 사용자 모델을 반환한다.
    - Authorization 헤더(Bearer) 우선, 없으면 access_token 쿠키 사용
    """
    token = _extract_bearer_token(request)
    payload = _decode_access_token(token)

    sub_val = payload.get("sub")
    if not isinstance(sub_val, str) or not sub_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )

    # ✅ 캐스트 없이 바로 전달 (mypy redundant-cast 방지)
    return await _load_active_user_from_sub(sub_val)


# ─────────────────────────────────────────────────────────
# 인증 도메인 서비스
class AuthService:
    repo_cls = AuthRepository

    # ---- 아이디/비밀번호 로그인 ----
    @classmethod
    async def login_password(
        cls,
        payload: LoginIn,
        ip: str | None = None,
        ua: str | None = None,
    ) -> tuple[str, str, int]:
        user = await User.filter(email=payload.username).first()

        if not user or not pwd.verify(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="없는 회원정보입니다.",
            )

        # 토큰 생성 (sub = UUID 문자열)
        u: uuid.UUID = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))
        sub = str(u)

        access, access_jti, access_ttl = create_access_token(username=sub)
        refresh, refresh_jti, _ = create_refresh_token(username=sub)

        # 세션 기록(access jti 기준) 및 만료
        access_exp = _utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRES_MIN)
        await cls.repo_cls.create_session(
            user_uuid=sub,
            jti=access_jti,
            expires_at=access_exp,
            ip=ip,
            ua=ua,
        )

        # 리프레시 토큰 저장(해시 + family)
        family_id = uuid.uuid4()
        r_payload = decode_jwt(refresh)
        r_exp = r_payload.get("exp")
        if not isinstance(r_exp, int):
            raise HTTPException(status_code=400, detail="invalid refresh token exp")
        refresh_exp = datetime.fromtimestamp(r_exp, tz=UTC)

        await cls.repo_cls.create_refresh_token_row(
            user_uuid=sub,
            jti=refresh_jti,
            token_hash=hash_refresh_token(refresh),
            family_id=family_id,
            expires_at=refresh_exp,
            ip=ip,
            ua=ua,
        )

        return access, refresh, access_ttl

    # ---- 리프레시 토큰으로 액세스 재발급 (로테이션 + 재사용 탐지) ----
    async def refresh(self, *, refresh_token: str) -> tuple[str, str, int]:
        payload = decode_jwt(refresh_token)
        if not is_refresh(payload):
            raise HTTPException(status_code=400, detail="not a refresh token")

        # 서버 보관 해시와 대조
        token_hash = hash_refresh_token(refresh_token)
        rt = await self.repo_cls.get_refresh_by_hash(token_hash)
        if not rt:
            raise HTTPException(status_code=401, detail="invalid refresh token")

        # 활성/유효 확인
        if not await self.repo_cls.is_refresh_active_and_valid(rt):
            # 재사용/만료 등 비정상 → 같은 family 전량 차단
            await self.repo_cls.revoke_family(rt.family_id)
            raise HTTPException(status_code=401, detail="reused or expired refresh token")

        # 정상 사용 흔적
        await self.repo_cls.mark_refresh_used(rt.id)
        # 로테이션: 현 토큰 revoke
        await self.repo_cls.revoke_refresh_by_id(rt.id)

        user_uuid = payload["sub"]
        access, _, access_ttl = create_access_token(username=user_uuid)
        new_refresh, new_refresh_jti, _ = create_refresh_token(username=user_uuid)

        # 새 리프레시 저장(같은 family 유지)
        new_payload = decode_jwt(new_refresh)
        new_exp_ts = new_payload.get("exp")
        if not isinstance(new_exp_ts, int):
            raise HTTPException(status_code=400, detail="invalid refresh token exp")
        new_exp = datetime.fromtimestamp(new_exp_ts, tz=UTC)

        await self.repo_cls.create_refresh_token_row(
            user_uuid=user_uuid,
            jti=new_refresh_jti,
            token_hash=hash_refresh_token(new_refresh),
            family_id=rt.family_id,
            expires_at=new_exp,
            ip=rt.ip_address,
            ua=rt.user_agent,
        )

        return access, new_refresh, access_ttl

    # ---- 로그아웃(현재 세션 철회) ----
    async def logout(self, *, access_token: str) -> None:
        payload = decode_jwt(access_token)
        jti = payload.get("jti")
        if jti:
            await self.repo_cls.revoke_session_by_jti(jti)

    # ---- API 키 해시로 사용자 확인(백오피스/게이트웨이) ----
    async def get_user_by_apikey_hash(self, *, key_hash: str) -> MeOut:
        user = await self.repo_cls.get_apikey_owner(key_hash)
        if not user:
            raise HTTPException(status_code=401, detail="invalid api key")
        u: uuid.UUID = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))
        return MeOut(id=str(u), email=user.email, username=user.username, role=str(user.role.value))

    # ---- me 정보 ----
    async def me(self, *, user_uuid: str) -> MeOut:
        repo = self.repo_cls()
        user = await repo.get_user_by_uuid(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        u: uuid.UUID = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))
        return MeOut(id=str(u), email=user.email, username=user.username, role=str(user.role.value))
