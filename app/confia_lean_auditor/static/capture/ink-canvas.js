(function exposeInkCanvas(root, factory) {
  const api = factory(root.ConfiaInkModel);
  root.ConfiaInkCanvas = api;
})(globalThis, function makeInkCanvas(InkModel) {
  "use strict";

  // Visual-only adjustment shared by the notebook, preview and PNG.
  // Preserve stroke.width and all captured data in existing documents.
  const VISUAL_WIDTH_SCALE = 0.75;

  function setupCanvas(canvas, page) {
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.max(1, globalThis.devicePixelRatio || 1);
    const pixelWidth = Math.max(1, Math.round(rect.width * ratio));
    const pixelHeight = Math.max(1, Math.round(rect.height * ratio));
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    const context = canvas.getContext("2d");
    context.setTransform(pixelWidth / page.logical_width, 0, 0, pixelHeight / page.logical_height, 0, 0);
    return context;
  }

  function drawGrid(context, page) {
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, page.logical_width, page.logical_height);
    context.strokeStyle = "#e7eef8";
    context.lineWidth = 1;
    const step = 40;
    for (let x = step; x < page.logical_width; x += step) {
      context.beginPath();
      context.moveTo(x, 0);
      context.lineTo(x, page.logical_height);
      context.stroke();
    }
    for (let y = step; y < page.logical_height; y += step) {
      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(page.logical_width, y);
      context.stroke();
    }
  }

  function drawStroke(context, stroke) {
    const points = stroke.points;
    if (!points.length) return;
    const visualWidth = stroke.width * VISUAL_WIDTH_SCALE;
    context.strokeStyle = stroke.color;
    context.fillStyle = stroke.color;
    context.lineWidth = visualWidth;
    context.lineCap = "round";
    context.lineJoin = "round";
    if (points.length === 1) {
      context.beginPath();
      context.arc(points[0].x, points[0].y, visualWidth / 2, 0, Math.PI * 2);
      context.fill();
      return;
    }
    context.beginPath();
    context.moveTo(points[0].x, points[0].y);
    for (let index = 1; index < points.length; index += 1) {
      context.lineTo(points[index].x, points[index].y);
    }
    context.stroke();
  }

  function render(canvas, document, pageId, options) {
    const settings = { grid: true, ...options };
    const page = document.pages.find((item) => item.page_id === pageId);
    if (!page) return;
    const context = setupCanvas(canvas, page);
    context.clearRect(0, 0, page.logical_width, page.logical_height);
    if (settings.grid) drawGrid(context, page);
    else {
      context.fillStyle = document.renderer.png_background;
      context.fillRect(0, 0, page.logical_width, page.logical_height);
    }
    for (const stroke of InkModel.activeStrokes(document, pageId)) drawStroke(context, stroke);
    if (settings.transientStroke) drawStroke(context, settings.transientStroke);
  }

  function eventPoint(event, canvas, page, startTime) {
    const rect = canvas.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * page.logical_width;
    const y = ((event.clientY - rect.top) / rect.height) * page.logical_height;
    return {
      x: Math.min(page.logical_width, Math.max(0, x)),
      y: Math.min(page.logical_height, Math.max(0, y)),
      t_ms: Math.max(0, event.timeStamp - startTime),
      pressure_reported:
        event.pointerType === "pen" && Number.isFinite(event.pressure) ? event.pressure : null,
    };
  }

  function appendEventPoints(points, event, canvas, page, startTime) {
    const events = typeof event.getCoalescedEvents === "function" ? event.getCoalescedEvents() : [];
    const samples = events.length ? [...events, event] : [event];
    for (const sample of samples) {
      const point = eventPoint(sample, canvas, page, startTime);
      const previous = points.at(-1);
      if (
        previous && previous.x === point.x && previous.y === point.y && previous.t_ms === point.t_ms
      ) continue;
      if (previous && point.t_ms < previous.t_ms) point.t_ms = previous.t_ms;
      points.push(point);
    }
  }

  function distanceToSegment(point, start, end) {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    if (dx === 0 && dy === 0) return Math.hypot(point.x - start.x, point.y - start.y);
    const ratio = Math.max(0, Math.min(1, ((point.x - start.x) * dx + (point.y - start.y) * dy) / (dx * dx + dy * dy)));
    return Math.hypot(point.x - (start.x + ratio * dx), point.y - (start.y + ratio * dy));
  }

  function hitTest(document, pageId, point, radius) {
    const strokes = InkModel.activeStrokes(document, pageId).slice().reverse();
    for (const stroke of strokes) {
      if (stroke.points.length === 1 && distanceToSegment(point, stroke.points[0], stroke.points[0]) <= radius) {
        return stroke.stroke_id;
      }
      for (let index = 1; index < stroke.points.length; index += 1) {
        if (distanceToSegment(point, stroke.points[index - 1], stroke.points[index]) <= radius) {
          return stroke.stroke_id;
        }
      }
    }
    return null;
  }

  function pngBlob(document, pageId) {
    const page = document.pages.find((item) => item.page_id === pageId);
    if (!page) return Promise.reject(new Error("Página não encontrada."));
    const canvas = globalThis.document.createElement("canvas");
    canvas.style.width = `${page.logical_width}px`;
    canvas.style.height = `${page.logical_height}px`;
    canvas.width = page.logical_width;
    canvas.height = page.logical_height;
    const context = canvas.getContext("2d");
    context.fillStyle = document.renderer.png_background;
    context.fillRect(0, 0, page.logical_width, page.logical_height);
    for (const stroke of InkModel.activeStrokes(document, pageId)) drawStroke(context, stroke);
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("Falha ao gerar PNG."))), "image/png");
    });
  }

  return { appendEventPoints, eventPoint, hitTest, pngBlob, render };
});
