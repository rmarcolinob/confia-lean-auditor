const test = require('node:test');
const assert = require('node:assert/strict');
const { page, record, detailData, id, summary, history, transcriptionId, descendants, flush, deferred, element } = require('./teacher-dom.cjs');
const aid = 'asmt_' + 'b'.repeat(32), iid = 'ait_' + 'c'.repeat(32);
const bound = { ...record, assessment_id: aid, assessment_item_id: iid, submitted_by_user_id: 'student-a' };
const examContext = { submissionId: id, assessmentId: aid, assessmentTitle: 'Avaliação 1', assessmentItemId: iid,
  studentId: 'student-a', studentName: 'Aluno Demo', questionOrder: 2, problemId: record.problem_id };
const otherId = 'sub_' + 'e'.repeat(32);
const secondTranscription = 'tr_' + 'd'.repeat(32);
const ok = data => ({ ok: true, json: async () => data });
function transport(url) {
  if (url === '/submissions') return ok([bound, { ...record, submission_id: otherId }]);
  if (url === '/submissions/recognition-providers' || url.endsWith('/audits')) return ok([]);
  if (url.endsWith('/teacher-decision')) return ok(null);
  if (url.endsWith('/transcriptions')) return ok([summary, { ...summary, transcription: { ...summary.transcription, transcription_id: secondTranscription } }]);
  if (url.startsWith('/transcriptions/')) return ok({ ...history, transcription: { ...history.transcription, transcription_id: url.split('/')[2] } });
  if (url === `/submissions/${id}`) return ok({ ...detailData(), submission: bound });
  if (url === `/submissions/${otherId}`) return ok({ ...detailData(), submission: { ...record, submission_id: otherId } });
  throw Error('unexpected URL ' + url);
}
const contextPanel = ui => descendants(ui.get('#manuscript-detail')).find(n => n.className === 'submission-context');

test('existing teacher workflow keeps assessment, student and question through transcription reload', async () => {
  const ui = page(transport);
  await ui.window.ConfIATeacher.openSubmission(id, examContext);
  await flush();
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.equal(contextPanel(ui).textContent, 'AvaliaçãoAvaliação 1AlunoAluno DemoQuestãoQ2 · ITA2025Q1');
  assert.match(ui.get('#manuscript-detail').textContent, /Manuscrito original.*Transcrição.*Análise ConfIA.*Decisão do professor/s);
  const selector = descendants(ui.get('#manuscript-detail')).find(n => n.tag === 'select' && n.value === transcriptionId);
  selector.value = secondTranscription;
  await selector.emit('change');
  assert.match(contextPanel(ui).textContent, /Avaliação 1AlunoAluno DemoQuestãoQ2/);
  assert(ui.calls.some(call => call.url === `/transcriptions/${secondTranscription}`));
});

test('context is checked against the returned submission binding before exposing the workflow', async () => {
  for (const key of ['assessmentId', 'assessmentItemId', 'studentId', 'problemId']) {
    const ui = page(transport);
    await ui.window.ConfIATeacher.openSubmission(id, { ...examContext, [key]: 'different' });
    assert.equal(ui.get('#manuscript-detail').hidden, true);
    assert.equal(ui.get('#manuscript-detail').textContent, '');
    assert.equal(ui.get('#manuscript-queue').hidden, false);
  }
});

test('returning to general queue and opening another solution never retains exam context', async () => {
  const ui = page(url => url === `/submissions/${otherId}/transcriptions` ? ok([]) : transport(url));
  await ui.window.ConfIATeacher.openSubmission(id, examContext);
  await flush();
  await descendants(ui.get('#manuscript-detail')).find(n => n.tag === 'button' && n.textContent === 'Voltar à fila de soluções').click();
  assert.equal(ui.get('#manuscript-queue').hidden, false);
  await ui.window.ConfIATeacher.openSubmission(otherId);
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.equal(contextPanel(ui), undefined);
  assert(!ui.get('#manuscript-detail').textContent.includes('Aluno Demo'));
});

test('a superseded queue refresh cannot reopen an older selected solution', async () => {
  const first = deferred(); let lists = 0;
  const ui = page(url => url === '/submissions' && ++lists === 1 ? first.promise
    : url === `/submissions/${otherId}/transcriptions` ? ok([]) : transport(url));
  const older = ui.window.ConfIATeacher.openSubmission(id, examContext);
  await ui.window.ConfIATeacher.openSubmission(otherId);
  first.resolve(ok([bound])); await older;
  assert.equal(contextPanel(ui), undefined);
  assert(!ui.calls.some(call => call.url === `/submissions/${id}`));
});

test('general queue resolves school, class, assessment, student and question through authorized endpoints', async () => {
  const institutional = { ...bound, school_id: 'school-a', classroom_id: 'class-a' };
  const ui = page(url => {
    if (url === `/submissions/${id}`) return ok({ ...detailData(), submission: institutional });
    if (url === `/assessments/${aid}`) return ok({ assessment: { assessment_id: aid, title: 'Avaliação 1' },
      classroom_name: '2ª série A', items: [{ assessment_item_id: iid, problem_id: record.problem_id, order: 2 }] });
    if (url === '/institutional/classrooms/class-a/students') return ok([{ user_id: 'student-a', display_name: 'Aluno Demo' }]);
    return transport(url);
  });
  const school = element('option'); school.value = 'school-a'; school.textContent = 'CETI Centro';
  ui.get('#teacher-school-select').appendChild(school);
  await ui.window.ConfIATeacher.openSubmission(id);
  assert.equal(contextPanel(ui).textContent, 'EscolaCETI CentroTurma2ª série AAvaliaçãoAvaliação 1AlunoAluno DemoQuestãoQ2 · ITA2025Q1');
  assert.equal(contextPanel(ui).attributes['aria-label'], 'Contexto da correção');
  const selector = descendants(ui.get('#manuscript-detail')).find(n => n.tag === 'select' && n.value === transcriptionId);
  selector.value = secondTranscription; await selector.emit('change');
  assert.match(contextPanel(ui).textContent, /CETI Centro.*Aluno Demo.*Q2/);
  assert.equal(ui.calls.filter(call => call.url === `/assessments/${aid}`).length, 1);
});

test('unavailable context names do not leak data from mismatched or unauthorized responses', async () => {
  const ui = page(url => {
    if (url === `/submissions/${id}`) return ok({ ...detailData(), submission: { ...bound, school_id: 'school-a', classroom_id: 'class-a' } });
    if (url === `/assessments/${aid}`) return ok({ assessment: { assessment_id: 'other', title: 'PRIVATE_EXAM' }, classroom_name: 'PRIVATE_CLASS' });
    if (url === '/institutional/classrooms/class-a/students') return { ok: false, status: 403, json: async () => ({ detail: 'PRIVATE_STUDENT' }) };
    return transport(url);
  });
  await ui.window.ConfIATeacher.openSubmission(id);
  assert.match(contextPanel(ui).textContent, /Avaliação indisponível.*Aluno indisponível/);
  assert.doesNotMatch(contextPanel(ui).textContent, /PRIVATE_/);
});
