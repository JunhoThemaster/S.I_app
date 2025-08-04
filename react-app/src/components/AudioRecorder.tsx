import React, { useState, useRef, useEffect, useCallback } from 'react';

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  isRecording: boolean;
  onRecordingStart: () => void;
  onRecordingStop: () => void;
  continuousMode?: boolean;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onstart: (() => void) | null;
  onend: (() => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onRecordingComplete,
  isRecording,
  onRecordingStart,
  onRecordingStop,
  continuousMode = false
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [duration, setDuration] = useState(0);
  const [audioLevels, setAudioLevels] = useState<number[]>(Array(30).fill(0));
  const [micAccess, setMicAccess] = useState<'granted' | 'denied' | 'pending'>('pending');
  const [debugInfo, setDebugInfo] = useState<string>('시스템 확인 중...');
  const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const speechRecognitionRef = useRef<SpeechRecognition | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | undefined>(undefined);
  const timerRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // 개선된 파형 시각화
  const updateAudioLevels = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = 512;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    const newLevels = Array(30).fill(0).map((_, i) => {
      const start = Math.floor((i * bufferLength) / 30);
      const end = Math.floor(((i + 1) * bufferLength) / 30);
      const slice = dataArray.slice(start, end);
      const average = slice.reduce((sum, value) => sum + value, 0) / slice.length;
      
      const normalized = Math.min(100, (average / 128) * 100);
      return normalized > 5 ? normalized * (1 + Math.random() * 0.3) : normalized;
    });

    setAudioLevels(newLevels);
    animationRef.current = requestAnimationFrame(updateAudioLevels);
  }, []);

  // 사용 가능한 마이크 장치 목록 가져오기
  const getAvailableDevices = useCallback(async () => {
    try {
      console.log('🎤 사용 가능한 마이크 장치 검색...');
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices.filter(device => device.kind === 'audioinput');
      
      console.log('🎤 발견된 마이크 장치들:');
      audioInputs.forEach((device, index) => {
        console.log(`  ${index + 1}. ${device.label || `마이크 ${index + 1}`} (ID: ${device.deviceId})`);
      });
      
      setAvailableDevices(audioInputs);
      
      // 기본 장치 선택
      if (audioInputs.length > 0 && !selectedDeviceId) {
        setSelectedDeviceId(audioInputs[0].deviceId);
        setDebugInfo(`기본 마이크: ${audioInputs[0].label || '마이크 1'}`);
      }
      
      return audioInputs;
    } catch (error) {
      console.error('❌ 장치 목록 가져오기 실패:', error);
      setDebugInfo('마이크 장치 목록을 가져올 수 없습니다');
      return [];
    }
  }, [selectedDeviceId]);

  // 권한 확인 (개선됨)
  const checkPermission = useCallback(async () => {
    console.log('🎤 마이크 권한 확인 시작...');
    setDebugInfo('마이크 권한 확인 중...');
    
    try {
      if (navigator.permissions) {
        try {
          const result = await navigator.permissions.query({ name: 'microphone' as PermissionName });
          console.log('📋 권한 상태:', result.state);
          setDebugInfo(`권한 상태: ${result.state}`);
          
          if (result.state === 'denied') {
            setMicAccess('denied');
            setDebugInfo('마이크 권한이 거부되었습니다.');
            return false;
          }
        } catch (e) {
          console.log('⚠️ 권한 API 사용 불가');
        }
      }

      setDebugInfo('마이크 접근 테스트 중...');
      
      // 먼저 기본 마이크로 테스트
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      console.log('✅ 마이크 접근 성공');
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length > 0) {
        const track = audioTracks[0];
        console.log('🎤 현재 사용 중인 마이크:', track.label);
        setDebugInfo(`현재 마이크: ${track.label || '기본 마이크'}`);
      }
      
      stream.getTracks().forEach(track => track.stop());
      
      // 권한 획득 후 사용 가능한 장치 목록 가져오기
      await getAvailableDevices();
      
      setMicAccess('granted');
      return true;
    } catch (error: any) {
      console.error('❌ 마이크 접근 실패:', error);
      setMicAccess('denied');
      
      if (error.name === 'NotAllowedError') {
        setDebugInfo('마이크 권한이 거부되었습니다.');
      } else if (error.name === 'NotFoundError') {
        setDebugInfo('마이크를 찾을 수 없습니다.');
      } else {
        setDebugInfo(`마이크 오류: ${error.message}`);
      }
      return false;
    }
  }, [getAvailableDevices]);

  // 음성 인식 초기화
  const initSpeechRecognition = useCallback(() => {
    console.log('🎙️ 음성 인식 초기화...');
    
    const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
    if (!SpeechRecognition) {
      console.error('❌ Web Speech API 지원 안됨');
      setDebugInfo('이 브라우저는 음성 인식을 지원하지 않습니다.');
      return null;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'ko-KR';

    recognition.onstart = () => {
      console.log('🎤 음성 인식 시작됨');
      setDebugInfo('음성 인식이 활성화되었습니다');
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      const allText = finalTranscript + interimTranscript;
      setTranscript(allText);
      
      if (allText) {
        setDebugInfo(`음성 인식 중: "${allText.slice(0, 30)}..."`);
      }

      // 확장된 종료 키워드
      const endKeywords = [
        '이상입니다', '끝입니다', '마칩니다', '감사합니다', '완료입니다', '다했습니다',
        '이상이에요', '끝이에요', '이상', '끝', '완료', '마침', '답변끝', '답변 끝',
        '그만', '여기까지', '다음', '넘어가', '이만'
      ];

      if (finalTranscript && endKeywords.some(keyword => allText.includes(keyword))) {
        console.log('🎯 종료 키워드 감지:', allText);
        setDebugInfo('종료 키워드 감지됨 - 녹음 중지');
        setTimeout(stopRecording, 500);
      }
    };

    recognition.onerror = (event) => {
      console.error('🎤 음성 인식 오류:', event.error);
      
      if (event.error === 'no-speech') {
        console.log('🔇 음성이 감지되지 않았습니다');
        setDebugInfo('음성이 감지되지 않았습니다. 다시 말씀해주세요.');
        // no-speech는 치명적이지 않으므로 녹음 중지하지 않음
        return;
      } else if (event.error === 'audio-capture') {
        setDebugInfo('마이크 오디오 캡처 실패');
        setMicAccess('denied');
      } else if (event.error === 'not-allowed') {
        setMicAccess('denied');
        setDebugInfo('마이크 권한이 거부되었습니다');
      } else if (event.error === 'network') {
        setDebugInfo('네트워크 오류로 음성 인식 실패');
      } else if (event.error === 'aborted') {
        console.log('🛑 음성 인식이 중단되었습니다');
        return; // 정상적인 중단
      } else {
        setDebugInfo(`음성 인식 오류: ${event.error}`);
      }
    };

    recognition.onend = () => {
      console.log('🎤 음성 인식 종료됨');
      if (isListening && continuousMode) {
        console.log('🔄 연속 모드 - 음성 인식 재시작');
        setTimeout(() => {
          if (speechRecognitionRef.current && isListening) {
            try {
              console.log('🔄 음성 인식 재시작 시도...');
              speechRecognitionRef.current.start();
              setDebugInfo('음성 인식 재시작됨');
            } catch (error: any) {
              console.warn('음성 인식 재시작 실패:', error);
              if (error.name === 'InvalidStateError') {
                console.log('🔄 이미 실행 중이거나 시작할 수 없는 상태');
                setDebugInfo('음성 인식 상태 오류 - 재시도 중...');
                // 잠시 후 다시 시도
                setTimeout(() => {
                  if (speechRecognitionRef.current && isListening) {
                    try {
                      speechRecognitionRef.current.start();
                    } catch (e) {
                      console.warn('재시도도 실패:', e);
                    }
                  }
                }, 1000);
              }
            }
          }
        }, 500); // 500ms 후 재시작 (더 안정적)
      }
    };

    return recognition;
  }, [isListening, continuousMode]);

  // 녹음 시작
  const startRecording = useCallback(async () => {
    console.log('🎬 녹음 시작 요청');
    setDebugInfo('녹음 준비 중...');
    
    if (!await checkPermission()) {
      console.error('❌ 권한 확인 실패');
      return;
    }

    try {
      const constraints = {
        audio: selectedDeviceId ? {
          deviceId: { exact: selectedDeviceId },
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        } : {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        }
      };
      
      console.log('🎤 선택된 마이크로 스트림 요청:', selectedDeviceId);
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      // 실제 사용 중인 장치 확인
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length > 0) {
        const track = audioTracks[0];
        console.log('🎤 실제 사용 중인 마이크:', track.label);
        setDebugInfo(`사용 중: ${track.label || '마이크'}`);
      }

      // 오디오 분석기 설정
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 1024;
      analyser.smoothingTimeConstant = 0.3;
      source.connect(analyser);
      analyserRef.current = analyser;

      // MediaRecorder 설정
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        console.log('🎬 MediaRecorder 중지됨');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        onRecordingComplete(audioBlob);
      };

      // 음성 인식 시작
      const recognition = initSpeechRecognition();
      if (recognition) {
        speechRecognitionRef.current = recognition;
        recognition.start();
      }

      mediaRecorder.start(500);
      updateAudioLevels();
      
      setIsListening(true);
      setDuration(0);
      setTranscript('');
      setDebugInfo('녹음 중...');
      onRecordingStart();

      // 타이머 시작
      timerRef.current = setInterval(() => setDuration(prev => prev + 1), 1000);

    } catch (error: any) {
      console.error('❌ 녹음 시작 실패:', error);
      setDebugInfo(`녹음 시작 실패: ${error.message}`);
      setMicAccess('denied');
    }
  }, [checkPermission, initSpeechRecognition, onRecordingComplete, onRecordingStart, updateAudioLevels]);

  // 녹음 중지
  const stopRecording = useCallback(() => {
    console.log('⏹️ 녹음 중지 요청');
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = undefined;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = undefined;
    }
    
    if (speechRecognitionRef.current) {
      speechRecognitionRef.current.abort();
      speechRecognitionRef.current = null;
    }
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track: MediaStreamTrack) => {
        track.stop();
      });
      streamRef.current = null;
    }
    
    setIsListening(false);
    setAudioLevels(Array(30).fill(0));
    setDebugInfo('녹음 중지됨');
    onRecordingStop();
  }, [onRecordingStop]);

  // 자동 시작/중지 관리
  useEffect(() => {
    if (continuousMode && isRecording && !isListening && micAccess === 'granted') {
      const timer = setTimeout(startRecording, 1000);
      return () => clearTimeout(timer);
    } else if (!isRecording && isListening) {
      stopRecording();
    }
  }, [continuousMode, isRecording, isListening, micAccess, startRecording, stopRecording]);

  useEffect(() => {
    checkPermission();
    return () => { 
      if (isListening) stopRecording(); 
    };
  }, [checkPermission, isListening, stopRecording]);

  const formatTime = (seconds: number) => `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;

  // 개선된 파형 컴포넌트
  const WaveForm = () => (
    <div style={{ 
      display: 'flex', 
      alignItems: 'end', 
      justifyContent: 'center',
      gap: '2px', 
      height: '60px',
      marginBottom: '15px',
      padding: '0 20px'
    }}>
      {audioLevels.map((level, i) => (
        <div
          key={i}
          style={{
            width: '4px',
            height: `${Math.max(3, (level / 100) * 60)}px`,
            background: level > 15 
              ? `linear-gradient(to top, #4caf50 0%, #8bc34a 50%, #cddc39 100%)` 
              : '#e0e0e0',
            borderRadius: '2px',
            transition: 'all 0.1s ease',
            animation: level > 15 ? `wave-${i % 3} 0.8s ease-in-out infinite alternate` : 'none',
            opacity: level > 5 ? 1 : 0.5
          }}
        />
      ))}
    </div>
  );

  if (micAccess === 'denied') {
    return (
      <div style={{ textAlign: 'center', padding: '25px', background: '#ffebee', borderRadius: '15px', maxWidth: '500px' }}>
        <div style={{ fontSize: '48px', marginBottom: '15px' }}>🎤❌</div>
        <div style={{ color: '#d32f2f', fontWeight: 'bold', fontSize: '18px', marginBottom: '10px' }}>
          마이크 권한이 필요합니다
        </div>
        <div style={{ fontSize: '14px', color: '#666', marginBottom: '15px', padding: '10px', background: '#f5f5f5', borderRadius: '8px' }}>
          <strong>디버그 정보:</strong><br/>
          {debugInfo}
        </div>
        <div style={{ fontSize: '14px', color: '#666', marginBottom: '20px', lineHeight: '1.5' }}>
          1. 브라우저 주소창 왼쪽의 🔒 아이콘 클릭<br/>
          2. 마이크 권한을 "허용"으로 변경<br/>
          3. 페이지 새로고침<br/>
          <strong>Chrome 브라우저 권장</strong>
        </div>
        <button onClick={checkPermission} style={{ 
          padding: '12px 24px', background: '#2196f3', color: 'white', 
          border: 'none', borderRadius: '8px', cursor: 'pointer', marginRight: '10px'
        }}>
          권한 다시 확인
        </button>
        <button onClick={() => window.location.reload()} style={{ 
          padding: '12px 24px', background: '#4caf50', color: 'white', 
          border: 'none', borderRadius: '8px', cursor: 'pointer'
        }}>
          페이지 새로고침
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
      {/* 디버그 정보 표시 */}
      <div style={{ 
        fontSize: '12px', color: '#666', background: '#f8f9fa', 
        padding: '8px 12px', borderRadius: '8px', maxWidth: '400px', textAlign: 'center'
      }}>
        {debugInfo}
      </div>

      {/* 마이크 장치 선택 */}
      {availableDevices.length > 1 && micAccess === 'granted' && !isListening && (
        <div style={{
          background: '#e3f2fd', padding: '15px', borderRadius: '12px', 
          border: '2px solid #2196f3', maxWidth: '400px', width: '100%'
        }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '10px', color: '#1976d2' }}>
            🎤 마이크 선택 ({availableDevices.length}개 발견)
          </div>
          <select
            value={selectedDeviceId}
            onChange={(e) => {
              setSelectedDeviceId(e.target.value);
              const selectedDevice = availableDevices.find(d => d.deviceId === e.target.value);
              setDebugInfo(`선택됨: ${selectedDevice?.label || '마이크'}`);
            }}
            style={{
              width: '100%', padding: '8px', borderRadius: '6px', 
              border: '1px solid #2196f3', fontSize: '14px'
            }}
          >
            {availableDevices.map((device, index) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label || `마이크 ${index + 1}`}
              </option>
            ))}
          </select>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
            원하는 마이크를 선택한 후 녹음을 시작하세요
          </div>
        </div>
      )}

      {/* 수동 녹음 버튼 */}
      {!continuousMode && (
        <button
          onClick={isListening ? stopRecording : startRecording}
          disabled={micAccess !== 'granted'}
          style={{
            width: '120px', height: '120px', borderRadius: '50%', border: 'none',
            background: isListening 
              ? 'linear-gradient(45deg, #ff6b6b, #ee5a24)' 
              : 'linear-gradient(45deg, #667eea, #764ba2)',
            color: 'white', fontSize: '16px', fontWeight: 'bold',
            cursor: micAccess === 'granted' ? 'pointer' : 'not-allowed',
            boxShadow: isListening 
              ? '0 8px 25px rgba(255, 107, 107, 0.4)' 
              : '0 8px 25px rgba(102, 126, 234, 0.4)',
            animation: isListening ? 'pulse 1.5s infinite' : 'none'
          }}
        >
          {isListening ? '⏹️\n녹음 중지' : '🎤\n녹음 시작'}
        </button>
      )}

      {/* 녹음 중 상태 */}
      {isListening && (
        <div style={{ 
          textAlign: 'center', padding: '25px', background: 'rgba(255,255,255,0.95)', 
          borderRadius: '20px', minWidth: '450px', boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
          border: '3px solid #667eea' 
        }}>
          <div style={{ 
            color: '#ff6b6b', fontWeight: 'bold', marginBottom: '20px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', fontSize: '18px' 
          }}>
            <div style={{ 
              width: '12px', height: '12px', background: '#ff6b6b', 
              borderRadius: '50%', animation: 'pulse 1s infinite' 
            }} />
            🎤 실시간 음성 인식
            <div style={{ 
              background: '#667eea', color: 'white', padding: '6px 15px', 
              borderRadius: '20px', fontSize: '16px' 
            }}>
              {formatTime(duration)}
            </div>
          </div>

          <WaveForm />

          <div style={{ 
            fontSize: '13px', marginBottom: '15px', fontWeight: 'bold',
            color: Math.max(...audioLevels) > 20 ? '#4caf50' : '#ff9800'
          }}>
            {Math.max(...audioLevels) > 20 ? '🔊 음성이 잘 인식되고 있습니다' : '🔇 더 크고 명확하게 말해주세요'}
          </div>

          {transcript && (
            <div style={{ 
              fontSize: '16px', maxHeight: '100px', overflow: 'auto', padding: '15px',
              background: '#f8f9fa', borderRadius: '12px', marginBottom: '15px',
              border: '2px solid #e9ecef', lineHeight: '1.6' 
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>💬 실시간 인식:</div>
              <div>"{transcript}"</div>
            </div>
          )}

          <div style={{ 
            fontSize: '13px', color: '#28a745', background: '#e8f5e9',
            padding: '10px 15px', borderRadius: '20px' 
          }}>
            💡 <strong>"이상"</strong>, <strong>"끝"</strong>, <strong>"완료"</strong> 등을 말하면 자동으로 다음 질문으로 이동
            <br />
            <div style={{ fontSize: '12px', marginTop: '5px', color: '#666' }}>
              🎤 마이크가 음성을 감지하지 못하면 더 크고 명확하게 말씀해주세요
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.05); opacity: 0.8; }
        }
        @keyframes wave-0 {
          0% { transform: scaleY(1); }
          100% { transform: scaleY(1.5); }
        }
        @keyframes wave-1 {
          0% { transform: scaleY(1.2); }
          100% { transform: scaleY(1.8); }
        }
        @keyframes wave-2 {
          0% { transform: scaleY(0.8); }
          100% { transform: scaleY(1.3); }
        }
      `}</style>
    </div>
  );
};

export default AudioRecorder;