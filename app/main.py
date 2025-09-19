from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import os
from typing import TYPE_CHECKING, Any, Protocol

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import TORTOISE_ORM, settings

from .features.auth.router import router as auth_router
from .features.health.router import router as health_router
from .features.inference_requests.router import router as inference_router
from .features.models_registry.router import router as model_router
from .features.users.router import router as user_router
from .middleware import setup_middlewares

# ── 여기부터 추가/변경 ─────────────────────────────────────────────
if TYPE_CHECKING:

    class _TortoiseProto(Protocol):
        async def init(self, *, config: dict[str, Any]) -> None: ...
        async def generate_schemas(self) -> None: ...
        async def close_connections(self) -> None: ...

    Tortoise: _TortoiseProto  # 타입 전용 선언(런타임 바인딩 아님)
else:
    from tortoise import Tortoise  # 런타임에만 임포트 (mypy는 건드리지 않음)
# ──────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
# Lifespan: 앱 시작/종료 훅 (필요하면 DB 헬스체크 로직 추가 가능)
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    attempts = int(os.getenv("DB_CONNECT_RETRY", "10"))
    delay = float(os.getenv("DB_CONNECT_DELAY", "1.0"))
    generate_schemas = os.getenv("DB_GENERATE_SCHEMAS", "true").lower() == "true"

    for i in range(1, attempts + 1):
        try:
            await Tortoise.init(config=dict(TORTOISE_ORM))
            if generate_schemas:
                await Tortoise.generate_schemas()
            print("✅ DB 연결 및 초기화 성공")

            break
        except Exception:
            if i == attempts:
                print(f"❌ DB 연결 실패: {attempts}회 시도 후 중단")
                break
            print(f"⏳ DB 연결 재시도 {i}/{attempts}…")
            await asyncio.sleep(delay)

    yield

    await Tortoise.close_connections()
    print("👋 DB 연결 종료")


# ─────────────────────────────────────────────────────────────
# OpenAPI 스키마 커스터마이즈 (Bearer + Cookie 보안 스키마)
# ─────────────────────────────────────────────────────────────
def build_openapi(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:  # 캐시 사용
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})

    # Bearer (JWT)
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Cookie (access_token)
    security_schemes["CookieAuth"] = {
        "type": "apiKey",
        "in": "cookie",
        "name": "access_token",
    }

    # 전역 보안 요구사항: Bearer 또는 Cookie 중 하나면 OK
    schema["security"] = [
        {"BearerAuth": []},
        {"CookieAuth": []},
    ]

    app.openapi_schema = schema
    return schema


# ─────────────────────────────────────────────────────────────
# 앱 생성
# ─────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    # 공통 미들웨어
    setup_middlewares(app)

    # CORS: settings.CORS_ORIGINS + 환경변수 병합
    extra_origins_env = os.getenv("CORS_ORIGINS", "")
    extra_origins: list[str] = [o.strip() for o in extra_origins_env.split(",") if o.strip()]
    allow_origins: list[str] = [*settings.CORS_ORIGINS, *extra_origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(model_router)
    app.include_router(inference_router)

    # OpenAPI 보안 스키마 주입 (메서드 재할당은 허용)
    app.openapi = lambda: build_openapi(app)  # type: ignore[method-assign]

    return app


app = create_app()


# 기본 엔드포인트
@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Flueman API 서버가 동작 중입니다."}


# 로컬 실행 (uvicorn app.main:app --reload)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )
