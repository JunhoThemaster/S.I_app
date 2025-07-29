export const drawLandmarks = (ctx: CanvasRenderingContext2D, landmarks: any[]) => {
  for (const landmark of landmarks) {
    const { x, y } = landmark;
    ctx.beginPath();
    ctx.arc(x * ctx.canvas.width, y * ctx.canvas.height, 4, 0, 2 * Math.PI);
    ctx.fillStyle = "#FF0000";
    ctx.fill();
  }
};

export const drawConnectors = (
  ctx: CanvasRenderingContext2D,
  landmarks: any[],
  connections: [number, number][],
  color: string
) => {
  for (const [startIdx, endIdx] of connections) {
    const start = landmarks[startIdx];
    const end = landmarks[endIdx];
    if (!start || !end) continue;

    ctx.beginPath();
    ctx.moveTo(start.x * ctx.canvas.width, start.y * ctx.canvas.height);
    ctx.lineTo(end.x * ctx.canvas.width, end.y * ctx.canvas.height);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
};
