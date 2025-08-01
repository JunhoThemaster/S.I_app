import random
from typing import List
import openai
import os

class InterviewGenerator:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY', '')
        
        # 직무별 핵심 정보 (간소화)
        self.job_domains = {
            "Management": {
                "areas": ["리더십", "전략기획", "인사관리", "재무관리"],
                "skills": ["의사결정", "팀빌딩", "갈등해결", "성과관리"],
                "scenarios": ["팀 갈등", "예산 부족", "목표 미달", "조직 개편"]
            },
            "Sales Marketing": {
                "areas": ["고객관리", "시장분석", "브랜드관리", "영업전략"],
                "skills": ["설득력", "분석력", "창의성", "협상"],
                "scenarios": ["신규시장 진입", "경쟁사 대응", "고객 이탈", "매출 부진"]
            },
            "Public Service": {
                "areas": ["정책수립", "행정업무", "시민서비스", "예산관리"],
                "skills": ["공정성", "투명성", "책임감", "소통능력"],
                "scenarios": ["민원 처리", "정책 반발", "예산 삭감", "갈등 조정"]
            },
            "RND": {
                "areas": ["기술연구", "제품개발", "실험설계", "데이터분석"],
                "skills": ["창의성", "논리적사고", "문제해결", "분석력"],
                "scenarios": ["연구 실패", "예산 부족", "기술 한계", "상용화 어려움"]
            },
            "ICT": {
                "areas": ["시스템개발", "네트워크관리", "보안", "클라우드"],
                "skills": ["기술전문성", "문제해결", "학습능력", "혁신사고"],
                "scenarios": ["시스템 장애", "보안 위협", "레거시 전환", "신기술 도입"]
            },
            "Design": {
                "areas": ["UX/UI설계", "시각디자인", "사용자조사", "브랜딩"],
                "skills": ["창의성", "미적감각", "사용자중심사고", "소통능력"],
                "scenarios": ["사용자 불만", "디자인 수정", "브랜드 변경", "기술 제약"]
            },
            "Product Manufacturing": {
                "areas": ["생산관리", "품질관리", "안전관리", "원가관리"],
                "skills": ["정확성", "효율성", "안전의식", "개선의지"],
                "scenarios": ["품질 불량", "생산 차질", "안전 사고", "원가 상승"]
            }
        }

    def generate_questions(self, job_position: str, num_questions: int) -> List[str]:
        """AI 기반 질문 생성 또는 백업 질문 제공"""
        if job_position not in self.job_domains:
            raise ValueError(f"지원하지 않는 직무: {job_position}")
        
        try:
            # AI 질문 생성 시도
            ai_questions = self._generate_ai_questions(job_position, num_questions)
            if ai_questions and len(ai_questions) >= num_questions:
                return ["자기소개를 해주세요."] + ai_questions[:num_questions-1]
            else:
                return self._generate_fallback_questions(job_position, num_questions)
        except:
            return self._generate_fallback_questions(job_position, num_questions)

    def _generate_ai_questions(self, job_position: str, num_questions: int) -> List[str]:
        """OpenAI를 사용한 질문 생성"""
        domain = self.job_domains[job_position]
        
        prompt = f"""
{job_position} 직무 면접 질문 {num_questions-1}개를 생성해주세요.

직무 정보:
- 핵심 영역: {', '.join(domain['areas'])}
- 주요 스킬: {', '.join(domain['skills'])}
- 상황 예시: {', '.join(domain['scenarios'])}

요구사항:
1. 실무 상황과 연관된 구체적인 질문
2. 역량 평가가 가능한 질문
3. "자기소개" 제외
4. 한국어로 작성
5. 각 질문을 한 줄씩 작성

{num_questions-1}개의 질문을 생성하세요:
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "당신은 전문 HR 면접관입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.8
            )
            
            content = response.choices[0].message.content.strip()
            questions = self._parse_questions(content)
            return self._validate_questions(questions)
            
        except Exception as e:
            print(f"AI 질문 생성 실패: {e}")
            return []

    def _parse_questions(self, content: str) -> List[str]:
        """응답에서 질문 추출"""
        import re
        lines = content.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 번호 제거
            line = re.sub(r'^[\d\.\-\*\•\s]*', '', line)
            
            # 질문 형태인지 확인
            if line and ('?' in line or line.endswith(('요', '까'))):
                if not line.endswith('?'):
                    line = line.rstrip('.요까') + '?'
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
        """백업 질문 생성"""
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
            "마지막으로 궁금한 점이 있다면 질문해주세요."
        ]
        
        # 자기소개 + 랜덤 선택
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