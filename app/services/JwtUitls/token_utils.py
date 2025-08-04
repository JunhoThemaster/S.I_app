import jwt
from fastapi import HTTPException
from jwt import PyJWTError

SECRET_KEY = "66a1d5781cc0ed773fd7899986441b110a85ce4d8ca1d19dd1a87e01a2a343bc"
ALGORITHM = "HS256"

def verify_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ 토큰 유효:", payload)
        return True
    except jwt.ExpiredSignatureError:
        print("⛔️ 토큰 만료")
    except jwt.JWTError as e:
        print(f"⛔️ 토큰 오류: {e}")
    return False
