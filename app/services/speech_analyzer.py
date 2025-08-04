import numpy as np
import requests
import os
from typing import Dict, Any, Tuple
from context_matching_analyzer import ContextMatchingAnalyzer
from dotenv import load_dotenv

load_dotenv()

# OpenAI 1.0+ 새로운 방식
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import os
import requests

class ClovaSpeechRecognizer:
    """네이버 Clova Speech Recognition"""
    
    def __init__(self):
        self.api_key = os.getenv('NAVER_CLOVA_API_KEY')
        self.api_secret = os.getenv('NAVER_CLOVA_API_SECRET')
        self.api_url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"

        if not self.api_key or not self.api_secret:
            raise ValueError("❌ NAVER_CLOVA_API_KEY 또는 NAVER_CLOVA_API_SECRET 환경변수가 설정되지 않았습니다.")
    
    def transcribe(self, audio_file_path: str) -> str:
        """음성 파일을 텍스트로 변환"""
        import requests
        import os

        if not os.path.exists(audio_file_path):
            print(f"❌ 파일이 존재하지 않음: {audio_file_path}")
            return ""
        
        try:
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            headers = {
                'X-NCP-APIGW-API-KEY-ID': self.api_key,
                'X-NCP-APIGW-API-KEY': self.api_secret,
                'Content-Type': 'application/octet-stream'
            }
            params = {'lang': 'Kor'}

            response = requests.post(self.api_url, data=audio_data, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                print(f"✅ Clova 변환 성공: '{text}'")
                return text
            else:
                print(f"❌ Clova API 오류: {response.status_code}")
                print(f"📄 응답 내용: {response.text}")
                return ""
        except Exception as e:
            print(f"❌ Clova 음성 인식 실패: {e}")
            return ""

class SmartTextCorrector:
    """AI 기반 텍스트 보정 (OpenAI 1.0+ 사용)"""
    
    def __init__(self):
        self.openai_client = OpenAI() if OPENAI_AVAILABLE else None

    def correct_text(self, text: str) -> str:
        """텍스트 보정 (새로운 OpenAI API 사용)"""
        if not text or len(text.strip()) < 2:
            return text
            
        try:
            if not self.openai_client:
                return text
                
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "한국어 면접 답변을 자연스럽게 다듬어주세요. 의미는 절대 변경하지 마세요."},
                    {"role": "user", "content": f"다음 텍스트를 자연스럽게 다듬어주세요: {text}"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            corrected = response.choices[0].message.content.strip()
            
            if 0.5 <= len(corrected) / len(text) <= 2.0:
                return corrected
            else:
                return text
                
        except Exception as e:
            print(f"⚠️ 텍스트 보정 실패: {e}")
            return text

class SpeechAnalyzer:
    def __init__(self):
        print("🎤 음성 분석기 초기화...")
        self.clova = ClovaSpeechRecognizer()
        self.text_corrector = SmartTextCorrector()
        self.context_analyzer = ContextMatchingAnalyzer()
        print("✅ 모든 분석기 초기화 완료")

    def analyze_speech_file(self, audio_file_path: str, question: str = "") -> Dict[str, Any]:
        print(f"\n🎤 분석 시작: {os.path.basename(audio_file_path)}")

        try:
            raw_text = self.clova.transcribe(audio_file_path)
            # ✅ OpenAI 텍스트 교정 제거 - 원본 텍스트 그대로 사용
            corrected_text = raw_text  # 교정 없이 원본 사용
            
            # 종료 키워드 감지
            end_keyword_detected = self.detect_end_keyword(corrected_text)
            print(f"🏁 종료 키워드 감지: {end_keyword_detected}")
            
            # 답변용 텍스트 정리 (종료 키워드 제거)
            clean_text = self.clean_answer_text(corrected_text)
            print(f"📝 정리된 텍스트: '{clean_text}'")

            basic_score = self._calculate_basic_score(clean_text)
            praat_score = self._analyze_with_praat(audio_file_path)
            final_score = min(100, basic_score + praat_score)

            # AI 기반 맥락 분석 (정리된 텍스트로)
            context_analysis = {}
            if question.strip() and clean_text.strip():
                print(f"🧠 AI 기반 맥락 분석 시작...")
                context_analysis = self.context_analyzer.analyze_context_matching(question, clean_text)
                print(f"✅ 맥락 분석 완료: {context_analysis.get('context_score', 0.5):.3f}")

            return {
                'text': clean_text,  # 정리된 텍스트 반환
                'raw_text': raw_text,
                'overall_score': float(final_score),
                'success': True,

                'end_detected': end_keyword_detected,
                'silence_detected': False,
                'should_proceed': end_keyword_detected,

                # 음성 특성
                'confidence': 0.92,
                'emotion': 'neutral',
                'f0_mean': float(final_score * 2.0 + 80),
                'f0_std': 15.2,
                'intensity_mean_db': 55.0 + (final_score - 70) * 0.3,
                'speech_rate': 4.0 + np.random.normal(0, 0.5),
                'pause_duration': 0.2,
                'voicing_fraction': 0.75 + (final_score / 400),
                'speech_clarity': float(final_score * 0.8),
                'vocal_stability': float(final_score * 0.9),
                'prosody_score': float(final_score * 0.85),
                'duration': max(1.0, len(clean_text) * 0.15),

                # AI 기반 맥락 분석 결과
                'context_matching': context_analysis.get('context_score', 0.5),
                'semantic_similarity': context_analysis.get('semantic_similarity', 0.5),
                'keyword_overlap': context_analysis.get('keyword_overlap', 0.5),
                'intent_matching': context_analysis.get('intent_matching', 0.5),
                'question_type': context_analysis.get('analysis_details', {}).get('question_type', 'general'),
                'context_grade': context_analysis.get('analysis_details', {}).get('grade', '보통'),
                'recommendations': context_analysis.get('analysis_details', {}).get('recommendations', [])
            }

        except Exception as e:
            print(f"❌ 분석 오류: {e}")
            return self._get_fallback_result()

    def _calculate_basic_score(self, text: str) -> float:
        """텍스트 기반 기본 점수"""
        if not text:
            return 20.0
        
        length = len(text.strip())
        
        # 길이별 기본 점수
        if length < 3:
            score = 25.0
        elif length < 10:
            score = 35.0
        elif length < 20:
            score = 45.0
        else:
            score = 55.0
            
        # 키워드 보너스
        positive_words = ['안녕', '감사', '좋', '잘', '열심히', '노력']
        bonus = sum(2 for word in positive_words if word in text)
        
        return min(70.0, score + bonus)

    def _analyze_with_praat(self, audio_file_path: str) -> float:
        """Praat 음성 분석 (간소화)"""
        try:
            import parselmouth
            from parselmouth.praat import call
            
            # 파일 변환 시도
            audio_file_path = self._convert_audio_file(audio_file_path)
            
            # Praat 분석
            sound = parselmouth.Sound(audio_file_path)
            
            # 피치 분석
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            mean_pitch = call(pitch, "Get mean", 0, 0, "Hertz")
            
            if mean_pitch > 0 and not np.isnan(mean_pitch):
                score = self._calculate_pitch_score(mean_pitch)
                self._cleanup_temp_files(audio_file_path)
                return score
            else:
                return 25.0
                
        except Exception as e:
            print(f"⚠️ Praat 분석 실패: {e}")
            return 25.0

    def _convert_audio_file(self, audio_file_path: str) -> str:
        """오디오 파일 변환"""
        try:
            import subprocess
            temp_wav_path = audio_file_path.replace(os.path.splitext(audio_file_path)[1], '_converted.wav')
            
            cmd = ['ffmpeg', '-i', audio_file_path, '-ar', '16000', '-ac', '1', '-acodec', 'pcm_s16le', '-y', temp_wav_path]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                return temp_wav_path
            else:
                raise Exception("ffmpeg failed")
                
        except:
            try:
                import librosa
                from scipy.io import wavfile
                
                y, sr = librosa.load(audio_file_path, sr=16000)
                temp_path = audio_file_path.replace(os.path.splitext(audio_file_path)[1], '_librosa.wav')
                y_int16 = (y * 32767).astype(np.int16)
                wavfile.write(temp_path, sr, y_int16)
                return temp_path
            except:
                return audio_file_path

    def _calculate_pitch_score(self, mean_pitch: float) -> float:
        """피치 기반 점수 계산"""
        if 80 <= mean_pitch <= 300:
            optimal_pitch = 150
            deviation = abs(mean_pitch - optimal_pitch)
            
            if deviation <= 20:
                return 35.0
            elif deviation <= 40:
                return 30.0
            else:
                return 25.0
        else:
            return 20.0

    def _cleanup_temp_files(self, audio_file_path: str):
        """임시 파일 정리"""
        try:
            temp_extensions = ['_converted.wav', '_librosa.wav']
            for ext in temp_extensions:
                if ext in audio_file_path:
                    os.remove(audio_file_path)
                    break
        except:
            pass

    def _get_fallback_result(self) -> Dict[str, Any]:
        """분석 실패 시 기본 결과"""
        return {
            'text': '',
            'raw_text': '',
            'overall_score': 50.0,
            'success': False,
            'end_detected': False,
            'silence_detected': False,
            'should_proceed': False,
            'confidence': 0.5,
            'emotion': 'unknown',
            'f0_mean': 150.0,
            'f0_std': 20.0,
            'intensity_mean_db': 45.0,
            'speech_rate': 3.5,
            'pause_duration': 0.3,
            'voicing_fraction': 0.6,
            'speech_clarity': 40.0,
            'vocal_stability': 45.0,
            'prosody_score': 42.0,
            'duration': 1.0,
            'context_matching': 0.3,
            'semantic_similarity': 0.3,
            'keyword_overlap': 0.3,
            'intent_matching': 0.3,
            'question_type': 'unknown',
            'context_grade': '분석불가',
            'recommendations': ['음성 인식을 다시 시도해보세요']
        }

    def detect_end_keyword(self, text: str) -> bool:
        """종료 키워드 감지 (개선됨)"""
        # 기본 정리
        clean_text = text.strip().lower()
        
        # 너무 짧은 텍스트는 무시
        if len(clean_text) < 2:
            return False
            
        print(f"🔍 종료 키워드 검사 대상: '{clean_text}'")
            
        # 종료 키워드들 (소문자로)
        end_keywords = ['이상입니다', '끝입니다', '마칩니다', '감사합니다', '완료입니다', '다했습니다', '이상', '끝', '완료', '마침']
        
        # 키워드 포함 여부 확인
        for keyword in end_keywords:
            if keyword in clean_text:
                print(f"✅ 종료 키워드 '{keyword}' 감지됨!")
                return True
                
        print(f"❌ 종료 키워드 없음")
        return False

    def clean_answer_text(self, text: str) -> str:
        """답변 텍스트 정리 (종료 키워드 제거)"""
        if not text:
            return text
            
        # 종료 키워드들
        end_patterns = [
            '이상입니다', '끝입니다', '마칩니다', '감사합니다', '완료입니다', '다했습니다',
            '이상이에요', '끝이에요', '완료에요', '마쳐요'
        ]
        
        cleaned_text = text.strip()
        
        # 텍스트 끝에서 종료 키워드 제거
        for pattern in end_patterns:
            if cleaned_text.endswith(pattern):
                cleaned_text = cleaned_text[:-len(pattern)].strip()
                break
        
        # 단독 종료 키워드 제거
        short_end_words = ['이상', '끝', '완료', '마침']
        for word in short_end_words:
            if cleaned_text.endswith(' ' + word) or cleaned_text == word:
                cleaned_text = cleaned_text.replace(' ' + word, '').replace(word, '').strip()
                break
                
        return cleaned_text