import numpy as np
from typing import List, Dict, Any
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class FeedbackGenerator:
    def __init__(self):
        self.openai_client = OpenAI() if OPENAI_AVAILABLE else None
        
        # 기본 템플릿 (AI 실패시 백업용)
        self.backup_templates = {
            'excellent': "매우 우수한 면접 실력을 보여주셨습니다.",
            'good': "전반적으로 양호한 면접이었습니다.",
            'needs_improvement': "면접 실력 향상이 필요합니다."
        }

    def generate_overall_feedback(self, questions: List[str], answers: List[str], 
                                audio_analyses: List[Dict]) -> Dict[str, Any]:
        """AI 기반 종합 피드백 생성"""
        if not audio_analyses:
            return self._get_default_feedback()
        
        # 기본 점수 계산
        scores = [a.get('overall_score', 70.0) for a in audio_analyses]
        overall_score = np.mean(scores)
        avg_features = self._calc_avg_features(audio_analyses)
        
        # AI 기반 맞춤형 피드백 생성
        ai_feedback = self._generate_ai_feedback(questions, answers, audio_analyses, overall_score)
        
        return {
            'overall_score': round(overall_score, 1),
            'individual_scores': [round(s, 1) for s in scores],
            'delivery_feedback': ai_feedback.get('delivery_feedback', '발음과 전달력을 개선해보세요.'),
            'tone_feedback': ai_feedback.get('tone_feedback', '목소리 톤을 안정적으로 유지해보세요.'),
            'rhythm_feedback': ai_feedback.get('rhythm_feedback', '말하기 속도를 조절해보세요.'),
            'strengths': ai_feedback.get('strengths', ['성실하게 참여해주셨습니다']),
            'improvement_areas': ai_feedback.get('improvement_areas', ['더 많은 연습이 필요합니다']),
            'recommendations': ai_feedback.get('recommendations', ['꾸준한 연습을 권장합니다']),
            'detailed_analysis': self._generate_detailed_analysis(questions, answers, audio_analyses),
            'timestamp': datetime.now().isoformat()
        }

    def _generate_ai_feedback(self, questions: List[str], answers: List[str], 
                            analyses: List[Dict], overall_score: float) -> Dict[str, Any]:
        """AI를 사용한 맞춤형 피드백 생성"""
        if not self.openai_client:
            print("❌ OpenAI 클라이언트 없음 - 백업 피드백 사용")
            return self._generate_fallback_feedback(overall_score)
        
        try:
            # 면접 데이터 요약
            interview_summary = self._create_interview_summary(questions, answers, analyses)
            
            print(f"🤖 종합 피드백 생성 시작...")
            print(f"📊 전체 점수: {overall_score:.1f}점")
            
            prompt = f"""
다음 면접 결과를 종합적으로 분석하여 구체적이고 개인화된 피드백을 생성해주세요.

면접 정보:
{interview_summary}

전체 점수: {overall_score:.1f}/100

다음 형식으로 상세한 피드백을 생성해주세요:

DELIVERY_FEEDBACK: 발음과 전달력에 대한 구체적이고 건설적인 피드백 (2-3문장)
TONE_FEEDBACK: 목소리 톤과 안정성에 대한 구체적 피드백 (2-3문장)
RHYTHM_FEEDBACK: 말하기 속도와 리듬에 대한 구체적 피드백 (2-3문장)

STRENGTHS:
- 구체적인 강점 1 (실제 답변 내용 기반)
- 구체적인 강점 2 (실제 답변 내용 기반)  
- 구체적인 강점 3 (실제 답변 내용 기반)

IMPROVEMENTS:
- 구체적인 개선점 1 (실제 답변 분석 기반)
- 구체적인 개선점 2 (실제 답변 분석 기반)
- 구체적인 개선점 3 (실제 답변 분석 기반)

RECOMMENDATIONS:
- 실용적인 개선 방법 1 (구체적 행동 방안)
- 실용적인 개선 방법 2 (구체적 행동 방안)
- 실용적인 개선 방법 3 (구체적 행동 방안)

요구사항:
- 실제 답변 내용을 반영한 구체적 분석
- 격려와 개선점의 균형
- 실용적이고 실행 가능한 조언
- 전문적이면서도 친근한 톤
- 한국어로 작성
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 경험이 풍부한 면접 전문 코치입니다. 면접자의 실제 답변을 바탕으로 구체적이고 건설적인 피드백을 제공하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            print(f"✅ OpenAI 종합 피드백 응답 받음: {len(content)}자")
            print(f"📝 응답 미리보기: {content[:200]}...")
            
            parsed_feedback = self._parse_ai_feedback(content)
            
            # 빈 항목 체크 및 기본값 설정
            if not parsed_feedback.get('strengths'):
                parsed_feedback['strengths'] = ['면접에 성실하게 참여해주셨습니다', '질문에 답변하려는 적극적인 자세를 보여주셨습니다', '면접 과정에서 꾸준한 집중력을 보여주셨습니다']
            
            if not parsed_feedback.get('improvement_areas'):
                parsed_feedback['improvement_areas'] = ['답변을 더 구체적으로 작성해보세요', '경험과 사례를 포함한 답변을 연습해보세요', '질문의 의도를 파악하는 연습이 필요합니다']
            
            if not parsed_feedback.get('recommendations'):
                parsed_feedback['recommendations'] = ['STAR 기법(상황-행동-결과)으로 답변을 구성해보세요', '모의 면접을 통해 실전 경험을 쌓아보세요', '각 질문별로 미리 답변을 준비해보세요']
            
            print(f"🎯 파싱된 피드백:")
            print(f"   강점: {len(parsed_feedback.get('strengths', []))}개")
            print(f"   개선점: {len(parsed_feedback.get('improvement_areas', []))}개") 
            print(f"   권장사항: {len(parsed_feedback.get('recommendations', []))}개")
            
            return parsed_feedback
            
        except Exception as e:
            print(f"⚠️ AI 피드백 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_feedback(overall_score)

    def _create_interview_summary(self, questions: List[str], answers: List[str], 
                                analyses: List[Dict]) -> str:
        """면접 데이터 요약"""
        summary = []
        
        for i, (q, a, analysis) in enumerate(zip(questions, answers, analyses)):
            score = analysis.get('overall_score', 70)
            context_score = analysis.get('context_matching', 0.5)
            
            summary.append(f"""
