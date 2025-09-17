############################
# base
############################
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl ca-certificates build-essential gcc \
  && rm -rf /var/lib/apt/lists/*

# uv 설치 (전역 경로에 배치)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
  mv /root/.local/bin/uv /usr/local/bin/uv

############################
# deps layer (캐시)
############################
FROM base AS deps
COPY pyproject.toml uv.lock ./

############################
# dev 이미지 (dev 의존성 포함, reload)
############################
FROM deps AS dev
RUN uv sync --frozen
COPY . .

## 스크립트 복사 및 권한 부여
EXPOSE 8000
COPY scripts/entrypoint.dev.sh /usr/local/bin/entrypoint.dev.sh
RUN chmod +x /usr/local/bin/entrypoint.dev.sh
# COPY scripts/entrypoint.dev.sh /app/scripts/entrypoint.dev.sh
# RUN chmod +x /app/scripts/entrypoint.dev.sh

# 비루트
# RUN useradd -m app && chown -R app:app /app
# USER app

# 개발 시 핫리로드
#ENTRYPOINT ["sh","-lc"]
# CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD ["/usr/local/bin/entrypoint.dev.sh"]
# CMD ["/app/scripts/entrypoint.dev.sh"]
############################
# prod 이미지 (런타임만)
############################
# FROM deps AS prod
# RUN uv sync --frozen --no-dev
# COPY . .
# RUN useradd -m app && chown -R app:app /app
# USER app
# EXPOSE 8000
# HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
#   CMD curl -fsS http://127.0.0.1:8000/ || exit 1
# CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
