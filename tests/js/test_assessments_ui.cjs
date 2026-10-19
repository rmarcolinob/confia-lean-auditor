const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants, deferred } = require('./ui-dom.cjs');

const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/assessments.js'), 'utf8');
const id = 'asmt_' + 'a'.repeat(32), itemId = 'ait_' + 'b'.repeat(32), submissionId = 'sub_' + 'c'.repeat(32);
const item2 = 'ait_' + 'd'.repeat(32), id2 = 'asmt_' + 'e'.repeat(32);
const exam = { assessment: { assessment_id: id, title: 'Avaliação 1', status: 'PUBLISHED',
  opens_at: '2026-10-16T12:00:00Z', closes_at: '2026-10-23T12:00:00Z', instructions: 'Resolva.' },
  items: [{ assessment_item_id: itemId, problem_id: 'ITA2025F2Q1', order: 1, points: 5 },
    { assessment_item_id: item2, problem_id: 'ITA2025F2Q2', order: 2, points: 3 }],
  classroom_name: '2ª série A', availability: 'DISPONÍVEL' };
const exam2 = { ...exam, assessment: { ...exam.assessment, assessment_id: id2, title: 'Avaliação 2' },
  items: [{ assessment_item_id: 'ait_second_exam', problem_id: 'ITA2025F2Q3', order: 1, points: 2 }] };
const student = { user_id: 'student-1', display_name: 'Aluno Demo', submissions: { [itemId]: submissionId } };
const progressData = (view, students = [student]) => ({ assessment: view.assessment, items: view.items, students });
const ok = data => ({ ok: true, json: async () => data });

async function page({ exams = [exam, exam2], transport, navigate = true } = {}) {
  const nodes = new Map(), calls = [], opened = [], navigated = [];
  const scope = { schoolId: 'ceti-centro', classroomId: 'centro-2a-2026' };
  const get = key => {
    if (!nodes.has(key)) nodes.set(key, element('div'));
    return nodes.get(key);
  };
  const context = { document: { getElementById: get, createElement: element }, Date, Number, console, setTimeout,
    window: { ConfIATeacher: { context: () => ({ ...scope }), openSubmission: (...args) => opened.push(args) },
      ConfIAShell: { navigate: (...args) => { navigated.push(args); return navigate; } } },
    fetch: async url => {
      calls.push(url);
      if (transport) { const response = await transport(url); if (response) return response; }
      if (url.startsWith('/assessments?')) return ok(exams);
      if (url === `/assessments/${id}/progress`) return ok(progressData(exam));
      if (url === `/assessments/${id2}/progress`) return ok(progressData(exam2, [{ ...student,
        display_name: 'Maria Silva', submissions: { ait_second_exam: 'sub_' + 'f'.repeat(32) } }]));
      throw Error('unexpected URL ' + url);
    } };
  vm.runInNewContext(source, context);
  const load = context.window.ConfIAAssessments.load;
  await load();
  const cards = () => get('teacher-exam-list').children.filter(node => node.tag === 'article');
  const select = index => descendants(cards()[index]).find(node => node.tag === 'button').click();
  const nodesInDetail = () => descendants(get('teacher-exam-progress'));
  return { get, calls, opened, navigated, cards, select, nodesInDetail, scope, load };
}

test('selected exam contains its summary and deliveries before the next exam', async () => {
  const ui = await page();
  assert(ui.calls[0].includes('school_id=ceti-centro&classroom_id=centro-2a-2026'));
  await ui.select(0);
  assert.equal(ui.get('teacher-exam-progress').parentNode, ui.cards()[0]);
  assert.equal(ui.cards()[0].children.at(-1), ui.get('teacher-exam-progress'));
  assert.equal(ui.cards()[1].children.some(n => n === ui.get('teacher-exam-progress')), false);
  assert.match(ui.get('teacher-exam-progress').textContent, /Avaliação 1Turma2ª série APeríodo.*Questões2Total de pontos8StatusDisponível.*Entregas dos alunos/);
  assert.equal(ui.nodesInDetail().find(n => n.tag === 'thead').textContent, 'AlunoQ1Q2Progresso');
  assert.equal(ui.nodesInDetail().find(n => n.tag === 'tbody').textContent, 'Aluno DemoEnviadaNão enviada1/2');
  assert.equal(ui.nodesInDetail().find(n => n.className === 'exam-deliveries-scroll').tabIndex, 0);
});

test('delivered cell opens exact Submission and its display context; missing cell has no action', async () => {
  const ui = await page();
  await ui.select(0);
  const missing = ui.nodesInDetail().find(n => n.tag === 'td' && n.textContent === 'Não enviada');
  assert.equal(descendants(missing).some(n => n.tag === 'button' || n.tag === 'a'), false);
  await missing.click();
  assert.equal(ui.opened.length, 0);
  await ui.nodesInDetail().find(n => n.tag === 'button' && n.textContent === 'Enviada').click();
  assert.deepEqual(ui.navigated, [['teacher', 'submissions']]);
  assert.equal(ui.opened[0][0], submissionId);
  assert.deepEqual(JSON.parse(JSON.stringify(ui.opened[0][1])), { submissionId, assessmentId: id, assessmentTitle: 'Avaliação 1', classroomName: '2ª série A',
    assessmentItemId: itemId, problemId: 'ITA2025F2Q1', questionOrder: 1, studentId: 'student-1', studentName: 'Aluno Demo' });
});

