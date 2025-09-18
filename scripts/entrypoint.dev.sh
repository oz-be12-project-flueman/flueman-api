#!/bin/sh
set -e

# (필요시) 마이그레이션 수행 (aerich 등)
# aerich 초기화 (한 번만)
if [ ! -f "migrations/aerich.ini" ]; then
  uv run aerich init -t app.core.config.TORTOISE_ORM
fi

if [ ! -d "migrations/models" ] || [ -z "$(ls -A migrations/models 2>/dev/null || true)" ]; then
  uv run aerich init-db
fi

uv run aerich migrate || true
uv run aerich upgrade || true

# FastAPI 앱 실행 (개발용 --reload 포함)
# app.main:app 에서 app.main은 위치를, :app은 main.py의 FastAPI 인스턴스 이름
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
