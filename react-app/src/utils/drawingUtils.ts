type Landmark = {
  x: number;
  y: number;
  z?: number;
  visibility?: number;
};

type DrawingStyle = {
  color: string;
  lineWidth: number;
};

export function drawLandmarks(
  ctx: CanvasRenderingContext2D,
  landmarks: Landmark[],
  style: DrawingStyle
) {
  ctx.save();
  ctx.fillStyle = style.color;
  landmarks.forEach((landmark) => {
    const x = landmark.x * ctx.canvas.width;
    const y = landmark.y * ctx.canvas.height;

    ctx.beginPath();
    ctx.arc(x, y, style.lineWidth, 0, 2 * Math.PI);
    ctx.fill();
  });
  ctx.restore();
}

export function drawConnectors(
  ctx: CanvasRenderingContext2D,
  landmarks: Landmark[],
  connections: [number, number][],
  style: DrawingStyle
) {
  ctx.save();
  ctx.strokeStyle = style.color;
  ctx.lineWidth = style.lineWidth;
  connections.forEach(([startIdx, endIdx]) => {
    const start = landmarks[startIdx];
    const end = landmarks[endIdx];
    if (start && end) {
      ctx.beginPath();
      ctx.moveTo(start.x * ctx.canvas.width, start.y * ctx.canvas.height);
      ctx.lineTo(end.x * ctx.canvas.width, end.y * ctx.canvas.height);
      ctx.stroke();
    }
  });
  ctx.restore();
}
