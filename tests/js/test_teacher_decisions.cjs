const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants, flush, deferred } = require('./ui-dom.cjs');
const teacher = require('./teacher-dom.cjs');
const { page: studentPage } = require('./workspace-dom.cjs');
const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/submissions/decisions.js'), 'utf8');
const aid = 'asmt_' + 'b'.repeat(32), iid = 'ait_' + 'c'.repeat(32), runId = 'aud_' + 'e'.repeat(64);
const bound = { ...teacher.record, assessment_id: aid, assessment_item_id: iid };
const base = { decision_id: 'dec_' + 'a'.repeat(32), submission_id: teacher.id, assessment_id: aid,
  assessment_item_id: iid, problem_id: bound.problem_id, status: 'DRAFT', version: 1,
  item_max_points: '5.0', teacher_final_points: null, teacher_feedback: '', teacher_internal_note: null,
  override_reason: null, confia_suggested_points: '4.00', confia_score_raw: '8.0', confia_max_score_raw: '10.0',
  audit_run_id: runId, audit_state: 'current' };
const opened = { audit_run_id: runId, revision_number: 1, created_at: '2026-10-18T12:00:00Z' };

async function decisionPage(initial = base, transport) {
  const panel = element('section'), calls = [], changes = [];
  let saved = initial ? { ...initial } : null;
  const context = { document: { createElement: element }, window: {},
    fetch: async (url, options) => {
      const body = options.body ? JSON.parse(options.body) : null;
      calls.push({ url, ...options, body });
      if (transport) { const response = await transport(url, options, body); if (response) return response; }
      if (options.method === 'POST' && url.endsWith('/teacher-decision')) {
        saved = { ...base, ...(body.audit_run_id ? {} : { audit_run_id: null, confia_suggested_points: null, audit_state: 'none' }) };
      }
      if (options.method === 'PATCH') {
        const { expected_version, ...changes } = body;
        assert.equal(expected_version, saved.version);
        saved = { ...saved, ...changes, version: saved.version + 1 };
        if ('audit_run_id' in changes && changes.audit_run_id === null) {
          saved.confia_suggested_points = null; saved.audit_state = 'none';
        }
      }
      if (url.endsWith('/finalize')) saved = { ...saved, status: 'FINALIZED', version: saved.version + 1 };
      if (url.endsWith('/release')) saved = { ...saved, status: 'RELEASED', version: saved.version + 1 };
      return { ok: true, json: async () => saved };
    } };
  vm.runInNewContext(source, context);
  const controller = context.window.ConfIADecisions.mount(panel, bound, value => changes.push(value));
  controller.setOpenedRun(opened, true);
  await flush();
  const nodes = () => descendants(panel);
  const button = text => nodes().find(node => node.tag === 'button' && node.textContent === text);
  const field = name => nodes().find(node => node.name === name);
  const input = async (name, value) => { field(name).value = value; await field(name).emit('input'); };
  return { panel, controller, calls, changes, button, field, input, nodes };
}

test('suggestion is normalized, copy stays a dirty draft, then save/finalize/release are separate writes', async () => {
  const ui = await decisionPage();
  assert.match(ui.panel.textContent, /Pontuação sugerida pelo ConfIA: 4,0 \/ 5,0/);
  assert.equal(ui.field('teacher_final_points').value, '');
  await ui.button('Usar sugestão').click();
  assert.equal(ui.field('teacher_final_points').value, '4,00');
  assert(ui.controller.isDirty());
  assert.equal(ui.calls.length, 1);
  await ui.input('teacher_feedback', 'Boa solução…');
  await ui.input('teacher_internal_note', 'Apenas para o professor');
  await ui.button('Salvar rascunho').click();
  assert.equal(ui.changes.at(-1).status, 'DRAFT');
  assert.equal(ui.calls.at(-1).method, 'PATCH');
  assert.equal(ui.calls.at(-1).body.teacher_internal_note, 'Apenas para o professor');
  assert(!ui.controller.isDirty());
  await ui.button('Finalizar decisão').click();
  assert.equal(ui.changes.at(-1).status, 'FINALIZED');
  assert.match(ui.panel.textContent, /Decisão finalizada.*Pontuação final do professor: 4,0 \/ 5,0/);
  assert.equal(ui.nodes().filter(node => ['input', 'textarea'].includes(node.tag)).length, 0);
  assert(!ui.button('Salvar rascunho'));
  await ui.button('Liberar resultado ao aluno').click();
  assert.equal(ui.changes.at(-1).status, 'RELEASED');
  assert.match(ui.panel.textContent, /Resultado liberado ao aluno/);
  assert.equal(ui.nodes().filter(node => ['input', 'textarea', 'button'].includes(node.tag)).length, 0);
});

