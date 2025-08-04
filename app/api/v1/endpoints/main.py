from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.users import router as user_router
from app.api.v1.endpoints.websocket_router import router as websocket_router  # ✅ WebSocket 라우터 등록


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(user_router)
app.include_router(websocket_router)



# 2. React index.html 라우팅
@app.get("/")
def serve_spa():
    return {"message": "Hello World"}

# 3. API 엔드포인트 예시
@app.get("/main")
def hello():
    return {"message": "Hello from FastAPI!"}
