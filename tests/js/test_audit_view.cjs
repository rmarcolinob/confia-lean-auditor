const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants } = require('./ui-dom.cjs');
const Teacher = require('./teacher-dom.cjs');
const { pilot, walk, text } = require('./tme-dom.cjs');
const fixture = require('../fixtures/rich_audit_response.json');
const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/audit-view.js'), 'utf8');
const clone = value => JSON.parse(JSON.stringify(value));
function run() {
  return { audit_run_id: 'aud_' + 'e'.repeat(64), status: 'COMPLETED', stale: false,
    submission_id: Teacher.id, transcription_id: Teacher.transcriptionId, revision_number: 1,
    acceptance_id: 'acc_' + 'c'.repeat(32), created_at: Teacher.revision.created_at,
    source: { accepted_at: Teacher.revision.created_at, warnings: [{ page_index: 0, message: 'Diagrama preservado; não analisado pelo auditor textual.' }],
      provenance: { revision: { provider: 'mathpix_image' } } },
    result: clone(fixture), result_sha256: 'a'.repeat(64), required_artifacts: [{ file: 'claim_1.lean' }],
    reproducibility_status: 'legacy_unversioned' };
}
function render(value, context = 'evaluator') {
  const window = {}, panel = element('div');
  vm.runInNewContext(source, { window, document: { createElement: element } });
  window.ConfIAReport.render(value.result, panel, { context, auditRun: value });
  return panel;
}
const find = (panel, name) => descendants(panel).find(n => n.className === name);
for (const score of [0, 7, 10, null]) test(`score ${score} preserves the global suggestion and raw run`, () => {
  const audit = run(); audit.result.score = score; audit.result.verdict = score === null ? 'inconclusivo' : 'correto';
  const before = JSON.stringify(audit), panel = render(audit);
  assert.equal(find(panel, 'audit-score').textContent, `Pontuação sugerida: ${score === null ? 'Não determinada' : score + ' / 10'}`);
  assert.doesNotMatch(panel.textContent, /[Ii]nconclusiv[oa]\s*\/\s*10/);
  assert.equal(JSON.stringify(audit), before);
});

test('all criteria, evidence, claims and selective formal statuses remain visible with no score substitution', () => {
  const panel = render(run()), nodes = descendants(panel);
  const criteria = nodes.filter(n => n.className === 'audit-criterion');
  assert.equal(criteria.length, 4);
  for (const item of fixture.rubric_assessment.items) {
    const row = criteria.find(n => n.dataset.criterionId === item.id);
    assert.ok(row.textContent.includes(item.description)); assert.ok(row.textContent.includes(item.evidence));
    assert.equal(row.dataset.mathematicalStatus, item.mathematical_status);
  }
  const pending = criteria.find(n => n.dataset.criterionId === 'pending');
  assert.match(pending.textContent, /Indeterminado.*Máximo: 3/);
  assert.doesNotMatch(pending.textContent, /0\s*\/\s*3|Refutado/);
  assert.match(find(panel, 'audit-inconclusive').textContent, /1 de 4 critérios.*Critérios decididos: 3\/4.*Pontos decididos: 7\/10.*não são nota oficial/);
  const claims = nodes.filter(n => n.className === 'audit-claim');
  assert.equal(claims.length, 4);
  assert.equal(claims.find(n => n.dataset.claimId === 'claim_2').dataset.formalStatus, 'technical_error');
  assert.match(claims.find(n => n.dataset.claimId === 'claim_2').textContent, /Verificação formal não concluída/);
  assert.doesNotMatch(claims.find(n => n.dataset.claimId === 'claim_2').textContent, /Refutado/);
  assert.match(find(panel, 'formal-checks-section').textContent, /1 claim verificado.*1 passo formal verificado/);
  assert.match(find(panel, 'formal-checks-section').textContent, /não verifica toda a solução/);
  assert.match(panel.textContent, /Não submetido à verificação formal/);
  assert.match(find(panel, 'audit-summary').textContent, new RegExp(fixture.pedagogical_report.summary));
  assert.match(find(panel, 'audit-warnings').textContent, /Diagrama preservado/);
  const technical = nodes.find(n => n.tag === 'details' && n.children[0].textContent === 'Detalhes técnicos da análise');
  assert.ok(!technical.open); assert.ok(technical.textContent.includes('aud_' + 'e'.repeat(64)));
  assert.match(technical.textContent, /claim_1.lean.*provenance|provenance.*claim_1.lean/s);
});

