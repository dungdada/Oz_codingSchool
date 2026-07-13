# 운영규칙

### 1. Core Time(코어 타임)
- 과제 Core Time(코어 타임)은 15:30부터 중간 출결 시간인 18:00까지로 정한다.
- Core Time(코어 타임)에는 가능한 한 팀 작업에 집중한다.
- 자리를 비워야 할 경우 팀 채팅방에 미리 공유한다.

### 2. 출결 / 일정 공유
- 휴가, 결석, 조퇴, 외출 등의 이슈는 반드시 팀 내에 미리 공유한다.
- 갑작스러운 일정 변경이 생기면 확인하는 즉시 팀 채팅방에 알린다.
- 마감 기한을 지키기 어려울 것 같으면 혼자 고민하지 않고 바로 공유한다.

### 3. Communication(커뮤니케이션)
- 모르는 내용이 있으면 혼자 오래 고민하지 않고 팀원에게 질문한다.
- 질문할 때는 “어디까지 해봤는지”, “어떤 부분이 막혔는지”를 함께 말한다.
- 팀원 질문에는 가능한 한 확인 후 답변하거나 같이 찾아본다.

### 4. 회의 규칙
- 회의에서는 각자 현재 진행 상황, 막힌 부분, 다음 작업을 공유한다.
- 회의 내용 중 결정된 사항은 Notion(노션)에 정리한다.
- 의견이 다를 경우 다수결 또는 팀장 최종 결정으로 정리한다.

### 5. 팀 문화
- 서로 존중하는 언어를 사용한다.
- 피드백을 줄 때는 비난이 아니라 개선 방향 중심으로 말한다.
- 어려운 일이 생기면 혼자 해결하려 하지 말고 팀에 도움을 요청한다.





# 협업 규칙

### 1. Git 브랜치 규칙

- `main` 브랜치에는 직접 커밋하지 않는다.
- 기능별 브랜치를 생성하여 작업한다.
- 브랜치명은 아래 형식을 사용한다.

```
feature/기능명
fix/수정내용
refactor/리팩토링내용
```

예시:

```
feature/user-api
feature/login
fix/user-validation
```

### 2. 커밋 메시지 규칙

커밋 메시지는 작업 내용을 쉽게 확인할 수 있도록 작성한다.

```
feat: 사용자 조회 API 추가
fix: 회원가입 유효성 검사 오류 수정
refactor: 서비스 로직 분리
docs: README 수정
test: 사용자 API 테스트 추가
chore: 패키지 및 환경 설정 수정
```

### 3. 프로젝트 구조 규칙

FastAPI 프로젝트의 역할을 분리하여 작성한다.

```
app/
├── main.py
├── routers/
├── schemas/
├── models/
├── services/
├── repositories/
├── database/
└── dependencies/
```

- `routers`: API 엔드포인트 관리
- `schemas`: Pydantic 요청 및 응답 모델 관리
- `models`: 데이터베이스 모델 관리
- `services`: 비즈니스 로직 관리
- `repositories`: 데이터베이스 접근 로직 관리
- `database`: DB 연결 및 세션 설정
- `dependencies`: 공통 의존성 관리

### 4. API 작성 규칙

- API 경로는 소문자와 복수형 명사를 사용한다.
- 단어 구분은 하이픈보다 언더스코어를 지양하고 REST 형식으로 작성한다.
- HTTP 메서드의 목적을 구분한다.

```
GET /users
GET /users/{user_id}
POST /users
PUT /users/{user_id}
DELETE /users/{user_id}
```

- 적절한 상태 코드를 반환한다.

```
200 OK
201 Created
204 No Content
400 Bad Request
404 Not Found
422 Unprocessable Entity
500 Internal Server Error
```

### 5. Pydantic 스키마 규칙

- 요청과 응답 스키마를 분리한다.
- 스키마 클래스명은 역할이 드러나도록 작성한다.

```python
UserCreate
UserUpdate
UserResponse
UserLogin
```

- 응답값은 가능한 한 `response_model`을 지정한다.
- 비밀번호 등 민감한 정보는 응답에 포함하지 않는다.

### 6. 코드 작성 규칙

- 변수명과 함수명은 `snake_case`를 사용한다.
- 클래스명은 `PascalCase`를 사용한다.
- 함수에는 한 가지 역할만 부여한다.
- 라우터에 모든 로직을 작성하지 않고 서비스 계층으로 분리한다.
- 공통 로직은 중복 작성하지 않는다.
- 필요한 함수에는 타입 힌트를 작성한다.

```python
def get_user(user_id: int) -> UserResponse:
    ...
```

### 7. 환경 변수 관리

- DB 주소, 비밀번호, API 키는 코드에 직접 작성하지 않는다.
- 환경 변수는 `.env` 파일로 관리한다.
- `.env` 파일은 GitHub에 업로드하지 않는다.
- 필요한 환경 변수 목록은 `.env.example`에 작성한다.

```
DATABASE_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=
```

### 8. 예외 처리

- 오류 발생 시 일관된 형식의 응답을 반환한다.
- 필요한 경우 `HTTPException`을 사용한다.
- 존재하지 않는 데이터는 `404`를 반환한다.
- 잘못된 요청은 `400` 또는 `422`를 반환한다.

### 9. 테스트 규칙

- 주요 API는 정상 요청과 실패 요청을 모두 테스트한다.
- 테스트 파일은 `tests/` 폴더에서 관리한다.
- 기능 병합 전 기존 테스트가 정상 작동하는지 확인한다.

```
tests/
├── test_users.py
├── test_auth.py
└── test_posts.py
```

### 10. Pull Request 규칙

- 기능 구현 후 Pull Request를 생성한다.
- PR에는 작업 내용, 테스트 결과, 변경 사항을 작성한다.
- 팀원 한 명 이상이 코드를 확인한 후 병합한다.
- 충돌이 발생하면 작업자가 해결한 후 다시 요청한다.

### 11. 문서화 규칙

- API 변경 사항은 README 또는 Swagger 문서에 반영한다.
- FastAPI의 `/docs`에서 요청값과 응답값이 정상적으로 표시되는지 확인한다.
- 새로운 기능 추가 시 실행 방법과 사용 방법을 문서에 기록한다.

### 12. 소통 및 일정 규칙

- 작업 시작 전 담당 기능을 공유한다.
- 진행 상황과 문제점을 매일 공유한다.
- 일정이 지연될 경우 즉시 팀원에게 알린다.
- 다른 팀원의 코드를 수정할 때는 먼저 내용을 공유한다.