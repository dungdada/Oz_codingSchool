# 환자 관리 API 명세서

## 1. 공통 사항

- Base URL: `/api/v1`
- 인증 방식: `Authorization: Bearer {access_token}`
- 기본 데이터 형식: `application/json`
- 진료기록 등록은 `multipart/form-data`를 사용한다.
- `PENDING` 권한 사용자는 마이페이지 외 서비스에 접근할 수 없다.
- 환자 등록·수정·삭제 및 진료기록 등록은 의료 실무진 권한이 필요하다.
- 모든 API는 비기능 요구사항에 따라 최대 3초 이내에 응답해야 한다.

## 2. API 목록

| Method | 기능 | Endpoint | 인증 |
| --- | --- | --- | --- |
| `POST` | 환자 등록 | `/patients` | 의료 실무진 |
| `GET` | 환자 목록 조회 | `/patients` | 사용자 |
| `GET` | 환자 상세 조회 | `/patients/{patient_id}` | 사용자 |
| `PUT` | 환자 정보 수정 | `/patients/{patient_id}` | 의료 실무진 |
| `DELETE` | 환자 정보 삭제 | `/patients/{patient_id}` | 의료 실무진 |
| `POST` | 진료기록 등록 | `/medical-records` | 의료 실무진 |
| `GET` | 환자별 진료기록 목록 조회 | `/patients/{patient_id}/medical-records` | 사용자 |
| `GET` | 진료기록 상세 조회 | `/medical-records/{medical_record_id}` | 사용자 |

---

## 3. API 상세

### 3.1 환자 등록

`POST /api/v1/patients`

신규 환자 정보를 등록한다.

#### 요청

```json
{
  "name": "김환자",
  "age": 34,
  "gender": "male",
  "phone_number": "010-1234-5678"
}
```

| 필드 | 타입 | 필수 | 조건 |
| --- | --- | --- | --- |
| name | string | Y | 환자 이름 |
| age | integer | Y | 환자 나이 |
| gender | string | Y | `male`, `female` |
| phone_number | string | Y | `010-XXXX-XXXX` 형식 |

#### 성공 응답 — `201 Created`

```json
{
  "id": 1,
  "name": "김환자",
  "age": 34,
  "gender": "male",
  "phone_number": "010-1234-5678",
  "created_at": "2026-07-21T09:00:00",
  "updated_at": "2026-07-21T09:00:00"
}
```

- `401`: 인증 실패
- `403`: 환자 등록 권한 없음
- `422`: 필수값 누락 또는 입력 형식 오류

> 의료 실무진 권한을 가진 사용자만 등록할 수 있다.

### 3.2 환자 목록 조회

`GET /api/v1/patients`

환자 이름, 성별 및 나이 범위를 기준으로 환자 목록을 조회한다.

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| name | string | N | 없음 | 환자 이름 부분 검색 |
| gender | string | N | 없음 | `male`, `female` |
| min_age | integer | N | 없음 | 최소 나이, 0 이상 |
| max_age | integer | N | 없음 | 최대 나이, 0 이상 |
| offset | integer | N | 0 | 건너뛸 데이터 수 |
| limit | integer | N | 20 | 조회 건수, 1~100 |

#### 성공 응답 — `200 OK`

```json
[
  {
    "id": 15,
    "name": "김환자",
    "age": 45,
    "gender": "female",
    "phone_number": "010-1234-5678",
    "created_at": "2026-07-20T15:30:10",
    "updated_at": "2026-07-20T15:30:10"
  }
]
```

목록이 없으면 빈 배열 `[]`을 반환한다.

- `400`: `min_age`가 `max_age`보다 큼
- `401`: 인증 실패
- `422`: 쿼리 파라미터 형식 또는 범위 오류

### 3.3 환자 상세 조회

`GET /api/v1/patients/{patient_id}`

#### Path Parameter

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 조회할 환자의 고유 ID |

#### 성공 응답 — `200 OK`

```json
{
  "id": 1,
  "name": "김환자",
  "age": 34,
  "gender": "male",
  "phone_number": "010-1234-5678",
  "created_at": "2026-07-21T09:00:00",
  "updated_at": "2026-07-21T09:00:00"
}
```

- `401`: 인증 실패
- `404`: 환자 정보 없음
- `422`: `patient_id` 형식 오류

> 삭제된 환자는 조회되지 않으며 `404 Not Found`를 반환한다.

### 3.4 환자 정보 수정

`PUT /api/v1/patients/{patient_id}`

의료 실무진이 환자 정보를 전체 수정한다.

#### 요청

