from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import tempfile
import os
import uuid
from speech_analyzer import SpeechAnalyzer
from context_matching_analyzer import ContextMatchingAnalyzer
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="면접 분석 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수들
interview_sessions: Dict[str, Dict] = {}
speech_analyzer = SpeechAnalyzer()

# Pydantic 모델들
class SpeechAnalysisResponse(BaseModel):
    session_id: str
    question_index: int
    text: str
    confidence: float
    emotion: str
    
    # CSV 30개 컬럼들
    jitter_local: float
    jitter_rap: float
    jitter_ppq5: float
    shimmer_local: float
    shimmer_apq3: float
    shimmer_apq5: float
    voice_breaks: float
    intensity_mean_db: float
    intensity_max_db: float
    intensity_min_db: float
    rms_intensity_db: float
    syllable_duration: float
    speech_rate: float
    articulation_rate: float
    pause_duration: float
    pause_number: int
    spectral_slope: float
    f0_mean: float
    f0_std: float
    f0_min: float
    f0_max: float
    pitch_period_mean: float
    voicing_fraction: float
    unvoicing_fraction: float
    mean_harmonicity: float
    duration: float
    
    # 계산된 지표들
    speech_clarity: float
    vocal_stability: float
    prosody_score: float
    overall_score: float
    end_detected: bool
    
    # 🆕 새로운 맥락 분석 필드들
    context_matching: float = 0.5
    semantic_similarity: float = 0.5  
    keyword_overlap: float = 0.5
    intent_matching: float = 0.5
    question_type: str = "general"
    context_grade: str = "보통"
    recommendations: List[str] = []

class InterviewSessionCreate(BaseModel):
    questions: List[str]

class InterviewSessionResponse(BaseModel):
    session_id: str
    questions: List[str]
    created_at: str

# API 엔드포인트들
@app.get("/")
async def root():
    return {"message": "면접 분석 API 서버가 실행 중입니다"}

@app.post("/api/interview/create", response_model=InterviewSessionResponse)
async def create_interview_session(session_data: InterviewSessionCreate):
    """새로운 면접 세션 생성"""
    session_id = str(uuid.uuid4())
    
    interview_sessions[session_id] = {
        "session_id": session_id,
        "questions": session_data.questions,
        "answers": [],
        "audio_analyses": [],
        "created_at": "2024-01-01T00:00:00Z"  # 실제 구현시 datetime.now()
    }
    
    return InterviewSessionResponse(
        session_id=session_id,
        questions=session_data.questions,
        created_at=interview_sessions[session_id]["created_at"]
    )

