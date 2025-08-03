from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
import datetime
from services.JwtUitls import token_utils
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel
from services.audio_module import save_and_transcribe,predict_service
from services.websocket import ms
import numpy as np



def convert_pcm16_bytes_to_float32_array(pcm_bytes: bytes) -> np.ndarray:
    int16_array = np.frombuffer(pcm_bytes, dtype=np.int16)
    float_array = int16_array.astype(np.float32) / 32768.0  # normalize to [-1, 1]
    return float_array





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



## 오디오 송신 웹소켓 엔드포인트

model = WhisperModel("base", device="cpu")
manager = ms.ConnectionManager()

@router.websocket("/ws/audio/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str):
    if not token_utils.verify_token(token):
        await websocket.close()
        return

    await manager.connect(websocket, user_id)

    buffer = bytearray()
    sample_rate = 16000
    bytes_per_sample = 2
    min_bytes = sample_rate * bytes_per_sample * 3  # 최소 3초 분량 이상일 때만 전사 시도

    try:
        while True:
            data = await websocket.receive_bytes()
            buffer.extend(data)

            # 일정 이상 길이 되었을 때 전사 시도
            if len(buffer) >= min_bytes:
                temp_buffer = buffer[:]  # 버퍼 복사 (삭제하지 않음)
                text = save_and_transcribe(temp_buffer, sample_rate, model)
                print(f"📝 {user_id} → {text}")

                await manager.send_to_user(user_id, {"text": text})

                if "이상입니다" in text:
                    print(f"✅ '{user_id}' 응답 종료 감지됨. 감정 분석 시작")
                    float_audio = convert_pcm16_bytes_to_float32_array(temp_buffer)    
                    # 🔹 감정 분석 모델에 버퍼 넘기기
                    emotion = predict_service.predict_emotion(float_audio)
                    print(f"🎯 감정 결과: {emotion}")

                    await manager.send_to_user(user_id, {
                        "command": "NEXT_QUESTION",
                        "emotion": emotion,
                        "answer": text
                    })

                    # 🔁 다음 응답 위해 버퍼 초기화
                    buffer = bytearray()

    except WebSocketDisconnect:
        manager.disconnect(user_id)










from fastapi import APIRouter, Query
import openai

class FieldRequest(BaseModel):
    field: str

@router.post("/questions")
def generate_questions(req: FieldRequest):
    field = req.field

    prompt = f"""
    신입 지원자를 위한 면접 질문 8개를 현실적이고 다양하게 제시해 주세요.
    분야: {field}
    형식: 리스트
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    questions = [q.strip("-• ") for q in content.split("\n") if q.strip()]
    return {"field": field, "questions": questions[:8]}














