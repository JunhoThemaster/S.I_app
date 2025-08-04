// 🔹 src/utils/drawingUtils.ts
import { drawConnectors, drawLandmarks } from "@mediapipe/drawing_utils";
import { POSE_CONNECTIONS, NormalizedLandmarkList } from "@mediapipe/pose";

/**
 * 포즈 랜드마크 연결선 + 점 그리기
 */
export function drawPoseSkeleton(
  ctx: CanvasRenderingContext2D,
  landmarks: NormalizedLandmarkList
) {
  drawConnectors(ctx, landmarks, POSE_CONNECTIONS, {
    color: "#00FF00",
    lineWidth: 2,
  });
  drawLandmarks(ctx, landmarks, {
    color: "#FF0000",
    lineWidth: 1,
  });
}

/**
 * 커스텀 얼굴 메쉬 (눈/코/입 점 + 윤곽선)
 */
export function drawCustomFaceMesh(
  ctx: CanvasRenderingContext2D,
  landmarks: NormalizedLandmarkList
) {
  const dotIndices = [33, 133, 362, 263, 1, 61, 291]; // 왼눈, 오른눈, 코, 입
  ctx.fillStyle = "#00FFFF";
  for (const i of dotIndices) {
    const lm = landmarks[i];
    if (!lm) continue;
    ctx.beginPath();
    ctx.arc(lm.x * ctx.canvas.width, lm.y * ctx.canvas.height, 2, 0, 2 * Math.PI);
    ctx.fill();
  }

  // 얼굴 외곽선 (FACEMESH_FACE_OVAL과 유사)
  const faceOvalIndices = [
    10, 338, 297, 332, 284, 251, 389, 356,
    454, 323, 361, 288, 397, 365, 379, 378,
    400, 377, 152, 148, 176, 149, 150, 136,
    172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
  ];

  ctx.beginPath();
  for (let i = 0; i < faceOvalIndices.length; i++) {
    const index = faceOvalIndices[i];
    const lm = landmarks[index];
    if (!lm) continue;
    const x = lm.x * ctx.canvas.width;
    const y = lm.y * ctx.canvas.height;
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.closePath();
  ctx.strokeStyle = "#00FFFF";
  ctx.lineWidth = 1.5;
  ctx.stroke();
}
