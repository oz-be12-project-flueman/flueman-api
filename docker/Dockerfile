FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

# uv 설치 (전역 경로에 배치)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
  mv /root/.local/bin/uv /usr/local/bin/uv

# 앱 디렉터리
WORKDIR /app

# ─────────────────────────────────────────────────────────────
# 의존성 설치 단계 (캐시 최적화)
# uv.lock / pyproject.toml만 먼저 복사 → 의존성 레이어 캐시 활용
# ─────────────────────────────────────────────────────────────
COPY pyproject.toml uv.lock ./
# 프로덕션: dev 의존성 제외
RUN uv sync --frozen --no-dev

# ─────────────────────────────────────────────────────────────
# 앱 소스 복사
# ─────────────────────────────────────────────────────────────
COPY . .

# 권한/사용자 전환
RUN useradd -m app && chown -R app:app /app
USER app
# 포트 노출
EXPOSE 8000

# ─────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────
# 주: 환경변수 HOST/PORT로 오버라이드 가능 (uvicorn 인자 그대로 연결)
# CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