test('switching exams replaces detail, scope and selection without leftover rows', async () => {
  const ui = await page();
  await ui.select(0);
  await ui.select(1);
  assert.equal(ui.get('teacher-exam-progress').parentNode, ui.cards()[1]);
  assert.equal(ui.cards()[0].dataset.selected, 'false');
  assert.equal(ui.cards()[1].dataset.selected, 'true');
  assert(!ui.cards()[0].textContent.includes('Aluno Demo'));
  assert.match(ui.get('teacher-exam-progress').textContent, /Avaliação 2.*Maria SilvaEnviada1\/1/);
  assert(!ui.get('teacher-exam-progress').textContent.includes('Aluno Demo'));
  await ui.nodesInDetail().find(n => n.tag === 'button' && n.textContent === 'Enviada').click();
  assert.equal(ui.opened[0][0], 'sub_' + 'f'.repeat(32));
  assert.equal(ui.opened[0][1].assessmentId, id2);
});

test('late responses cannot restore the previous exam after selection changes', async () => {
  const first = deferred(), second = deferred();
  const ui = await page({ transport: url => url.endsWith('/progress')
    ? (url.includes(id2) ? second.promise : first.promise) : null });
  const firstClick = ui.select(0);
  const secondClick = ui.select(1);
  assert.match(ui.get('teacher-exam-progress').textContent, /Avaliação 2.*Carregando entregas/);
  second.resolve(ok(progressData(exam2, []))); await secondClick;
  first.resolve(ok(progressData(exam))); await firstClick;
  assert.match(ui.get('teacher-exam-progress').textContent, /Nenhum aluno matriculado/);
  assert(!ui.get('teacher-exam-progress').textContent.includes('Aluno Demo'));
});

test('class changes clear detail and invalidate pending progress requests', async () => {
  const pending = deferred();
  const ui = await page({ transport: url => url.endsWith('/progress') ? pending.promise : null });
  const selecting = ui.select(0);
  ui.scope.classroomId = '';
  await ui.load();
  pending.resolve(ok(progressData(exam))); await selecting;
  assert.equal(ui.get('teacher-exam-progress').hidden, true);
  assert.equal(ui.get('teacher-exam-progress').textContent, '');
  assert.equal(ui.get('teacher-exam-list').textContent, '');
  assert.equal(ui.get('teacher-create-exam').disabled, true);
});

test('progress counts only this exam items and maps correction states without duplicate student cards', async () => {
  const states = ['SUBMITTED', 'TRANSCRIPTION_REVIEW', 'ANALYSIS_AVAILABLE', 'DECISION_DRAFT', 'DECISION_FINALIZED', 'RESULT_RELEASED'];
  const students = states.map((state, i) => ({ user_id: `student-${i}`, display_name: `Aluno ${i}`,
    submissions: { [itemId]: submissionId, [item2]: submissionId + i, unrelated: 'other-exam-submission' },
    correction_statuses: { [itemId]: state, [item2]: state } }));
  const ui = await page({ transport: url => url.endsWith('/progress') ? ok(progressData(exam, students)) : null });
  await ui.select(0);
  const rows = ui.nodesInDetail().find(n => n.tag === 'tbody').children;
  assert.equal(rows.length, 6);
  for (const [index, label] of ['Enviada', 'Em correção', 'Em correção', 'Em correção', 'Corrigida', 'Corrigida'].entries()) {
    assert.equal(rows[index].textContent, `Aluno ${index}${label}${label}2/2`);
  }
});

test('denied or mismatched progress never shows previous student deliveries', async () => {
  for (const response of [{ ok: false, status: 403 }, ok(progressData(exam))]) {
    const ui = await page({ transport: url => url.includes(id2) ? response : null });
    await ui.select(0); await ui.select(1);
    assert.match(ui.get('teacher-exam-progress').textContent, /Avaliação 2.*Não foi possível carregar as entregas/);
    assert(!ui.get('teacher-exam-progress').textContent.includes('Aluno Demo'));
    assert(!ui.nodesInDetail().some(n => n.tag === 'table'));
  }
});

test('draft shows local summary without requesting progress; blocked navigation does not open a Submission', async () => {
  const draft = { ...exam, assessment: { ...exam.assessment, status: 'DRAFT' }, availability: 'RASCUNHO' };
  const ui = await page({ exams: [draft] });
  await ui.select(0);
  assert.match(ui.get('teacher-exam-progress').textContent, /Publique o exame/);
  assert(!ui.calls.some(url => url.endsWith('/progress')));
  const guarded = await page({ navigate: false });
  await guarded.select(0);
  await guarded.nodesInDetail().find(n => n.tag === 'button').click();
  assert.equal(guarded.opened.length, 0);
});

test('selection brings an offscreen exam header into view instead of scrolling to the deliveries bottom', async () => {
  const ui = await page();
  await ui.select(0);
  const card = ui.cards()[1], scrolled = [];
  let bounds = { top: -250, bottom: -220 };
  descendants(card).find(n => n.tag === 'button').getBoundingClientRect = () => bounds;
  card.scrollIntoView = options => { scrolled.push(options); bounds = { top: 16, bottom: 46 }; };
  await ui.select(1);
  assert.equal(scrolled.length, 1);
  assert.equal(scrolled[0].block, 'start');
});
