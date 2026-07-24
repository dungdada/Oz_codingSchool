# 회원 관리 API 명세서

## 1. 공통 사항

- Base URL: `/api/v1`
- 인증 방식: `Authorization: Bearer {access_token}`
- 기본 데이터 형식: `application/json`
- 로그인 요청만 `application/x-www-form-urlencoded`를 사용한다.

## 2. API 목록

| ID | Method | 기능 | Endpoint | 인증 |
| --- | --- | --- | --- | --- |
| REQ-USER-001 | `POST` | 회원가입 | `/users/signup` | - |
| REQ-USER-002 | `POST` | 로그인 | `/users/login` | - |
| NFR-USER-001 | `POST` | Access Token 재발급 | `/users/token/refresh` | Refresh Token Cookie |
| REQ-USER-003 | `POST` | 로그아웃 | `/users/logout` | 사용자 |
| REQ-USER-004 | `GET` | 회원 목록 조회 | `/admin/users` | 관리자 |
| REQ-USER-005 | `PATCH` | 회원 권한 변경 | `/admin/users/role` | 관리자 |
| REQ-USER-006 | `GET` | 마이페이지 조회 | `/users/me` | 사용자 |
| REQ-USER-007 | `PATCH` | 회원 정보 수정 | `/users/me` | 사용자 |
| REQ-USER-008 | `PATCH` | 비밀번호 변경 | `/users/me/password` | 사용자 |
| REQ-USER-009 | `DELETE` | 회원 탈퇴 | `/users/me` | 사용자 |

---

## 3. API 상세

### 3.1 회원가입

`POST /api/v1/users/signup`

신규 회원을 등록한다. 가입 직후 권한은 `PENDING`이다.

#### 요청

```json
{
  "email": "example@example.com",
  "password": "Password1!",
  "name": "박강호",
  "department": "DEVELOPMENT",
  "gender": "M",
  "phone_number": "010-1234-5678"
}
```

| 필드 | 필수 | 조건 |
| --- | --- | --- |
| email | Y | 이메일 형식, 중복 불가 |
| password | Y | 8자 이상, 영문·숫자·특수문자 포함 |
| name | Y | 사용자 이름 |
| department | Y | `RESEARCH`, `MEDICAL`, `DEVELOPMENT` |
| gender | Y | `M`, `F` |
| phone_number | Y | `010-XXXX-XXXX` 형식 |

#### 응답

- `201`: 회원 생성 성공 및 회원 정보 반환
- `409`: 이미 가입된 이메일
- `422`: 입력값 검증 실패

> 비밀번호는 Argon2로 해싱하며 응답에 포함하지 않는다.

### 3.2 로그인

`POST /api/v1/users/login`

이메일과 비밀번호를 검증하고 Access Token을 발급한다.

#### 요청

Content-Type: `application/x-www-form-urlencoded`

```text
username=jihyun@example.com
password=Password1234!
```

#### 성공 응답 — `200 OK`

Response Header:

```http
Set-Cookie: refresh_token={token}; HttpOnly; Path=/api/v1/users; Max-Age=604800; SameSite=Lax
```

Response Body:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

- `401`: 이메일 또는 비밀번호 불일치
- `403`: 비활성화된 사용자
- `422`: 필수값 누락 또는 요청 형식 오류

> 화면에서는 이메일을 입력하지만 요청 필드명은 `username`을 사용한다.
> Refresh Token은 응답 본문이 아닌 HttpOnly Cookie로 전달한다. 프로덕션 HTTPS 환경에서는 Cookie에 `Secure` 옵션을 추가한다.

### 3.3 로그아웃

`POST /api/v1/users/logout`

- 인증: 필요
- 요청 본문: 없음
- 성공: `204 No Content`
- 실패: `401 Unauthorized`

로그아웃 후 클라이언트에 저장된 Access Token을 삭제한다.
서버에 Refresh Token 또는 토큰 식별자를 저장하는 경우 즉시 폐기하고, 응답의 `Set-Cookie`를 통해 Refresh Token Cookie를 만료시킨다.

### 3.4 회원 목록 조회

`GET /api/v1/admin/users`

관리자가 회원 목록을 검색·필터링한다.

#### Query Parameters

| 파라미터 | 필수 | 설명 |
| --- | --- | --- |
| keyword | N | 이름 또는 이메일 검색 |
| department | N | 부서 필터 |
| page | N | 페이지 번호 |
| size | N | 페이지 크기 |

#### 성공 응답 — `200 OK`

```json
{
  "users": [
    {
      "id": 1,
      "email": "example@example.com",
      "name": "김오즈",
      "department": "DEVELOPMENT",
      "gender": "M",
      "phone_number": "010-1234-5678",
      "is_active": true
    }
  ]
}
```

- `401`: 인증 실패
- `403`: 관리자 권한 없음

### 3.5 회원 권한 변경

`PATCH /api/v1/admin/users/role`

관리자가 선택한 회원들의 권한을 일괄 변경한다.

#### 요청

```json
{
  "user_ids": [1, 2, 3],
  "new_role": "staff"
}
```