test('manual decimal entry and override require a reason before finalizing, while draft may be saved', async () => {
  const ui = await decisionPage();
  await ui.input('teacher_final_points', '3,75');
  assert.equal(ui.field('override_reason').required, true);
  assert.equal(ui.nodes().find(node => node.tag === 'label' && node.children.includes(ui.field('override_reason'))).hidden, false);
  await ui.button('Finalizar decisão').click();
  assert.match(ui.panel.textContent, /Justifique a alteração/);
  assert.equal(ui.field('override_reason').getAttribute('aria-invalid'), 'true');
  assert.equal(ui.field('override_reason').focused, true);
  assert.equal(ui.calls.length, 1);
  await ui.button('Salvar rascunho').click();
  assert.equal(ui.changes.at(-1).status, 'DRAFT');
  assert.equal(ui.calls.at(-1).body.teacher_final_points, '3.75');
  await ui.input('override_reason', 'Critério pedagógico docente');
  await ui.button('Finalizar decisão').click();
  assert.equal(ui.changes.at(-1).status, 'FINALIZED');
});

test('a missing or inconclusive audit allows manual points without an override reason', async () => {
  const ui = await decisionPage(null);
  ui.controller.setOpenedRun(null, false);
  assert(ui.button('Iniciar decisão com análise aberta').disabled);
  await ui.button('Iniciar decisão manual').click();
  assert.equal(ui.changes.at(-1).audit_run_id, null);
  assert(!ui.button('Usar sugestão'));
  await ui.input('teacher_final_points', '5');
  assert.equal(ui.field('override_reason').required, false);
  await ui.button('Finalizar decisão').click();
  assert.equal(ui.changes.at(-1).status, 'FINALIZED');
});

test('the opened audit is explicitly selected and provenance stays visible in a disclosure', async () => {
  const ui = await decisionPage(null);
  const selected = { ...opened, audit_run_id: 'aud_' + 'f'.repeat(64), revision_number: 2 };
  ui.controller.setOpenedRun(selected, true);
  await ui.button('Iniciar decisão com análise aberta').click();
  assert.equal(ui.calls.find(call => call.method === 'POST').body.audit_run_id, selected.audit_run_id);
  assert(ui.nodes().some(node => node.tag === 'summary' && node.textContent === 'Análise vinculada à decisão'));
});

test('stale suggestion is not reusable and explicit manual mode clears the linkage', async () => {
  const ui = await decisionPage({ ...base, audit_state: 'stale' });
  ui.controller.setOpenedRun(opened, false);
  assert.match(ui.panel.textContent, /desatualizada/);
  assert(ui.button('Usar sugestão').disabled);
  assert(ui.button('Vincular análise aberta').disabled);
  await ui.button('Decidir sem sugestão ConfIA').click();
  assert.equal(ui.calls.at(-1).body.audit_run_id, null);
  assert(!ui.button('Usar sugestão'));
  await ui.input('teacher_final_points', '2.5');
  await ui.button('Finalizar decisão').click();
  assert.equal(ui.changes.at(-1).status, 'FINALIZED');
});

test('invalid points are rejected before transport and server conflicts preserve unsaved text', async () => {
  const ui = await decisionPage(base, async (_url, options) => options.method === 'PATCH'
    ? { ok: false, status: 409, json: async () => ({ detail: 'Rascunho alterado em outra sessão.' }) } : null);
  for (const value of ['-1', '6', '1.001', 'NaN']) {
    await ui.input('teacher_final_points', value);
    await ui.button('Salvar rascunho').click();
    assert.equal(ui.calls.length, 1);
    assert.equal(ui.field('teacher_final_points').getAttribute('aria-invalid'), 'true');
    assert.equal(ui.field('teacher_final_points').focused, true);
  }
  await ui.input('teacher_final_points', '4');
  await ui.input('teacher_feedback', 'Texto preservado');
  await ui.button('Salvar rascunho').click();
  assert.equal(ui.field('teacher_feedback').value, 'Texto preservado');
  assert(ui.controller.isDirty());
  assert.match(ui.panel.textContent, /outra sessão/);
  await ui.button('Descartar alterações da decisão').click();
  assert(!ui.controller.isDirty());
});