질문 {i+1}: {q}
답변: {a}
음성 점수: {score:.1f}/100
맥락 일치도: {context_score:.2f}
""")
        
        return "\n".join(summary)

    def _parse_ai_feedback(self, content: str) -> Dict[str, Any]:
        """AI 응답 파싱 (개선됨)"""
        feedback = {
            'delivery_feedback': '',
            'tone_feedback': '',
            'rhythm_feedback': '',
            'strengths': [],
            'improvement_areas': [],
            'recommendations': []
        }
        
        try:
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 섹션 헤더 감지
                if line.startswith('DELIVERY_FEEDBACK:'):
                    feedback['delivery_feedback'] = line.replace('DELIVERY_FEEDBACK:', '').strip()
                elif line.startswith('TONE_FEEDBACK:'):
                    feedback['tone_feedback'] = line.replace('TONE_FEEDBACK:', '').strip()
                elif line.startswith('RHYTHM_FEEDBACK:'):
                    feedback['rhythm_feedback'] = line.replace('RHYTHM_FEEDBACK:', '').strip()
                elif line.startswith('STRENGTHS:'):
                    current_section = 'strengths'
                    continue
                elif line.startswith('IMPROVEMENTS:'):
                    current_section = 'improvements'
                    continue
                elif line.startswith('RECOMMENDATIONS:'):
                    current_section = 'recommendations'
                    continue
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    # 리스트 항목 처리
                    item = line[1:].strip()
                    if item and current_section:
                        if current_section == 'strengths':
                            feedback['strengths'].append(item)
                        elif current_section == 'improvements':
                            feedback['improvement_areas'].append(item)
                        elif current_section == 'recommendations':
                            feedback['recommendations'].append(item)
            
            # 기본값 설정 (빈 항목 방지)
            if not feedback['delivery_feedback']:
                feedback['delivery_feedback'] = '발음이 명확하고 전달력이 양호합니다. 조금 더 자신감 있게 말씀하시면 더욱 좋겠습니다.'
            
            if not feedback['tone_feedback']:
                feedback['tone_feedback'] = '목소리 톤이 안정적입니다. 중요한 내용을 강조할 때 톤의 변화를 주시면 더욱 효과적일 것입니다.'
            
            if not feedback['rhythm_feedback']:
                feedback['rhythm_feedback'] = '말하기 속도가 적절합니다. 핵심 내용에서 잠시 멈춤을 두시면 더욱 인상적인 답변이 될 것입니다.'
            
            print(f"🔍 파싱 결과 확인:")
            print(f"   전달력: {len(feedback['delivery_feedback'])}자")
            print(f"   톤: {len(feedback['tone_feedback'])}자")
            print(f"   리듬: {len(feedback['rhythm_feedback'])}자")
            print(f"   강점: {len(feedback['strengths'])}개")
            print(f"   개선점: {len(feedback['improvement_areas'])}개")
            print(f"   권장사항: {len(feedback['recommendations'])}개")
        
        except Exception as e:
            print(f"⚠️ AI 피드백 파싱 실패: {e}")
        
        return feedback

    def _generate_fallback_feedback(self, score: float) -> Dict[str, Any]:
        """AI 실패시 백업 피드백"""
        if score >= 80:
            grade = 'excellent'
        elif score >= 60:
            grade = 'good'
        else:
            grade = 'needs_improvement'
        
        return {
            'delivery_feedback': self.backup_templates[grade],
            'tone_feedback': self.backup_templates[grade],
            'rhythm_feedback': self.backup_templates[grade],
            'strengths': ['면접에 참여해주셨습니다'],
            'improvement_areas': ['더 많은 연습이 필요합니다'],
            'recommendations': ['꾸준한 연습을 권장합니다']
        }

    def _calc_avg_features(self, analyses: List[Dict]) -> Dict[str, float]:
        """평균 특성 계산"""
        features = {}
        keys = ['speech_clarity', 'vocal_stability', 'prosody_score', 'context_matching']
        
        for key in keys:
            values = [a.get(key, 0) for a in analyses if key in a]
            features[key] = np.mean(values) if values else 0
        
        return features

    def _generate_detailed_analysis(self, questions: List[str], answers: List[str], 
                                  analyses: List[Dict]) -> Dict[str, Any]:
        """상세 분석 (간소화)"""
        return {
            'question_count': len(questions),
            'avg_answer_length': round(np.mean([len(a) for a in answers if a]), 1),
            'avg_context_score': round(np.mean([a.get('context_matching', 0.5) for a in analyses]), 2),
            'total_duration': round(sum([a.get('duration', 3.0) for a in analyses]), 1)
        }

    def _get_default_feedback(self) -> Dict[str, Any]:
        """기본 피드백"""
        return {
            'overall_score': 70.0,
            'individual_scores': [70.0],
            'delivery_feedback': "분석할 데이터가 충분하지 않습니다.",
            'tone_feedback': "분석할 데이터가 충분하지 않습니다.",
            'rhythm_feedback': "분석할 데이터가 충분하지 않습니다.",
            'strengths': ["면접에 참여해주셔서 감사합니다"],
            'improvement_areas': ["더 많은 데이터로 정확한 분석을 제공하겠습니다"],
            'recommendations': ["다음 면접에서 더 상세한 분석을 받으실 수 있습니다"],
            'detailed_analysis': {'question_count': 0, 'avg_answer_length': 0, 'avg_context_score': 0, 'total_duration': 0},
            'timestamp': datetime.now().isoformat()
        }