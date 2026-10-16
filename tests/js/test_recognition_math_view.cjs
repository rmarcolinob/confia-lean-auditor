const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants } = require('./ui-dom.cjs');

const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/recognition-view.js'), 'utf8');
function view({ fail, softFail } = {}) {
  const calls = [];
  const context = { document: { createElement: element }, katex: { render(latex, target, options) {
    calls.push({ latex, options });
    if (fail?.(latex)) throw Error('invalid TeX');
    if (softFail?.(latex)) { target.textContent = 'KaTeX error'; target.querySelector = () => ({}); return; }
    target.textContent = `rendered:${latex}`;
  } } };
  vm.runInNewContext(source, context);
  return { api: context.ConfiaRecognitionView, calls, host: element('div') };
}

test('plain text remains literal and preserves line breaks', () => {
  const ui = view(), original = 'Primeira linha\nSegunda linha · R$ 10 e R$20';
  ui.api.render(ui.host, [{ page_index: 0, kind: 'text', text: original }]);
  assert.equal(ui.host.children[0].children[1].textContent, original);
  assert.equal(ui.calls.length, 0);
  assert.match(fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/submissions/teacher.css'), 'utf8'),
    /\.recognized-content\s*\{\s*white-space:\s*pre-wrap/);
});

test('inline math, bare fraction and mixed Portuguese use local KaTeX without changing source', () => {
  const ui = view();
  const sample = String.raw`Seja \(p(x)=x^{57}+a x^{14}+b x^7+1\)`;
  const segments = Object.freeze([{ page_index: 0, kind: 'text', text: sample }]);
  ui.api.render(ui.host, segments);
  const content = ui.host.children[0].children[1];
  assert.equal(content.textContent, 'Seja rendered:p(x)=x^{57}+a x^{14}+b x^7+1');
  assert.doesNotMatch(content.textContent, /\\\(|\\\)/);
  assert.equal(segments[0].text, sample);
  assert.equal(ui.calls[0].options.displayMode, false);
  assert.equal(ui.calls[0].options.throwOnError, false);
  assert.equal(ui.calls[0].options.trust, false);
  ui.api.render(ui.host, [{ page_index: 0, kind: 'text', text: String.raw`\frac{1}{2}` }]);
  assert(ui.calls.some(call => call.latex === String.raw`\frac{1}{2}`));
  assert.equal(ui.host.children[0].children[1].children[0].textContent, String.raw`rendered:\frac{1}{2}`);
});

test('multiple inline and display formulas stay in sequence with paragraphs', () => {
  const ui = view();
  const original = String.raw`Texto \(x^2+1\)
$$\frac{1}{2}$$
Outro $y_1$ e \[z^3\]`;
  ui.api.render(ui.host, [{ page_index: 0, kind: 'text', text: original }]);
  assert.deepEqual(ui.calls.map(call => call.latex), ['x^2+1', String.raw`\frac{1}{2}`, 'y_1', 'z^3']);
  assert.deepEqual(ui.calls.map(call => call.options.displayMode), [false, true, false, true]);
  const content = ui.host.children[0].children[1];
  assert.match(content.textContent, /Texto rendered:x\^2\+1\nrendered:/);
  assert.match(content.textContent, /\nOutro rendered:y_1 e rendered:z\^3/);
});

test('mixed Mathpix latex_styled keeps prose outside its math delimiters', () => {
  const ui = view();
  const original = String.raw`Seja \(p(x)=x^{57}+a x^{14}+b x^7+1\)`;
  ui.api.render(ui.host, [{ page_index: 0, kind: 'mixed', text: original, latex: original }]);
  const main = ui.host.children[0].children[1];
  assert.equal(main.textContent, 'Seja rendered:p(x)=x^{57}+a x^{14}+b x^7+1');
  assert.equal(ui.host.children[0].children[2].children[1].textContent, original);
  assert.equal(ui.host.children[0].children[2].children[2].textContent, original);
});

test('invalid math and missing KaTeX preserve exact recognized expression', () => {
  const original = String.raw`Antes \(\frac{1}\) depois`;
  const ui = view({ fail: () => true });
  ui.api.render(ui.host, [{ page_index: 0, kind: 'text', text: original }]);
  assert.equal(ui.host.children[0].children[1].textContent, original);
  assert(descendants(ui.host).some(node => node.className?.includes('recognized-math-fallback')));
  const soft = view({ softFail: () => true });
  soft.api.render(soft.host, [{ page_index: 0, kind: 'text', text: original }]);
  assert.equal(soft.host.children[0].children[1].textContent, original);
  const context = { document: { createElement: element } };
  vm.runInNewContext(source, context);
  const host = element('div');
  context.ConfiaRecognitionView.render(host, [{ page_index: 0, kind: 'text', text: original }]);
  assert.equal(host.children[0].children[1].textContent, original);
});

test('untrusted HTML is text, and incorrect mathematics remains incorrect', () => {
  const ui = view();
  const original = String.raw`<img src=x onerror=alert(1)> \(30+15=46\)`;
  ui.api.render(ui.host, [{ page_index: 0, kind: 'text', text: original }]);
  assert.equal(ui.host.children[0].children[1].textContent,
    '<img src=x onerror=alert(1)> rendered:30+15=46');
  assert.equal(ui.calls[0].latex, '30+15=46');
  assert(!descendants(ui.host).some(node => ['img', 'script'].includes(node.tag)));
  assert.doesNotMatch(source, /innerHTML|insertAdjacentHTML/);
});
