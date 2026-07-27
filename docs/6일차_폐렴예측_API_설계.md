# AI 폐렴 예측 API 및 비기능 요구사항 명세서

## 1. 요구사항 범위

| ID | 구분 | 요구사항 |
| --- | --- | --- |
| REQ-PRED-001 | 기능 | 진료기록의 X-Ray 이미지를 이용한 폐렴 예측 수행 및 결과 반환 |
| REQ-PRED-002 | 기능 | 진료기록별 AI 폐렴 예측 결과 목록 조회 |
| NFR-PRED-001 | 비기능 | Recall 최소 0.90, Accuracy 0.80 이상을 목표로 모델 평가 |
| NFR-PRED-002 | 비기능 | 모든 예측 API는 3초 이내 응답 |

## 2. 공통 사항

- Base URL: `/api/v1`
- 인증 방식: `Authorization: Bearer {access_token}`
- 기본 데이터 형식: `application/json`
- 접근 권한: `staff`, `admin`
- `pending` 사용자는 접근할 수 없다.
- 예측에는 해당 진료기록에 저장된 `xray_image_url`의 이미지를 사용한다.
- 같은 진료기록과 같은 모델의 결과가 이미 존재하면 재추론하지 않고 저장된 결과를 반환한다.
- 응답 시간은 캐시된 결과와 신규 추론 모두 최대 3초 이내를 목표로 한다.

## 3. API 목록

| ID | Method | 기능 | Endpoint | 인증 |
| --- | --- | --- | --- | --- |
| REQ-PRED-001 | `POST` | 폐렴 예측 수행 또는 저장 결과 반환 | `/medical-records/{medical_record_id}/predictions` | 스태프·관리자 |
| REQ-PRED-002 | `GET` | 진료기록별 예측 결과 목록 조회 | `/medical-records/{medical_record_id}/predictions` | 스태프·관리자 |

---

## 4. API 상세

### 4.1 AI 폐렴 예측

`POST /api/v1/medical-records/{medical_record_id}/predictions`

진료기록에 저장된 흉부 X-Ray 이미지로 폐렴 예측을 수행한다. 동일한 진료기록과 모델 조합의 결과가 이미 저장되어 있으면 AI 추론을 다시 실행하지 않고 기존 결과를 반환한다.

#### Headers

| Key | 값 | 필수 | 설명 |
| --- | --- | --- | --- |
| Authorization | `Bearer {access_token}` | Y | JWT Access Token |

#### Path Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| medical_record_id | integer | Y | 예측 대상 진료기록 ID |

#### 요청

