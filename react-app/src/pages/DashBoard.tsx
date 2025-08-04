import React, { useState } from "react";
import PoseTracker from "../components/PoseTracker";
// ✅ 이렇게 되어야 함
import VoiceLevelMeter from "../components/VoiceLevelMeter";

import "../dashboard.css";
import { parse } from "path";

function getUserIdFromToken(token: string): string | null {
  try {
    const payload = token.split(".")[1];         // JWT의 payload 부분
    const decoded = atob(payload);               // base64 디코딩
    const parsed = JSON.parse(decoded);
    console.log(parsed.sub)          // JSON 파싱
    return parsed.sub || null;                   // "sub"에서 user_id 추출
  } catch (err) {
    console.error("❌ 토큰 파싱 실패:", err);
    return null;
  }
}




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

  const token = localStorage.getItem("token") ?? "";
  var UserId = null;
  if (token){
      UserId = getUserIdFromToken(token);
  }
  

  return (
    <div style={{ padding: "2rem" }}>
      <h1>📺 Dashboard</h1>

     {/* ✅ 마이크 감지 표시 (카메라와 함께 제어됨) */}
      <VoiceLevelMeter isActive={showCamera} userId={UserId || " "} token={token} />



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
