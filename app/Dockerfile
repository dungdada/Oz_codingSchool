# syntax=docker/dockerfile:1

# ---------- 1. builder: 의존성 빌드 ----------
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/.venv

# asyncmy(MySQL 드라이버), argon2-cffi 등 C 확장 빌드에 필요한 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

WORKDIR /

# 의존성 정의 파일만 먼저 복사 (레이어 캐시 활용: 코드만 바뀌면 재설치 안 함)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ---------- 2. runtime: 실행 전용 경량 이미지 ----------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/.venv/bin:$PATH"

# 런타임에 필요한 MySQL 클라이언트 공유 라이브러리 (빌드 도구는 제외해 이미지 경량화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# builder 스테이지에서 만든 가상환경만 그대로 가져옴 (/app 볼륨 마운트와 겹치지 않는 위치)
COPY --from=builder /.venv /.venv

WORKDIR /

# 애플리케이션 코드 복사
# (docker-compose 로컬 개발환경에서는 ./app:/app 볼륨 마운트로 덮어써지지만,
#  볼륨 마운트가 없는 환경(예: 운영 배포)에서도 이미지 자체로 실행 가능하도록 포함)
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY worker ./worker
COPY static ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
