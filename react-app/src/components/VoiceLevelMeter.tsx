// src/components/VoiceLevelMeter.tsx
import React, { useEffect, useRef, useState } from "react";

const VoiceLevelMeter: React.FC = () => {
  const [volume, setVolume] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const animationFrameId = useRef<number | null>(null);

  useEffect(() => {
    let audioContext: AudioContext;
    let analyser: AnalyserNode;
    let microphone: MediaStreamAudioSourceNode;

    const startListening = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);

        analyser.fftSize = 512;
        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        const updateVolume = () => {
          analyser.getByteFrequencyData(dataArray);
          const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
          const normalized = Math.min(avg / 256, 1); // 0~1
          setVolume(normalized);
          animationFrameId.current = requestAnimationFrame(updateVolume);
        };

        setIsListening(true);
        updateVolume();
      } catch (err) {
        console.error("Mic access error:", err);
        setIsListening(false);
      }
    };

    startListening();

    return () => {
      if (animationFrameId.current) cancelAnimationFrame(animationFrameId.current);
      if (audioContext) audioContext.close();
    };
  }, []);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
      <div style={{
        width: "150px",
        height: "20px",
        background: "#ddd",
        borderRadius: "10px",
        overflow: "hidden"
      }}>
        <div style={{
          width: `${volume * 100}%`,
          height: "100%",
          background: volume > 0.7 ? "red" : volume > 0.3 ? "orange" : "green",
          transition: "width 0.1s ease"
        }} />
      </div>
      <span style={{ fontWeight: "bold", fontSize: "1rem" }}>
        {isListening ? "🎧 듣는 중..." : "❌ 마이크 꺼짐"}
      </span>
    </div>
  );
};

export default VoiceLevelMeter;
