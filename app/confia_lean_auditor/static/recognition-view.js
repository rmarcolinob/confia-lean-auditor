(function exposeRecognitionView(root) {
  "use strict";
  function node(tag, value) {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = value;
    return element;
  }
  function renderMath(host, latex) {
    const math = node("div");
    math.className = "recognized-math";
    if (root.katex?.render) {
      try {
        root.katex.render(latex, math, { displayMode: true, throwOnError: true, trust: false, strict: "ignore" });
      } catch (_) {
        math.textContent = latex;
      }
    } else math.textContent = latex;
    host.appendChild(math);
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
      if (segment.latex) renderMath(row, segment.latex);
      else if (segment.text) row.appendChild(node("p", segment.text));
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
  root.ConfiaRecognitionView = { render };
  if (typeof module === "object" && module.exports) module.exports = { render };
})(globalThis);