test('decision controls expose labels, live feedback and one primary action per stage', async () => {
  const ui = await decisionPage();
  const message = ui.nodes().find(node => node.getAttribute('role') === 'status');
  assert.equal(message.getAttribute('aria-live'), 'polite');
  for (const name of ['teacher_final_points', 'teacher_feedback', 'teacher_internal_note', 'override_reason']) {
    assert.equal(ui.field(name).parentNode.tag, 'label');
    assert.equal(ui.field(name).getAttribute('aria-describedby'), message.id);
  }
  assert.equal(ui.field('teacher_final_points').inputMode, 'decimal');
  assert.equal(ui.field('override_reason').parentNode.hidden, true);
  assert.equal(ui.button('Salvar rascunho').className, 'secondary-action');
  assert.equal(ui.button('Finalizar decisão').className, 'primary-action');
  assert(!ui.button('Liberar resultado ao aluno'));
  await ui.button('Usar sugestão').click();
  await ui.button('Finalizar decisão').click();
  assert.equal(ui.button('Liberar resultado ao aluno').className, 'primary-action');
});

test('server diagnostics never become end-user messages and failed saves retain edits', async () => {
  const ui = await decisionPage(base, (_url, options) => options.method === 'PATCH'
    ? { ok: false, status: 500, json: async () => ({ detail: 'Traceback PRIVATE_INTERNAL_TOKEN' }) } : null);
  await ui.input('teacher_feedback', 'Meu feedback');
  await ui.button('Salvar rascunho').click();
  assert.equal(ui.field('teacher_feedback').value, 'Meu feedback');
  assert(ui.controller.isDirty());
  assert.match(ui.panel.textContent, /Não foi possível concluir a ação/);
  assert.doesNotMatch(ui.panel.textContent, /Traceback|PRIVATE_INTERNAL_TOKEN/);
  assert.equal(ui.panel.getAttribute('aria-busy'), 'false');
});

test('student clears earlier detail while refreshing and on failed or late responses', async () => {
  let next = { ok: true, json: async () => [exam] };
  const ui = await studentPage(undefined, { examsTransport: () => next });
  await openExam(ui);
  assert.match(ui.get('#student-exam-items').textContent, /Questão 1/);
  const pending = deferred(); next = pending.promise;
  ui.visit('exams');
  assert.equal(ui.get('#student-exam-items').textContent, '');
  assert.equal(ui.get('#student-exam-detail').hidden, true);
  assert.equal(ui.get('#student-exams').getAttribute('aria-busy'), 'true');
  next = { ok: false, status: 403 };
  ui.visit('exams'); await flush();
  assert.match(ui.get('#student-exams-message').textContent, /Não foi possível consultar os exames/);
  pending.resolve({ ok: true, json: async () => [exam] }); await flush();
  assert.equal(ui.get('#student-exam-list').textContent, '');
  assert.equal(ui.get('#student-exam-items').textContent, '');
  assert.equal(ui.get('#student-exams').getAttribute('aria-busy'), 'false');
});

test('double clicks while saving cannot publish duplicate mutations', async () => {
  const pending = deferred();
  const ui = await decisionPage(base, async (_url, options) => {
    if (options.method === 'PATCH') await pending.promise;
  });
  await ui.input('teacher_final_points', '4');
  const save = ui.button('Salvar rascunho');
  const first = save.click();
  assert(ui.controller.busy);
  await save.click();
  assert.equal(ui.calls.filter(call => call.method === 'PATCH').length, 1);
  pending.resolve(); await first;
  assert(!ui.controller.busy);
});

