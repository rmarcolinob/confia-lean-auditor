(function exposeProblemMath(root) {
  "use strict";

  const options = {
    trust: false,
    strict: "ignore",
    output: "htmlAndMathml",
    maxSize: 10,
    maxExpand: 1000,
  };

  // Deliberately small grammar, not a general text-to-LaTeX converter. Recognize
  // integer monomials in a,b,x,y,z; spaced coefficients a x / b x; one level of
  // parentheses; and optional p(x), f(x), g(x) assignments. No prose identifiers,
  // fractions, commands, subscripts, decimal numbers or symbolic exponents.
  const power = "(?:\\^[0-9]{1,6})?";
  const variable = `[abxyz]${power}`;
  const atom = `(?:[ab][ \\t]+[xyz]${power}|[0-9]{1,6}${power}(?:${variable}){0,2}|(?:${variable}){1,2})`;
  const sum = `${atom}(?:[ \\t]*[+-][ \\t]*${atom})*`;
  const term = `(?:\\([ \\t]*-?${sum}[ \\t]*\\)${power}|${atom})`;
  const algebra = `-?${term}(?:[ \\t]*[+-][ \\t]*${term})*`;
  const legacyPattern = new RegExp(`(?:[pfg]\\([xyz]\\)[ \\t]*=[ \\t]*)?${algebra}(?:[ \\t]*=[ \\t]*${algebra})?`, "g");

  function renderCurated(element, source, problemId, registry) {
    const entries = registry.filter(entry => entry?.problem_id === problemId);
    if (!entries.length) return false;
    if (entries.length !== 1) throw new Error("Apresentação matemática duplicada.");
    const entry = entries[0];
    // A known-but-stale entry is terminal: never silently reinterpret the new
    // statement with either the delimiter layer or the legacy heuristic.
    if (entry.source_statement !== source) return true;
    if (!Number.isSafeInteger(entry.display_version) || entry.display_version < 1 ||
        !Array.isArray(entry.segments) || !entry.segments.length) {
      throw new Error("Apresentação matemática inválida.");
    }
    const fragment = root.document.createDocumentFragment();
    for (const segment of entry.segments) {
      if (!segment || typeof segment.content !== "string" || !["text", "math"].includes(segment.type)) {
        throw new Error("Segmento de apresentação inválido.");
      }
      if (segment.type === "text") {
        fragment.appendChild(root.document.createTextNode(segment.content));
      } else {
        if (!segment.content.trim() || typeof root.katex?.render !== "function") {
          throw new Error("Renderizador ou expressão indisponível.");
        }
        const math = root.document.createElement("span");
        root.katex.render(segment.content, math, { ...options, throwOnError: true, macros: {} });
        fragment.appendChild(math);
      }
    }
    // Commit only after every segment succeeds; exceptions keep the full source.
    element.textContent = "";
    element.appendChild(fragment);
    return true;
  }

  function renderLegacy(element, source) {
    // Existing partial TeX, code or HTML-like text is outside this fallback.
    if (/[\\_{}<>`]/.test(source)) return;
    const matches = [...source.matchAll(legacyPattern)].filter(match => {
      const candidate = match[0];
      if (candidate.length > 160) return false;
      // A caret power is a strong signal. Without it, require both a variable,
      // a digit and addition/equality: isolated letters and hyphenated labels
      // such as a-1 stay text (subtraction with powers remains supported).
      if (!/\^[0-9]+/.test(candidate) && !(/[abxyz]/.test(candidate) && /[0-9]/.test(candidate) && /[+=]/.test(candidate))) return false;
      const before = source.slice(0, match.index).trimEnd().slice(-1);
      const after = source.slice(match.index + candidate.length).trimStart()[0] || "";
      // Reject fragments touching unsupported/malformed math or identifiers.
      // Spaces separate prose, but must not hide an adjacent math operator.
      const adjacentBefore = source[match.index - 1] || "";
      const adjacentAfter = source[match.index + candidate.length] || "";
      if (/[\p{L}\p{N}]/u.test(adjacentBefore + adjacentAfter)) return false;
      if (/[\^_/{}\[\]\\=+*()\-∑²≥≤×÷∈π]/.test(before + after)) return false;
      if (adjacentBefore === "." || (adjacentAfter === "." && /[0-9]/.test(source[match.index + candidate.length + 1] || ""))) return false;
      if ((adjacentAfter === "," && /[0-9]/.test(source[match.index + candidate.length + 1] || "")) || (adjacentBefore === "," && /[0-9]/.test(source[match.index - 2] || ""))) return false;
      return true;
    });
    if (!matches.length) return;
    if (typeof root.katex?.render !== "function") throw new Error("Renderizador matemático indisponível.");
    const fragment = root.document.createDocumentFragment();
    let cursor = 0;
    for (const match of matches) {
      fragment.appendChild(root.document.createTextNode(source.slice(cursor, match.index)));
      const math = root.document.createElement("span");
      // Braces are presentation-only; catalog strings are never rewritten.
      const latex = match[0].replace(/\^([0-9]+)/g, "^{$1}");
      root.katex.render(latex, math, { ...options, throwOnError: true, macros: {} });
      fragment.appendChild(math);
      cursor = match.index + match[0].length;
    }
    fragment.appendChild(root.document.createTextNode(source.slice(cursor)));
    element.textContent = "";
    element.appendChild(fragment);
  }

  function render(element, message, { problemId, registry = [] } = {}) {
    const source = element.textContent;
    message.textContent = "";
    message.hidden = true;

    try {
      if (problemId && renderCurated(element, source, problemId, registry)) return;
      if (!/(\$|\\\(|\\\[)/.test(source)) {
        renderLegacy(element, source);
        return;
      }
      if (typeof root.renderMathInElement !== "function") {
        throw new Error("Renderizador matemático indisponível.");
      }
      root.renderMathInElement(element, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true },
        ],
        throwOnError: false,
        ...options,
        macros: {},
      });
      if (element.querySelector(".katex-error")) {
        message.textContent = "Uma expressão não pôde ser renderizada. Seu texto original foi mantido no enunciado.";
        message.hidden = false;
      }
    } catch (error) {
      // Never turn catalog text or an exception into arbitrary HTML.
      element.textContent = source;
      message.textContent = "Não foi possível renderizar a matemática. O enunciado permanece disponível em texto.";
      message.hidden = false;
    }
  }

  root.ConfiaProblemMath = Object.freeze({ render });
})(globalThis);
