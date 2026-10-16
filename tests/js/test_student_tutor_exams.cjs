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
  ui.visit('tutoria');
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
  assert(calls.some(call => call.url === '/audit'));
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
  const ui = await workspacePage(undefined, { exams:[{ exam_id:'exam-a', title:'Prova A', problem_ids:['B'] }] });
  ui.visit('tutoria'); await ui.get('#resolve-question').click(); ui.notebook();
  const frame = ui.frame;
  ui.visit('exams'); await flush();
  assert.equal(ui.get('#student-exam-list').children.length, 1);
  await ui.get('#student-exam-list').children[0].children[2].click();
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
});

test('an exam remains available when its manifest loads before the problem catalog', async () => {
  const pending = deferred();
  const ui = await workspacePage(undefined, { catalogResponse:pending.promise,
    exams:[{ exam_id:'exam-a', title:'Prova A', problem_ids:['B'] }] });
  ui.visit('exams'); await flush();
  assert.match(ui.get('#student-exams-message').textContent, /Carregando catálogo/);
  pending.resolve({ ok:true, json:async () => [{ problem_id:'B', title:'B', statement:'Enunciado B', examples:[] }] });
  await flush(); await flush();
  assert.equal(ui.get('#student-exam-list').children.length, 1);
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
  ui.visit('tutoria'); await ui.get('#resolve-question').click();
  ui.notebook({ local_snapshot_id:'snapshot:A', receipt:{ ...receipt, snapshot_id:'snapshot:A', problem_id:'A', submission_id:'sub_tutor' } });
  assert.doesNotMatch(ui.get('#student-receipt-list').textContent, /sub_tutor/);
  ui.document.body.classList = { contains: value => value === 'auth-enabled' };
  ui.window.ConfIAAuthProfile = 'student';
  ui.visit('submissions'); await flush();
  assert.match(ui.get('#student-receipt-list').textContent, /sub_exam/);
  assert.doesNotMatch(ui.get('#student-receipt-list').textContent, /sub_tutor/);
  assert(ui.calls.some(call => call.url === '/submissions'));
});