```json
{
  "name": "김환자",
  "age": 35,
  "gender": "male",
  "phone_number": "010-9876-5432"
}
```

등록 API와 동일하게 모든 필드를 필수로 전달한다.

#### 성공 응답 — `200 OK`

```json
{
  "id": 1,
  "name": "김환자",
  "age": 35,
  "gender": "male",
  "phone_number": "010-9876-5432",
  "created_at": "2026-07-21T09:00:00",
  "updated_at": "2026-07-22T14:30:00"
}
```

- `401`: 인증 실패
- `403`: 환자 수정 권한 없음
- `404`: 환자 정보 없음
- `422`: 필수값 누락 또는 입력 형식 오류

> 수정 시 `created_at`은 유지하고 `updated_at`만 변경한다.

### 3.5 환자 정보 삭제

`DELETE /api/v1/patients/{patient_id}`

환자와 연결된 진료기록 및 의료 이미지를 함께 삭제한다.

#### 성공 응답 — `200 OK`

```json
{
  "detail": "환자 정보와 연관된 진료기록 및 이미지가 삭제되었습니다."
}
```

- `401`: 인증 실패
- `403`: 환자 삭제 권한 없음
- `404`: 환자 정보 없음

> 환자, 진료기록, 이미지 삭제는 하나의 트랜잭션으로 처리하고 실패하면 전체 작업을 롤백한다.

### 3.6 진료기록 등록

`POST /api/v1/medical-records`

Content-Type: `multipart/form-data`

#### 요청 필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| patient_id | integer | Y | 대상 환자 ID |
| chart_number | string | Y | 진료 차트 번호 |
| symptom | string | Y | 진료 증상 |
| xray_image | file | Y | JPG, JPEG, PNG 이미지 |

#### 요청 예시

```text
patient_id=15
chart_number=CH-20260720-001
symptom=지속적인 기침과 발열 증상
xray_image=chest_xray.png
```

#### 성공 응답 — `201 Created`

```json
{
  "medical_record_id": 101,
  "patient_id": 15,
  "chart_number": "CH-20260720-001",
  "symptom": "지속적인 기침과 발열 증상",
  "xray_image_url": "/uploads/xray/chest_xray.png",
  "created_at": "2026-07-20T15:30:10"
}
```

- `401`: 인증 실패
- `403`: 의료 실무진 권한 없음
- `404`: 대상 환자 없음
- `415`: 지원하지 않는 이미지 형식
- `422`: 필수값 누락 또는 입력 형식 오류

> 업로드된 이미지는 서버 로컬 저장소에 저장한다. 현재 권한 확인에 임시 `X-User-Role` 헤더를 사용하며 JWT 인증 구현 후 교체한다.

### 3.7 환자별 진료기록 목록 조회

`GET /api/v1/patients/{patient_id}/medical-records`

#### 성공 응답 — `200 OK`

```json
{
  "medical_records": [
    {
      "medical_record_id": 1,
      "chart_number": "CHART-2026-0001",
      "symptom": "기침과 발열 증상이 있으며 호흡 시 가슴 통증을 호소함",
      "created_at": "2026-07-20T14:30:00"
    }
  ]
}
```

- 진료기록이 없으면 `{"medical_records": []}`을 반환한다.
- 생성일시 기준 최신순으로 정렬한다.
- 증상이 100자를 초과하면 목록에서 100자까지만 표시하고 `...`을 붙인다.
- 원본 증상 데이터는 변경하지 않는다.

실패 응답:

- `401`: 인증 실패
- `403`: 조회 권한 없음
- `404`: 환자 정보 없음
- `422`: `patient_id` 형식 오류
- `500`: 서버 오류

### 3.8 진료기록 상세 조회

`GET /api/v1/medical-records/{medical_record_id}`

#### 성공 응답 — `200 OK`

```json
{
  "medical_record_id": 1,
  "patient_id": 3,
  "chart_number": "CHART-2026-0001",
  "symptom": "환자는 3일 전부터 기침과 고열 증상이 지속되었으며 호흡 시 가슴 통증과 호흡곤란을 호소하여 흉부 X-Ray 촬영을 진행하였다.",
  "xray_image_url": "/uploads/xrays/medical_record_1.png",
  "created_at": "2026-07-20T14:30:00"
}
```

- `401`: 인증 실패
- `403`: 조회 권한 없음
- `404`: 진료기록 없음
- `422`: `medical_record_id` 형식 오류
- `500`: 서버 오류

> 상세 응답에는 축약하지 않은 증상 전체 내용과 X-Ray 이미지 경로를 반환한다.