test('proven refutation and a technical failure keep independent semantics', () => {
  const audit = run();
  audit.result.student_claim_checks[0] = { id: 'claim_1', status: 'refuted', refutation_verified: true, refutation_lean_file: 'refutation.lean' };
  const panel = render(audit), nodes = descendants(panel);
  assert.equal(nodes.find(n => n.className === 'audit-claim' && n.dataset.claimId === 'claim_1').dataset.formalStatus, 'refuted');
  assert.equal(nodes.find(n => n.className === 'audit-claim' && n.dataset.claimId === 'claim_2').dataset.formalStatus, 'technical_error');
});

test('missing pedagogical report still shows the full rubric and uses existing feedback', () => {
  const audit = run(); audit.result.pedagogical_report = null;
  const panel = render(audit);
  assert.match(find(panel, 'audit-summary').textContent, /Relatório explicativo existente/);
  assert.equal(descendants(panel).filter(n => n.className === 'audit-criterion').length, 4);
});

const semanticTree = node => ({ tag: node.tag, className: node.className || '', dataset: { ...node.dataset },
  text: node.children.length ? '' : node.textContent, children: node.children.map(semanticTree) });
for (const mode of ['IMAGE_SCAN', 'DIGITAL_INK']) test(`teacher and ${mode} pilot use the same complete run and semantic view; manual decision remains available`, async () => {
  const audit = run(), accepted = { ...Teacher.revision, status: 'ACCEPTED' };
  const base = Teacher.transportFor(true, true);
  const ok = data => ({ ok: true, json: async () => data });
  const teacher = Teacher.page(async url => {
    if (url.endsWith('/audits')) return ok([audit]);
    if (url.endsWith('/transcriptions')) return ok([{ ...Teacher.summary, latest_revision: accepted }]);
    if (url.startsWith('/transcriptions/')) return ok({ ...Teacher.history, revisions: [accepted], acceptances: [{
      acceptance_id: audit.acceptance_id, submission_id: Teacher.id, transcription_id: Teacher.transcriptionId,
      revision_number: 1, accepted_revision_sha256: 'd'.repeat(64), accepted_at: audit.created_at }] });
    return base(url);
  }, '', { realReport: true });
  await teacher.get('#refresh-manuscripts').click(); await teacher.get('#manuscript-list').children[0].click();
  const ui = await pilot({ auditRun: audit, mode });
  await ui.click('Abrir');
  assert.equal(teacher.reports.length, 1); assert.equal(ui.reports.length, 1);
  assert.equal(teacher.reports[0].options.auditRun, audit); assert.equal(ui.reports[0].options.auditRun, audit);
  assert.deepEqual(teacher.reports[0].data, ui.reports[0].data); // Same payload, workspace disclosures differ.
  const criteria = walk(ui.root).filter(n => n.className === 'audit-criterion');
  assert.equal(criteria.length, 4);
  assert.match(text(ui.root), /Sugestão ConfIA.*Não determinada/);
  const controls = walk(ui.root).filter(n => n.tag === 'input');
  assert.equal(controls.length, 2); controls.find(n => n.name === 'final').value = '8';
  await ui.click('Finalizar correção');
  const request = ui.calls.find(c => c.url.endsWith('/decision') && c.options.method === 'POST');
  assert.equal(JSON.parse(request.options.body).final_points, 8);
  assert.equal(JSON.parse(request.options.body).audit_run_id, audit.audit_run_id);
  assert.match(text(ui.root), /Pontuação final do avaliador: 8 \/ 10/);
  assert.equal(walk(ui.root).filter(n => n.className === 'audit-criterion').length, 4);
});
