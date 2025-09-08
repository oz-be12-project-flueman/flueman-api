from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .core.config import settings
from .core.db import engine
from .features.health.router import router as health_router
from .middleware import setup_middlewares


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ DB 연결 확인 완료")
    except Exception as e:
        print("❌ DB 연결 실패:", e)
        raise
    yield
    print("🛑 앱 종료 시점: 연결 정리")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,  # ✅ lifespan 등록
    )
    setup_middlewares(app)

    # 각 기능(feature) 라우터 등록
    app.include_router(health_router)
    # app.include_router(auth_router)  # 추후 추가

    return app


app = create_app()
