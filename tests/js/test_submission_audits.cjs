const test = require('node:test');
const assert = require('node:assert/strict');
const { id, transcriptionId, record, revision, summary, history, page, transportFor, descendants, primaryText, deferred, flush } = require('./teacher-dom.cjs');
const ok = data => ({ ok: true, json: async () => data });
const acceptance = { submission_id: id, transcription_id: transcriptionId, revision_number: 1,
  acceptance_id: 'acc_' + 'c'.repeat(32), accepted_at: revision.created_at,
  accepted_revision_sha256: 'd'.repeat(64) };
const accepted = { ...revision, status: 'ACCEPTED' };
const run = { audit_run_id: 'aud_' + 'd'.repeat(64), submission_id: id, transcription_id: transcriptionId,
  revision_number: 1, acceptance_id: acceptance.acceptance_id, created_at: revision.created_at, status: 'COMPLETED', stale: false,
  source: { accepted_at: acceptance.accepted_at, solution_text: '2 + 2 = 5', warnings: [] },
  result: { pedagogical_report: { summary: 'Erro matemático identificado' } } };
const tree = ui => descendants(ui.get('#manuscript-detail'));
const button = (ui, label) => tree(ui).find(n => n.tag === 'button' && n.textContent === label);
const panel = ui => tree(ui).find(n => n.className === 'manuscript-analysis-panel');
async function open({ state = 'ACCEPTED', acceptances = [acceptance], intact = true, runs = [], post, readFailure = false } = {}) {
  const base = transportFor(intact, true);
  const ui = page(async (url, options = {}) => {
    if (options.method === 'POST' && url.endsWith('/audits')) return post ? post(url, options) : ok(run);
    if (url.endsWith('/audits')) return readFailure ? { ok: false, status: typeof readFailure === "object" ? 409 : 503, json: async () => typeof readFailure === "object" ? readFailure : ({}) } : ok(runs);
    if (url.endsWith('/transcriptions')) return ok([{ ...summary, latest_revision: { ...revision, status: state } }]);
    if (url.startsWith('/transcriptions/')) return ok({ ...history, revisions: [{ ...revision, status: state }], acceptances });
    return base(url, options);
  });
  await ui.get('#refresh-manuscripts').click();
  await ui.get('#manuscript-list').children[0].click();
  return ui;
}

for (const options of [{ state: 'DRAFT' }, { state: 'NEEDS_REVIEW' }, { acceptances: [] },
  { acceptances: [{ ...acceptance, accepted_revision_sha256: null }] },
  { acceptances: [{ ...acceptance, revision_number: 2 }] }, { intact: false }, { readFailure: true }]) {
  test(`analysis blocked for ${JSON.stringify(options)}`, async () => {
    const ui = await open(options);
    const action = button(ui, 'Executar Análise ConfIA');
    assert.equal(action.disabled, true);
    await action.click();
    assert.equal(ui.calls.some(call => call.options.method === 'POST'), false);
    assert.equal(ui.reports.length, 0);
  });
}

test('only persisted IDs reach bridge; dirty edit disables and discard restores action', async () => {
  let body;
  const ui = await open({ post: (_url, options) => { body = JSON.parse(options.body); return ok(run); } });
  const action = button(ui, 'Executar Análise ConfIA');
  assert.equal(action.disabled, false);
  assert(ui.calls.every(call => !call.options.method));
  const latex = tree(ui).find(n => n.tag === 'textarea' && /LaTeX/.test(n.placeholder));
  latex.value = '2 + 2 = 4, not saved'; await latex.emit('input');
  assert.equal(action.disabled, true);
  await action.click();
  await button(ui, 'Cancelar').click();
  assert.equal(action.disabled, false);
  await action.click();
  assert.deepEqual(body, { transcription_id: transcriptionId, revision_number: 1, acceptance_id: acceptance.acceptance_id });
  assert.equal(tree(ui).find(n => n.tag === 'textarea' && /LaTeX/.test(n.placeholder)).value, '\\[2 + 2 = 5\\]');
  assert.equal(ui.reports.length, 1);
  assert.equal(ui.reports[0].data, run.result);
  assert.equal(ui.reports[0].options.context, 'teacher');
  assert.match(primaryText(panel(ui)), /Concluída.*Erro matemático identificado/);
  assert.match(ui.get('#manuscript-list').textContent, /Análise ConfIA: Concluída/);
  assert.equal(ui.calls.some(call => call.url === '/audit'), false);
  const evaluation = tree(ui).find(n => n.className === 'teacher-decision-panel');
  assert.equal(descendants(evaluation).some(n => ['button', 'input'].includes(n.tag)), false);
});

