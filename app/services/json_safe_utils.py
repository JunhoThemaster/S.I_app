# json_safe_utils.py
import json
import numpy as np
from typing import Any, Dict

def make_json_safe(data: Any) -> Any:
    """
    모든 데이터를 JSON 직렬화 가능하게 변환
    numpy 타입, set, 기타 직렬화 불가능한 객체들을 안전하게 변환
    """
    if isinstance(data, dict):
        return {key: make_json_safe(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_json_safe(item) for item in data]
    elif isinstance(data, tuple):
        return [make_json_safe(item) for item in data]
    elif isinstance(data, set):
        return list(data)  # set → list 변환
    elif isinstance(data, (np.integer, np.floating)):
        return float(data)  # numpy 숫자 → Python float
    elif isinstance(data, np.ndarray):
        return data.tolist()  # numpy 배열 → Python list
    elif isinstance(data, np.bool_):
        return bool(data)  # numpy bool → Python bool
    elif hasattr(data, 'item'):  # numpy 스칼라
        return data.item()
    else:
        return data

def safe_json_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    API 응답용 안전한 JSON 변환 + 검증
    """
    try:
        # 1단계: 타입 변환
        safe_data = make_json_safe(data)
        
        # 2단계: JSON 직렬화 테스트
        json_str = json.dumps(safe_data)
        
        # 3단계: 역직렬화 테스트 (데이터 무결성 확인)
        json.loads(json_str)
        
        print(f"✅ JSON 안전성 검증 완료: {type(safe_data)}")
        return safe_data
        
    except (TypeError, ValueError) as e:
        print(f"❌ JSON 안전성 검증 실패: {e}")
        
        # 실패 시 최소한의 안전한 응답
        return {
            'text': str(data.get('text', '')),
            'overall_score': float(data.get('overall_score', 50.0)),
            'success': bool(data.get('success', False)),
            'error': 'JSON serialization fallback applied'
        }

# FastAPI 앱에서 사용하는 방법:
"""
from json_safe_utils import safe_json_response

@app.post("/api/speech/analyze/{session_id}")
async def analyze_speech(session_id: str, question_index: int = 0):
    try:
        # ... 기존 분석 로직
        result = analyzer.analyze_speech_file(temp_file.name)
        
        # JSON 안전성 보장
        safe_result = safe_json_response(result)
        
        return safe_result
        
    except Exception as e:
        # 예외 발생 시에도 안전한 응답
        return safe_json_response({
            'text': '',
            'overall_score': 50.0,
            'success': False,
            'error': str(e)
        })
"""