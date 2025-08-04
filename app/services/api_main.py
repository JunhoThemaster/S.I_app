from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any
import tempfile
import os
import uuid
from datetime import datetime
from speech_analyzer import SpeechAnalyzer
from interview_generator import InterviewGenerator
from feedback_generator import FeedbackGenerator
from json_safe_utils import safe_json_response
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI 면접 분석 API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 객체들 (싱글톤)
interview_sessions: Dict[str, Dict] = {}
speech_analyzer = SpeechAnalyzer()
interview_generator = InterviewGenerator()
feedback_generator = FeedbackGenerator()

# Pydantic 모델들
class InterviewSetupRequest(BaseModel):
    job_position: str
    num_questions: int

class IndividualFeedbackRequest(BaseModel):
    question: str
    answer: str

class InterviewSetupResponse(BaseModel):
    session_id: str
    questions: List[str]
    job_position: str
    message: str

class SpeechAnalysisResponse(BaseModel):
    session_id: str
    question_index: int
    text: str
    confidence: float
    emotion: str
    
    # 핵심 음성 분석 컬럼들 (30개 → 15개로 간소화)
    f0_mean: float
    f0_std: float
    intensity_mean_db: float
    speech_rate: float
    pause_duration: float
    voicing_fraction: float
    speech_clarity: float
    vocal_stability: float
    prosody_score: float
    overall_score: float
    duration: float
    
    # 맥락 분석 (핵심)
    context_matching: float
    semantic_similarity: float
    question_type: str
    context_grade: str
    recommendations: List[str]
    
    # 상태 정보
    end_detected: bool

# API 엔드포인트들
@app.get("/")
async def root():
    return {"message": "AI 면접 분석 API v2.0 실행 중", "status": "ready"}

@app.get("/api/questions/categories")
async def get_job_categories():
    """직무 카테고리 반환"""
    try:
        categories = interview_generator.get_available_positions()
        return {"categories": categories}
    except Exception as e:
        print(f"❌ 카테고리 조회 오류: {e}")
        return {"categories": ["Management", "Sales Marketing", "ICT", "Design"]}

@app.post("/api/interview/setup", response_model=InterviewSetupResponse)
async def setup_interview(request: InterviewSetupRequest):
    """면접 세션 설정"""
    try:
        session_id = str(uuid.uuid4())
        
        # 질문 생성
        questions = interview_generator.generate_questions(
            request.job_position, 
            request.num_questions
        )
        
        # 세션 저장 (간소화)
        interview_sessions[session_id] = {
            "session_id": session_id,
            "job_position": request.job_position,
            "questions": questions,
            "answers": [],
            "audio_analyses": [],
            "created_at": datetime.now().isoformat()
        }
        
        return InterviewSetupResponse(
            session_id=session_id,
            questions=questions,
            job_position=request.job_position,
            message="면접 세션이 생성되었습니다."
        )
        
    except Exception as e:
        print(f"❌ 면접 설정 오류: {e}")
        raise HTTPException(status_code=500, detail=f"면접 설정 오류: {str(e)}")