test('pending analysis locks navigation and editor; double click produces one POST', async () => {
  const waiting = deferred();
  const ui = await open({ post: () => waiting.promise });
  const action = button(ui, 'Executar Análise ConfIA');
  const pending = action.click(); await flush();
  assert.match(primaryText(panel(ui)), /Analisando solução\.\.\./);
  assert.equal(action.disabled, true);
  assert(tree(ui).filter(n => n.tag === 'textarea').every(n => n.disabled));
  await action.click();
  await button(ui, 'Voltar à fila de soluções').click();
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.equal(ui.calls.filter(call => call.options.method === 'POST').length, 1);
  waiting.resolve(ok(run)); await pending;
  assert.equal(action.disabled, false);
});

test('newer revision shows old result with explicit stale notice and disables fresh audit until accepted', async () => {
  const ui = await open({ state: 'NEEDS_REVIEW', runs: [{ ...run, stale: true }] });
  assert.match(primaryText(panel(ui)), /Esta análise corresponde a uma versão anterior/);
  assert.doesNotMatch(primaryText(panel(ui)), /Concluída/);
  assert.equal(ui.reports.length, 1);
  assert.equal(button(ui, 'Executar Análise ConfIA').disabled, true);
  assert.match(ui.get('#manuscript-list').textContent, /Análise ConfIA: Transcrição anterior/);
});

for (const diagnostic of ['Integridade da revisão ou do aceite divergente',
  'A transcrição precisa ser conferida antes da análise.', 'source stale', 'result_sha256 divergente']) {
  test(`409 invalidates the current presentation and preserves only historical context: ${diagnostic}`, async () => {
    const original = JSON.stringify(run);
    const ui = await open({ runs: [run], post: () => ({ ok: false, status: 409,
      json: async () => ({ detail: diagnostic }) }) });
    assert.match(primaryText(panel(ui)), /Concluída/);
    assert.equal(ui.reports.length, 1);
    await button(ui, 'Executar novamente').click();
    const expected = diagnostic.startsWith('Integridade') ? 'A fonte desta análise não passou na verificação de integridade.'
      : diagnostic.startsWith('A transcrição') ? diagnostic
        : diagnostic.startsWith('result_sha256') ? 'Não foi possível validar a integridade do resultado desta análise.'
          : 'Não foi possível recuperar esta análise. Atualize a solução ou execute uma nova análise.';
    assert(primaryText(panel(ui)).includes(expected));
    assert.match(primaryText(panel(ui)), /Análise anterior indisponível/);
    assert.doesNotMatch(primaryText(panel(ui)), /Concluída|HTTP 409|Erro matemático identificado/);
    assert.match(ui.get('#manuscript-list').textContent, /Análise ConfIA: Conflito/);
    assert.doesNotMatch(ui.get('#manuscript-list').textContent, /Análise ConfIA: Concluída/);
    const stages = tree(ui).find(n => n.className === 'teacher-workflow-stages');
    const analysisStage = descendants(stages).find(n => n.tag === 'li' && /Análise ConfIA/.test(n.textContent));
    assert.equal(analysisStage.dataset.complete, 'false');
    assert.match(analysisStage.textContent, /Conflito/);
    assert.equal(button(ui, 'Executar Análise ConfIA').disabled, true);
    const selection = descendants(panel(ui)).find(n => n.tag === 'select');
    assert.equal(selection.children.length, 1);
    assert.equal(selection.children[0].value, run.audit_run_id);
    assert.match(selection.children[0].textContent, /Análise anterior indisponível/);
    await selection.emit('change');
    assert.doesNotMatch(primaryText(panel(ui)), /Concluída|Erro matemático identificado/);
    assert.equal(ui.reports.length, 1);
    assert.equal(ui.calls.filter(call => call.options.method === 'POST').length, 1);
    assert.equal(JSON.stringify(run), original);
  });
}

test('failed transport with a cached report leaves the current workflow failed, then retry restores completion', async () => {
  let fail = true;
  const ui = await open({ runs: [run], post: () => {
    if (fail) { fail = false; return { ok: false, status: typeof readFailure === "object" ? 409 : 503, json: async () => typeof readFailure === "object" ? readFailure : ({}) }; }
    return ok(run);
  } });
  await button(ui, 'Executar novamente').click();
  assert.doesNotMatch(primaryText(panel(ui)), /Concluída/);
  assert.match(primaryText(panel(ui)), /Análise anterior desta revisão/);
  assert.doesNotMatch(primaryText(panel(ui)), /versão anterior/);
  assert.match(ui.get('#manuscript-list').textContent, /Não foi possível concluir/);
  await button(ui, 'Executar novamente').click();
  assert.match(primaryText(panel(ui)), /Concluída/);
  assert.match(ui.get('#manuscript-list').textContent, /Análise ConfIA: Concluída/);
});

