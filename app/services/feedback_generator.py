import numpy as np
from typing import List, Dict, Any
from datetime import datetime

class FeedbackGenerator:
    def __init__(self):
        self.feedback_templates = {
            'excellent': {
                'delivery': "발음이 매우 명확하고 전달력이 뛰어납니다. 음성 강도와 명확성이 우수합니다.",
                'tone': "목소리 톤이 안정적이고 자신감이 느껴집니다. 감정 표현이 적절합니다.",
                'rhythm': "말하기 속도와 리듬이 매우 적절하여 듣기 편합니다."
            },
            'good': {
                'delivery': "전반적으로 명확한 발음이나, 조금 더 또렷하게 말씀하시면 좋겠습니다.",
                'tone': "목소리 톤은 안정적이나, 조금 더 다양한 톤 변화가 있으면 좋겠습니다.",
                'rhythm': "적절한 속도이지만, 중요한 부분에서 잠시 멈춤이 있으면 더 좋겠습니다."
            },
            'needs_improvement': {
                'delivery': "발음 명확성 개선이 필요합니다. 더 크고 또렷하게 말씀해주세요.",
                'tone': "목소리에 떨림이 있어 긴장감이 느껴집니다. 안정된 톤으로 말씀해주세요.",
                'rhythm': "말하기 속도 조절이 필요합니다. 천천히 말씀해주세요."
            }
        }

    def generate_overall_feedback(self, questions: List[str], answers: List[str], 
                                audio_analyses: List[Dict]) -> Dict[str, Any]:
        """종합 피드백 생성"""
        if not audio_analyses:
            return self._get_default_feedback()
        
        # 평균 점수 계산
        scores = [a.get('overall_score', 70.0) for a in audio_analyses]
        overall_score = np.mean(scores)
        
        # 평균 특성 계산
        avg_features = self._calc_avg_features(audio_analyses)
        
        # 3개 분야별 피드백 생성
        delivery_feedback = self._generate_feedback('delivery', avg_features)
        tone_feedback = self._generate_feedback('tone', avg_features)
        rhythm_feedback = self._generate_feedback('rhythm', avg_features)
        
        return {
            'overall_score': round(overall_score, 1),
            'individual_scores': [round(s, 1) for s in scores],
            'delivery_feedback': delivery_feedback,
            'tone_feedback': tone_feedback,
            'rhythm_feedback': rhythm_feedback,
            'strengths': self._identify_strengths(avg_features),
            'improvement_areas': self._identify_improvements(avg_features),
            'recommendations': self._generate_recommendations(overall_score),
            'detailed_analysis': self._generate_detailed_analysis(questions, answers, audio_analyses),
            'timestamp': datetime.now().isoformat()
        }

    def _calc_avg_features(self, analyses: List[Dict]) -> Dict[str, float]:
        """평균 특성 계산"""
        features = {}
        keys = ['speech_clarity', 'vocal_stability', 'prosody_score', 'f0_mean', 
                'intensity_mean_db', 'speech_rate', 'pause_duration', 'voicing_fraction']
        
        for key in keys:
            values = [a.get(key, 0) for a in analyses if key in a]
            features[key] = np.mean(values) if values else 0
        
        return features

    def _generate_feedback(self, category: str, features: Dict[str, float]) -> str:
        """카테고리별 피드백 생성"""
        score = features.get('speech_clarity', 70) if category == 'delivery' else \
                features.get('vocal_stability', 70) if category == 'tone' else \
                features.get('prosody_score', 70)
        
        if score >= 85:
            grade = 'excellent'
        elif score >= 70:
            grade = 'good'
        else:
            grade = 'needs_improvement'
        
        # 기본 템플릿에 특성값 추가
        template = self.feedback_templates[grade][category]
        
        if category == 'delivery':
            return f"{template} (명확성: {score:.1f}점)"
        elif category == 'tone':
            f0 = features.get('f0_mean', 150)
            return f"{template} (기본주파수: {f0:.1f}Hz, 안정성: {score:.1f}점)"
        else:  # rhythm
            rate = features.get('speech_rate', 4)
            return f"{template} (발화속도: {rate:.1f}음절/초, 리듬: {score:.1f}점)"

    def _identify_strengths(self, features: Dict[str, float]) -> List[str]:
        """강점 식별"""
        strengths = []
        
        if features.get('speech_clarity', 0) >= 80:
            strengths.append("발음이 명확하고 전달력이 우수합니다")
        if features.get('vocal_stability', 0) >= 80:
            strengths.append("목소리가 안정적이고 일관성이 있습니다")
        if features.get('prosody_score', 0) >= 80:
            strengths.append("말하기 리듬과 속도가 적절합니다")
        if 3.0 <= features.get('speech_rate', 0) <= 6.0:
            strengths.append("발화 속도가 적절합니다")
        
        return strengths if strengths else ["전반적으로 균형잡힌 답변을 하셨습니다"]

    def _identify_improvements(self, features: Dict[str, float]) -> List[str]:
        """개선 영역 식별"""
        improvements = []
        
        if features.get('speech_clarity', 0) < 70:
            improvements.append("발음 명확성 향상이 필요합니다")
        if features.get('vocal_stability', 0) < 70:
            improvements.append("목소리 안정성 개선이 필요합니다")
        if features.get('prosody_score', 0) < 70:
            improvements.append("말하기 리듬 개선이 필요합니다")
        
        rate = features.get('speech_rate', 4)
        if rate > 6:
            improvements.append("말하기 속도를 조금 늦춰주세요")
        elif rate < 3:
            improvements.append("말하기 속도를 조금 높여주세요")
        
        return improvements if improvements else ["전반적으로 양호한 수준입니다"]

    def _generate_recommendations(self, score: float) -> List[str]:
        """개선 권장사항 생성"""
        if score < 60:
            return [
                "기본적인 발음 연습이 필요합니다",
                "천천히 또렷하게 말하는 연습을 해보세요",
                "면접 상황 모의 연습을 권장합니다"
            ]
        elif score < 75:
            return [
                "적절한 말하기 속도 유지 연습을 해보세요",
                "목소리 톤 변화 연습이 도움이 될 것입니다",
                "침묵 구간을 효과적으로 활용해보세요"
            ]
        elif score < 85:
            return [
                "자연스러운 운율 연습을 해보세요",
                "핵심 내용 강조 기법을 익혀보세요",
                "다양한 질문 유형 답변을 준비하세요"
            ]
        else:
            return [
                "현재 수준을 유지하면서 표현력을 기르세요",
                "다양한 상황 적응력을 높여보세요",
                "전문성을 보여줄 수 있는 답변을 준비하세요"
            ]

    def _generate_detailed_analysis(self, questions: List[str], answers: List[str], 
                                  analyses: List[Dict]) -> Dict[str, Any]:
        """상세 분석 생성"""
        return {
            'question_count': len(questions),
            'avg_answer_length': np.mean([len(a.split()) for a in answers if a]),
            'avg_speech_rate': np.mean([a.get('speech_rate', 0) for a in analyses]),
            'avg_clarity': np.mean([a.get('speech_clarity', 0) for a in analyses]),
            'avg_stability': np.mean([a.get('vocal_stability', 0) for a in analyses]),
            'emotions': [a.get('emotion', '중립') for a in analyses]
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
            'detailed_analysis': {},
            'timestamp': datetime.now().isoformat()
        }