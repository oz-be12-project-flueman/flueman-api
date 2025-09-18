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
COPY . .

## 스크립트 복사 및 권한 부여
EXPOSE 8000
COPY scripts/entrypoint.dev.sh /usr/local/bin/entrypoint.dev.sh
RUN chmod +x /usr/local/bin/entrypoint.dev.sh


CMD ["/usr/local/bin/entrypoint.dev.sh"]

############################
# prod 이미지 (런타임만)
############################
# FROM deps AS prod
# COPY . .

# EXPOSE 8000