```json
{
  "ai_model": "pneumonia-resnet50-v1"
}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| ai_model | string | N | 사용할 모델 식별자. 생략 시 서버 기본 모델 사용 |

#### 성공 응답 — `200 OK`

```json
{
  "id": 12,
  "medical_record_id": 101,
  "is_pneumonia": true,
  "confidence": 0.94,
  "heatmap_image_url": "/media/heatmaps/analysis_12.png",
  "ai_model": "pneumonia-resnet50-v1",
  "created_at": "2026-07-24T14:30:00",
  "cached": false
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | integer | 예측 결과 고유 ID |
| medical_record_id | integer | 진료기록 ID |
| is_pneumonia | boolean | 폐렴 예측 여부 |
| confidence | number | 예측 신뢰도, `0.0` 이상 `1.0` 이하 |
| heatmap_image_url | string \| null | 히트맵 이미지 URL, 생성하지 않으면 `null` |
| ai_model | string | 예측에 사용한 모델 |
| created_at | datetime | 최초 예측 수행 일시 |
| cached | boolean | 저장된 결과를 반환했는지 여부 |

저장된 결과를 반환할 때도 `200 OK`를 사용하며 `cached`는 `true`이다.

#### 실패 응답

- `401 Unauthorized`: 인증 정보가 없거나 Access Token이 유효하지 않음
- `403 Forbidden`: 예측 기능 접근 권한 없음
- `404 Not Found`: 진료기록 또는 X-Ray 이미지가 없음
- `422 Unprocessable Entity`: 경로 또는 요청값 형식 오류
- `500 Internal Server Error`: 이미지 로드, AI 추론 또는 결과 저장 실패
- `503 Service Unavailable`: AI 모델을 사용할 수 없음

> 중복 추론 방지를 위해 `(medical_record_id, ai_model)` 조합에 데이터베이스 Unique 제약조건을 두는 것을 권장한다.

### 4.2 AI 폐렴 예측 결과 목록 조회

`GET /api/v1/medical-records/{medical_record_id}/predictions`

특정 진료기록에 저장된 폐렴 예측 결과를 최신순으로 조회한다.

#### Headers

| Key | 값 | 필수 | 설명 |
| --- | --- | --- | --- |
| Authorization | `Bearer {access_token}` | Y | JWT Access Token |

#### Path Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| medical_record_id | integer | Y | 조회할 진료기록 ID |

#### 성공 응답 — `200 OK`

```json
{
  "medical_record_id": 101,
  "xray_image_url": "/media/xray/record_101.png",
  "predictions": [
    {
      "id": 12,
      "is_pneumonia": true,
      "confidence": 0.94,
      "heatmap_image_url": "/media/heatmaps/analysis_12.png",
      "created_at": "2026-07-24T14:30:00",
      "ai_model": "pneumonia-resnet50-v1"
    }
  ]
}
```

예측 결과가 없으면 `predictions`에 빈 배열을 반환한다.

```json
{
  "medical_record_id": 101,
  "xray_image_url": "/media/xray/record_101.png",
  "predictions": []
}
```

#### 실패 응답

- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 조회 권한 없음
- `404 Not Found`: 진료기록 없음
- `422 Unprocessable Entity`: `medical_record_id` 형식 오류
- `500 Internal Server Error`: 서버 오류

## 5. AI 모델 평가 기준

### NFR-PRED-001

| 구분 | 의미 |
| --- | --- |
| TP | 폐렴 환자를 폐렴으로 예측 |
| FP | 정상인을 폐렴으로 예측 |
| FN | 폐렴 환자를 정상으로 예측하며 가장 위험한 오류 |
| TN | 정상인을 정상으로 예측 |

| 평가 지표 | 계산식 | 기준 |
| --- | --- | --- |
| Recall(민감도) | `TP / (TP + FN)` | 최소 `0.90`, 권장 `0.90~0.95` |
| Accuracy(정확도) | `(TP + TN) / 전체 표본 수` | 최소 `0.80`, 권장 `0.80~0.90` |

- 의료 안전상 FN을 줄이는 것을 우선한다.
- 모델 버전별 평가 결과를 분리하여 기록한다.
- 운영 모델은 Recall 최소 기준을 충족한 모델만 사용한다.
- Accuracy는 보조 지표로 활용하며 Recall보다 우선하지 않는다.

## 6. API 성능 기준

### NFR-PRED-002

- 모든 예측 관련 API는 3초 이내에 응답해야 한다.
- 저장된 결과가 있으면 DB 조회만 수행하고 AI 추론은 생략한다.
- 모델은 요청마다 다시 로드하지 않고 애플리케이션 시작 시 한 번 로드하는 것을 권장한다.
- X-Ray 전처리와 추론 시간을 각각 측정할 수 있도록 로그를 남긴다.
- 목록 조회 시 `medical_record_id`, `created_at` 및 `(medical_record_id, ai_model)`에 적절한 인덱스를 사용한다.

## 7. 구현 전 확인사항

- 현재 `AIAnalysis` 모델에는 `heatmap_image_url` 컬럼이 없으므로 선택 기능을 구현하려면 컬럼과 Alembic 마이그레이션을 추가해야 한다.
- 현재 `confidence` 컬럼은 `DECIMAL(5, 2)`이므로 소수 둘째 자리까지만 저장된다. 더 정밀한 값이 필요하면 컬럼 정밀도를 변경한다.
- 모델에 중복 추론 방지를 위한 `(medical_record_id, ai_model)` Unique 제약조건이 아직 없다.
- 요구사항의 `Hitmap`은 일반적으로 사용하는 명칭인 `Heatmap`으로 표기하고 API 필드는 `heatmap_image_url`로 통일한다.
