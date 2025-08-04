import React, { useState } from "react";
import PoseTracker from "../components/PoseTracker";
import "../dashboard.css";

const DashBoard: React.FC = () => {
  const [cameraOn, setCameraOn] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleCameraReady = () => {
    console.log("🎥 카메라 준비 완료 → 로딩 종료");
    setLoading(false);
  };

  const handleCameraToggle = () => {
    if (!cameraOn) {
      setCameraOn(true);
      setLoading(true);
      console.log("🎬 카메라 열기 시도");
    } else {
      setCameraOn(false);
      console.log("🛑 카메라 종료");
    }
  };

  return (
    <div className="dashboard">
      <h1>감정 및 자세 분석 대시보드</h1>

      <button className="camera-toggle-button" onClick={handleCameraToggle}>
        {cameraOn ? "카메라 끄기" : "카메라 열기"}
      </button>

      {loading && (
        <div className="loading">
          <div className="loader"></div>
          <p>카메라 준비 중...</p>
        </div>
      )}

      {cameraOn && (
        <div className="camera-wrapper">
          <PoseTracker onCameraReady={handleCameraReady} />
        </div>
      )}
    </div>
  );
};

export default DashBoard;