@app.post("/api/speech/analyze/{session_id}", response_model=SpeechAnalysisResponse)
async def analyze_speech(session_id: str, question_index: int, audio_file: UploadFile = File(...)):
    """음성 파일 분석 (핵심 기능)"""
    try:
        if session_id not in interview_sessions:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
                
        session = interview_sessions[session_id]
        if question_index >= len(session["questions"]):
            raise HTTPException(status_code=400, detail="잘못된 질문 인덱스입니다.")
                
        current_question = session["questions"][question_index]
        
        # 임시 파일 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
                
        print(f"🎤 음성 분석 시작: {question_index + 1}번 질문")
                
        # 음성 분석 수행
        analysis = speech_analyzer.analyze_speech_file(temp_file_path, current_question)
        end_detected = speech_analyzer.detect_end_keyword(analysis['text'])
                
        # 결과 저장
        session["audio_analyses"].append(analysis)
        session["answers"].append(analysis['text'])
                         
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        
        # JSON 안전성 보장
        safe_analysis = safe_json_response(analysis)
                
        # 간소화된 응답 생성
        return SpeechAnalysisResponse(
            session_id=session_id,
            question_index=question_index,
            text=str(safe_analysis['text']),
            confidence=float(safe_analysis.get('confidence', 0.9)),
            emotion=str(safe_analysis.get('emotion', 'neutral')),
            
            # 핵심 음성 분석 (간소화)
            f0_mean=float(safe_analysis.get('f0_mean', 150.0)),
            f0_std=float(safe_analysis.get('f0_std', 15.0)),
            intensity_mean_db=float(safe_analysis.get('intensity_mean_db', 55.0)),
            speech_rate=float(safe_analysis.get('speech_rate', 4.0)),
            pause_duration=float(safe_analysis.get('pause_duration', 0.2)),
            voicing_fraction=float(safe_analysis.get('voicing_fraction', 0.8)),
            speech_clarity=float(safe_analysis.get('speech_clarity', 70.0)),
            vocal_stability=float(safe_analysis.get('vocal_stability', 75.0)),
            prosody_score=float(safe_analysis.get('prosody_score', 72.0)),
            overall_score=float(safe_analysis.get('overall_score', 70.0)),
            duration=float(safe_analysis.get('duration', 3.0)),
            
            # 맥락 분석 (핵심)
            context_matching=float(safe_analysis.get('context_matching', 0.5)),
            semantic_similarity=float(safe_analysis.get('semantic_similarity', 0.5)),
            question_type=str(safe_analysis.get('question_type', 'general')),
            context_grade=str(safe_analysis.get('context_grade', '보통')),
            recommendations=safe_analysis.get('recommendations', []),
            
            # 상태
            end_detected=bool(end_detected)
        )
            
    except Exception as e:
        print(f"❌ 음성 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=f"음성 분석 오류: {str(e)}")

@app.post("/api/feedback/individual")
async def generate_individual_feedback(request: IndividualFeedbackRequest):
    """개별 질문에 대한 OpenAI 피드백 생성"""
    print(f"🤖 개별 피드백 요청 받음: '{request.question[:50]}...' / '{request.answer}'")
    
    try:
        from openai import OpenAI
        client = OpenAI()
        
        # 종료 키워드 확인
        end_keywords = ['이상', '끝', '완료', '마침', '이상입니다', '끝입니다']
        is_end_keyword = any(keyword in request.answer.lower() for keyword in end_keywords)
        
        if len(request.answer.strip()) < 5 or is_end_keyword:
            print("⚠️ 답변이 너무 짧거나 종료 키워드만 포함됨")
            return {
                "feedback": "답변이 충분하지 않습니다. 질문에 대한 구체적인 경험이나 생각을 더 자세히 설명해보세요.",
                "recommendations": [
                    "구체적인 사례나 경험을 포함해보세요",
                    "상황-행동-결과(STAR) 방식으로 답변해보세요", 
                    "개인적인 견해나 배운 점을 추가해보세요"
                ]
            }
        
        print("🤖 OpenAI API 호출 시작...")
        
        prompt = f"""
다음 면접 질문과 답변을 분석하여 구체적이고 건설적인 피드백을 제공해주세요.

질문: {request.question}
답변: {request.answer}

다음 관점에서 분석해주세요:
1. 질문의 의도를 잘 파악했는가?
2. 답변이 구체적이고 충분한가?
3. 경험이나 사례가 포함되었는가?
4. 면접관이 원하는 정보를 제공했는가?

결과를 다음 형식으로 제공해주세요:
FEEDBACK: 한두 문장으로 요약된 피드백
RECOMMENDATIONS:
- 구체적 개선 방안 1
- 구체적 개선 방안 2  
- 구체적 개선 방안 3

요구사항:
- 피드백은 격려와 개선점이 균형있게
- 개선 방안은 실용적이고 구체적으로
- 한국어로 작성
- 면접자를 존중하는 톤으로
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 전문 면접 코치입니다. 건설적이고 구체적인 피드백을 제공하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        print(f"✅ OpenAI 응답 받음: {len(content)}자")
        print(f"📝 OpenAI 응답: {content}")
        
        # 응답 파싱
        feedback = "적절한 답변입니다."
        recommendations = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('FEEDBACK:'):
                feedback = line.replace('FEEDBACK:', '').strip()
            elif line.startswith('RECOMMENDATIONS:'):
                continue
            elif line.startswith('-') or line.startswith('•'):
                rec = line[1:].strip()
                if rec:
                    recommendations.append(rec)
        
        if not recommendations:
            recommendations = [
                "구체적인 사례를 더 포함해보세요",
                "상황과 결과를 명확히 설명해보세요",
                "개인적인 성장이나 배운 점을 추가해보세요"
            ]
        
        result = {
            "feedback": feedback,
            "recommendations": recommendations[:3]  # 최대 3개
        }
        
        print(f"✅ 최종 피드백: {result}")
        return result
        
    except Exception as e:
        print(f"❌ 개별 피드백 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "feedback": "답변을 더 구체적이고 상세하게 작성해보세요.",
            "recommendations": [
                "구체적인 경험이나 사례를 포함해보세요",
                "상황-행동-결과 순서로 설명해보세요",
                "배운 점이나 성장한 부분을 언급해보세요"
            ]
        }

@app.post("/api/feedback/generate")
async def generate_feedback(request: dict):
    """최종 피드백 생성"""
    try:
        session_id = request.get('session_id')
        if session_id not in interview_sessions:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        session = interview_sessions[session_id]
        
        feedback = feedback_generator.generate_overall_feedback(
            session["questions"],
            session["answers"], 
            session["audio_analyses"]
        )
        
        return safe_json_response(feedback)
        
    except Exception as e:
        print(f"❌ 피드백 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"피드백 생성 오류: {str(e)}")

# 서버 실행
if __name__ == "__main__":
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)