const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { flush } = require('./capture-dom.cjs');
const { pilot, walk, text } = require('./tme-dom.cjs');
const fixture = require('../fixtures/rich_audit_response.json');
const run = () => ({ audit_run_id: 'aud_' + 'e'.repeat(64), status: 'COMPLETED', stale: false, acceptance_id: 'acc_auto', result: structuredClone(fixture) });
const getButton = (ui, label) => walk(ui.root).find(n => n.tag === 'button' && n.textContent === label);
const visibleText = n => n.hidden || n.tag === 'pre' || n.tag === 'details' && !n.open ? '' : [n.textContent, ...n.children.map(visibleText)].join(' ');

test('automatic transcription can be analyzed without a review gate; exact revision receipt is retained', async () => {
  const ui = await pilot({ auditRun: run(), pendingAudit: true }); await ui.click('Abrir');
  assert.ok(!getButton(ui, 'Analisar com ConfIA').disabled);
  assert.doesNotMatch(visibleText(ui.root), /Conferir transcrição|mixed|acceptance_id/);
  await ui.click('Analisar com ConfIA');
  const writes = ui.calls.filter(c => c.options.method === 'POST');
  assert.ok(writes[0].url.endsWith('/accept')); assert.ok(writes[1].url.endsWith('/audits'));
  const binding = JSON.parse(writes[0].options.body), audit = JSON.parse(writes[1].options.body);
  assert.equal(binding.reviewer_identity_verified, false);
  assert.match(binding.acceptance_note, /automática.*sem conferência humana/);
  assert.equal(audit.revision_number, binding.revision_number); assert.equal(audit.acceptance_id, 'accept_auto');
  assert.equal(walk(ui.root).filter(n => n.className === 'audit-criterion').length, 4);
  assert.match(text(ui.root), /Sugestão ConfIA/);
});

test('tabs, comparison, zoom, analysis disclosure and decision draft preserve DOM and avoid refetching', async () => {
  const ui = await pilot({ auditRun: run() }); await ui.click('Abrir');
  const controls = walk(ui.root).filter(n => n.tag === 'input'); controls.find(n => n.name === 'final').value = '8'; controls.find(n => n.name === 'final').handlers.input();
  const manuscript = walk(ui.root).find(n => n.tag === 'img'), count = ui.calls.length;
  await ui.click('Zoom +'); await ui.click('Rotacionar'); await ui.click('Transcrição'); await ui.click('Comparar'); await ui.click('Original');
  await ui.click('Recolher análise'); await ui.click('Expandir análise');
  assert.equal(ui.calls.length, count); assert.equal(walk(ui.root).find(n => n.tag === 'img'), manuscript);
  assert.match(manuscript.style.transform, /1.25.*90deg/); assert.equal(controls.find(n => n.name === 'final').value, '8');
  await ui.nav[0].click(); await flush(); await ui.click('Abrir');
  assert.equal(walk(ui.root).find(n => n.name === 'final').value, '8');
  assert.match(walk(ui.root).find(n => n.tag === 'img').style.transform, /1.25.*90deg/);
});

test('optional editing publishes a new revision and preserves unsaved decision', async () => {
  const ui = await pilot({ automatic: true }); await ui.click('Abrir');
  const final = walk(ui.root).find(n => n.name === 'final'); final.value = '6'; final.handlers.input();
  await ui.click('Editar');
  const editor = walk(ui.root).find(n => n.className === 'transcription-editor');
  const area = walk(editor).find(n => n.tag === 'textarea'); area.value = 'x = -2'; area.handlers.input();
  await ui.click('Salvar nova revisão');
  const write = ui.calls.find(c => c.url.endsWith('/revisions')); assert.ok(write);
  const body = JSON.parse(write.options.body); assert.equal(body.based_on_revision_number, 1); assert.equal(body.segments[0].text, 'x = -2');
  assert.equal(walk(ui.root).find(n => n.name === 'final').value, '6');
  assert.equal(ui.calls.filter(c => c.url.endsWith('/accept')).length, 0);
  assert.match(text(ui.root), /Nova revisão salva/);
});

test('queue filters, context, progress and null score remain explicit', async () => {
  const ui = await pilot({ auditRun: run() });
  assert.match(text(ui.root), /Código.*Questão.*Origem.*Status.*Sugestão.*Atualização/);
  const search = walk(ui.root).find(n => n.type === 'search'); search.value = 'absent'; search.handlers.input(); assert.match(text(ui.root), /0 correções/);
  search.value = 'PROVA'; search.handlers.input(); await ui.click('Abrir');
  assert.match(text(ui.root), /Prova PROVA-1 · Questão 1 · Foto \/ scan/);
  const steps = walk(ui.root).find(n => n.className === 'steps');
  assert.deepEqual(steps.children.map(n => n.textContent), ['Entrada', 'Transcrição', 'Análise', 'Decisão']);
  assert.equal(steps.children[2].attributes['aria-current'], 'step');
  assert.match(text(ui.root), /Sugestão ConfIA.*Não determinada/);
  assert.match(text(ui.root), /Verificação formal não concluída/);
  const claims = walk(ui.root).find(n => n.className === 'solution-map'); assert.ok(claims);
});

