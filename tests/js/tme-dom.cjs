const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { File } = require('node:buffer');
const Scan = require('../../app/confia_lean_auditor/static/tme/scan-model.js');
const { flush } = require('./capture-dom.cjs');
function element(tag) {
  return { tag, children: [], style: { setProperty(name, value) { this[name] = value; } }, dataset: {}, attributes: {}, handlers: {}, textContent: '', className: '', value: '',
    append(...items) { this.children.push(...items); }, appendChild(item) { this.append(item); return item; },
    replaceChildren(...items) { this.children = items; },
    addEventListener(event, handler) { this.handlers[event] = handler; },
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name]; }, focus() { this.focused = true; },
    querySelectorAll(selector) { return walk(this).filter(e => selector.split(',').includes(e.tag)); },
    checkValidity() { return true; }, reportValidity() { return true; }, scrollIntoView() {},
    classList: { add() {}, remove() {}, toggle() {} },
    setPointerCapture() {}, getBoundingClientRect() { return { left: 0, width: 1000 }; },
    async click() { if (!this.disabled) await this.handlers.click?.(); },
  };
}
function walk(root) { return [root, ...root.children.flatMap(walk)]; }
function text(root) { return walk(root).map(e => e.textContent).join(' '); }
const json = data => ({ ok: true, json: async () => data });

