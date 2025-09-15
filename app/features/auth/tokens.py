import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

# settings.SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES 활용
from app.core.config import settings

ALGO = "HS256"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_jwt(
    sub: str,
    *,
    jti: str | None = None,
    minutes: int = 60,
    extra: dict[str, Any] | None = None,
) -> str:
    now = _utcnow()
    payload = {
        "iss": "flueman",
        "sub": sub,
        "jti": jti or str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGO)


def decode_jwt(token: str) -> dict[str, Any]:
    # 필요 시 audience/issuer 검증 옵션 추가
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])


def create_access_token(
    username: str,
    *,
    minutes: int | None = None,
    session_id: str | None = None,
) -> tuple[str, str, int]:
    ttl = minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    jti = str(uuid.uuid4())
    token = create_jwt(
        sub=username,
        jti=jti,
        minutes=ttl,
        extra={"typ": "access", "sid": session_id},
    )
    return token, jti, ttl * 60  # seconds


def create_refresh_token(username: str, *, minutes: int = 60 * 24 * 14) -> tuple[str, str, int]:
    # 기본 14일
    jti = str(uuid.uuid4())
    token = create_jwt(sub=username, jti=jti, minutes=minutes, extra={"typ": "refresh"})
    return token, jti, minutes * 60


def is_refresh(payload: dict[str, Any]) -> bool:
    return payload.get("typ") == "refresh"


def is_access(payload: dict[str, Any]) -> bool:
    return payload.get("typ") == "access"