test('shell isolates correction navigation and supports keyboard, collapse and responsive stacking', async () => {
  const ui = await pilot(); await ui.shell['sidebar-toggle'].click(); assert.equal(ui.shell['sidebar-toggle'].attributes['aria-expanded'], 'false');
  const html = fs.readFileSync('app/confia_lean_auditor/static/tme/index.html', 'utf8');
  assert.match(html, /aria-controls="workspace-nav recent-cases"/); assert.match(html, /Ir para conteúdo/);
  assert.doesNotMatch(html, /TutorIA|Gestão|Exames escolares/);
  const css = fs.readFileSync('app/confia_lean_auditor/static/tme/tme.css', 'utf8');
  assert.match(css, /--solution-share, 60%/);
  assert.match(css, /@media \(max-width: 767px\)/); assert.match(css, /\.solution-views.compare \{ grid-template-columns: 1fr; \}/);
});

test('splitter supports pointer capture, keyboard bounds, reset and persisted width', async () => {
  const key = 'confia.correction.split-percent.v1';
  const ui = await pilot({ auditRun: run(), initialStorage: [[key, '64']] }); await ui.click('Abrir');
  let handle = walk(ui.root).find(n => n.className === 'pane-splitter');
  const layout = walk(ui.root).find(n => n.className === 'correction-workspace');
  assert.equal(handle.attributes.role, 'separator'); assert.equal(handle.attributes['aria-valuenow'], '64');
  assert.equal(layout.style['--solution-share'], '64%');
  const keydown = key => handle.handlers.keydown({ key, preventDefault() {} });
  keydown('ArrowLeft'); assert.equal(ui.storage.get(key), '62');
  keydown('Home'); keydown('ArrowLeft'); assert.equal(ui.storage.get(key), '40');
  keydown('End'); keydown('ArrowRight'); assert.equal(ui.storage.get(key), '75');
  handle.handlers.pointerdown({ button: 0, pointerId: 1, preventDefault() {} });
  handle.handlers.pointermove({ clientX: 570 });
  assert.equal(handle.attributes['aria-valuenow'], '57'); assert.equal(ui.storage.get(key), '75');
  handle.handlers.pointerup(); assert.equal(Math.round(Number(ui.storage.get(key))), 57);
  await ui.nav[0].click(); await flush(); await ui.click('Abrir');
  handle = walk(ui.root).find(n => n.className === 'pane-splitter');
  assert.equal(handle.attributes['aria-valuenow'], '57');
  handle.handlers.dblclick(); assert.equal(ui.storage.get(key), '60');
});

test('semantic tabs use roving focus and preserve page, zoom and decision fields', async () => {
  const ui = await pilot({ auditRun: run(), pageCount: 2 }); await ui.click('Abrir');
  const tabs = walk(ui.root).filter(n => n.attributes.role === 'tab');
  assert.equal(tabs.length, 3); assert.equal(tabs[0].tabIndex, 0);
  await ui.click('Próxima'); await ui.click('Zoom +');
  tabs[0].handlers.keydown({ key: 'End', preventDefault() {} });
  assert.equal(tabs[2].attributes['aria-selected'], 'true'); assert.equal(tabs[2].focused, true);
  assert.equal(tabs[0].tabIndex, -1); assert.equal(tabs[2].tabIndex, 0);
  const count = ui.calls.length;
  tabs[2].handlers.keydown({ key: 'ArrowRight', preventDefault() {} });
  assert.equal(tabs[0].attributes['aria-selected'], 'true'); assert.equal(ui.calls.length, count);
  await ui.nav[0].click(); await flush(); await ui.click('Abrir');
  assert.match(text(ui.root), /125% · Página 2\/2/);
});

