import React, { useState } from "react";
import PoseTracker from "../components/PoseTracker";
import VoiceLevelMeter from "../components/VoiceLevelMeter"; // ✅ 추가
import "../dashboard.css";

const DashBoard: React.FC = () => {
  const [showCamera, setShowCamera] = useState(false);
  const [animate, setAnimate] = useState(false);

  const handleStartCamera = () => {
    setAnimate(true);
    setTimeout(() => {
      setShowCamera(true);
      setAnimate(false);
    }, 800);
  };

  const handleStopCamera = () => {
    setShowCamera(false);
  };

  const handleResult = (landmarkBatch: any, imageBlob: Blob) => {
    console.log("🟡 15개 프레임 수집 완료");
    console.log("🟢 랜드마크:", landmarkBatch);
    console.log("🖼 이미지 Blob:", imageBlob);
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>📺 Dashboard</h1>

      {/* ✅ 마이크 감지 표시 */}
      <VoiceLevelMeter />

      {/* ✅ 버튼 영역 */}
      {!showCamera && (
        <button onClick={handleStartCamera} className="tv-button">
          카메라 열기
        </button>
      )}
      {showCamera && (
        <button onClick={handleStopCamera} className="tv-button stop">
          카메라 끄기
        </button>
      )}

      {/* 📦 PoseTracker 렌더링 영역 */}
      <div className="pose-wrapper">
        {animate && <div className="tv-startup-overlay" />}
        {showCamera && <PoseTracker onResult={handleResult} />}
      </div>
    </div>
  );
};

export default DashBoard;
