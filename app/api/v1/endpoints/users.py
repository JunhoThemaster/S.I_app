from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/user",  # 이 경로가 모든 API 앞에 붙음
    tags=["user"]        # Swagger에서 보여질 카테고리 이름
)

FAKE_USERNAME = "admin"
FAKE_PASSWORD = "1234"

class LoginData(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginData):
    if data.username == FAKE_USERNAME and data.password == FAKE_PASSWORD:
        return {"success": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")