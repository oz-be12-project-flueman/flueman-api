from __future__ import annotations

from dataclasses import dataclass
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────
def _getenv_int(name: str, default: int) -> int:
    v = os.getenv(name)
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default


def _getenv_float(name: str, default: float) -> float:
    v = os.getenv(name)
    try:
        return float(v) if v is not None else default
    except ValueError:
        return default


# ─────────────────────────────────────────────────────────────
# (선택) Tortoise ORM 설정: 사용한다면 import 해서 쓰고,
# 사용하지 않으면 이 블록은 무시해도 됨.
# ─────────────────────────────────────────────────────────────
TORTOISE_ORM = {
    "connections": {
        "default": os.getenv("TORTOISE_DSN"),
    },
    "apps": {
        "models": {
            "models": [
                "app.features.users.models",
                "app.features.auth.models",
                "app.features.models_registry.models",
                # "app.features.datasets.models",
                # "app.features.feedback.models",
                # "app.features.health.models",
                # "app.features.inference.models",
                # "app.features.monitoring.models",
                # "app.features.preproc_jobs.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}


# ─────────────────────────────────────────────────────────────
# (옵션) 외부 AI 설정을 dataclass로 노출하고 싶을 때 사용
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class AISettings:
    google_api_key: str | None
    model_name: str
    max_tokens: int
    temperature: float

    @property
    def enabled(self) -> bool:
        return bool(self.google_api_key)


def load_ai_settings() -> AISettings:
    return AISettings(
        google_api_key=os.getenv("GOOGLE_API_KEY") or None,
        model_name=os.getenv("AI_MODEL_NAME", "gemini-2.5-flash"),
        max_tokens=_getenv_int("AI_MAX_TOKENS", 1000),
        temperature=_getenv_float("AI_TEMPERATURE", 0.7),
    )


# ─────────────────────────────────────────────────────────────
# Pydantic Settings: 모든 값은 .env에서만 로드(기본값 없음)
# ─────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    """
    모든 설정은 .env에서만 읽는다.
    - 기본값 없음(필수): 누락 시 ValidationError
    - 초과 키 forbid, 대소문자 구분
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=True,
    )

    # ─ App ─
    APP_NAME: str = Field(..., alias="APP_NAME")
    APP_ENV: str = Field(..., alias="APP_ENV")
    APP_DEBUG: bool = Field(..., alias="APP_DEBUG")
    APP_HOST: str = Field(..., alias="APP_HOST")
    APP_PORT: int = Field(..., alias="APP_PORT")
    CORS_ORIGINS: list[str] = Field(..., alias="CORS_ORIGINS")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: object) -> object:
        """
        'a,b' 또는 '["a","b"]' 모두 허용.
        JSON 리터럴('[]')은 그대로 두고, 콤마 구분 문자열은 split.
        """
        if isinstance(v, str):
            s = v.strip()
            if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
                return s
            return [item.strip() for item in s.split(",") if item.strip()]
        return v

    # ─ Security (JWT) ─
    JWT_SECRET: str = Field(..., alias="JWT_SECRET")
    JWT_ALGORITHM: str = Field(..., alias="JWT_ALGORITHM")
    JWT_ACCESS_EXPIRES_MIN: int = Field(..., alias="JWT_ACCESS_EXPIRES_MIN")
    JWT_REFRESH_HASH_PEPPER: str = Field(..., alias="JWT_REFRESH_HASH_PEPPER")

    # ─ DB (MySQL) ─
    DB_ROOT_PASSWORD: str = Field(..., alias="DB_ROOT_PASSWORD")
    DB_USER: str = Field(..., alias="DB_USER")
    DB_PASSWORD: str = Field(..., alias="DB_PASSWORD")
    DB_HOST: str = Field(..., alias="DB_HOST")
    DB_PORT: int = Field(..., alias="DB_PORT")
    DB_NAME: str = Field(..., alias="DB_NAME")
    TORTOISE_DSN: str = Field(..., alias="TORTOISE_DSN")

    @property
    def database_url(self) -> str:
        """
        예) mysql+aiomysql://user:pass@host:3306/db?charset=utf8mb4
        """
        return (
            "mysql+aiomysql://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )

    # ─ Cloudinary ─
    CLOUDINARY_CLOUD_NAME: str = Field(..., alias="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = Field(..., alias="CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = Field(..., alias="CLOUDINARY_API_SECRET")

    # ─ AWS ─
    AWS_REGION: str = Field(..., alias="AWS_REGION")

    # ─ AI (Google / Gemini) ─
    GOOGLE_API_KEY: str = Field(..., alias="GOOGLE_API_KEY")
    AI_MODEL_NAME: str = Field(..., alias="AI_MODEL_NAME")
    AI_MAX_TOKENS: int = Field(..., alias="AI_MAX_TOKENS")
    AI_TEMPERATURE: float = Field(..., alias="AI_TEMPERATURE")


def load_settings() -> Settings:
    # BaseSettings는 런타임에 .env로 채워지지만, mypy는 인자 미제공을 오류로 본다.
    # 호출 지점 한정 억제로 해결.
    return Settings()  # type: ignore[call-arg]


settings: Settings = load_settings()
