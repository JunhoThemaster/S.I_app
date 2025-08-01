import numpy as np
from typing import Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
import re

class ContextMatchingAnalyzer:
    """질문과 답변의 맥락/의도 일치도를 분석하는 클래스"""
    
    def __init__(self):
        print("🧠 맥락 분석기 초기화...")
        self.sentence_model = None
        self._init_sentence_transformer()
        
    def _init_sentence_transformer(self):
        """한국어 Sentence-BERT 모델 초기화"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 한국어 특화 모델들 (우선순위 순)
            models_to_try = [
                'jhgan/ko-sbert-sts',           # KorSTS 데이터로 학습된 모델
                'KDHyun08/TAACO_STS',          # KLUE-STS로 학습된 모델  
                'sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens'  # 다국어 대안
            ]
            
            for model_name in models_to_try:
                try:
                    print(f"   🔄 모델 로드 시도: {model_name}")
                    self.sentence_model = SentenceTransformer(model_name)
                    print(f"   ✅ 모델 로드 성공: {model_name}")
                    break
                except Exception as e:
                    print(f"   ❌ 모델 로드 실패: {model_name} - {e}")
                    continue
                    
            if self.sentence_model is None:
                print("   ⚠️ 모든 모델 로드 실패, 기본 키워드 분석 모드로 동작")
                
        except ImportError:
            print("   ⚠️ sentence-transformers 미설치, 기본 키워드 분석 모드로 동작")
            print("   💡 설치 명령: pip install sentence-transformers")
    
    def analyze_context_matching(self, question: str, answer: str) -> Dict[str, Any]:
        """질문과 답변의 맥락 일치도 종합 분석"""
        print(f"\n🔍 맥락 일치도 분석 시작")
        print(f"   질문: '{question}'")
        print(f"   답변: '{answer}'")
        
        results = {
            'semantic_similarity': 0.0,
            'keyword_overlap': 0.0,
            'intent_matching': 0.0,
            'context_score': 0.0,
            'analysis_details': {}
        }
        
        try:
            # 1. 의미적 유사도 (Sentence-BERT)
            semantic_score = self._calculate_semantic_similarity(question, answer)
            results['semantic_similarity'] = semantic_score
            print(f"   📊 의미적 유사도: {semantic_score:.3f}")
            
            # 2. 키워드 겹침도
            keyword_score = self._calculate_keyword_overlap(question, answer)
            results['keyword_overlap'] = keyword_score
            print(f"   🔤 키워드 겹침도: {keyword_score:.3f}")
            
            # 3. 의도 일치도 (질문 유형별 분석)
            intent_score = self._analyze_intent_matching(question, answer)
            results['intent_matching'] = intent_score
            print(f"   🎯 의도 일치도: {intent_score:.3f}")
            
            # 4. 종합 맥락 점수 계산 (가중평균)
            context_score = self._calculate_final_context_score(
                semantic_score, keyword_score, intent_score
            )
            results['context_score'] = context_score
            print(f"   🏆 종합 맥락 점수: {context_score:.3f}")
            
            # 5. 상세 분석 정보
            results['analysis_details'] = self._get_detailed_analysis(
                question, answer, semantic_score, keyword_score, intent_score
            )
            
            return results
            
        except Exception as e:
            print(f"   ❌ 맥락 분석 오류: {e}")
            return {
                'semantic_similarity': 0.5,
                'keyword_overlap': 0.5,
                'intent_matching': 0.5,
                'context_score': 0.5,
                'analysis_details': {'error': str(e)}
            }
    
    def _calculate_semantic_similarity(self, question: str, answer: str) -> float:
        """의미적 유사도 계산 (Sentence-BERT 활용)"""
        if self.sentence_model is None:
            # Fallback: 간단한 단어 기반 유사도
            return self._simple_word_similarity(question, answer)
        
        try:
            # 문장 임베딩 생성
            embeddings = self.sentence_model.encode([question, answer])
            
            # 코사인 유사도 계산
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            # -1~1 범위를 0~1 범위로 변환
            normalized_similarity = (similarity + 1) / 2
            
            return float(normalized_similarity)
            
        except Exception as e:
            print(f"     ⚠️ Sentence-BERT 실패, 단어 기반 유사도 사용: {e}")
            return self._simple_word_similarity(question, answer)
    
    def _simple_word_similarity(self, question: str, answer: str) -> float:
        """간단한 단어 기반 유사도 (Fallback)"""
        q_words = set(self._extract_keywords(question))
        a_words = set(self._extract_keywords(answer))
        
        if not q_words or not a_words:
            return 0.3
        
        # 자카드 유사도
        intersection = len(q_words.intersection(a_words))
        union = len(q_words.union(a_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_keyword_overlap(self, question: str, answer: str) -> float:
        """키워드 겹침도 계산"""
        q_keywords = self._extract_keywords(question)
        a_keywords = self._extract_keywords(answer)
        
        if not q_keywords:
            return 0.3  # 질문에 키워드가 없으면 중간값
            
        # 질문 키워드가 답변에 포함된 비율
        overlap_count = sum(1 for kw in q_keywords if kw in answer)
        overlap_ratio = overlap_count / len(q_keywords)
        
        return float(overlap_ratio)
    
    def _extract_keywords(self, text: str) -> list:
        """텍스트에서 중요 키워드 추출 (한국어 특화)"""
        # 기본 전처리
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        
        # 불용어 제거
        stopwords = {'은', '는', '이', '가', '을', '를', '에', '에서', '으로', '로', 
                    '과', '와', '도', '만', '까지', '부터', '에게', '한테', '께',
                    '그', '저', '이', '그런', '저런', '이런', '것', '수', '때',
                    '다', '하다', '되다', '있다', '없다', '이다', '아니다'}
        
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]
        
        return keywords
    
    def _analyze_intent_matching(self, question: str, answer: str) -> float:
        """질문 유형별 의도 일치도 분석"""
        # 질문 유형 분류
        question_type = self._classify_question_type(question)
        
        # 답변 적절성 검사
        appropriateness = self._check_answer_appropriateness(question_type, question, answer)
        
        return float(appropriateness)
    
    def _classify_question_type(self, question: str) -> str:
        """질문 유형 분류"""
        q_lower = question.lower()
        
        # 면접 질문 유형별 키워드
        if any(word in q_lower for word in ['자기소개', '소개', '본인', '자신']):
            return 'self_introduction'
        elif any(word in q_lower for word in ['장점', '강점', '잘하는']):
            return 'strengths'
        elif any(word in q_lower for word in ['단점', '약점', '부족한']):
            return 'weaknesses'
        elif any(word in q_lower for word in ['경험', '프로젝트', '업무', '일']):
            return 'experience'
        elif any(word in q_lower for word in ['동기', '이유', '왜', '지원']):
            return 'motivation'
        elif any(word in q_lower for word in ['목표', '계획', '꿈', '미래']):
            return 'goals'
        elif any(word in q_lower for word in ['어려운', '힘든', '극복', '문제']):
            return 'challenges'
        else:
            return 'general'
    
    def _check_answer_appropriateness(self, question_type: str, question: str, answer: str) -> float:
        """질문 유형별 답변 적절성 검사"""
        answer_lower = answer.lower()
        
        # 기본 점수
        score = 0.5
        
        # 질문 유형별 적절성 키워드
        appropriateness_keywords = {
            'self_introduction': ['저는', '제가', '이름', '전공', '학교', '회사'],
            'strengths': ['잘', '좋은', '능력', '실력', '장점', '강점'],
            'weaknesses': ['부족', '약점', '개선', '노력', '보완'],
            'experience': ['했습니다', '경험', '프로젝트', '업무', '참여'],
            'motivation': ['때문에', '이유', '동기', '관심', '좋아서'],
            'goals': ['목표', '계획', '하고싶다', '되고싶다', '미래'],
            'challenges': ['어려웠지만', '힘들었지만', '극복', '해결', '노력']
        }
        
        # 해당 유형의 키워드가 포함되어 있는지 확인
        if question_type in appropriateness_keywords:
            keywords = appropriateness_keywords[question_type]
            matches = sum(1 for kw in keywords if kw in answer_lower)
            
            if matches > 0:
                score += 0.3  # 적절한 키워드 보너스
            
            # 답변 길이 적절성 (너무 짧으면 감점)
            if len(answer.strip()) < 5:
                score -= 0.2
            elif len(answer.strip()) > 20:
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_final_context_score(self, semantic: float, keyword: float, intent: float) -> float:
        """종합 맥락 점수 계산 (가중평균)"""
        # 가중치: 의미적 유사도 50%, 키워드 겹침 30%, 의도 일치 20%
        weights = {
            'semantic': 0.5,
            'keyword': 0.3,
            'intent': 0.2
        }
        
        final_score = (
            semantic * weights['semantic'] +
            keyword * weights['keyword'] +
            intent * weights['intent']
        )
        
        return float(final_score)
    
    def _get_detailed_analysis(self, question: str, answer: str, 
                             semantic: float, keyword: float, intent: float) -> Dict[str, Any]:
        """상세 분석 정보 생성"""
        question_type = self._classify_question_type(question)
        q_keywords = self._extract_keywords(question)
        a_keywords = self._extract_keywords(answer)
        
        # 성능 등급 판정
        overall_score = self._calculate_final_context_score(semantic, keyword, intent)
        if overall_score >= 0.8:
            grade = "우수"
        elif overall_score >= 0.6:
            grade = "양호"
        elif overall_score >= 0.4:
            grade = "보통"
        else:
            grade = "미흡"
        
        return {
            'question_type': question_type,
            'question_keywords': q_keywords,
            'answer_keywords': a_keywords,
            'grade': grade,
            'recommendations': self._generate_recommendations(overall_score, question_type)
        }
    
    def _generate_recommendations(self, score: float, question_type: str) -> list:
        """점수와 질문 유형에 따른 개선 권장사항"""
        recommendations = []
        
        if score < 0.4:
            recommendations.append("질문의 핵심 키워드를 답변에 포함해보세요")
            recommendations.append("질문의 의도를 더 명확히 파악해보세요")
        elif score < 0.6:
            recommendations.append("답변을 더 구체적으로 작성해보세요")
        
        # 질문 유형별 권장사항
        type_recommendations = {
            'self_introduction': ["개인 정보와 전문성을 균형있게 소개하세요"],
            'strengths': ["구체적인 사례를 들어 강점을 설명하세요"],
            'weaknesses': ["개선 노력과 함께 약점을 언급하세요"],
            'experience': ["구체적인 성과와 배운 점을 포함하세요"],
            'motivation': ["진정성 있는 동기를 구체적으로 설명하세요"],
            'goals': ["현실적이면서도 구체적인 목표를 제시하세요"]
        }
        
        if question_type in type_recommendations:
            recommendations.extend(type_recommendations[question_type])
        
        return recommendations