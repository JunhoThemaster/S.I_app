import React, { useState, useEffect, useCallback } from 'react';
import { interviewAPI, InterviewSetupResponse, SpeechAnalysisResponse, FinalFeedbackResponse } from '../api/interview';
import AudioRecorder from '../components/AudioRecorder';

interface QuestionFeedback {
  questionNumber: number;
  question: string;
  answer: string;
  contextScore: number;
  contextGrade: string;
  contextFeedback: string;
  recommendations: string[];
  overallScore: number;
}

const InterviewSimulator: React.FC = () => {
  const [jobCategories, setJobCategories] = useState<string[]>([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [numQuestions, setNumQuestions] = useState(3);
  
  const [interviewSession, setInterviewSession] = useState<InterviewSetupResponse | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<SpeechAnalysisResponse[]>([]);
  const [finalFeedback, setFinalFeedback] = useState<FinalFeedbackResponse | null>(null);
  const [questionFeedbacks, setQuestionFeedbacks] = useState<QuestionFeedback[]>([]);
  
  const [chatMessages, setChatMessages] = useState<Array<{
    type: 'question' | 'answer';
    text: string;
    number: number;
    timestamp: string;
  }>>([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState<'setup' | 'interview' | 'results'>('setup');
  const [isInterviewComplete, setIsInterviewComplete] = useState(false);

  // 직무 카테고리 로드
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const data = await interviewAPI.getJobCategories();
        setJobCategories(data.categories);
        if (data.categories.length > 0) setSelectedJob(data.categories[0]);
      } catch (error) {
        console.error('카테고리 로드 실패:', error);
      }
    };
    loadCategories();
  }, []);

  // 채팅 메시지 추가
  const addMessage = useCallback((type: 'question' | 'answer', text: string, number: number) => {
    setChatMessages(prev => [...prev, {
      type, text, number,
      timestamp: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
    }]);
  }, []);

  // OpenAI 기반 개별 질문 피드백 생성
  const generateQuestionFeedback = async (question: string, answer: string, analysis: SpeechAnalysisResponse): Promise<QuestionFeedback> => {
    try {
      console.log('🤖 OpenAI로 개별 질문 피드백 생성 시작...');
      
      // 종료 키워드로만 이루어진 답변인지 확인
      const endKeywords = ['이상', '끝', '완료', '마침', '이상입니다', '끝입니다', '완료입니다', '마칩니다'];
      const isOnlyEndKeyword = endKeywords.some(keyword => 
        answer.trim().toLowerCase() === keyword.toLowerCase() || 
        answer.trim() === keyword + '입니다'
      );

      let contextFeedback = '';

      if (isOnlyEndKeyword || answer.length < 5) {
        // 종료 키워드나 너무 짧은 답변의 경우
        contextFeedback = "답변이 충분하지 않습니다. 질문에 대한 구체적인 경험이나 생각을 더 자세히 설명해보세요.";
      } else {
        try {
          // 백엔드 OpenAI API 호출
          console.log('📡 백엔드 OpenAI API 호출...');
          const response = await fetch('http://localhost:8000/api/feedback/individual', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            },
            body: JSON.stringify({ 
              question: question,
              answer: answer 
            })
          });

          console.log('📡 API 응답 상태:', response.status);

          if (response.ok) {
            const aiResult = await response.json();
            console.log('✅ OpenAI 피드백 받음:', aiResult);
            contextFeedback = aiResult.feedback || '분석을 완료했습니다.';
          } else {
            console.error('❌ API 호출 실패:', response.status, response.statusText);
            // API 실패시 백엔드 분석 결과 사용
            contextFeedback = analysis.recommendations.length > 0 
              ? analysis.recommendations.join(' ') 
              : '질문에 대한 답변을 더 구체적으로 해보세요.';
          }
        } catch (fetchError) {
          console.error('❌ OpenAI API 호출 중 오류:', fetchError);
          contextFeedback = '피드백 생성 중 오류가 발생했습니다. 답변을 더 구체적으로 작성해보세요.';
        }
      }
      
      return {
        questionNumber: analysis.question_index + 1,
        question,
        answer,
        contextScore: analysis.context_matching * 100,
        contextGrade: analysis.context_grade,
        contextFeedback,
        recommendations: analysis.recommendations,
        overallScore: analysis.overall_score
      };
    } catch (error) {
      console.error('❌ 전체 피드백 생성 실패:', error);
      return {
        questionNumber: analysis.question_index + 1,
        question,
        answer,
        contextScore: analysis.context_matching * 100,
        contextGrade: analysis.context_grade,
        contextFeedback: '답변을 더 구체적이고 상세하게 작성해보세요.',
        recommendations: ['구체적인 사례를 포함해보세요', '경험을 바탕으로 설명해보세요', '결과와 배운 점을 추가해보세요'],
        overallScore: analysis.overall_score
      };
    }
  };

  // 면접 시작
  const startInterview = async () => {
    if (!selectedJob) return alert('직무를 선택해주세요.');

    setIsLoading(true);
    try {
      const session = await interviewAPI.setupInterview(selectedJob, numQuestions);
      setInterviewSession(session);
      setStep('interview');
      setCurrentQuestionIndex(0);
      setAnalysisResults([]);
      setQuestionFeedbacks([]);
      setIsInterviewComplete(false);
      
      setChatMessages([
        { type: 'question', text: '안녕하세요! AI 면접에 참여해주셔서 감사합니다.', number: 0, timestamp: new Date().toLocaleTimeString('ko-KR') },
        { type: 'question', text: session.questions[0], number: 1, timestamp: new Date().toLocaleTimeString('ko-KR') }
      ]);
    } catch (error) {
      console.error('면접 시작 실패:', error);
      alert('면접 시작에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 음성 분석 완료 후 처리
  const handleAudioRecorded = async (audioBlob: Blob) => {
    if (!interviewSession) return;

    setIsLoading(true);
    try {
      const analysis = await interviewAPI.analyzeAudio(interviewSession.session_id, currentQuestionIndex, audioBlob);
      setAnalysisResults(prev => [...prev, analysis]);
      
      const questionFeedback = await generateQuestionFeedback(
        interviewSession.questions[currentQuestionIndex], analysis.text, analysis
      );
      setQuestionFeedbacks(prev => [...prev, questionFeedback]);
      
      addMessage('answer', analysis.text, currentQuestionIndex + 1);
      
      setTimeout(handleNextQuestion, 1500);
    } catch (error) {
      console.error('음성 분석 실패:', error);
      alert('음성 분석에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 다음 질문으로 진행
  const handleNextQuestion = useCallback(() => {
    if (!interviewSession) return;
    
    const nextIndex = currentQuestionIndex + 1;
    
    if (nextIndex < interviewSession.questions.length) {
      setCurrentQuestionIndex(nextIndex);
      addMessage('question', interviewSession.questions[nextIndex], nextIndex + 1);
      setIsRecording(true);
    } else {
      setIsInterviewComplete(true);
      setIsRecording(false);
      addMessage('question', '모든 질문이 완료되었습니다. 면접 완료 버튼을 눌러주세요.', 999);
    }
  }, [currentQuestionIndex, interviewSession, addMessage]);

  // 자동 녹음 시작
  useEffect(() => {
    if (step === 'interview' && interviewSession && !isRecording && !isInterviewComplete && !isLoading) {
      setTimeout(() => setIsRecording(true), 2000);
    }
  }, [step, interviewSession, isRecording, isInterviewComplete, isLoading]);

  // 최종 피드백 생성
  const generateFinalFeedback = async () => {
    if (!interviewSession) return;

    setIsLoading(true);
    try {
      const feedback = await interviewAPI.generateFeedback(interviewSession.session_id);
      setFinalFeedback(feedback);
      addMessage('question', `🎉 면접 완료!\n\n종합 점수: ${feedback.overall_score}점`, 999);
      setStep('results');
    } catch (error) {
      console.error('피드백 생성 실패:', error);
      alert('피드백 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetInterview = () => {
    setInterviewSession(null);
    setCurrentQuestionIndex(0);
    setAnalysisResults([]);
    setFinalFeedback(null);
    setQuestionFeedbacks([]);
    setChatMessages([]);
    setIsInterviewComplete(false);
    setIsRecording(false);
    setStep('setup');
  };

  // 설정 화면
  if (step === 'setup') {
    return (
      <div style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>🤖 AI 면접 시뮬레이터</h1>
        
        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>직무 선택</label>
          <select 
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            style={{ width: '100%', padding: '0.75rem', fontSize: '1rem', border: '2px solid #ddd', borderRadius: '8px' }}
          >
            {jobCategories.map(job => <option key={job} value={job}>{job}</option>)}
          </select>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            질문 개수: {numQuestions}개
          </label>
          <input
            type="range" min="1" max="5" value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>

        <button
          onClick={startInterview}
          disabled={isLoading}
          style={{
            width: '100%', padding: '1rem', fontSize: '1.1rem',
            backgroundColor: '#007bff', color: 'white', border: 'none',
            borderRadius: '8px', cursor: 'pointer', opacity: isLoading ? 0.6 : 1
          }}
        >
          {isLoading ? '준비 중...' : '면접 시작'}
        </button>
      </div>
    );
  }

  // 면접 화면
  if (step === 'interview' && interviewSession) {
    const progress = ((currentQuestionIndex + 1) / interviewSession.questions.length) * 100;

    return (
      <div style={{ display: 'flex', height: '100vh' }}>
        {/* 면접 패널 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #e0e0e0' }}>
          <div style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', color: 'white', padding: '20px', textAlign: 'center' }}>
            <h1 style={{ margin: '0 0 10px 0' }}>🎤 AI 면접</h1>
            <div style={{ background: 'rgba(255,255,255,0.2)', padding: '10px', borderRadius: '10px' }}>
              <div>직무: {selectedJob}</div>
              <div style={{ background: '#e0e0e0', height: '6px', borderRadius: '3px', margin: '10px 0', overflow: 'hidden' }}>
                <div style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', height: '100%', width: `${progress}%`, borderRadius: '3px', transition: 'width 0.3s ease' }} />
              </div>
              <div>{currentQuestionIndex + 1} / {interviewSession.questions.length}</div>
            </div>
          </div>

          <div style={{ flex: 1, padding: '30px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: '#f8f9fa' }}>
            {!isInterviewComplete ? (
              <>
                <div style={{ background: 'white', borderRadius: '15px', padding: '30px', boxShadow: '0 5px 15px rgba(0,0,0,0.1)', maxWidth: '500px', width: '100%', textAlign: 'center', marginBottom: '30px' }}>
                  <div style={{ color: '#667eea', fontWeight: 'bold', fontSize: '18px', marginBottom: '15px' }}>
                    질문 {currentQuestionIndex + 1}
                  </div>
                  <div style={{ fontSize: '20px', lineHeight: '1.6', color: '#333' }}>
                    {interviewSession.questions[currentQuestionIndex]}
                  </div>
                </div>

                <AudioRecorder
                  onRecordingComplete={handleAudioRecorded}
                  isRecording={isRecording}
                  onRecordingStart={() => setIsRecording(true)}
                  onRecordingStop={() => setIsRecording(false)}
                  continuousMode={true}
                />

                {isLoading && (
                  <div style={{ marginTop: '15px', padding: '10px 20px', borderRadius: '20px', background: '#fff3e0', color: '#f57c00', fontWeight: 'bold' }}>
                    🔄 음성 분석 중...
                  </div>
                )}
              </>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <div style={{ background: 'white', borderRadius: '15px', padding: '30px', boxShadow: '0 5px 15px rgba(0,0,0,0.1)', maxWidth: '500px', marginBottom: '30px' }}>
                  <div style={{ color: '#667eea', fontWeight: 'bold', fontSize: '18px', marginBottom: '15px' }}>면접 완료</div>
                  <div style={{ fontSize: '20px', lineHeight: '1.6', color: '#333' }}>모든 질문이 완료되었습니다.</div>
                </div>
                <button
                  onClick={generateFinalFeedback}
                  disabled={isLoading}
                  style={{ padding: '15px 30px', background: '#4caf50', color: 'white', border: 'none', borderRadius: '10px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer', opacity: isLoading ? 0.6 : 1 }}
                >
                  {isLoading ? '피드백 생성 중...' : '면접 완료'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* 채팅 패널 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#f0f4f8' }}>
          <div style={{ background: 'white', padding: '20px', borderBottom: '1px solid #e0e0e0', textAlign: 'center' }}>
            <h2 style={{ margin: 0, color: '#333', fontSize: '20px' }}>💬 면접 대화</h2>
          </div>
          <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {chatMessages.map((message, index) => (
              <div
                key={`${message.type}-${message.number}-${index}`}
                style={{
                  maxWidth: '80%',
                  padding: '15px 20px',
                  borderRadius: '18px',
                  fontSize: '14px',
                  lineHeight: '1.4',
                  alignSelf: message.type === 'question' ? 'flex-start' : 'flex-end',
                  background: message.type === 'question' ? 'white' : '#667eea',
                  color: message.type === 'question' ? '#333' : 'white',
                  border: message.type === 'question' ? '2px solid #667eea' : 'none',
                  position: 'relative'
                }}
              >
                {message.number > 0 && message.number < 999 && (
                  <div style={{
                    position: 'absolute',
                    top: '-10px',
                    [message.type === 'question' ? 'left' : 'right']: '15px',
                    background: message.type === 'question' ? '#667eea' : 'white',
                    color: message.type === 'question' ? 'white' : '#667eea',
                    width: '24px', height: '24px', borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 'bold', fontSize: '12px'
                  }}>
                    {message.type === 'question' ? 'Q' : 'A'}{message.number}
                  </div>
                )}
                <div style={{ whiteSpace: 'pre-line' }}>{message.text}</div>
                <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '8px', textAlign: message.type === 'answer' ? 'right' : 'left' }}>
                  {message.type === 'question' ? '면접관' : '나'} • {message.timestamp}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 결과 화면 (간소화)
  if (step === 'results' && finalFeedback) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa', padding: '2rem 0' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '0 2rem' }}>
          
          {/* 전체 결과 */}
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h1>🎉 면접 완료!</h1>
            <div style={{
              fontSize: '3rem', fontWeight: 'bold', marginBottom: '1rem',
              color: finalFeedback.overall_score >= 80 ? '#28a745' : finalFeedback.overall_score >= 60 ? '#ffc107' : '#dc3545'
            }}>
              {finalFeedback.overall_score.toFixed(1)}점
            </div>
            <p style={{ fontSize: '1.1rem', color: '#666' }}>
              {finalFeedback.overall_score >= 80 ? '🌟 훌륭한 면접!' : finalFeedback.overall_score >= 60 ? '👍 좋은 면접!' : '💪 더 연습하면 좋아질 거예요!'}
            </p>
          </div>

          {/* 개별 질문 피드백 */}
          {questionFeedbacks.map((feedback, index) => (
            <div key={index} style={{ backgroundColor: '#fff', borderRadius: '15px', padding: '2rem', marginBottom: '2rem', boxShadow: '0 5px 15px rgba(0,0,0,0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ color: '#007bff', margin: 0 }}>Q{feedback.questionNumber}. 질문별 분석</h3>
                <div style={{ padding: '0.5rem 1rem', borderRadius: '20px', backgroundColor: feedback.overallScore >= 80 ? '#d4edda' : feedback.overallScore >= 60 ? '#fff3cd' : '#f8d7da', color: feedback.overallScore >= 80 ? '#155724' : feedback.overallScore >= 60 ? '#856404' : '#721c24', fontWeight: 'bold' }}>
                  {feedback.overallScore.toFixed(1)}점
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#495057', marginBottom: '0.5rem' }}>❓ 질문</h4>
                <p style={{ backgroundColor: '#f8f9fa', padding: '1rem', borderRadius: '8px', margin: 0 }}>{feedback.question}</p>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#495057', marginBottom: '0.5rem' }}>💬 답변</h4>
                <p style={{ backgroundColor: '#e3f2fd', padding: '1rem', borderRadius: '8px', margin: 0 }}>"{feedback.answer}"</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <div>
                  <h4 style={{ color: '#007bff', marginBottom: '1rem' }}>🎯 문맥 적합성</h4>
                  <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '10px' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: feedback.contextScore >= 80 ? '#28a745' : feedback.contextScore >= 60 ? '#ffc107' : '#dc3545' }}>
                      {feedback.contextScore.toFixed(1)}점
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#666', marginTop: '0.5rem' }}>{feedback.contextGrade}</div>
                  </div>
                </div>
                <div>
                  <h4 style={{ color: '#28a745', marginBottom: '1rem' }}>🎵 음성 품질</h4>
                  <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '10px' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: feedback.overallScore >= 80 ? '#28a745' : feedback.overallScore >= 60 ? '#ffc107' : '#dc3545' }}>
                      {feedback.overallScore.toFixed(1)}점
                    </div>
                    <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>발음, 톤, 속도</div>
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#ffc107', marginBottom: '1rem' }}>🤖 AI 피드백</h4>
                <div style={{ backgroundColor: '#fff8e1', padding: '1.5rem', borderRadius: '10px', border: '2px solid #ffecb3' }}>
                  <p style={{ margin: 0, fontSize: '1rem', lineHeight: '1.6' }}>{feedback.contextFeedback}</p>
                </div>
              </div>

              {feedback.recommendations.length > 0 && (
                <div>
                  <h4 style={{ color: '#dc3545', marginBottom: '1rem' }}>💡 개선 권장사항</h4>
                  <ul style={{ backgroundColor: '#ffebee', padding: '1.5rem', borderRadius: '10px', margin: 0, paddingLeft: '2rem' }}>
                    {feedback.recommendations.map((rec, idx) => (
                      <li key={idx} style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          {/* 종합 피드백 */}
          <div style={{ backgroundColor: '#fff', borderRadius: '20px', padding: '3rem', marginBottom: '2rem', boxShadow: '0 10px 30px rgba(0,0,0,0.1)', border: '3px solid #007bff' }}>
            <h2 style={{ textAlign: 'center', marginBottom: '2rem', color: '#007bff', fontSize: '2rem' }}>📊 종합 분석 결과</h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
              <div style={{ backgroundColor: '#e8f5e8', padding: '1.5rem', borderRadius: '12px', border: '2px solid #28a745' }}>
                <h3 style={{ color: '#28a745', marginBottom: '1rem' }}>💪 전체 강점</h3>
                <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                  {finalFeedback.strengths.map((strength, index) => (
                    <li key={index} style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{strength}</li>
                  ))}
                </ul>
              </div>
              <div style={{ backgroundColor: '#fff3e0', padding: '1.5rem', borderRadius: '12px', border: '2px solid #ffc107' }}>
                <h3 style={{ color: '#ffc107', marginBottom: '1rem' }}>🎯 개선 영역</h3>
                <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                  {finalFeedback.improvement_areas.map((area, index) => (
                    <li key={index} style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{area}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <h3 style={{ marginBottom: '1rem', color: '#007bff' }}>🎤 음성 분석 결과</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '12px' }}>
                  <h4 style={{ color: '#007bff', margin: '0 0 1rem 0' }}>🗣️ 전달력</h4>
                  <p style={{ margin: 0, fontSize: '1rem', lineHeight: '1.4' }}>{finalFeedback.delivery_feedback}</p>
                </div>
                <div style={{ textAlign: 'center', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '12px' }}>
                  <h4 style={{ color: '#28a745', margin: '0 0 1rem 0' }}>🎵 음성 톤</h4>
                  <p style={{ margin: 0, fontSize: '1rem', lineHeight: '1.4' }}>{finalFeedback.tone_feedback}</p>
                </div>
                <div style={{ textAlign: 'center', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '12px' }}>
                  <h4 style={{ color: '#ffc107', margin: '0 0 1rem 0' }}>⏱️ 말하기 리듬</h4>
                  <p style={{ margin: 0, fontSize: '1rem', lineHeight: '1.4' }}>{finalFeedback.rhythm_feedback}</p>
                </div>
              </div>
            </div>

            <div style={{ backgroundColor: '#e7f3ff', padding: '2rem', borderRadius: '15px', marginBottom: '2rem' }}>
              <h3 style={{ color: '#007bff', marginBottom: '1rem' }}>💡 전체 개선 권장사항</h3>
              <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
                {finalFeedback.recommendations.map((rec, index) => (
                  <li key={index} style={{ marginBottom: '0.8rem', fontSize: '1.1rem', lineHeight: '1.5' }}>{rec}</li>
                ))}
              </ul>
            </div>

            <div style={{ backgroundColor: '#f8f9fa', padding: '2rem', borderRadius: '15px', textAlign: 'center' }}>
              <h3 style={{ color: '#495057', marginBottom: '1.5rem' }}>📈 점수 요약</h3>
              <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                {finalFeedback.individual_scores.map((score, index) => (
                  <div key={index} style={{ textAlign: 'center', minWidth: '80px' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: score >= 80 ? '#28a745' : score >= 60 ? '#ffc107' : '#dc3545', marginBottom: '0.5rem' }}>
                      {score.toFixed(1)}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>질문 {index + 1}</div>
                  </div>
                ))}
                <div style={{ textAlign: 'center', minWidth: '80px', borderLeft: '2px solid #007bff', paddingLeft: '1rem' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#007bff', marginBottom: '0.5rem' }}>
                    {finalFeedback.overall_score.toFixed(1)}
                  </div>
                  <div style={{ fontSize: '1rem', color: '#007bff', fontWeight: 'bold' }}>종합</div>
                </div>
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'center' }}>
            <button
              onClick={resetInterview}
              style={{
                padding: '1rem 2rem', fontSize: '1.2rem', backgroundColor: '#007bff',
                color: 'white', border: 'none', borderRadius: '12px', cursor: 'pointer',
                boxShadow: '0 5px 15px rgba(0,123,255,0.3)'
              }}
            >
              🔄 새로운 면접 시작
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default InterviewSimulator;