# app/core/config.py

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env 로딩 + 초과 키 금지
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=True,  # 대소문자 구분
    )

    # ─────────────────────────────
    # App
    # ─────────────────────────────
    APP_NAME: str = Field(..., alias="APP_NAME")
    APP_ENV: str = Field("local", alias="APP_ENV")
    APP_DEBUG: bool = Field(False, alias="APP_DEBUG")
    APP_HOST: str = Field("0.0.0.0", alias="APP_HOST")
    APP_PORT: int = Field(8000, alias="APP_PORT")
    CORS_ORIGINS: list[str] = Field(
        default_factory=list,
        alias="CORS_ORIGINS",
    )  # '["...","..."]' 형태를 자동 파싱

    # ─────────────────────────────
    # Security (JWT)
    # ─────────────────────────────
    JWT_SECRET: str = Field(..., alias="JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", alias="JWT_ALGORITHM")
    JWT_ACCESS_EXPIRES_MIN: int = Field(30, alias="JWT_ACCESS_EXPIRES_MIN")

    # ─────────────────────────────
    # DB (MySQL)
    # ─────────────────────────────
    DB_USER: str = Field(..., alias="DB_USER")
    DB_PASSWORD: str = Field(..., alias="DB_PASSWORD")
    DB_HOST: str = Field(..., alias="DB_HOST")
    DB_PORT: int = Field(3306, alias="DB_PORT")
    DB_NAME: str = Field(..., alias="DB_NAME")

    # 필요하면 아래처럼 DSN 프로퍼티 만들어서 사용
    @property
    def database_url(self) -> str:
        # SQLAlchemy 형태 예: mysql+pymysql://user:pwd@host:port/dbname?charset=utf8mb4
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    # ─────────────────────────────
    # Cloudinary
    # ─────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = Field(..., alias="CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str = Field(..., alias="CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str = Field(..., alias="CLOUDINARY_API_SECRET")

    # ─────────────────────────────
    # AWS
    # ─────────────────────────────
    AWS_REGION: str = Field("ap-northeast-2", alias="AWS_REGION")

    # ─────────────────────────────
    # AI (Google / Gemini)
    # ─────────────────────────────
    GOOGLE_API_KEY: str = Field(..., alias="GOOGLE_API_KEY")
    AI_MODEL_NAME: str = Field("gemini-2.5-flash", alias="AI_MODEL_NAME")
    AI_MAX_TOKENS: int = Field(1000, alias="AI_MAX_TOKENS")
    AI_TEMPERATURE: float = Field(0.7, alias="AI_TEMPERATURE")


settings = Settings()
