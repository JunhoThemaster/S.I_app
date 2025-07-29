from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
import datetime
router = APIRouter(
    prefix="/api/user",  # 이 경로가 모든 API 앞에 붙음
    tags=["user"]        # Swagger에서 보여질 카테고리 이름
)

FAKE_USERNAME = "admin"
FAKE_PASSWORD = "1234"

SECRET_KEY = "66a1d5781cc0ed773fd7899986441b110a85ce4d8ca1d19dd1a87e01a2a343bc"
ALGORITHM = "HS256"


class LoginData(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginData):
    if data.username == "admin" and data.password == "1234":
        payload = {
            "sub": data.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")