# AI Health Web Assignment

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