test('criteria, coverage and selected evidence retain server meaning and expansion state', async () => {
  const auditRun = run(), original = JSON.stringify(auditRun);
  const ui = await pilot({ auditRun }); await ui.click('Abrir');
  const criteria = walk(ui.root).filter(n => n.className === 'audit-criterion');
  assert.equal(criteria.length, 4); assert.equal(criteria[2].open, false);
  criteria[2].open = true; criteria[2].handlers.toggle();
  assert.match(text(criteria[2]), /Indeterminado.*Verificação formal não concluída/);
  const coverage = walk(ui.root).find(n => n.className === 'coverage');
  assert.match(text(coverage), /3\/4 critérios decididos.*1 claim formalmente verificado.*1 indeterminado/);
  const map = walk(ui.root).filter(n => n.className === 'audit-claim');
  await map[2].click();
  assert.equal(map[2].attributes['aria-pressed'], 'true'); assert.equal(map[0].attributes['aria-pressed'], 'false');
  assert.equal(map[2].dataset.formalStatus, 'technical_error');
  assert.match(map[2].attributes['aria-label'], /z = 4/);
  const detail = walk(ui.root).find(n => n.className === 'claim-detail');
  assert.match(text(detail), /z = 4.*Verificação formal não concluída.*Sem vínculo preciso/);
  assert.equal(walk(ui.root).filter(n => n.tag === 'mark').length, 0);
  const summary = walk(ui.root).find(n => n.className === 'formal-checks-section');
  assert.match(text(summary), /1 claim verificado formalmente.*1 não formalizado.*1 falha técnica/);
  await ui.nav[0].click(); await flush(); await ui.click('Abrir');
  assert.equal(walk(ui.root).find(n => n.dataset.criterionId === 'pending').open, true);
  assert.equal(walk(ui.root).find(n => n.dataset.claimId === 'claim_2').attributes['aria-pressed'], 'true');
  assert.equal(JSON.stringify(auditRun), original);
});

test('evidence selection exposes a null mapping hook without inventing offsets', async () => {
  const ui = await pilot({ auditRun: run() }); await ui.click('Abrir');
  const {data, target} = ui.reports[0], selected = [];
  ui.window.ConfiaWorkspaceReport.render(data, target, {onEvidenceSelection: event => selected.push(event)});
  await walk(target).filter(n => n.className === 'audit-claim')[1].click();
  assert.equal(selected.at(-1).claimId, 'claim_1'); assert.equal(selected.at(-1).mapping, null);
});

test('suggestion action distinguishes a valid zero from an undetermined score', async () => {
  const auditRun = run(); auditRun.result.score = 0;
  const ui = await pilot({ auditRun }); await ui.click('Abrir');
  assert.equal(getButton(ui, 'Usar sugestão').disabled, false); await ui.click('Usar sugestão');
  assert.equal(walk(ui.root).find(n => n.name === 'final').value, '0');
  assert.equal(ui.calls.filter(c => c.options.method === 'POST').length, 0);
  const pending = await pilot({ auditRun: run() }); await pending.click('Abrir');
  assert.equal(getButton(pending, 'Usar sugestão').disabled, true);
  assert.equal(walk(pending.root).find(n => n.name === 'final').value, '');
  assert.equal(walk(pending.root).find(n => n.className === 'decision-observation').open, false);
});

test('queue filters and sidebar preference survive navigation independently of results filters', async () => {
  const ui = await pilot({ auditRun: run(), initialStorage: [['confia.correction.sidebar-collapsed', 'true']] });
  assert.equal(ui.shell['sidebar-toggle'].attributes['aria-expanded'], 'false');
  const search = walk(ui.root).find(n => n.type === 'search'); search.value = 'PROVA'; search.handlers.input();
  const selects = walk(ui.root).filter(n => n.tag === 'select');
  selects[0].value = 'ITA2025F2Q1'; selects[0].handlers.change();
  selects[2].value = 'Foto / scan'; selects[2].handlers.change();
  await ui.click('Abrir'); await ui.nav[2].click(); await flush();
  assert.equal(walk(ui.root).find(n => n.type === 'search').value, '');
  await ui.nav[0].click(); await flush();
  assert.equal(walk(ui.root).find(n => n.type === 'search').value, 'PROVA');
  assert.deepEqual(walk(ui.root).filter(n => n.tag === 'select').map(n => n.value), ['ITA2025F2Q1', '', 'Foto / scan']);
  await ui.shell['sidebar-toggle'].click(); assert.equal(ui.storage.get('confia.correction.sidebar-collapsed'), 'false');
  assert.ok(walk(ui.shell['recent-cases']).some(n => n.attributes['aria-label']?.includes('PROVA-1')));
});

test('analysis drawer opens, retains decision draft and closes with Escape restoring focus', async () => {
  const ui = await pilot({ auditRun: run() }); await ui.click('Abrir');
  const pane = walk(ui.root).find(n => n.id === 'analysis-pane');
  const final = walk(ui.root).find(n => n.name === 'final'); final.value = '7'; final.handlers.input();
  await ui.click('Abrir análise'); assert.equal(pane.dataset.open, 'true');
  assert.equal(getButton(ui, 'Fechar análise').focused, true);
  pane.handlers.keydown({ key: 'Escape' });
  assert.equal(pane.dataset.open, 'false'); assert.equal(getButton(ui, 'Abrir análise').focused, true);
  assert.equal(final.value, '7');
  const css = fs.readFileSync('app/confia_lean_auditor/static/tme/tme.css', 'utf8');
  assert.match(css, /min-width: 768px.*max-width: 1199px/);
  assert.match(css, /\.analysis-column\[data-open="true"\]/);
  assert.match(css, /\.decision-bar \{[^}]*position: sticky; bottom: 0;/);
});
