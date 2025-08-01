  // src/components/AudioRecorder.tsx (WAV 전용 - 최적화)
  import React, { useState, useRef, useEffect } from 'react';

  interface AudioRecorderProps {
    onRecordingComplete: (audioBlob: Blob) => void;
    isRecording: boolean;
    onRecordingStart: () => void;
    onRecordingStop: () => void;
  }

  const AudioRecorder: React.FC<AudioRecorderProps> = ({
    onRecordingComplete,
    isRecording,
    onRecordingStart,
    onRecordingStop
  }) => {
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const [recordingTime, setRecordingTime] = useState(0);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
      if (isRecording) {
        timerRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
      } else {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        setRecordingTime(0);
      }

      return () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };
    }, [isRecording]);

    const startRecording = async () => {
      try {
        console.log('🎤 WAV 녹음 시작...');
        
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 16000
          }
        });

        // WAV 포맷만 시도
        let mediaRecorder;
        if (MediaRecorder.isTypeSupported('audio/wav')) {
          mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/wav' });
          console.log('✅ 순수 WAV 포맷 사용');
        } else {
          // WAV 지원 안 하면 기본값 (대부분 WebM)
          mediaRecorder = new MediaRecorder(stream);
          console.log('⚠️ WAV 미지원 - 기본 포맷 사용');
        }

        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = () => {
          // 항상 WAV로 Blob 생성
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          console.log(`🎵 WAV 파일 생성완료: ${audioBlob.size} bytes`);
          
          onRecordingComplete(audioBlob);
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start(100);
        onRecordingStart();
        
      } catch (error) {
        console.error('🚨 녹음 오류:', error);
        alert('마이크 접근 권한이 필요합니다.');
      }
    };

    const stopRecording = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
        onRecordingStop();
      }
    };

    const formatTime = (seconds: number) => {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
      <div style={{ textAlign: 'center', margin: '1rem 0' }}>
        {!isRecording ? (
          <button 
            onClick={startRecording}
            style={{
              padding: '1rem 2rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '50px',
              fontSize: '1.1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              margin: '0 auto'
            }}
          >
            🎤 녹음 시작
          </button>
        ) : (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <div style={{
                width: '12px',
                height: '12px',
                backgroundColor: '#ff4757',
                borderRadius: '50%',
                animation: 'pulse 1s infinite'
              }} />
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                녹음 중... {formatTime(recordingTime)}
              </span>
            </div>
            
            <button 
              onClick={stopRecording}
              style={{
                padding: '1rem 2rem',
                backgroundColor: '#ff4757',
                color: 'white',
                border: 'none',
                borderRadius: '50px',
                fontSize: '1.1rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                margin: '0 auto'
              }}
            >
              ⏹️ 녹음 완료
            </button>
          </div>
        )}
        
        <style>
          {`
            @keyframes pulse {
              0% { opacity: 1; }
              50% { opacity: 0.5; }
              100% { opacity: 1; }
            }
          `}
        </style>
      </div>
    );
  };

  export default AudioRecorder;