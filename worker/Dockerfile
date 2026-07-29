# syntax=docker/dockerfile:1
#
# AI 워커 전용 이미지. FastAPI 앱(app/Dockerfile)과 완전히 분리되어 있고,
# torch/timm 등 AI 추론에 필요한 의존성만 설치한다. (worker/pyproject.toml 참고)

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/.venv \
    PATH="/.venv/bin:$PATH"

# uv 설치 (버전 고정)
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

WORKDIR /

# 워커 전용 의존성만 설치 (fastapi, sqlalchemy, argon2 등은 포함되지 않음 -> 이미지 경량화)
COPY worker/pyproject.toml worker/uv.lock ./worker/
RUN cd worker && uv sync --frozen --no-install-project

# 워커 코드와, 워커가 참조하는 모델 파일 복사
COPY worker ./worker

CMD ["python", "-m", "worker.main"]