`new_role`은 `pending`, `staff`, `admin` 중 하나다.

#### 성공 응답 — `200 OK`

```json
{
  "updated_count": 3,
  "users": [
    {
      "id": 1,
      "role": "staff"
    }
  ]
}
```

- `403`: 관리자 권한 없음
- `404`: 존재하지 않는 회원 포함
- `422`: 허용되지 않은 권한값

> 현재 관리자 확인에 임시 `X-User-Role: admin` 헤더를 사용하며, JWT 권한 검증 구현 후 제거한다.

### 3.6 마이페이지 조회

`GET /api/v1/users/me`

로그인한 사용자가 자신의 정보를 조회한다.

#### 성공 응답 — `200 OK`

```json
{
  "id": 1,
  "email": "example@example.com",
  "name": "김오즈",
  "department": "DEVELOPMENT",
  "gender": "M",
  "phone_number": "010-1234-5678",
  "role": "USER",
  "is_active": true
}
```

- `401`: 인증 실패
- `404`: 사용자 없음

### 3.7 회원 정보 수정

`PATCH /api/v1/users/me`

부서와 휴대폰 번호를 부분 수정한다.

#### 요청

```json
{
  "department": "RESEARCH",
  "phone_number": "010-1234-1234"
}
```

두 필드는 선택값이지만 최소 하나는 전달해야 한다. 전달하지 않은 값은 기존 값을 유지한다.

- `200`: 수정 성공
- `401`: 인증 실패
- `422`: 수정할 값이 없거나 형식 오류
- `500`: 서버 오류

### 3.8 비밀번호 변경

`PATCH /api/v1/users/me/password`

현재 비밀번호를 확인한 후 새 비밀번호로 변경한다.

#### 요청

```json
{
  "current_password": "CurrentPassword123!",
  "new_password": "NewPassword123!"
}
```

- `200`: 변경 성공
- `400`: 현재 비밀번호 불일치
- `401`: 인증 실패
- `422`: 필수값 누락 또는 형식 오류
- `500`: 서버 오류

> 새 비밀번호는 8자 이상이며 대문자·소문자·숫자·특수문자를 각각 하나 이상 포함해야 한다.

### 3.9 회원 탈퇴

`DELETE /api/v1/users/me`

- 인증: 필요
- 요청 본문: 없음
- `200`: 탈퇴 성공
- `401`: 인증 실패
- `500`: 서버 오류

성공 후 클라이언트에서 로그아웃 처리한다. 실제 삭제와 소프트 삭제 중 어떤 방식을 사용할지는 팀 정책으로 결정한다.

---

## 4. 비기능 요구사항 (Non-Functional Requirements)

### 4.1 요구사항 범위

| ID | 구분 | 요구사항 |
| --- | --- | --- |
| NFR-USER-001 | 인증·인가 | Access Token과 Refresh Token을 이용한 JWT 인증 |
| NFR-USER-002 | 입력 보안 | 모든 비밀번호 입력값의 기본 마스킹 및 보기 기능 |
| NFR-USER-003 | 성능 | 모든 사용자 API 3초 이내 응답 |

### 4.2 NFR-USER-001 인증 / 인가

#### 4.2.1 정책

- 로그인 성공 시 JWT Access Token과 Refresh Token을 발급한다.
- Access Token 만료 시간은 발급 시점부터 30분이다.
- Refresh Token 만료 시간은 발급 시점부터 7일이다.
- Access Token은 API의 `Authorization` 헤더로 전달한다.
- Refresh Token은 JavaScript에서 접근할 수 없는 HttpOnly Cookie로 전달한다.
- Access Token 만료 시 유효한 Refresh Token으로 Access Token을 재발급한다.
- Refresh Token까지 만료되거나 유효하지 않으면 `401 Unauthorized`를 반환하고 재로그인을 유도한다.
- JWT Payload의 사용자 식별 정보는 `user_id`만 저장한다.
- `exp`, `iat`, `jti`, `token_type` 등 토큰 검증을 위한 표준 메타데이터는 포함할 수 있다.
- 비밀번호, 이메일, 이름, 부서, 성별, 휴대폰 번호, 권한은 JWT Payload에 저장하지 않는다.
- API 인가 시 JWT에 저장된 권한을 신뢰하지 않고, `user_id`로 DB 사용자를 조회하여 현재 권한과 활성 상태를 확인한다.

#### 4.2.2 관련 API

| Method | 기능 | Endpoint | 인증 |
| --- | --- | --- | --- |
| `POST` | 로그인 및 토큰 발급 | `/api/v1/users/login` | 불필요 |
| `POST` | Access Token 재발급 | `/api/v1/users/token/refresh` | Refresh Token Cookie |
| `POST` | 로그아웃 및 Refresh Token 폐기 | `/api/v1/users/logout` | 사용자 |

#### 4.2.3 Access Token 재발급

`POST /api/v1/users/token/refresh`

브라우저가 HttpOnly Cookie를 자동으로 전달하므로 요청 본문에는 Refresh Token을 포함하지 않는다.

