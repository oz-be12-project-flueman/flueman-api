from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .core.config import settings


def setup_middlewares(app: FastAPI) -> None:
    origins = settings.CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if isinstance(origins, list) else [origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
