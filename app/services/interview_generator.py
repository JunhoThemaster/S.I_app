import random
from typing import List
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

load_dotenv()

# OpenAI 1.0+ 새로운 방식
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    print("✅ OpenAI 1.0+ 라이브러리 로드 성공")
except ImportError:
    print("⚠️ OpenAI 라이브러리 없음 - 백업 질문 사용")
    OPENAI_AVAILABLE = False

class InterviewGenerator:
    def __init__(self):
        # OpenAI 클라이언트 초기화 (새로운 방식)
        self.openai_client = OpenAI() if OPENAI_AVAILABLE else None
        
        # 직무별 핵심 정보 (간소화)
        self.job_domains = {
            "Management": {
                "areas": ["리더십", "전략기획", "인사관리"],
                "skills": ["의사결정", "팀빌딩", "갈등해결"],
                "scenarios": ["팀 갈등 상황", "예산 부족", "목표 미달"]
            },
            "Sales Marketing": {
                "areas": ["고객관리", "시장분석", "영업전략"],
                "skills": ["설득력", "분석력", "협상"],
                "scenarios": ["신규시장 진입", "경쟁사 대응", "고객 이탈"]
            },
            "Public Service": {
                "areas": ["정책수립", "행정업무", "시민서비스"],
                "skills": ["공정성", "투명성", "소통능력"],
                "scenarios": ["민원 처리", "정책 반발", "예산 삭감"]
            },
            "RND": {
                "areas": ["기술연구", "제품개발", "데이터분석"],
                "skills": ["창의성", "논리적사고", "문제해결"],
                "scenarios": ["연구 실패", "기술 한계", "상용화 어려움"]
            },
            "ICT": {
                "areas": ["시스템개발", "네트워크관리", "보안"],
                "skills": ["기술전문성", "문제해결", "학습능력"],
                "scenarios": ["시스템 장애", "보안 위협", "신기술 도입"]
            },
            "Design": {
                "areas": ["UX/UI설계", "시각디자인", "사용자조사"],
                "skills": ["창의성", "미적감각", "사용자중심사고"],
                "scenarios": ["사용자 불만", "디자인 수정", "브랜드 변경"]
            },
            "Product Manufacturing": {
                "areas": ["생산관리", "품질관리", "안전관리"],
                "skills": ["정확성", "효율성", "안전의식"],
                "scenarios": ["품질 불량", "생산 차질", "안전 사고"]
            }
        }

    def generate_questions(self, job_position: str, num_questions: int) -> List[str]:
        """AI 질문 생성 또는 백업 질문 제공"""
        if job_position not in self.job_domains:
            raise ValueError(f"지원하지 않는 직무: {job_position}")
        
        try:
            # OpenAI 클라이언트가 있으면 AI 질문 생성
            if self.openai_client:
                ai_questions = self._generate_ai_questions(job_position, num_questions)
                if ai_questions and len(ai_questions) >= num_questions-1:
                    return ["자기소개를 해주세요."] + ai_questions[:num_questions-1]
            
            # 백업 질문 사용
            print(f"🔄 백업 질문 사용 (OpenAI 클라이언트: {self.openai_client is not None})")
            return self._generate_fallback_questions(job_position, num_questions)
            
        except Exception as e:
            print(f"⚠️ AI 질문 생성 실패: {e}")
            return self._generate_fallback_questions(job_position, num_questions)

    def _generate_ai_questions(self, job_position: str, num_questions: int) -> List[str]:
        """OpenAI GPT를 사용한 질문 생성 (중복 방지 개선)"""
        domain = self.job_domains[job_position]
        
        # 세션별 고유 시드 추가
        import time
        session_seed = str(int(time.time() * 1000))[-6:]  # 마지막 6자리
        
        prompt = f"""
{job_position} 직무 면접 질문을 {num_questions-1}개 생성해주세요.

세션 ID: {session_seed} (매번 다른 질문 생성을 위한 고유값)

직무 정보:
- 핵심 영역: {', '.join(domain['areas'])}
- 주요 스킬: {', '.join(domain['skills'])}
- 상황 예시: {', '.join(domain['scenarios'])}

필수 요구사항:
1. 매번 완전히 새로운 질문들을 생성
2. 각 질문은 서로 다른 역량/상황을 다뤄야 함
3. 실무 중심의 구체적 경험을 묻는 질문
4. 창의적이고 다양한 관점의 질문
5. "자기소개"는 제외
6. 한국어로 작성

다양성 확보를 위한 카테고리 분산:
- 기술적 도전 경험
- 프로젝트 관리 경험  
- 문제 해결 사례
- 팀워크/협업 경험
- 창의적 아이디어 구현
- 실패 극복 사례
- 최신 기술 적용 경험

출력 형식 (각 줄에 하나씩):
질문1
질문2
질문3

⚠️ 금지사항:
- "실패를 어떻게 극복했는지" 같은 뻔한 패턴 반복 금지
- 비슷한 상황/경험을 묻는 질문 중복 금지
- 이전에 자주 사용된 질문 패턴 피하기
"""

        try:
            print(f"🎲 질문 생성 세션 ID: {session_seed}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"당신은 창의적인 HR 면접관입니다. 세션 {session_seed}에서 독창적이고 다양한 질문을 생성하세요. 절대 뻔한 질문은 만들지 마세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.9,  # 더 높은 다양성
                top_p=0.95,       # 창의성 증가
                frequency_penalty=0.8,  # 반복 방지
                presence_penalty=0.6    # 새로운 주제 선호
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📋 OpenAI 원본 응답:\n{content}")
            
            # 줄바꿈으로 분리하여 질문 추출
            questions = []
            for line in content.split('\n'):
                line = line.strip()
                if line and len(line) > 15:  # 더 긴 질문만
                    # 앞의 번호나 기호 제거
                    line = re.sub(r'^\s*[\d]+[\.|\)]\s*', '', line)
                    line = re.sub(r'^[\-\*\•\s]+', '', line)
                    if not line.endswith('?'):
                        line += '?'
                    
                    # 중복 확인 (유사도 체크)
                    is_duplicate = False
                    for existing_q in questions:
                        if self._is_similar_question(line, existing_q):
                            print(f"⚠️ 중복 질문 감지하여 제외: '{line[:50]}...'")
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        questions.append(line)
                        print(f"✅ 새로운 질문 추가: '{line[:50]}...'")
            
            print(f"🎯 최종 생성된 질문 {len(questions)}개:")
            for i, q in enumerate(questions[:num_questions-1], 1):
                print(f"   {i}. {q}")
                
            return questions[:num_questions-1]  # 필요한 개수만 반환
            
        except Exception as e:
            print(f"❌ OpenAI 질문 생성 실패: {e}")
            return []
    
    def _is_similar_question(self, q1: str, q2: str) -> bool:
        """두 질문이 유사한지 확인"""
        # 간단한 키워드 기반 유사도 검사
        q1_words = set(q1.lower().split())
        q2_words = set(q2.lower().split())
        
        # 공통 키워드 비율
        intersection = len(q1_words.intersection(q2_words))
        union = len(q1_words.union(q2_words))
        
        similarity = intersection / union if union > 0 else 0
        
        # 70% 이상 유사하면 중복으로 판단
        return similarity > 0.7

    def _parse_questions(self, content: str) -> List[str]:
        """응답에서 질문 추출"""
        lines = content.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 번호 제거 (예: "1. ", "2. ", "- ", "* ", "• ")
            line = re.sub(r'^\s*[\d]+[\.|\)]\s*', '', line)  # 숫자 + 점 또는 괄호 제거
            line = re.sub(r'^[\-\*\•\s]+', '', line)         # -, *, • 등 기호 제거
            
            # 질문 형태 판단 (물음표 포함 또는 특정 어미)
            if ('?' in line) or line.endswith(('요', '까', '나요')):
                if not line.endswith('?'):
                    line = line.rstrip('.요까나') + '?'
                questions.append(line)
        
        return questions

    def _validate_questions(self, questions: List[str]) -> List[str]:
        """질문 유효성 검증"""
        validated = []
        for q in questions:
            if 10 <= len(q) <= 200 and '자기소개' not in q:
                validated.append(q)
        return validated

    def _generate_fallback_questions(self, job_position: str, num_questions: int) -> List[str]:
        """백업 질문 생성 (OpenAI 없을 때)"""
        domain = self.job_domains[job_position]
        
        fallback_pool = [
            "자기소개를 해주세요.",
            f"{job_position} 분야에서 가장 중요한 역량은 무엇인가요?",
            f"{domain['areas'][0]} 관련 경험을 구체적으로 설명해주세요.",
            f"{domain['scenarios'][0]} 상황에서 어떻게 대처하시겠습니까?",
            f"{domain['skills'][0]} 능력을 보여줄 수 있는 사례가 있나요?",
            "팀워크가 중요한 상황에서의 경험을 공유해주세요.",
            "업무에서 가장 어려웠던 문제와 해결 과정을 설명해주세요.",
            "앞으로의 커리어 목표는 무엇인가요?",
            f"{job_position} 분야의 최신 트렌드에 대해 어떻게 생각하시나요?",
            "궁금한 점이 있다면 질문해주세요."
        ]
        
        selected = [fallback_pool[0]]  # 자기소개 고정
        remaining = fallback_pool[1:]
        selected.extend(random.sample(remaining, min(num_questions-1, len(remaining))))
        
        return selected[:num_questions]

    def get_available_positions(self) -> List[str]:
        """사용 가능한 직무 목록"""
        return list(self.job_domains.keys())

    def get_position_info(self, job_position: str) -> dict:
        """직무 정보 반환"""
        return self.job_domains.get(job_position, {})