import os
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
from app.apis import practice_apis, user_apis

from app.apis import (
    user_apis,
    admin_user_api, 
    user_management_apis, 
    user_change_pw_apis, 
    patient_apis,
    delete_user_apis,
    medical_record_query_apis
    )




app = FastAPI()
## API router 연결
app.include_router(admin_user_api.router)           #권한변경
app.include_router(user_apis.router)                #회원가입
app.include_router(user_management_apis.router)     #회원정보수정
app.include_router(user_change_pw_apis.router)      #비번변경
app.include_router(patient_apis.router)             #환자등록/상세조회
app.include_router(delete_user_apis.router)         #회원탈퇴
app.include_router(medical_record_query_apis.router)#진료기록목록조회/진료기록상세조회




app.include_router(practice_apis.router)
app.include_router(user_apis.router)

BASE_DIR = Path(__file__).resolve().parent.parent

# 만약 static, media 폴더가 존재하지 않으면 생성
if not (BASE_DIR / "static").exists():
    os.mkdir(BASE_DIR / "static")
if not (BASE_DIR / "media").exists():
    os.mkdir(BASE_DIR / "media")

# 'static' 폴더를 '/static' 경로로 마운트 (CSS, JS 파일 서빙용)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# 'media' 폴더를 '/media' 경로로 마운트 (사용자 업로드 파일 서빙용)
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")


@app.get(path="/healthcheck", status_code=200, include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    # API나 정적 파일 경로는 제외 (FastAPI가 먼저 매칭하지 못한 경우에만 실행됨)
    if (
        path.startswith("api/v1")
        or path.startswith("static/")
        or path.startswith("media/")
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / "static" / "index.html")
