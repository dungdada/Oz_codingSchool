# AI Health Web Assignment

## 프로젝트 과정 총 정리

흉부 X-Ray AI 진단 서비스를 5명이 협업하여 만들면서, 각 단계를 어떻게 진행했는지 되돌아봅니다.

### 1. Team Rule 정의

프로젝트 초반에 팀 규칙 문서(`docs/1일차_team_rules.md`)를 만들어 회의 방식, 커뮤니케이션 규칙(진행 상황·막힌 부분·다음 작업 공유), 코드 컨벤션의 기준을 세웠습니다. 이 규칙은 프로젝트가 진행되면서 실제 상황에 맞게 계속 갱신되었습니다. 예를 들어 여러 팀원이 같은 파일(`app/main.py`, `pyproject.toml`)을 동시에 수정하면서 merge 충돌이 반복되자, "각자 PR에는 해당 파일 수정을 포함하지 않고 PR 코멘트로 반영 요청 문구를 남긴다"는 규칙을 새로 정해 충돌을 줄였습니다.

### 2. 사용자 요구사항 정의

운영진이 제공한 요구사항 정의서(회원, 환자, 진료기록, AI 예측)를 각 팀원이 맡은 파트별로 꼼꼼히 읽고, 요구사항 ID(REQ-USER-001 등) 단위로 구현 범위를 명확히 했습니다. 요구사항 문서의 표기(예: 부서 `RESEARCH`/`MEDICAL`/`DEVELOPMENT`, 성별 `M`/`F`)와 실제 DB 모델의 enum 값(`developer`/`medical team`/`researcher`, `male`/`female`)이 다른 경우가 있어, 이런 불일치는 발견 즉시 팀에 공유하고 실제 모델 값을 기준으로 통일했습니다.

### 3. API 명세서 작성

담당 기능별로 API 명세서를 정해진 팀 포맷(API 개요/요청/응답 성공·실패/비고)에 맞춰 작성한 뒤 Notion에 업로드하고, 조장이 전체를 취합해 `docs/N일차_..._API_설계.md` 파일로 만들어 `main`에 병합하는 흐름으로 진행했습니다. 팀원 이탈 등으로 담당이 재배분되는 경우, 새로 맡은 부분의 명세서를 추가로 작성해 기존 문서에 반영했습니다.

### 4. Git & GitHub Branch 전략 구성

`features/기능이름`, `docs/문서이름`, `fix/버그이름`, `docker/작업이름` 형태로 브랜치를 나누고, PR에 3명 이상(또는 배분표에 따라 지정된 리뷰어)의 승인을 받은 뒤 `main`에 merge하는 전략을 사용했습니다. 여러 팀원이 병렬로 작업하면서 브랜치 간 충돌, 존재하지 않는 파일을 import하는 문제 등이 반복적으로 발생했는데, 그때마다 원인을 함께 찾아 정리하며 브랜치 전략을 다듬어갔습니다.

### 5. 프로젝트 세팅

FastAPI + SQLAlchemy(비동기) + MySQL 조합으로 프로젝트를 구성했고, `uv`로 패키지를 관리했습니다. 로컬 개발 환경은 Docker Desktop(WSL2) + `docker-compose`(MySQL, 이후 Redis 추가)로 세팅했습니다. 개발 초기에는 Docker/WSL2 설치, MySQL 계정 생성 시 `MYSQL_USER`에 `root`를 쓸 수 없는 문제 등 인프라 설정 자체에서도 여러 시행착오를 겪었습니다.

### 6. API 및 AI 워커 코드 작성 후 Branch 전략을 통한 코드 병합

각자 맡은 API를 브랜치에서 구현하고 PR로 병합했습니다. 로그인(JWT) 기능이 먼저 완성되지 않은 시점에는 팀에서 임시로 `X-User-Role` 헤더 기반 인증 패턴을 합의해서 쓰다가, 실제 JWT 인증이 merge된 뒤 `get_current_user` 기반으로 전체 교체했습니다. AI 폐렴 예측 코드는 팀에서 검증한 EfficientNet 모델을 `worker/` 아래에 배치하고, 이후 아키텍처 개선 단계에서 FastAPI와 완전히 분리된 별도 프로세스로 재구성했습니다.

### 7. 아키텍처 설계 및 적용