test('institutional decision panel follows the analysis and dirty decision blocks navigation', async () => {
  const ok = data => ({ ok: true, json: async () => data });
  const fallback = teacher.transportFor(true, true);
  const ui = teacher.page(async url => {
    if (url === '/submissions') return ok([bound]);
    if (url === `/submissions/${teacher.id}`) return ok({ ...teacher.detailData(), submission: bound });
    if (url.endsWith('/teacher-decision')) return ok(base);
    return fallback(url);
  });
  await ui.get('#refresh-manuscripts').click();
  await ui.get('#manuscript-list').children[0].click(); await flush();
  const detail = ui.get('#manuscript-detail');
  const analysis = detail.children.find(node => node.className === 'manuscript-analysis-panel');
  const decision = detail.children.find(node => node.className === 'teacher-decision-panel');
  assert(detail.children.indexOf(decision) > detail.children.indexOf(analysis));
  assert.match(ui.get('#manuscript-list').textContent, /Decisão em rascunho/);
  assert.match(ui.get('#manuscript-list').children[0].attributes['aria-label'], /Decisão em rascunho/);
  const field = descendants(decision).find(node => node.name === 'teacher_feedback');
  field.value = 'Não perder este feedback'; await field.emit('input');
  const back = descendants(detail).find(node => node.tag === 'button' && node.textContent === 'Voltar à fila de soluções');
  await back.click();
  assert.equal(detail.hidden, false);
  assert.match(ui.get('#manuscript-message').textContent, /Salve ou descarte as alterações da decisão/);
});

const exam = { assessment: { assessment_id: aid, title: 'Avaliação 1', opens_at: '2026-10-01T00:00:00Z',
  closes_at: '2026-12-01T00:00:00Z', instructions: 'Resolva.' }, teacher_name: 'Professor Demo', classroom_name: '2ª série A',
  availability: 'DISPONÍVEL', submitted_item_ids: [iid],
  items: [{ assessment_item_id: iid, problem_id: 'A', order: 1, points: 5 }], released_results: [] };

async function openExam(ui) {
  ui.visit('exams'); await flush();
  await descendants(ui.get('#student-exam-list')).find(node => node.tag === 'button' && node.textContent === 'Abrir avaliação').click();
}

test('student sees only delivery before release and the released teacher result afterward', async () => {
  const exams = [{ ...exam }];
  const ui = await studentPage(undefined, { exams });
  await openExam(ui);
  assert.equal(ui.get('#student-exams-message').textContent, '');
  assert.match(ui.get('#student-exam-items').textContent, /Enviada/);
  assert.doesNotMatch(ui.get('#student-exam-items').textContent, /Pontuação|Feedback do professor|Corrigida/);
  exams[0] = { ...exam, released_results: [{ assessment_id: aid, item_id: iid, problem_id: 'A', status: 'corrected',
    final_points: '4.00', max_points: '5.0', teacher_feedback: 'Boa solução… <img src=x onerror=unsafe>',
    released_at: '2026-10-18T12:00:00Z',
    // Even unexpected technical extras must never be rendered by the student UI.
    audit_run_id: runId, confia_suggested_points: '3', feedback: 'PRIVATE_CONFIA', lean_status: 'compiled',
    claims: ['PRIVATE_CLAIM'], override_reason: 'PRIVATE_OVERRIDE', teacher_internal_note: 'PRIVATE_NOTE' }] };
  await openExam(ui);
  const result = ui.get('#student-exam-items');
  assert.match(result.textContent, /Corrigida.*Pontuação: 4,0 \/ 5,0.*Feedback do professor.*Boa solução/);
  assert.match(ui.get('#student-exam-list').textContent, /Correção: 1 de 1 questões corrigidas/);
  assert.doesNotMatch(result.textContent, /ConfIA|PRIVATE_|Lean|claims|compiled|aud_/);
  assert.equal(descendants(result).some(node => node.tag === 'img'), false);
  assert.equal(ui.calls.some(call => /teacher-decision|submission-audits|\/audits/.test(call.url)), false);
});

test('student refuses unmatched or nonreleased results', async () => {
  for (const changes of [{ status: 'FINALIZED' }, { assessment_id: 'another' }, { item_id: 'another' }, { problem_id: 'another' }]) {
    const ui = await studentPage(undefined, { exams: [{ ...exam, released_results: [{ assessment_id: aid, item_id: iid,
      problem_id: 'A', status: 'corrected', final_points: '4', max_points: '5', teacher_feedback: 'Not visible', ...changes }] }] });
    await openExam(ui);
    assert.doesNotMatch(ui.get('#student-exam-items').textContent, /Pontuação|Not visible/);
  }
});