@app.get("/api/interview/{session_id}")
async def get_interview_session(session_id: str):
    """면접 세션 정보 조회"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return interview_sessions[session_id]

@app.post("/api/speech/analyze/{session_id}", response_model=SpeechAnalysisResponse)
async def analyze_speech(session_id: str, question_index: int, audio_file: UploadFile = File(...)):
    """음성 파일 분석 (30개 컬럼 + 맥락 분석)"""
    try:
        if session_id not in interview_sessions:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
                
        session = interview_sessions[session_id]
        if question_index >= len(session["questions"]):
            raise HTTPException(status_code=400, detail="잘못된 질문 인덱스입니다.")
                
        # 현재 질문 가져오기 (맥락 분석용)
        current_question = session["questions"][question_index]
        
        # 임시 파일 저장
        file_extension = '.wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
                
        print(f"🎤 음성 파일 저장됨: {temp_file_path}")
        print(f"📁 파일 크기: {len(content)} bytes")
        print(f"❓ 분석 질문: {current_question}")
                
        # 음성 분석 수행 (질문 포함)
        analysis = speech_analyzer.analyze_speech_file(temp_file_path, current_question)
        end_detected = speech_analyzer.detect_end_keyword(analysis['text'])
                
        print(f"📝 변환된 텍스트: {analysis['text']}")
        print(f"💯 분석 점수: {analysis['overall_score']}")
        print(f"🧠 맥락 점수: {analysis.get('context_matching', 0):.3f}")
                
        # 결과 저장
        session["audio_analyses"].append(analysis)
        session["answers"].append(analysis['text'])
                         
        # 임시 파일 삭제
        os.unlink(temp_file_path)
                
        # JSON 안전성을 위한 명시적 변환
        return SpeechAnalysisResponse(
            session_id=session_id,
            question_index=question_index,
            text=str(analysis['text']),
            confidence=float(analysis['confidence']),
            emotion=str(analysis['emotion']),
                        
            # CSV 30개 컬럼 - 모두 float로 명시적 변환
            jitter_local=float(analysis['jitter_local']),
            jitter_rap=float(analysis['jitter_rap']),
            jitter_ppq5=float(analysis['jitter_ppq5']),
            shimmer_local=float(analysis['shimmer_local']),
            shimmer_apq3=float(analysis['shimmer_apq3']),
            shimmer_apq5=float(analysis['shimmer_apq5']),
            voice_breaks=float(analysis['voice_breaks']),
            intensity_mean_db=float(analysis['intensity_mean_db']),
            intensity_max_db=float(analysis['intensity_max_db']),
            intensity_min_db=float(analysis['intensity_min_db']),
            rms_intensity_db=float(analysis['rms_intensity_db']),
            syllable_duration=float(analysis['syllable_duration']),
            speech_rate=float(analysis['speech_rate']),
            articulation_rate=float(analysis['articulation_rate']),
            pause_duration=float(analysis['pause_duration']),
            pause_number=int(analysis['pause_number']),
            spectral_slope=float(analysis['spectral_slope']),
            f0_mean=float(analysis['f0_mean']),
            f0_std=float(analysis['f0_std']),
            f0_min=float(analysis['f0_min']),
            f0_max=float(analysis['f0_max']),
            pitch_period_mean=float(analysis['pitch_period_mean']),
            voicing_fraction=float(analysis['voicing_fraction']),
            unvoicing_fraction=float(analysis['unvoicing_fraction']),
            mean_harmonicity=float(analysis['mean_harmonicity']),
            duration=float(analysis['duration']),
                        
            # 계산된 지표들
            speech_clarity=float(analysis['speech_clarity']),
            vocal_stability=float(analysis['vocal_stability']),
            prosody_score=float(analysis['prosody_score']),
            overall_score=float(analysis['overall_score']),
            end_detected=bool(end_detected),
            
            # 🆕 새로운 맥락 분석 필드들
            context_matching=float(analysis.get('context_matching', 0.5)),
            semantic_similarity=float(analysis.get('semantic_similarity', 0.5)),
            keyword_overlap=float(analysis.get('keyword_overlap', 0.5)),
            intent_matching=float(analysis.get('intent_matching', 0.5)),
            question_type=str(analysis.get('question_type', 'general')),
            context_grade=str(analysis.get('context_grade', '보통')),
            recommendations=analysis.get('recommendations', [])
        )
            
    except Exception as e:
        print(f"❌ API 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"음성 분석 오류: {str(e)}")

@app.get("/api/interview/{session_id}/results")
async def get_interview_results(session_id: str):
    """면접 결과 종합 조회"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    session = interview_sessions[session_id]
    
    return {
        "session_id": session_id,
        "questions": session["questions"],
        "answers": session["answers"],
        "analyses": session["audio_analyses"],
        "summary": {
            "total_questions": len(session["questions"]),
            "answered_questions": len(session["answers"]),
            "completion_rate": len(session["answers"]) / len(session["questions"]) * 100 if session["questions"] else 0
        }
    }

@app.delete("/api/interview/{session_id}")
async def delete_interview_session(session_id: str):
    """면접 세션 삭제"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    del interview_sessions[session_id]
    return {"message": f"세션 {session_id}가 삭제되었습니다."}

# 서버 실행 코드 (개발용)
if __name__ == "__main__":
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)