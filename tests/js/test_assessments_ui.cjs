const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants } = require('./ui-dom.cjs');

const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/assessments.js'), 'utf8');
const id = 'asmt_' + 'a'.repeat(32), itemId = 'ait_' + 'b'.repeat(32), submissionId = 'sub_' + 'c'.repeat(32);
const exam = { assessment: { assessment_id: id, title: 'Avaliação 1', status: 'PUBLISHED',
  opens_at: '2026-10-16T12:00:00Z', closes_at: '2026-10-23T12:00:00Z', instructions: 'Resolva.' },
  items: [{ assessment_item_id: itemId, problem_id: 'ITA2025F2Q1', order: 1, points: 5 }],
  classroom_name: '2ª série A', availability: 'DISPONÍVEL' };

test('teacher Exames loads scoped assessments and opens an existing Submission from progress', async () => {
  const nodes = new Map(), calls = [], opened = [], navigated = [];
  const get = key => {
    if (!nodes.has(key)) nodes.set(key, element('div'));
    return nodes.get(key);
  };
  get('teacher-exam-form').hidden = true;
  const context = { document: { getElementById: get, createElement: element }, Date, Number, console,
    setTimeout, window: { ConfIATeacher: { context: () => ({ schoolId: 'ceti-centro', classroomId: 'centro-2a-2026' }),
      openSubmission: sid => opened.push(sid) }, ConfIAShell: { navigate: (...args) => navigated.push(args) } },
    fetch: async url => {
      calls.push(url);
      if (url.startsWith('/assessments?')) return { ok: true, json: async () => [exam] };
      if (url.endsWith('/progress')) return { ok: true, json: async () => ({ items: exam.items,
        students: [{ user_id: 'student-1', display_name: 'Aluno Demo', submissions: { [itemId]: submissionId } }] }) };
      throw Error('unexpected URL ' + url);
    },
  };
  vm.runInNewContext(source, context);
  await context.window.ConfIAAssessments.load();
  assert.match(get('teacher-exam-list').textContent, /Publicados.*Avaliação 1.*2ª série A/);
  assert(calls[0].includes('school_id=ceti-centro&classroom_id=centro-2a-2026'));
  const openExam = descendants(get('teacher-exam-list')).find(node => node.tag === 'button' && node.textContent === 'Abrir exame');
  await openExam.click();
  assert.match(get('teacher-exam-progress').textContent, /Aluno Demo.*Enviado/);
  const sent = descendants(get('teacher-exam-progress')).find(node => node.tag === 'button' && node.textContent === 'Enviado');
  await sent.click();
  assert.deepEqual(navigated, [['teacher', 'submissions']]);
  assert.deepEqual(opened, [submissionId]);
});