for (const response of [ok({ ...run, status: 'FAILED', result: null }),
  { ok: false, status: 503, json: async () => ({ detail: 'private provider error' }) }]) {
  test(`failure ${response.ok} never renders a successful report`, async () => {
    const ui = await open({ post: () => response });
    await button(ui, 'Executar Análise ConfIA').click();
    assert.match(primaryText(panel(ui)), /Não foi possível concluir a Análise ConfIA/);
    assert.doesNotMatch(primaryText(panel(ui)), /Concluída|private provider error/);
    assert.equal(ui.reports.length, 0);
  });
}

test('explicit rerun uses key, transport retry preserves it and completed rerun resets it', async () => {
  const bodies = [];
  let failed = true;
  const ui = await open({ runs: [run], post: (_url, options) => {
    bodies.push(JSON.parse(options.body));
    if (failed) { failed = false; return { ok: false, status: typeof readFailure === "object" ? 409 : 503, json: async () => typeof readFailure === "object" ? readFailure : ({}) }; }
    return ok({ ...run, audit_run_id: 'aud_' + 'e'.repeat(64) });
  } });
  await button(ui, 'Executar novamente').click();
  await button(ui, 'Executar novamente').click();
  assert.match(bodies[0].execution_key, /^teacher:/);
  assert.deepEqual(bodies[1], bodies[0]);
  await button(ui, 'Executar Análise ConfIA').click();
  assert.equal(bodies[2].execution_key, undefined);
});

test('diagram warning remains visible beside the report and traceability remains collapsed', async () => {
  const ui = await open({ runs: [{ ...run, source: { ...run.source, warnings: [
    { page_index: 0, message: 'Diagrama preservado; não analisado pelo auditor textual.' } ] } }] });
  assert.match(primaryText(panel(ui)), /Diagrama preservado; não analisado/);
  const source = descendants(panel(ui)).find(n => n.tag === 'details');
  assert.equal(Boolean(source.open), false);
  assert.match(source.textContent, /source.*2 \+ 2 = 5/s);
});

test('historical analysis of artificial recognition keeps an explicit primary warning', async () => {
  const ui = await open({ runs: [{ ...run, stale: true, source: { ...run.source,
    provenance: { revision: { provider: 'fake_test' } } } }] });
  assert.match(primaryText(panel(ui)), /transcrição de teste artificial; não é reconhecimento real/);
});

for (const [code, message] of Object.entries({
  TRANSCRIPTION_NOT_ACCEPTED: 'A transcrição precisa ser conferida antes da análise.',
  SOURCE_INTEGRITY_MISMATCH: 'A fonte desta análise não passou na verificação de integridade.',
  REPRODUCIBILITY_INTEGRITY_MISMATCH: 'Não foi possível validar os metadados desta análise.',
  RESULT_INTEGRITY_MISMATCH: 'Não foi possível validar a integridade do resultado desta análise.',
  REVISION_CONFLICT: 'Existe uma revisão mais recente ou um aceite de outra revisão. Atualize a solução.',
  AUDIT_RUN_CONFLICT: 'Não foi possível recuperar esta análise. Atualize a solução ou execute uma nova análise.',
})) {
  for (const stage of ['execute', 'list']) {
    test(`${stage} displays domain ${code} without exposing private diagnostics`, async () => {
      const privatePaths = ['/Users/teste/projeto/a', '/home/teste/projeto/a', 'C:\\Users\\teste\\a', 'file:///Users/teste/a'];
      const diagnostic = { error_code: code, detail: privatePaths.join(' ') };
      const ui = await open(stage === 'list' ? { readFailure: diagnostic } : {
        runs: [run], post: () => ({ ok: false, status: 409, json: async () => diagnostic }),
      });
      if (stage === 'execute') await button(ui, 'Executar novamente').click();
      assert(primaryText(panel(ui)).includes(message));
      assert(!primaryText(panel(ui)).includes(code));
      assert(!primaryText(panel(ui)).includes("versão anterior"));
      assert(descendants(panel(ui)).some(n => n.tag === 'details' && n.textContent.includes(code)));
      for (const path of privatePaths) {
        assert(!panel(ui).textContent.includes(path));
        assert(!JSON.stringify(ui.logs).includes(path));
      }
    });
  }
}
