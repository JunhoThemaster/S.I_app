import numpy as np
import os
from typing import Dict, Any

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ContextMatchingAnalyzer:
    """AI 기반 질문-답변 맥락 분석기"""
    
    def __init__(self):
        print("🧠 AI 맥락 분석기 초기화...")
        try:
            self.openai_client = OpenAI() if OPENAI_AVAILABLE else None
            if self.openai_client:
                print("✅ OpenAI 클라이언트 초기화 성공")
                # API 키 확인 (앞 4자리만 표시)
                api_key = os.getenv('OPENAI_API_KEY', '')
                if api_key:
                    print(f"🔑 OpenAI API 키 확인됨: {api_key[:4]}...{api_key[-4:]}")
                else:
                    print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다!")
            else:
                print("❌ OpenAI 라이브러리를 사용할 수 없습니다")
        except Exception as e:
            print(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
            self.openai_client = None
        
    def analyze_context_matching(self, question: str, answer: str) -> Dict[str, Any]:
        """AI 기반 맥락 일치도 분석"""
        print(f"\n🔍 AI 맥락 분석 시작")
        print(f"   질문: '{question}'")
        print(f"   답변: '{answer}'")
        
        if not self.openai_client:
            return self._fallback_analysis(question, answer)
        
        try:
            # AI 기반 종합 분석
            ai_analysis = self._analyze_with_ai(question, answer)
            
            return {
                'semantic_similarity': ai_analysis.get('semantic_similarity', 0.5),
                'keyword_overlap': ai_analysis.get('keyword_overlap', 0.5),
                'intent_matching': ai_analysis.get('intent_matching', 0.5),
                'context_score': ai_analysis.get('context_score', 0.5),
                'analysis_details': ai_analysis.get('analysis_details', {})
            }
            
        except Exception as e:
            print(f"   ❌ AI 맥락 분석 오류: {e}")
            return self._fallback_analysis(question, answer)
    
    def _analyze_with_ai(self, question: str, answer: str) -> Dict[str, Any]:
        """AI를 사용한 맥락 분석"""
        if not self.openai_client:
            print("❌ OpenAI 클라이언트가 없습니다. 환경변수를 확인하세요.")
            raise Exception("OpenAI 클라이언트 없음")
            
        prompt = f"""
다음 면접 질문과 답변의 맥락 일치도를 전문적으로 분석해주세요.

질문: {question}
답변: {answer}

다음 4가지 측면에서 0.0-1.0 점수로 평가하고 분석해주세요:

1. SEMANTIC_SIMILARITY: 질문과 답변의 의미적 연관성 (0.0-1.0)
2. KEYWORD_OVERLAP: 핵심 키워드의 일치도 (0.0-1.0)
3. INTENT_MATCHING: 질문 의도와 답변 내용의 일치도 (0.0-1.0)  
4. CONTEXT_SCORE: 종합적인 맥락 적절성 (0.0-1.0)

출력 형식 (정확히 이 형식으로):
SEMANTIC_SIMILARITY: 0.X
KEYWORD_OVERLAP: 0.X  
INTENT_MATCHING: 0.X
CONTEXT_SCORE: 0.X
QUESTION_TYPE: 질문_유형
GRADE: 우수/양호/보통/미흡
ANALYSIS: 상세 분석 내용 한 문장
RECOMMENDATIONS:
- 구체적 개선 방안 1
- 구체적 개선 방안 2
- 구체적 개선 방안 3

요구사항:
- 점수는 반드시 0.0-1.0 사이 소수점 1자리
- 분석은 객관적이고 구체적으로
- 개선 방안은 실용적으로 제안
"""

        try:
            print(f"🤖 OpenAI API 호출 시작...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 면접 전문가입니다. 질문과 답변의 맥락 일치도를 정확하게 분석하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            print(f"✅ OpenAI 응답 받음: {len(content)}자")
            print(f"📝 응답 미리보기: {content[:200]}...")
            
            return self._parse_ai_analysis(content)
            
        except Exception as e:
            print(f"❌ OpenAI API 오류: {e}")
            raise e
    
    def _parse_ai_analysis(self, content: str) -> Dict[str, Any]:
        """AI 분석 결과 파싱"""
        result = {
            'semantic_similarity': 0.5,
            'keyword_overlap': 0.5,
            'intent_matching': 0.5,
            'context_score': 0.5,
            'analysis_details': {}
        }
        
        try:
            lines = content.split('\n')
            recommendations = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('SEMANTIC_SIMILARITY:'):
                    score = self._extract_score(line)
                    result['semantic_similarity'] = score
                elif line.startswith('KEYWORD_OVERLAP:'):
                    score = self._extract_score(line)
                    result['keyword_overlap'] = score
                elif line.startswith('INTENT_MATCHING:'):
                    score = self._extract_score(line)
                    result['intent_matching'] = score
                elif line.startswith('CONTEXT_SCORE:'):
                    score = self._extract_score(line)
                    result['context_score'] = score
                elif line.startswith('QUESTION_TYPE:'):
                    q_type = line.replace('QUESTION_TYPE:', '').strip()
                    result['analysis_details']['question_type'] = q_type
                elif line.startswith('GRADE:'):
                    grade = line.replace('GRADE:', '').strip()
                    result['analysis_details']['grade'] = grade
                elif line.startswith('ANALYSIS:'):
                    analysis = line.replace('ANALYSIS:', '').strip()
                    result['analysis_details']['detailed_analysis'] = analysis
                elif line.startswith('RECOMMENDATIONS:'):
                    continue
                elif line.startswith('-') and 'RECOMMENDATIONS' in content:
                    rec = line[1:].strip()
                    recommendations.append(rec)
            
            result['analysis_details']['recommendations'] = recommendations
            
            print(f"   📊 AI 분석 완료:")
            print(f"      의미 유사도: {result['semantic_similarity']:.3f}")
            print(f"      키워드 일치: {result['keyword_overlap']:.3f}")
            print(f"      의도 일치: {result['intent_matching']:.3f}")
            print(f"      종합 점수: {result['context_score']:.3f}")
            
        except Exception as e:
            print(f"   ⚠️ AI 응답 파싱 실패: {e}")
        
        return result
    
    def _extract_score(self, line: str) -> float:
        """점수 추출"""
        try:
            # 0.X 형태의 점수 추출
            import re
            matches = re.findall(r'0\.\d+', line)
            if matches:
                return float(matches[0])
            
            # 정수 점수를 소수로 변환
            matches = re.findall(r'\d+', line)
            if matches:
                score = int(matches[0])
                if score > 10:  # 100점 만점을 0-1 스케일로
                    return score / 100.0
                elif score > 1:  # 10점 만점을 0-1 스케일로
                    return score / 10.0
                else:
                    return float(score)
        except:
            pass
        
        return 0.5  # 기본값
    
    def _fallback_analysis(self, question: str, answer: str) -> Dict[str, Any]:
        """AI 실패시 백업 분석"""
        # 간단한 키워드 기반 분석
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        
        if not a_words:
            overlap = 0.0
        else:
            overlap = len(q_words.intersection(a_words)) / len(q_words.union(a_words))
        
        # 기본 점수
        base_score = 0.5
        if len(answer.strip()) > 10:
            base_score += 0.1
        if len(answer.strip()) > 30:
            base_score += 0.1
        
        context_score = min(1.0, base_score + overlap * 0.3)
        
        return {
            'semantic_similarity': context_score,
            'keyword_overlap': overlap,
            'intent_matching': context_score,
            'context_score': context_score,
            'analysis_details': {
                'question_type': 'general',
                'grade': '보통',
                'recommendations': ['더 구체적인 답변을 해보세요', 'AI 분석을 위해 시스템을 확인해주세요']
            }
        }