AI 추론이 FastAPI와 같은 프로세스에서 동작하면 무거운 연산이 API 서버 전체에 영향을 준다는 문제를 인식하고, Redis 기반 Event-Driven Architecture를 설계했습니다(`docs/9일차_동시성문제_해결을위한_아키텍처설계.md`). Redis List·Pub/Sub·Stream을 비교해 "작업 큐는 Stream+Consumer Group, 결과 반환은 Pub/Sub" 구조를 택했고, Excalidraw로 도식화한 뒤 실제 코드(`app/core/redis_client.py`, `worker/redis_client.py`, `worker/main.py`)로 구현했습니다. 동시 요청 중복 방지(Redis 락)와 워커 비정상 종료 시 복구(XAUTOCLAIM)도 함께 구현했습니다.

### 8. 도커 인프라 관련 파일 작성

`app/Dockerfile`을 멀티스테이지로 작성해 FastAPI 이미지를 구성했고, AI 워커는 `pyproject.toml`을 app/ai 의존성으로 분리해 별도의 `worker/pyproject.toml` + `worker/Dockerfile`로 완전히 독립된 이미지를 만들었습니다. 이를 통해 FastAPI 이미지에서 torch 등 무거운 AI 의존성을 제거해 경량화했습니다. `docker-compose.yml`에 `mysql`, `redis`, `fastapi`, `ai-worker` 4개 서비스를 정의하고, 로컬에서 실제로 4개 컨테이너를 함께 띄워 회원가입부터 AI 예측까지 전체 플로우를 컨테이너 단위로 검증했습니다.

### 9. AWS 배포

*(진행 예정)*

### 10. QA 진행

*(진행 예정)*

## 배운 점

- 팀 규칙이나 브랜치 전략은 한 번 정하고 끝이 아니라, 실제로 작업하면서 부딪히는 문제(파일 충돌, enum 값 불일치, 팀원 이탈에 따른 재배분 등)에 맞춰 계속 다듬어가는 것이 중요했습니다.
- 로컬 개발 환경에서 여러 프로세스(FastAPI, AI 워커, Redis, MySQL)를 동시에 운용하다 보면 겉보기엔 코드 문제 같아도 실제로는 인프라(포트 충돌, 소켓 타임아웃, 컨테이너 미기동)가 원인인 경우가 많아, 문제 발생 시 코드와 인프라 양쪽을 모두 점검하는 습관을 갖게 되었습니다.
- 요구사항 문서와 실제 구현(DB 모델, enum 값 등) 사이의 불일치는 초기에 발견해서 팀에 공유할수록 후속 작업의 재작업 비용을 줄일 수 있었습니다.

---

## X-ray 폐렴 분석

진료기록에 저장된 X-ray는 다음 API로 분석합니다.

```http
POST /api/v1/medical-records/{record_id}/analysis
Authorization: Bearer <access-token>
```

모델은 `app/ml/final_seed42_best8_full_model.pth`의 2-class EfficientNet을
CPU에서 지연 로드합니다. 현재 추론 설정은 224×224 RGB, ImageNet 정규화,
class index `1`을 폐렴으로 간주하며 임계값은 `0.5`입니다. 학습 당시 클래스
순서나 전처리가 다르면 `.env`의 `AI_PNEUMONIA_CLASS_INDEX`,
`AI_IMAGE_SIZE`, `AI_DECISION_THRESHOLD`를 맞춰야 합니다.

전체 모델 pickle은 임의 코드 실행 위험이 있으므로 저장소에 포함된 검증된
체크포인트 외의 `.pth` 파일로 교체하지 마세요.

## 개발 관리자 계정

DB 마이그레이션 후 개발 관리자 시드를 실행합니다.

```bash
uv run alembic upgrade head
uv run python scripts/seed_admin.py
```

기본 개발 계정:

```text
이메일: admin@example.com
비밀번호: Admin1234!
```

기존에 같은 이메일이 있으면 비밀번호와 역할을 개발 관리자 값으로 갱신합니다.
이 스크립트는 `APP_ENV=production`에서는 실행되지 않습니다. 실제 운영 환경에서는
기본 비밀번호를 사용하지 마세요.

## Alembic Migration Guide

이 프로젝트는 데이터베이스 마이그레이션을 위해 Alembic을 사용합니다.

### 1. 마이그레이션 파일 생성 (자동 생성)
모델(`app/models/`)이 변경된 경우 다음 명령어를 실행하여 마이그레이션 파일을 생성합니다.
```bash
uv run alembic revision --autogenerate -m "변경 내용 설명"
```

### 2. 데이터베이스에 반영
생성된 마이그레이션을 데이터베이스에 적용하려면 다음 명령어를 실행합니다.
```bash
uv run alembic upgrade head
```

### 3. 이전 상태로 되돌리기 (Rollback)
마지막 마이그레이션을 취소하려면 다음 명령어를 실행합니다.
```bash
uv run alembic downgrade -1
```
