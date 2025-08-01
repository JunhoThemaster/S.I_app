// src/components/PoseTracker.tsx
import React, { useEffect, useRef } from "react";
import { Pose, POSE_CONNECTIONS } from "@mediapipe/pose";
import { Camera } from "@mediapipe/camera_utils";
import * as drawingUtils from "../utils/drawingUtils"; // 상대 경로에 주의


interface Props {
  onResult: (landmarks: any, image: Blob) => void;
}

const PoseTracker: React.FC<Props> = ({ onResult }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bufferRef = useRef<any[]>([]);

  useEffect(() => {
    const pose = new Pose({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
    });
    pose.setOptions({
      modelComplexity: 1,
      smoothLandmarks: true,
      enableSegmentation: false,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    pose.onResults((results) => {
          const canvasCtx = canvasRef.current?.getContext("2d");
          if (!canvasCtx || !canvasRef.current || !videoRef.current) return;

          canvasCtx.save();

          // ✅ 반전 적용
          canvasCtx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
          canvasCtx.scale(-1, 1); // 좌우 반전
          canvasCtx.translate(-canvasRef.current.width, 0); // 반전된 캔버스 위치 조정

          // ✅ 반전된 상태로 이미지와 랜드마크 그리기
          canvasCtx.drawImage(results.image, 0, 0, canvasRef.current.width, canvasRef.current.height);

          if (results.poseLandmarks) {
            drawingUtils.drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {
              color: "#00FF00",
              lineWidth: 4,
            });
            drawingUtils.drawLandmarks(canvasCtx, results.poseLandmarks, {
              color: "#ff0000ff",
              lineWidth: 2,
            });

            bufferRef.current.push({ landmarks: results.poseLandmarks });

            if (bufferRef.current.length >= 15) {
              canvasRef.current.toBlob((blob) => {
                if (blob) {
                  const batch = [...bufferRef.current];
                  bufferRef.current = [];
                  onResult(batch, blob);
                }
              }, "image/jpeg");
            }
          }

          canvasCtx.restore();
        });


    const camera = new Camera(videoRef.current!, {
        onFrame: async () => {
            if (videoRef.current) {
            await pose.send({ image: videoRef.current });
            }
        },
        width: 640,
        height: 480,
        });
    camera.start();

    return () => {
      camera.stop();
    };
  }, [onResult]);

  return (
   <div style={{ position: "relative", width: 640, height: 480, marginLeft: "30px"}}>
    <video
      ref={videoRef}
      autoPlay
      playsInline
      width={640}
      height={480}
      style={{ transform: "scaleX(-1)", position: "absolute" }}
    />
    <canvas
      ref={canvasRef}
      width={640}
      height={480}
      style={{ position: "absolute", zIndex: 1 }}
    />
  </div>
  );
};  

export default PoseTracker;
