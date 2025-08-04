import React, { useEffect, useRef, useState } from "react";

interface Props {
  isActive: boolean;
  userId: string;
  token: string;
}

const VoiceLevelMeter: React.FC<Props> = ({ isActive, userId, token }) => {
  const [volume, setVolume] = useState(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const tempBufferRef = useRef<Float32Array[]>([]); // ✅ 최상단으로 이동

  useEffect(() => {
    if (!isActive) {
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      tempBufferRef.current = []; // cleanup
      setVolume(0);
      return;
    }

    const float32ToInt16 = (float32Array: Float32Array): ArrayBuffer => {
      const int16Array = new Int16Array(float32Array.length);
      for (let i = 0; i < float32Array.length; i++) {
        int16Array[i] = Math.max(-32768, Math.min(32767, float32Array[i] * 32767));
      }
      return int16Array.buffer;
    };

    const startMic = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioCtx = new AudioContext();
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);

        const ws = new WebSocket(`ws://localhost:8000/api/user/ws/audio/${userId}?token=${token}`);
        ws.onopen = () => console.log("✅ WebSocket 연결됨");
        ws.onclose = () => console.log("❌ WebSocket 연결 종료됨");
        ws.onerror = (e) => console.error("WebSocket 에러:", e);

        const sampleRate = audioCtx.sampleRate; // 대부분 48000

        processor.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);
          tempBufferRef.current.push(new Float32Array(input));

          const totalLength = tempBufferRef.current.reduce((sum, chunk) => sum + chunk.length, 0);
          const durationSec = totalLength / sampleRate;

          if (durationSec >= 3.0) {
            const merged = new Float32Array(totalLength);
            let offset = 0;
            for (const chunk of tempBufferRef.current) {
              merged.set(chunk, offset);
              offset += chunk.length;
            }

            const buffer = float32ToInt16(merged);
            if (websocketRef.current?.readyState === WebSocket.OPEN) {
              websocketRef.current.send(buffer);
            }

            tempBufferRef.current = []; // 초기화
          }

          const avg = input.reduce((a, v) => a + Math.abs(v), 0) / input.length;
          setVolume(Math.min(100, Math.round(avg * 100)));
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);

        audioContextRef.current = audioCtx;
        websocketRef.current = ws;
        processorRef.current = processor;
      } catch (err) {
        console.error("마이크 접근 실패:", err);
      }
    };

    startMic();
  }, [isActive, userId, token]); // ✅ 의존성도 안전하게 추가

  return (
    <div style={{ marginTop: "1rem" }}>
      <div>🎤 마이크 레벨</div>
      <div
        style={{
          width: "100%",
          height: "10px",
          background: "#eee",
          borderRadius: "5px",
          marginTop: "5px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${volume}%`,
            height: "100%",
            background: volume > 70 ? "red" : volume > 40 ? "orange" : "green",
            transition: "width 0.1s linear",
          }}
        />
      </div>
    </div>
  );
};

export default VoiceLevelMeter;
