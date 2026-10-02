const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const presentations = JSON.parse(fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/problem-presentations/registry.json"), "utf8"));

// Minimal DOM for exercising the actual vendored KaTeX and auto-render assets.
// No browser/build dependency is required for these presentation unit tests.
class Node {
  constructor(tag = "", text = "", type = 1) {
    this.nodeName = tag.toUpperCase();
    this.nodeType = type;
    this.data = text;
    this.childNodes = [];
    this.attributes = {};
    this.style = {};
    this.className = "";
    this.hidden = false;
  }
  get textContent() { return this.nodeType === 3 ? this.data : this.childNodes.map(node => node.textContent).join(""); }
  set textContent(value) {
    this.childNodes = [];
    if (value) this.appendChild(new Node("", value, 3));
  }
  get nextSibling() {
    const siblings = this.parentNode?.childNodes || [];
    return siblings[siblings.indexOf(this) + 1] || null;
  }
  appendChild(node) {
    if (node.nodeType === 11) {
      for (const child of [...node.childNodes]) this.appendChild(child);
    } else {
      node.remove();
      node.parentNode = this;
      this.childNodes.push(node);
    }
    return node;
  }
  remove() {
    if (this.parentNode) {
      this.parentNode.childNodes.splice(this.parentNode.childNodes.indexOf(this), 1);
      this.parentNode = null;
    }
  }
  replaceChild(fragment, old) {
    const index = this.childNodes.indexOf(old);
    const children = fragment.nodeType === 11 ? [...fragment.childNodes] : [fragment];
    for (const child of children) { child.remove(); child.parentNode = this; }
    this.childNodes.splice(index, 1, ...children);
    old.parentNode = null;
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  setAttributeNS(namespace, name, value) { this.setAttribute(name, value); }
  querySelectorAll(selector) {
    const matches = [];
    for (const child of this.childNodes) {
      const classes = child.className.split(" ");
      if (selector.startsWith(".") ? classes.includes(selector.slice(1)) : child.nodeName.toLowerCase() === selector) matches.push(child);
      matches.push(...child.querySelectorAll(selector));
    }
    return matches;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}

function renderer({ missing = false, failingLegacy = false } = {}) {
  const root = path.join(__dirname, "../../app/confia_lean_auditor/static/capture");
  const document = {
    compatMode: "CSS1Compat",
    createElement: tag => new Node(tag),
    createElementNS: (namespace, tag) => new Node(tag),
    createTextNode: text => new Node("", text, 3),
    createDocumentFragment: () => new Node("", "", 11),
  };
  const context = { document, Node: { TEXT_NODE: 3 }, console };
  vm.createContext(context);
  if (!missing) {
    for (const asset of ["vendor/katex-0.18.9/katex.min.js", "vendor/katex-0.18.9/contrib/auto-render.min.js"]) {
      vm.runInContext(fs.readFileSync(path.join(root, asset), "utf8"), context);
    }
  }
  if (failingLegacy) context.katex.render = () => { throw new Error("Falha simulada"); };
  vm.runInContext(fs.readFileSync(path.join(root, "problem-math.js"), "utf8"), context);
  return (text, presentation = {}) => {
    const element = new Node("div");
    const message = new Node("p");
    element.textContent = text;
    context.ConfiaProblemMath.render(element, message, presentation);
    return { element, message };
  };
}

test("plain catalog text is preserved literally, including HTML-like text", () => {
  const source = "Texto comum: x < y e <img src=x onerror=alert(1)>.";
  const { element, message } = renderer()(source);
  assert.equal(element.textContent, source);
  assert.equal(element.querySelector("img"), null);
  assert.equal(element.querySelector(".katex"), null);
  assert.equal(message.hidden, true);
});

for (const [left, right, display] of [["$", "$", false], ["$$", "$$", true], ["\\(", "\\)", false], ["\\[", "\\]", true]]) {
  test(`mixed text renders ${left}…${right} as ${display ? "display" : "inline"} math`, () => {
    const { element, message } = renderer()(`Antes ${left}\\frac{1}{2}${right} depois.`);
    assert.ok(element.querySelector(".katex"));
    assert.equal(Boolean(element.querySelector(".katex-display")), display);
    assert.equal(element.childNodes[0].textContent, "Antes ");
    assert.equal(element.childNodes.at(-1).textContent, " depois.");
    assert.equal(message.hidden, true);
  });
}

test("invalid LaTeX stays legible while the following valid math still renders", () => {
  const { element, message } = renderer()(String.raw`Antes $\frac{1}$ depois $x^2$.`);
  assert.ok(element.querySelector(".katex-error"));
  assert.equal(element.querySelector(".katex-error").textContent, String.raw`\frac{1}`);
  assert.ok(element.querySelector(".katex"));
  assert.equal(message.hidden, false);
  assert.match(message.textContent, /texto original/);
});

test("missing renderer preserves the source and shows a readable fallback", () => {
  const source = "Texto $x^2$";
  const { element, message } = renderer({ missing: true })(source);
  assert.equal(element.textContent, source);
  assert.equal(message.hidden, false);
  assert.match(message.textContent, /permanece disponível em texto/);
});

test("untrusted TeX cannot create image or link elements", () => {
  const { element } = renderer()(String.raw`$\includegraphics{https://example.com/test.png}$ $\href{javascript:alert(1)}{clique}$`);
  assert.equal(element.querySelector("img"), null);
  assert.equal(element.querySelector("a"), null);
});

function annotations(element) {
  return element.querySelectorAll("annotation").map(node => node.textContent);
}

test("legacy polynomial gets braced multi-digit exponents, without changing prose", () => {
  const { element, message } = renderer()("Calcule x^57+ax^14 e justifique.");
  assert.deepEqual(annotations(element), ["x^{57}+ax^{14}"]);
  assert.equal(element.childNodes[0].textContent, "Calcule ");
  assert.equal(element.childNodes.at(-1).textContent, " e justifique.");
  assert.equal(message.hidden, true);
});

test("actual catalog polynomial, divisor and remainder all render conservatively", () => {
  const source = JSON.parse(fs.readFileSync(path.join(__dirname, "../../problems/ITA2025F2Q1/problem.json"), "utf8")).statement;
  const { element } = renderer()(source);
  assert.deepEqual(annotations(element), ["p(x)=x^{57}+a x^{14}+b x^{7}+1", "x^{2}-x+1", "2x+1"]);
  assert.equal(element.childNodes[0].textContent, "Encontre os valores reais a e b tais que o polinômio ");
  assert.equal(element.childNodes[2].textContent, ", ao ser dividido por ");
  assert.equal(element.childNodes.at(-1).textContent, ".");
});

test("simple powers, parenthesized polynomials and equalities are supported", () => {
  const { element } = renderer()("Use a^14, (x^2-x+1)^2 e x^2=2x+1. Também 3^100.");
  assert.deepEqual(annotations(element), ["a^{14}", "(x^{2}-x+1)^{2}", "x^{2}=2x+1", "3^{100}"]);
});

test("delimited math uses the explicit layer, without guessing the surrounding text", () => {
  const { element } = renderer()("Legado x^57 e explícito $x^{14}$.");
  assert.deepEqual(annotations(element), ["x^{14}"]);
  assert.equal(element.childNodes[0].textContent, "Legado x^57 e explícito ");
});

test("ordinary prose, isolated letters and hyphenated words remain literal", () => {
  const source = "Sejam a e b reais. O aluno usa a caneta x vezes em 01-10-2026. Releia Argand-Gauss, a+b e item a-1.";
  const { element } = renderer()(source);
  assert.equal(element.textContent, source);
  assert.equal(element.querySelector(".katex"), null);
});

for (const source of [
  "x^2+", "x^2+texto+x^3", "(x^2", "x^2)", "x^2/y", "(x^2 + 1/x)^6",
  "x^2^3", "x^1234567", "aux^2", "máx^2", "x^2é", "αx^2", "x^2foo", "x^2 =", "x^2 * y", "x^2 × y",
  "x^2+1,5", "0.5x^2", "0,5x^2", "1/x^2", "a_n+x^2", String.raw`\sqrt{x^2}`,
  "`x^2`", "<img src=x onerror=alert(1)> x^2", "https://example.com/x^2.json",
  "x^2".repeat(60),
]) {
  test(`unsafe or unsupported legacy source stays literal: ${source.slice(0, 60)}`, () => {
    const { element, message } = renderer()(source);
    assert.equal(element.textContent, source);
    assert.equal(element.querySelector(".katex"), null);
    assert.equal(element.querySelector("img"), null);
    assert.equal(message.hidden, true);
  });
}

for (const options of [{ missing: true }, { failingLegacy: true }]) {
  test(`legacy renderer failure preserves the exact source: ${JSON.stringify(options)}`, () => {
    const source = "Calcule x^57+ax^14, sem alterar o texto.";
    const { element, message } = renderer(options)(source);
    assert.equal(element.textContent, source);
    assert.equal(element.querySelector(".katex"), null);
    assert.equal(message.hidden, false);
  });
}

for (const entry of presentations) {
  test(`curated ${entry.problem_id} renders every math segment and preserves literal prose`, () => {
    const source = JSON.parse(fs.readFileSync(path.join(__dirname, `../../problems/${entry.problem_id}/problem.json`), "utf8")).statement;
    assert.equal(entry.source_statement, source);
    const before = JSON.stringify(entry);
    const { element, message } = renderer()(source, { problemId: entry.problem_id, registry: presentations });
    assert.deepEqual(annotations(element), entry.segments.filter(segment => segment.type === "math").map(segment => segment.content));
    assert.equal(element.childNodes.length, entry.segments.length);
    entry.segments.forEach((segment, index) => {
      if (segment.type === "text") {
        assert.equal(element.childNodes[index].nodeType, 3);
        assert.equal(element.childNodes[index].textContent, segment.content);
      }
    });
    assert.equal(message.hidden, true);
    assert.equal(element.querySelector(".katex-error"), null);
    assert.equal(JSON.stringify(entry), before);
  });

  test(`curated ${entry.problem_id} mismatch preserves the exact received statement`, () => {
    const source = entry.source_statement + " ";
    const { element, message } = renderer()(source, { problemId: entry.problem_id, registry: presentations });
    assert.equal(element.textContent, source);
    assert.equal(element.querySelector(".katex"), null);
    assert.equal(message.hidden, true);
  });
}

test("curation includes reviewed powers, fractions, indices, sums and trigonometry", () => {
  const math = id => presentations.find(entry => entry.problem_id === id).segments.filter(segment => segment.type === "math").map(segment => segment.content);
  assert.ok(math("ITA2025Q1").includes("z^{2}"));
  assert.ok(math("ITA2025Q3").includes(String.raw`\left(x + \frac{1}{x}\right)^{6} \left(x - \frac{2}{x}\right)^{5}`));
  assert.ok(math("ITA2025Q5").includes(String.raw`S_n = \sum_{k=1}^{n} a_k = b_{n+1} - b_1`));
  assert.ok(math("ITA2025Q8").includes(String.raw`f(x) = \sqrt{\frac{2\operatorname{sen}(2x) + 2\operatorname{sen}(x) - 2\cos(x) - 1}{8(\cos(2x) + 1)}}`));
  assert.ok(math("ITA2025F2Q3").includes(String.raw`\operatorname{sen}\alpha - 2\operatorname{sen}\beta + \cos\beta = \frac{3}{4}`));
  assert.ok(math("ITA2025F2Q5").includes(String.raw`\log_{10} 2 = 0{,}3010`));
  assert.ok(math("ITA2025F2Q8").includes(String.raw`a_{ij}=\max\{i,j\}`));
});

test("curated data takes priority even if its source contains explicit delimiters", () => {
  const source = "Texto $x^2$";
  const registry = [{ problem_id: "test", source_statement: source, display_version: 1,
    segments: [{ type: "text", content: "Texto " }, { type: "math", content: "x^{2}" }] }];
  const { element } = renderer()(source, { problemId: "test", registry });
  assert.deepEqual(annotations(element), ["x^{2}"]);
  assert.equal(element.childNodes.length, 2);
});

test("a stale curated entry must not fall through to explicit math or legacy guessing", () => {
  const registry = [{ problem_id: "test", source_statement: "Antigo", display_version: 1, segments: [] }];
  for (const source of ["Novo $x^2$", "Novo x^57+ax^14", "Novo\\n", "Antigo "]) {
    const { element } = renderer()(source, { problemId: "test", registry });
    assert.equal(element.textContent, source);
    assert.equal(element.querySelector(".katex"), null);
  }
});

test("absent curation still resolves explicit math, then restricted legacy, then text", () => {
  const render = renderer();
  for (const [source, expected] of [["Antes $x^{2}$", ["x^{2}"]], ["Antes x^57+ax^14", ["x^{57}+ax^{14}"]], ["Texto comum", []]]) {
    const { element } = render(source, { problemId: "unknown", registry: presentations });
    assert.deepEqual(annotations(element), expected);
    if (!expected.length) assert.equal(element.textContent, source);
  }
});

test("invalid curated LaTeX restores the whole source; a subsequent question still renders", () => {
  const render = renderer();
  const source = "Original x^2 e x^3.";
  const registry = [{ problem_id: "test", source_statement: source, display_version: 1,
    segments: [{ type: "math", content: "x^{2}" }, { type: "math", content: String.raw`\frac{1}` }] }];
  const { element, message } = render(source, { problemId: "test", registry });
  assert.equal(element.textContent, source);
  assert.equal(element.querySelector(".katex"), null);
  assert.equal(message.hidden, false);
  const next = presentations.find(entry => entry.problem_id === "ITA2025Q3");
  assert.equal(render(next.source_statement, { problemId: next.problem_id, registry: presentations }).message.hidden, true);
});

test("curated literal text cannot create HTML, and TeX retains trust:false", () => {
  const source = "Texto <img src=x onerror=alert(1)>";
  const registry = [{ problem_id: "test", source_statement: source, display_version: 1,
    segments: [{ type: "text", content: source }, { type: "math", content: String.raw`\href{javascript:alert(1)}{clique}` }] }];
  const { element } = renderer()(source, { problemId: "test", registry });
  assert.equal(element.childNodes[0].textContent, source);
  assert.equal(element.querySelector("img"), null);
  assert.equal(element.querySelector("a"), null);
});

test("malformed or duplicate curated records cannot silently fall through", () => {
  const source = "Original x^2";
  const entry = { problem_id: "test", source_statement: source, display_version: 1, segments: [{ type: "text", content: "Original " }] };
  for (const registry of [
    [entry, entry],
    [{ ...entry, display_version: 0 }],
    [{ ...entry, segments: [{ type: "html", content: "<img>" }] }],
    [{ ...entry, segments: [{ type: "math", content: 2 }] }],
  ]) {
    const { element, message } = renderer()(source, { problemId: "test", registry });
    assert.equal(element.textContent, source);
    assert.equal(element.querySelector(".katex"), null);
    assert.equal(message.hidden, false);
  }
});

test("missing KaTeX preserves the original curated statement with a readable message", () => {
  const entry = presentations[0];
  const { element, message } = renderer({ missing: true })(entry.source_statement, { problemId: entry.problem_id, registry: presentations });
  assert.equal(element.textContent, entry.source_statement);
  assert.equal(message.hidden, false);
});
