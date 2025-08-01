// src/pages/InterviewSimulator.tsx
import React, { useState, useEffect } from 'react';
import { interviewAPI, InterviewSetupResponse, SpeechAnalysisResponse, FinalFeedbackResponse } from '../api/interview';
import AudioRecorder from '../components/AudioRecorder';

const InterviewSimulator: React.FC = () => {
  // 설정 상태
  const [jobCategories, setJobCategories] = useState<string[]>([]);
  const [selectedJob, setSelectedJob] = useState('');
  const [numQuestions, setNumQuestions] = useState(3);
  
  // 면접 상태
  const [interviewSession, setInterviewSession] = useState<InterviewSetupResponse | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<SpeechAnalysisResponse[]>([]);
  const [finalFeedback, setFinalFeedback] = useState<FinalFeedbackResponse | null>(null);
  
  // UI 상태
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState<'setup' | 'interview' | 'results'>('setup');

  // 컴포넌트 마운트 시 직무 카테고리 로드
  useEffect(() => {
    loadJobCategories();
  }, []);

  const loadJobCategories = async () => {
    try {
      const data = await interviewAPI.getJobCategories();
      setJobCategories(data.categories);
      if (data.categories.length > 0) {
        setSelectedJob(data.categories[0]);
      }
    } catch (error) {
      console.error('직무 카테고리 로드 실패:', error);
      alert('직무 카테고리를 불러오는데 실패했습니다.');
    }
  };

  const startInterview = async () => {
    if (!selectedJob) {
      alert('직무를 선택해주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const session = await interviewAPI.setupInterview(selectedJob, numQuestions);
      setInterviewSession(session);
      setStep('interview');
      setCurrentQuestionIndex(0);
      setAnalysisResults([]);
    } catch (error) {
      console.error('면접 시작 실패:', error);
      alert('면접을 시작하는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioRecorded = async (audioBlob: Blob) => {
    if (!interviewSession) return;

    setIsLoading(true);
    try {
      const analysis = await interviewAPI.analyzeAudio(
        interviewSession.session_id,
        currentQuestionIndex,
        audioBlob
      );
      
      setAnalysisResults(prev => [...prev, analysis]);
      
      // 종료 키워드 감지 또는 마지막 질문인 경우
      if (analysis.end_detected || currentQuestionIndex >= interviewSession.questions.length - 1) {
        await generateFinalFeedback();
      } else {
        setCurrentQuestionIndex(prev => prev + 1);
      }
    } catch (error) {
      console.error('음성 분석 실패:', error);
      alert('음성 분석에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const generateFinalFeedback = async () => {
    if (!interviewSession) return;

    setIsLoading(true);
    try {
      const feedback = await interviewAPI.generateFeedback(interviewSession.session_id);
      setFinalFeedback(feedback);
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
    setStep('setup');
  };

  const renderSetup = () => (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '2rem' }}>🤖 AI 면접 시뮬레이터</h1>
      
      <div style={{ marginBottom: '2rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          직무 선택
        </label>
        <select 
          value={selectedJob}
          onChange={(e) => setSelectedJob(e.target.value)}
          style={{
            width: '100%',
            padding: '0.75rem',
            fontSize: '1rem',
            border: '2px solid #ddd',
            borderRadius: '8px'
          }}
        >
          {jobCategories.map(job => (
            <option key={job} value={job}>{job}</option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          질문 개수: {numQuestions}개
        </label>
        <input
          type="range"
          min="1"
          max="5"
          value={numQuestions}
          onChange={(e) => setNumQuestions(Number(e.target.value))}
          style={{ width: '100%' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#666' }}>
          <span>1개</span>
          <span>5개</span>
        </div>
      </div>

      <button
        onClick={startInterview}
        disabled={isLoading}
        style={{
          width: '100%',
          padding: '1rem',
          fontSize: '1.1rem',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          opacity: isLoading ? 0.6 : 1
        }}
      >
        {isLoading ? '준비 중...' : '면접 시작'}
      </button>
    </div>
  );

  const renderInterview = () => {
    if (!interviewSession) return null;

    const currentQuestion = interviewSession.questions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / interviewSession.questions.length) * 100;

    return (
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>질문 {currentQuestionIndex + 1} / {interviewSession.questions.length}</h2>
            <span style={{ fontSize: '0.9rem', color: '#666' }}>{selectedJob}</span>
          </div>
          
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#f0f0f0',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: '#007bff',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '2rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          border: '2px solid #e9ecef'
        }}>
          <h3 style={{ color: '#007bff', marginBottom: '1rem' }}>💬 면접관의 질문</h3>
          <p style={{ fontSize: '1.2rem', lineHeight: '1.6', margin: 0 }}>
            {currentQuestion}
          </p>
        </div>

        <AudioRecorder
          onRecordingComplete={handleAudioRecorded}
          isRecording={isRecording}
          onRecordingStart={() => setIsRecording(true)}
          onRecordingStop={() => setIsRecording(false)}
        />

        {isLoading && (
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <div style={{ fontSize: '1.1rem', color: '#666' }}>
              🤖 AI가 음성을 분석 중입니다...
            </div>
          </div>
        )}

        {analysisResults.length > 0 && (
          <div style={{ marginTop: '2rem' }}>
            <h4>지금까지의 답변 분석</h4>
            {analysisResults.map((result, index) => (
              <div key={index} style={{
                backgroundColor: '#fff',
                padding: '1rem',
                marginBottom: '1rem',
                borderRadius: '8px',
                border: '1px solid #ddd'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <strong>질문 {index + 1}</strong>
                  <span style={{ color: result.overall_score >= 80 ? '#28a745' : result.overall_score >= 60 ? '#ffc107' : '#dc3545' }}>
                    점수: {result.overall_score.toFixed(1)}점
                  </span>
                </div>
                <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
                  "{result.text.substring(0, 100)}{result.text.length > 100 ? '...' : ''}"
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderResults = () => {
    if (!finalFeedback) return null;

    return (
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1>🎉 면접 완료!</h1>
          <div style={{
            fontSize: '3rem',
            fontWeight: 'bold',
            color: finalFeedback.overall_score >= 80 ? '#28a745' : 
                   finalFeedback.overall_score >= 60 ? '#ffc107' : '#dc3545',
            marginBottom: '1rem'
          }}>
            {finalFeedback.overall_score.toFixed(1)}점
          </div>
          <p style={{ fontSize: '1.1rem', color: '#666' }}>
            {finalFeedback.overall_score >= 80 ? '🌟 훌륭한 면접이었습니다!' :
             finalFeedback.overall_score >= 60 ? '👍 좋은 면접이었습니다!' : '💪 더 연습하면 분명 좋아질 거예요!'}
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
          <div style={{
            backgroundColor: '#fff',
            padding: '1.5rem',
            borderRadius: '12px',
            border: '2px solid #e9ecef'
          }}>
            <h3 style={{ color: '#007bff', marginBottom: '1rem' }}>💪 강점</h3>
            <ul style={{ paddingLeft: '1.2rem' }}>
              {finalFeedback.strengths.map((strength, index) => (
                <li key={index} style={{ marginBottom: '0.5rem' }}>{strength}</li>
              ))}
            </ul>
          </div>

          <div style={{
            backgroundColor: '#fff',
            padding: '1.5rem',
            borderRadius: '12px',
            border: '2px solid #e9ecef'
          }}>
            <h3 style={{ color: '#ffc107', marginBottom: '1rem' }}>🎯 개선점</h3>
            <ul style={{ paddingLeft: '1.2rem' }}>
              {finalFeedback.improvement_areas.map((area, index) => (
                <li key={index} style={{ marginBottom: '0.5rem' }}>{area}</li>
              ))}
            </ul>
          </div>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>📊 세부 분석</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <h4 style={{ color: '#007bff', margin: '0 0 0.5rem 0' }}>🗣️ 전달력</h4>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>{finalFeedback.delivery_feedback}</p>
            </div>
            
            <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <h4 style={{ color: '#28a745', margin: '0 0 0.5rem 0' }}>🎵 톤</h4>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>{finalFeedback.tone_feedback}</p>
            </div>
            
            <div style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <h4 style={{ color: '#ffc107', margin: '0 0 0.5rem 0' }}>⏱️ 리듬</h4>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>{finalFeedback.rhythm_feedback}</p>
            </div>
          </div>
        </div>

        <div style={{
          backgroundColor: '#e7f3ff',
          padding: '2rem',
          borderRadius: '12px',
          marginBottom: '2rem'
        }}>
          <h3 style={{ color: '#007bff', marginBottom: '1rem' }}>💡 개선 권장사항</h3>
          <ul style={{ paddingLeft: '1.2rem' }}>
            {finalFeedback.recommendations.map((rec, index) => (
              <li key={index} style={{ marginBottom: '0.5rem' }}>{rec}</li>
            ))}
          </ul>
        </div>

        <div style={{ textAlign: 'center' }}>
          <button
            onClick={resetInterview}
            style={{
              padding: '1rem 2rem',
              fontSize: '1.1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            🔄 새로운 면접 시작
          </button>
        </div>
      </div>
    );
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      {step === 'setup' && renderSetup()}
      {step === 'interview' && renderInterview()}
      {step === 'results' && renderResults()}
    </div>
  );
};

export default InterviewSimulator;