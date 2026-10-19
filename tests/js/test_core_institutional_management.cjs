const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants, flush } = require('./ui-dom.cjs');

const script = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/management.js'), 'utf8');
const base = { number_of_schools: 2, number_of_classrooms: 3, number_of_students: 3, number_of_teachers: 2,
  submissions_count: 1, transcriptions_count: 1, recognition_success_count: 1, recognition_failure_count: 0,
  audit_runs_count: 0, completed_audits: 0, inconclusive_audits: 0,
  decisions_finalized_count: 1, decisions_released_count: 0, override_count: 1 };
const schoolA = { school_id: 'school-a', name: 'Escola A', municipality: 'Teresina' };
const schoolB = { school_id: 'school-b', name: 'Escola B', municipality: 'Parnaíba' };
const classroom = { classroom_id: 'class-a', school_id: 'school-a', name: '2ª série A' };
const overview = (scope, extra = {}, metrics = base) => ({ scope, academic_year: 2026, metrics, ...extra });

function page(role) {
  const ids = ['management-heading', 'management-message', 'management-cards', 'management-breadcrumb', 'management-table'];
  const nodes = Object.fromEntries(ids.map(id => [id, element('div')]));
  const calls = [];
  const data = {
    '/management/network/overview': overview('network'),
    '/management/schools': [{ school: schoolA, metrics: { ...base, number_of_schools: 1 } },
      { school: schoolB, metrics: { ...base, number_of_schools: 1, submissions_count: 0 } }],
    '/management/schools/school-a/overview': overview('school', { school: schoolA }, { ...base, number_of_schools: 1 }),
    '/management/schools/school-a/classrooms': [{ classroom, metrics: { ...base, number_of_schools: 1, number_of_classrooms: 1 } }],
    '/management/classrooms/class-a/overview': overview('classroom', { school: schoolA, classroom },
      { ...base, number_of_schools: 1, number_of_classrooms: 1 }),
  };
  const window = { ConfIAAuthUser: { role } };
  vm.runInNewContext(script, { window, document: {
    querySelector: selector => nodes[selector.slice(1)], createElement: element,
  }, fetch: async url => { calls.push(url); return { ok: Object.hasOwn(data, url), json: async () => data[url] }; } });
  return { nodes, calls, load: () => window.ConfIAManagement.load() };
}

test('network management drills down through real aggregate endpoints only', async () => {
  const ui = page('NETWORK_MANAGER');
  await ui.load();
  assert.equal(ui.nodes['management-heading'].textContent, 'Visão geral da rede');
  assert.equal(ui.nodes['management-cards'].children.length, 14);
  assert.match(ui.nodes['management-cards'].textContent, /Decisões finalizadas.*Resultados liberados.*Decisões com alteração da sugestão/);
  assert.match(ui.nodes['management-table'].textContent, /Escola A/);
  assert.match(ui.nodes['management-table'].textContent, /Escola B/);
  assert(ui.calls.every(url => url.startsWith('/management/')));
  const schoolButton = descendants(ui.nodes['management-table']).find(n => n.tag === 'button' && n.textContent === 'Escola A');
  await schoolButton.click(); await flush();
  assert.equal(ui.nodes['management-heading'].textContent, 'Escola A');
  assert.match(ui.nodes['management-table'].textContent, /2ª série A/);
  const classButton = descendants(ui.nodes['management-table']).find(n => n.tag === 'button' && n.textContent === '2ª série A');
  await classButton.click(); await flush();
  assert.equal(ui.nodes['management-heading'].textContent, 'Escola A · 2ª série A');
  assert(ui.calls.includes('/management/classrooms/class-a/overview'));
  assert(!/snapshot|transcription_text|png_base64|solution_text/.test(ui.nodes['management-cards'].textContent));
});

test('school manager starts in own school and never loads network overview', async () => {
  const ui = page('SCHOOL_MANAGER'); await ui.load();
  assert.equal(ui.nodes['management-heading'].textContent, 'Escola A');
  assert(!ui.calls.includes('/management/network/overview'));
  assert(!ui.nodes['management-table'].textContent.includes('Escola B'));
});
