const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { page: workspacePage } = require('./workspace-dom.cjs');
const { page: capturePage, flush } = require('./capture-dom.cjs');
const { deferred } = require('./ui-dom.cjs');
const Model = require('../../app/confia_lean_auditor/static/capture/ink-model.js');

const staticDir = path.join(__dirname, '../../app/confia_lean_auditor/static');
const html = fs.readFileSync(path.join(staticDir, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(staticDir, 'styles.css'), 'utf8');
const exam = { assessment:{ assessment_id:'asmt_' + 'a'.repeat(32), title:'Prova A',
  opens_at:'2026-10-16T12:00:00Z', closes_at:'2026-10-23T12:00:00Z', instructions:'Resolva.' },
  items:[{ assessment_item_id:'ait_' + 'b'.repeat(32), problem_id:'B', order:1, points:5 }],
  teacher_name:'Professor Demo', classroom_name:'2ª série A', availability:'DISPONÍVEL', submitted_item_ids:[] };

const examTwoItems = { ...exam, items: [
  { assessment_item_id:'ait_' + '1'.repeat(32), problem_id:'A', order:1, points:5 },
  { assessment_item_id:'ait_' + '2'.repeat(32), problem_id:'B', order:2, points:5 },
] };

test('student home and primary navigation separate TutorIA, Exames and submissions', async () => {
  const ui = await workspacePage();
  ui.visit('home');
  const studentLinks = [...html.matchAll(/<a href="(#student\/[^\"]+)" data-shell-link[^>]*>([^<]+)/g)].map(match => [match[1], match[2]]);
  assert(studentLinks.some(([href, label]) => href === '#student/tutoria' && label === 'TutorIA'));
  assert(studentLinks.some(([href, label]) => href === '#student/exams' && label === 'Exames'));
  assert(studentLinks.some(([href, label]) => href === '#student/submissions' && label === 'Minhas submissões'));
  assert(!studentLinks.some(([href]) => href === '#student/resolve'));
  assert.match(html, /Entrar no TutorIA/);
  assert.match(html, /Ver exames/);
  assert(ui.get('#student-home').hidden === false);
});

test('TutorIA uses practice notebook and transient preview without an institutional submission', async () => {
  const calls = [];
  const ui = await workspacePage(async (url, options) => {
    calls.push({ url, options });
    return { ok:true, json: async () => ({ problem_id:'A', pedagogical_report:{ summary:'Feedback de estudo' } }) };
  });
  ui.visit('tutoria/practice');
  await ui.get('#resolve-question').click();
  ui.notebook({ controls:{ document_id:'draft:A', can_tutor_preview:true, tutor_preview_segments:[{ page_index:0, kind:'math', text:'x = 2', latex:'x=2' }] } });
  assert.equal(ui.window.ConfIAWorkspace.experience, 'TUTOR');
  assert.equal(ui.window.ConfIAWorkspace.mode, 'practice');
  await ui.get('#submission-mode').click();
  assert.equal(ui.window.ConfIAWorkspace.mode, 'practice');
  assert.equal(ui.get('#workspace-submission-actions').hidden, true);
  assert.equal(ui.get('#workspace-tutor-actions').hidden, false);
  assert.equal(ui.get('#notebook-problem-context').hidden, false);
  assert.equal(ui.get('#workspace-ink-toolbar').hidden, false);
  await ui.get('#workspace-tutor-preview').click();
  assert.equal(ui.commands.at(-1).message.action, 'tutor-preview');
  await ui.get('#workspace-tutor-feedback').click(); await flush();
  assert.equal(ui.get('#solution-input').value, 'x = 2');
  assert(!calls.some(call => call.url === '/audit'));
  assert.match(ui.get('#result-panel').textContent, /Feedback demonstrativo/);
  assert(!calls.some(call => call.url === '/submissions'));
  assert.match(css, /body\[data-resolution-active="true"\] #notebook-problem-context\s*\{\s*position: sticky/);
  assert.match(css, /\.workspace-ink-toolbar\s*\{\s*position: sticky/);
});

test('Exames starts empty and opens only an explicitly available activity in the same notebook', async () => {
  const empty = await workspacePage(); empty.visit('exams'); await flush();
  assert.equal(empty.get('#student-exam-list').children.length, 0);
  assert.equal(empty.get('#student-workspace').hidden, true);
  await empty.get('#submission-mode').click();
  assert.equal(empty.window.ConfIAWorkspace.mode, null);
  const ui = await workspacePage(undefined, { exams:[exam] });
  ui.visit('tutoria/practice'); await ui.get('#resolve-question').click(); ui.notebook();
  const frame = ui.frame;
  ui.visit('exams'); await flush();
  assert.equal(ui.get('#student-exam-list').children.length, 2);
  await ui.get('#student-exam-list').children[1].children.find(child => child.tag === 'button').click();
  assert.equal(ui.get('#student-exam-detail').hidden, false);
  assert.match(ui.get('#student-exam-items').textContent, /Questão 1 · B5 pontosNão enviada/);
  await ui.get('#student-exam-items').children[0].children.find(child => child.tag === 'button').click();
  assert.equal(ui.get('#problem-select').value, 'B');
  assert.equal(ui.get('#problem-select').children.find(option => option.value === 'A').disabled, true);
  assert.equal(ui.get('#student-exams').hidden, true);
  assert.equal(ui.get('#student-workspace').hidden, false);
  await ui.get('#resolve-question').click(); ui.notebook({ controls:{ document_id:'draft:B' } });
  assert.equal(ui.window.ConfIAWorkspace.experience, 'EXAM');
  assert.equal(ui.window.ConfIAWorkspace.mode, 'submission');
  assert.equal(ui.frame, frame);
  assert.equal(ui.get('#workspace-submission-actions').hidden, false);
  assert.equal(ui.get('#workspace-tutor-actions').hidden, true);
  assert.equal(ui.get('#notebook-problem-context').hidden, false);
  assert.equal(ui.get('#workspace-ink-toolbar').hidden, false);
  assert.equal(ui.commands.at(-1).message.submission_target,
    `/assessments/${exam.assessment.assessment_id}/items/${exam.items[0].assessment_item_id}/submissions`);
});

test('student exam progress refreshes from the server after receipt and survives new page and session', async () => {
  const serverExams = [{ ...examTwoItems, submitted_item_ids: [] }];
  const examId = examTwoItems.assessment.assessment_id;
  const firstItem = examTwoItems.items[0], secondItem = examTwoItems.items[1];
  const ui = await workspacePage(undefined, { exams: serverExams });
  ui.visit('exams'); await flush();
  assert.match(ui.get('#student-exam-list').textContent, /2 questões · 0\/2 enviadas.*Não iniciada/);
  await ui.get('#student-exam-list').children[1].children.find(child => child.tag === 'button').click();
  assert.equal(ui.get('#student-exam-progress').textContent, 'Progresso: 0/2 · Não iniciada');
  assert.match(ui.get('#student-exam-items').textContent, /Questão 1 · A5 pontosNão enviada.*Questão 2 · B5 pontosNão enviada/);
  await ui.get('#student-exam-items').children[0].children.find(child => child.tag === 'button').click();
  await ui.get('#resolve-question').click();
  const target = `/assessments/${examId}/items/${firstItem.assessment_item_id}/submissions`;
  assert.match(ui.frame.src, new RegExp(`submission_target=${encodeURIComponent(target)}`));
  ui.notebook({ submission_target: '/submissions' });
  assert.equal(ui.commands.at(-1).message.submission_target, target);

  serverExams[0] = { ...examTwoItems, submitted_item_ids: [firstItem.assessment_item_id] };
  const receipt = { submission_id:'sub_' + '1'.repeat(32), assessment_id:examId,
    assessment_item_id:firstItem.assessment_item_id, snapshot_id:'snapshot:A', problem_id:'A' };
  ui.notebook({ local_snapshot_id:'snapshot:A', receipt, submission_target:target });
  await flush();
  assert.equal(ui.get('#student-exam-progress').textContent, 'Progresso: 1/2 · Em andamento');
  assert.match(ui.get('#student-exam-items').textContent, /Questão 1 · A5 pontosEnviada.*Questão 2 · B5 pontosNão enviada/);
  assert.match(ui.get('#student-exam-list').textContent, /2 questões · 1\/2 enviadas.*Em andamento/);
  ui.notebook({ local_snapshot_id:'snapshot:A', receipt, submission_target:target });
  await flush();
  assert.equal(ui.get('#student-exam-progress').textContent, 'Progresso: 1/2 · Em andamento');

  const reloaded = await workspacePage(undefined, { exams: serverExams });
  reloaded.visit('exams'); await flush();
  assert.match(reloaded.get('#student-exam-list').textContent, /2 questões · 1\/2 enviadas.*Em andamento/);
  const relogged = await workspacePage(undefined, { exams: serverExams });
  relogged.visit('exams'); await flush();
  assert.match(relogged.get('#student-exam-list').textContent, /2 questões · 1\/2 enviadas.*Em andamento/);
  await relogged.get('#student-exam-list').children[1].children.find(child => child.tag === 'button').click();
  await relogged.get('#student-exam-items').children[1].children.find(child => child.tag === 'button').click();
  await relogged.get('#resolve-question').click();
  serverExams[0] = { ...examTwoItems, submitted_item_ids: [firstItem.assessment_item_id, secondItem.assessment_item_id] };
  relogged.notebook({ local_snapshot_id:'snapshot:B', receipt: { ...receipt,
    submission_id:'sub_' + '2'.repeat(32), assessment_item_id:secondItem.assessment_item_id,
    snapshot_id:'snapshot:B', problem_id:'B' },
    submission_target:`/assessments/${examId}/items/${secondItem.assessment_item_id}/submissions` });
  await flush();
  assert.equal(relogged.get('#student-exam-progress').textContent, 'Progresso: 2/2 · Concluída');
  assert.match(relogged.get('#student-exam-list').textContent, /2 questões · 2\/2 enviadas.*Concluída/);
});

test('embedded exam starts with its bound submission target before any configure message', async () => {
  const target = `/assessments/${exam.assessment.assessment_id}/items/${exam.items[0].assessment_item_id}/submissions`;
  let sentTo = null;
  const catalog = deferred();
  const ui = await capturePage({ embedded:true, autoSave:true,
    search:`?embedded=1&problem_id=ITA2025Q1&mode=submission&submission_target=${encodeURIComponent(target)}`,
    catalogResponse:catalog.promise,
    sender:{ send:async (_snapshot, destination) => { sentTo = destination; throw new Error('Interromper antes do transporte'); } },
  });
  await ui.command({ problem_id:'ITA2025Q1', mode:'submission', submission_target:'/submissions' });
  catalog.resolve({ ok:true, json:async () => [{ problem_id:'ITA2025Q1', title:'Questão', statement:'Enunciado' }] });
  await flush(); await flush();
  assert.equal(ui.messages.at(-1).context.submission_target, target);
  await ui.click('prepare-snapshot');
  await ui.click('send-solution');
  assert.equal(sentTo, target);
});

test('an exam remains available when its manifest loads before the problem catalog', async () => {
  const pending = deferred();
  const ui = await workspacePage(undefined, { catalogResponse:pending.promise,
    exams:[exam] });
  ui.visit('exams'); await flush();
  assert.match(ui.get('#student-exams-message').textContent, /Carregando catálogo/);
  pending.resolve({ ok:true, json:async () => [{ problem_id:'B', title:'B', statement:'Enunciado B', examples:[] }] });
  await flush(); await flush();
  assert.equal(ui.get('#student-exam-list').children.length, 2);
});

test('TutorIA preview freezes only in memory and never invokes submission or official recognition', async () => {
  const draft = Model.createDraft('ITA2025Q1');
  const written = Model.addStroke(draft, { page_id:draft.pages[0].page_id, pointer_type:'pen',
    points:[{ x:10, y:20, t_ms:0, pressure_reported:0.5 }] });
  const calls = []; let sends = 0;
  const ui = await capturePage({ embedded:true, autoSave:true, initialDocument:written,
    search:`?embedded=1&problem_id=ITA2025Q1&mode=practice&draft_id=${written.draft_id}`,
    sender:{ send() { sends++; } },
    fetch:async (url, init) => {
      calls.push({ url, init });
      const body = JSON.parse(init.body), snapshot = JSON.parse(body.snapshot_json);
      return { ok:true, json:async () => ({ client_preview_id:body.client_preview_id,
        problem_id:snapshot.problem_id, snapshot_id:snapshot.local_snapshot_id,
        snapshot_sha256:createHash('sha256').update(body.snapshot_json).digest('hex'),
        page_count:snapshot.pages.length, active_stroke_count:snapshot.active_stroke_ids.length,
        result:{ segments:[{ page_index:0, order:0, kind:'math', text:'x = 2', latex:'x=2' }] } }) };
    },
  });
  const controls = ui.messages.at(-1).context.controls;
  assert.equal(controls.can_tutor_preview, true);
  await ui.command({ action:'tutor-preview', problem_id:'ITA2025Q1', mode:'practice', document_id:controls.document_id });
  await flush();
  assert.deepEqual(calls.map(call => call.url), ['/submissions/recognition-preview']);
  assert.equal(sends, 0);
  assert.equal(ui.messages.at(-1).context.controls.tutor_preview_segments[0].latex, 'x=2');
  assert.equal(ui.saves.some(save => save.document.document_kind === 'local_snapshot'), false);
});

test('Minhas submissões reads official records and ignores TutorIA attempts', async () => {
  const receipt = { submission_id:'sub_exam', snapshot_id:'snapshot:B', problem_id:'B', received_at:'2026-10-16T12:00:00Z' };
  const ui = await workspacePage(async url => ({ ok:true, json:async () => url === '/submissions' ? [receipt] : {} }));
  ui.visit('tutoria/practice'); await ui.get('#resolve-question').click();
  ui.notebook({ local_snapshot_id:'snapshot:A', receipt:{ ...receipt, snapshot_id:'snapshot:A', problem_id:'A', submission_id:'sub_tutor' } });
  assert.doesNotMatch(ui.get('#student-receipt-list').textContent, /sub_tutor/);
  ui.document.body.classList = { contains: value => value === 'auth-enabled' };
  ui.window.ConfIAAuthProfile = 'student';
  ui.visit('submissions'); await flush();
  assert.match(ui.get('#student-receipt-list').textContent, /sub_exam/);
  assert.doesNotMatch(ui.get('#student-receipt-list').textContent, /sub_tutor/);
  assert(ui.calls.some(call => call.url === '/submissions'));
});
