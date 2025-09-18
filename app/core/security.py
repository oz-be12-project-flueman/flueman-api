from datetime import UTC, datetime, timedelta
import hashlib

import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)


def create_access_token(sub: str, minutes: int | None = None) -> str:
    expire = datetime.now(tz=UTC) + timedelta(
        minutes=minutes or settings.JWT_ACCESS_EXPIRES_MIN,
    )
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256((settings.JWT_REFRESH_HASH_PEPPER + raw).encode("utf-8")).hexdigest()