async function pilot({ auditRun = null, mode = 'IMAGE_SCAN', automatic = false, pendingAudit = false, initialStorage = [], pageCount = 1, startHome = false, homeCases = null, homeSummary = null, homeError = false } = {}) {
  const root = element('main'), calls = [], rendered = [], reports = [];
  let existingDecision = null, revisionNumber = 1, editedText = 'x = 2', accepted = Boolean(auditRun) && !pendingAudit, hasAudit = Boolean(auditRun) && !pendingAudit;
  let current = { case_id: 'case_' + 'a'.repeat(32), source_mode: mode,
    submission_id: 'sub_' + 'b'.repeat(32), problem_id: 'ITA2025F2Q1', external_candidate_ref: 'PROVA-1' };
  let feedback = { state: auditRun || automatic ? 'RECOGNIZED' : 'WAITING' }, attempts = 0, recognized = Boolean(auditRun || automatic);
  const snapshot = { ...current };
  const acceptedAt = '2026-10-19T10:00:00Z';
  const shell = Object.fromEntries(['sidebar-toggle', 'sidebar', 'session-label', 'session-detail', 'logout', 'recent-cases', 'home-bottom-nav', 'evaluator-avatar', 'home-session'].map(id => [id, element('div')]));
  shell['sidebar-toggle'].attributes['aria-expanded'] = 'true';
  const nav = ['cases', 'new', 'results', 'home'].map(view => { const el = element('button'); el.dataset.view = view; return el; });
  const ctx = { console, document: { body: element('body'), querySelector: selector => selector === '#app' ? root : shell[selector.slice(1)], querySelectorAll: () => nav, createElement: element },
    Blob, File, URL: { createObjectURL: () => 'blob:preserved', revokeObjectURL() {} },
    FileReader: class { readAsDataURL(file) { file.arrayBuffer().then(bytes => { this.result = 'data:image/png;base64,' + Buffer.from(bytes).toString('base64'); this.onload(); }); } },
    createImageBitmap() {},
    fetch: async (url, options = {}) => {
      calls.push({ url, options });
      const base = `/tme/cases/${current.case_id}`;
      if (url === '/auth/me') return json({ display_name: 'Avaliador de teste' });
      if (url.endsWith('/audits')) { if (options.method === 'POST') { hasAudit = true; return json(auditRun); } return json(hasAudit ? [auditRun] : []); }
      if (url.endsWith('/decision')) {
        if (options.method === 'POST') existingDecision = { ...JSON.parse(options.body), decided_at: acceptedAt };
        return json(existingDecision);
      }
      if (url === '/tme/cases' && options.method === 'POST') {
        current = { ...current, case_id: 'case_' + 'c'.repeat(32), submission_id: null };
        return json(current);
      }
      if (url.startsWith('/tme/home-summary?')) {
        if (homeError) throw new Error('private stack trace');
        const period = url.split('period=')[1];
        return json(typeof homeSummary === 'function' ? homeSummary(period) : homeSummary || {
          period, counts: {pending:0,in_progress:1,inconclusive:0,finalized:0},
          priority_cases:[{...current,exam_code:current.external_candidate_ref,question_label:'Q1',operational_status:'in_progress'}],
          exam_progress:[{exam_code:current.external_candidate_ref,known_items:1,completed_items:0,percent:0}],
          generated_at:acceptedAt,
        });
      }
      if (url === '/tme/cases') { if (homeError) throw new Error('private stack trace'); return json(homeCases || [current]); }
      if (url === '/tme/problems') return json([{ problem_id: 'ITA2025F2Q1', title: 'Questão 1' }]);
      if (url.endsWith('/scan-manifest')) return json({ pages: [{ index: 0, original_mime: 'image/png', captured_at: acceptedAt, rotation_degrees: 90 }] });
      if (url.endsWith('/originals/0')) return { ok: true, blob: async () => new Blob(['original-bytes'], { type: 'image/png' }) };
      if (url.endsWith('/scan') && options.method === 'POST') { current.submission_id = 'sub_' + 'd'.repeat(32); return json({ submission_id: current.submission_id }); }
      if (url.endsWith('/recognize')) {
        assert.match(text(root), /Reconhecendo/);
        assert.ok(walk(root).find(e => e.tag === 'button' && ['Tentar novamente', 'Reconhecer'].includes(e.textContent)).disabled);
        attempts++;
        if (attempts === 1) {
          feedback = { state: 'FAILED', error_code: 'PROVIDER_RATE_LIMITED', message: 'O limite do serviço de reconhecimento foi atingido. As páginas foram preservadas.' };
          return json({ status: 'FAILED', error_code: feedback.error_code });
        }
        recognized = true; feedback = { state: 'RECOGNIZED', message: 'Transcrição automática disponível.' };
        return json({ status: 'NEEDS_REVIEW' });
      }
      if (url.endsWith('/recognition-status')) return json(feedback);
      if (url.endsWith('/submission')) return json({ submission: { page_images: Array.from({ length: pageCount }, (_, page_index) => ({ page_index })) } });
      if (url.endsWith('/revisions')) { revisionNumber++; editedText = JSON.parse(options.body).segments[0].text; accepted = false; return json({ revision_number: revisionNumber }); }
      if (url.endsWith('/accept')) { accepted = true; return json({ acceptance: { revision_number: revisionNumber, acceptance_id: 'accept_auto' } }); }
      const revision = { revision_number: revisionNumber, segments: [{ page_index: 0, order: 0, kind: 'mixed', text: editedText, latex: editedText }] };
      if (url.endsWith('/transcriptions')) return json(recognized ? [{ transcription: { transcription_id: 'tr_demo' } }] : []);
      if (url.endsWith('/transcriptions/tr_demo')) return json({ transcription: { transcription_id: 'tr_demo' }, revisions: [revision],
        acceptances: accepted ? [{ revision_number: revisionNumber, acceptance_id: auditRun?.acceptance_id || 'accept_auto' }] : [] });
      if (url === base) return json({ ...current });
      throw new Error('Unexpected route: ' + url);
    },
  };
  const storage = new Map(initialStorage);
  ctx.window = { localStorage: { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value) }, ConfiaTMEScan: { ...Scan, derive: async () => ({ derived_png_base64: 'ZGVyaXZlZA==', derived_width: 10, derived_height: 20 }) },
    ConfiaRecognitionView: { renderMathText(node, content) { node.textContent = content; rendered.push(content); } },
    scrollTo() {}, addEventListener() {}, location: { origin: 'http://test' } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/audit-view.js'), 'utf8'), ctx);
  for (const file of ['workspace-controls.js', 'workspace-report.js', 'home.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/tme/' + file), 'utf8'), ctx);
  const render = ctx.window.ConfIAReport.render;
  ctx.window.ConfIAReport.render = (data, target, options) => {
    reports.push({ data, target, options }); return render(data, target, options);
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/tme/tme.js'), 'utf8'), ctx);
  await flush();
  if (!startHome) { await nav[0].click(); await flush(); }
  async function click(label) { const item = walk(root).find(e => e.tag === 'button' && (e.textContent === label || label === 'Abrir' && e.textContent === 'PROVA-1')); assert.ok(item, `Missing button ${label}`); await item.click(); await flush(); }
  return { root, calls, rendered, reports, snapshot, click, acceptedAt, shell, nav, storage, window: ctx.window };
}

module.exports = { pilot, walk, text };
