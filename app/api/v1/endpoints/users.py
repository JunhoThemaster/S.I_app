from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
import datetime
from ....services.JwtUitls import token_utils
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel
from ....services.audio_module import save_and_transcribe,predict_service
from ....services.websocket import manager as ms
import numpy as np
from scipy.signal import resample_poly
from fastapi import APIRouter, Query
import openai
import librosa


def convert_pcm16_bytes_to_float32_array(pcm_bytes: bytes) -> np.ndarray:
    int16_array = np.frombuffer(pcm_bytes, dtype=np.int16)
    float_array = int16_array.astype(np.float32) / 32768.0  # normalize to [-1, 1]
    return float_array
def downsample_to_16k(audio: np.ndarray, orig_sr: int) -> np.ndarray:
    if orig_sr == 16000:
        return audio
    # up/down 비율 계산
    gcd = np.gcd(orig_sr, 16000)
    up = 16000 // gcd
    down = orig_sr // gcd
    return resample_poly(audio, up, down)




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


import tempfile
from fastapi import APIRouter, UploadFile, File, WebSocket, HTTPException, Query

model = WhisperModel("base", device="cuda", compute_type="float16")
manager = ms.ConnectionManager()

from ....services.audio_module import save_and_transcribe, predict_service
from ....services.audio_module.audio_io import load_audio_float32  # librosa 대체용
@router.post("/audio/{user_id}")
async def audio_analyze(user_id: str, token: str = Query(...), file: UploadFile = File(...)):
    if not token_utils.verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 1. .webm 파일 저장
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    # 2. Whisper 전사
    text = save_and_transcribe.save_wave_and_transcribe_from_path(
        path=tmp_path,
        sample_rate=16000,
        model=model
    )

    # 3. float32 waveform 로드
    y = load_audio_float32(tmp_path)

    # 4. 감정 분석
    emotion = predict_service.predict_emotion(y)

    # 5. WebSocket으로 결과 전달
    await manager.send_to_user(user_id, {
        "command": "AUDIO_ANALYSIS_RESULT",
        "text": text.strip(),
        "emotion": emotion
    })

    return {
        "text": text.strip(),
        "emotion": emotion
    }



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














