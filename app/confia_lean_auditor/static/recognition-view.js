(function exposeRecognitionView(root) {
  "use strict";
  function node(tag, value) {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = value;
    return element;
  }
  function renderMath(host, latex, original, display) {
    const math = node(display ? "div" : "span");
    math.className = display ? "recognized-math" : "recognized-inline-math";
    if (root.katex?.render) {
      try {
        root.katex.render(latex, math, { displayMode: display, throwOnError: false, trust: false, strict: "ignore" });
        if (math.querySelector?.(".katex-error")) throw new Error("invalid TeX");
      } catch (_) {
        math.replaceChildren();
        math.textContent = original;
        math.className += " recognized-math-fallback";
      }
    } else math.textContent = original;
    host.appendChild(math);
  }

  function markerAt(source, index) {
    if (source.startsWith("\\(", index)) return { open: "\\(", close: "\\)", display: false };
    if (source.startsWith("\\[", index)) return { open: "\\[", close: "\\]", display: true };
    if (source[index] !== "$" || (index > 0 && source[index - 1] === "\\")) return null;
    if (source.startsWith("$$", index)) return { open: "$$", close: "$$", display: true };
    if (/\s/.test(source[index + 1] || "") || /[\p{L}\p{N}]/u.test(source[index - 1] || "")) return null;
    return { open: "$", close: "$", display: false };
  }
  function closingAt(source, marker, start) {
    for (let index = start; index < source.length; index++) {
      if (!source.startsWith(marker.close, index)) continue;
      if (marker.close[0] === "$" && index > 0 && source[index - 1] === "\\") continue;
      if (marker.close === "$" && source[index + 1] === "$") continue;
      if (marker.close === "$" && /\s/.test(source[index - 1] || "")) continue;
      return index;
    }
    return -1;
  }
  function splitMathText(source, bareMath = false) {
    const value = typeof source === "string" ? source : "";
    const markers = [];
    for (let index = 0; index < value.length; index++) {
      const marker = markerAt(value, index);
      if (marker) { markers.push({ index, marker }); index += marker.open.length - 1; }
    }
    if (!markers.length) {
      return [{ math: bareMath && Boolean(value.trim()), value: bareMath && value.trim() ? value.trim() : value,
        source: value, display: bareMath }];
    }
    const parts = [];
    const text = value => parts.push({ math: false, value, source: value });
    let cursor = 0;
    while (cursor < value.length) {
      let next = null;
      for (const candidate of markers) if (candidate.index >= cursor) { next = candidate; break; }
      if (!next) { text(value.slice(cursor)); break; }
      if (next.index > cursor) text(value.slice(cursor, next.index));
      const start = next.index + next.marker.open.length;
      const end = closingAt(value, next.marker, start);
      if (end < 0 || end === start) {
        text(value.slice(next.index));
        break;
      }
      const original = value.slice(next.index, end + next.marker.close.length);
      parts.push({ math: true, value: value.slice(start, end), source: original, display: next.marker.display });
      cursor = end + next.marker.close.length;
    }
    return parts;
  }
  function renderMathText(host, source, bareMath = false) {
    const parts = splitMathText(source, bareMath);
    if (parts.length === 1 && !parts[0].math) { host.textContent = parts[0].value; return; }
    for (const part of parts) {
      if (part.math) renderMath(host, part.value, part.source, part.display);
      else host.appendChild(node("span", part.value));
    }
  }
  function render(host, segments) {
    host.replaceChildren();
    const kinds = { text: "Texto", math: "Matemática", mixed: "Misto", diagram: "Diagrama", unknown: "Não identificado" };
    for (const segment of segments || []) {
      const row = node("section");
      row.className = "recognized-segment";
      row.appendChild(node("strong", `Página ${segment.page_index + 1} · ${kinds[segment.kind] || kinds.unknown}`));
      // For Mathpix mixed results, text is often the plain form of latex_styled.
      // Keep it in details so the same expression is not presented twice.
      if (segment.latex) {
        if (!["\\(", "\\[", "$"].some(marker => segment.latex.includes(marker))) {
          renderMath(row, segment.latex, segment.latex, true);
        }
        else {
          const content = node("div");
          content.className = "recognized-content";
          renderMathText(content, segment.latex, true);
          row.appendChild(content);
        }
      } else if (segment.text) {
        const content = node("p");
        content.className = "recognized-content";
        const bareMath = /^\s*\\(?:frac|sqrt|sum|int|lim|left|begin)\b/.test(segment.text);
        renderMathText(content, segment.text, bareMath);
        row.appendChild(content);
      }
      if (segment.latex) {
        const details = node("details");
        details.appendChild(node("summary", "Texto reconhecido / LaTeX"));
        if (segment.text) details.appendChild(node("pre", segment.text));
        if (segment.latex) details.appendChild(node("pre", segment.latex));
        row.appendChild(details);
      }
      host.appendChild(row);
    }
  }
  root.ConfiaRecognitionView = { render, renderMathText, splitMathText };
  if (typeof module === "object" && module.exports) module.exports = { render, renderMathText, splitMathText };
})(globalThis);