성공 응답 — `200 OK`

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Refresh Token Rotation 정책을 적용하는 경우 새로운 Refresh Token을 `Set-Cookie`로 함께 전달하고 기존 토큰은 즉시 폐기한다.

실패 응답 — `401 Unauthorized`

```json
{
  "detail": "리프레시 토큰이 만료되었거나 유효하지 않습니다. 다시 로그인해주세요."
}
```

#### 4.2.4 로그아웃 시 Cookie 삭제

성공 시 `204 No Content`를 반환하고 Refresh Token Cookie를 만료시킨다.

```http
Set-Cookie: refresh_token=; HttpOnly; Path=/api/v1/users; Max-Age=0; SameSite=Lax
```

#### 4.2.5 인증 실패 공통 응답

`401 Unauthorized`

```json
{
  "detail": "로그인이 필요합니다."
}
```

```http
WWW-Authenticate: Bearer
```

`403 Forbidden`

```json
{
  "detail": "이 작업을 수행할 권한이 없습니다."
}
```

`401`은 인증 정보가 없거나 유효하지 않을 때, `403`은 인증된 사용자가 필요한 권한을 갖지 못했을 때 사용한다.

#### 4.2.6 보안 구현 기준

- JWT 서명 키는 소스 코드에 하드코딩하지 않고 환경 변수로 관리한다.
- Refresh Token은 가능하면 원문이 아닌 해시값 또는 `jti`를 서버에 저장한다.
- 회원탈퇴, 비밀번호 변경 및 권한 변경 시 기존 Refresh Token 폐기 정책을 적용한다.
- 비활성 사용자와 삭제된 사용자는 토큰이 남아 있어도 인증할 수 없어야 한다.
- CORS 사용 시 Refresh Token Cookie 전송을 위해 허용 출처를 명시하고 credentials 설정을 적용한다.
- 운영 환경에서는 Cookie에 `HttpOnly`, `Secure`, 적절한 `SameSite` 및 제한된 `Path`를 적용한다.

### 4.3 NFR-USER-002 비밀번호 입력 보안

#### 4.3.1 적용 화면

- 회원가입
- 로그인
- 현재 비밀번호 확인
- 새 비밀번호 및 새 비밀번호 확인

#### 4.3.2 구현 기준

- 기본 입력 타입은 `password`로 설정한다.
- 보기 아이콘을 누른 동안 또는 토글이 활성화된 동안만 `text`로 변경한다.
- 아이콘에는 스크린 리더용 `aria-label`을 제공한다.
- 비밀번호를 콘솔, 분석 도구, 에러 로그 또는 URL Query Parameter에 기록하지 않는다.
- 페이지를 벗어나거나 제출이 완료되면 입력값을 제거한다.
- 브라우저 개발자 도구와 네트워크 통신에서는 값이 확인될 수 있으므로 반드시 HTTPS를 사용한다.

프론트엔드 예시:

```html
<input
  id="password"
  name="password"
  type="password"
  autocomplete="current-password"
/>
<button
  type="button"
  aria-label="비밀번호 보기"
  aria-controls="password"
>
  비밀번호 보기
</button>
```

> 마스킹은 화면 노출을 줄이는 UI 보안 기능이며, 서버의 Argon2 해싱과 HTTPS를 대체하지 않는다.

### 4.4 NFR-USER-003 API 성능

#### 4.4.1 성능 기준

- 모든 사용자 관련 API는 서버가 요청을 받은 시점부터 응답을 완료할 때까지 최대 3초 이내에 처리한다.
- 정상 요청뿐 아니라 인증 실패, 권한 실패 및 입력 검증 실패 응답도 기준에 포함한다.
- 목표 측정값은 운영 환경 또는 운영 환경과 유사한 테스트 환경의 응답 시간이다.

#### 4.4.2 적용 대상

- 회원가입, 로그인, 로그아웃 및 토큰 재발급
- 회원 목록 및 권한 변경
- 마이페이지 조회 및 회원정보 수정
- 비밀번호 변경 및 회원탈퇴

#### 4.4.3 구현 및 검증 기준

- 이메일, 사용자 ID 등 자주 조회하는 필드에 인덱스를 사용한다.
- 목록 API는 페이지네이션을 적용하고 필요한 필드만 조회한다.
- 하나의 요청에서 동일한 사용자 정보를 반복 조회하지 않는다.
- DB 트랜잭션 범위를 최소화하고 실패 시 롤백한다.
- 비밀번호 해싱 비용은 보안을 훼손하지 않는 범위에서 3초 기준을 충족하도록 측정한다.
- API별 응답 시간을 로그 또는 APM으로 수집한다.
- 자동화 테스트에서 각 API의 응답 시간이 3초 미만인지 검증한다.

### 4.5 인수 조건 요약

| ID | 완료 조건 |
| --- | --- |
| NFR-USER-001 | Access Token 30분, Refresh Token 7일, HttpOnly Cookie, 재발급 및 재로그인 흐름 구현 |
| NFR-USER-002 | 모든 비밀번호 입력 기본 마스킹, 보기 토글 및 평문 로그 금지 |
| NFR-USER-003 | 모든 User API가 테스트 환경에서 3초 이내 응답 |
