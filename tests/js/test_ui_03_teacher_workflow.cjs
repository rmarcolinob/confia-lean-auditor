const test = require('node:test');
const assert = require('node:assert/strict');
const { id, record, detailData, transcriptionId, revision, summary, history, page, transportFor, descendants, primaryText } = require('./teacher-dom.cjs');
const ok = data => ({ ok: true, json: async () => data });
const tree = ui => descendants(ui.get('#manuscript-detail'));
const byClass = (ui, name) => tree(ui).find(n => n.className === name);
async function load(transport = transportFor()) {
  const ui = page(transport);
  await ui.get('#refresh-manuscripts').click();
  return ui;
}
async function open(transport) {
  const ui = await load(transport);
  await ui.get('#manuscript-list').children[0].click();
  return ui;
}

for (const [state, label] of [['NEEDS_REVIEW', 'Aguardando conferência'], ['ACCEPTED', 'Transcrição conferida'], ['DRAFT', 'Rascunho da transcrição']]) {
  test(`queue uses the persisted ${state} transcription separately from RECEIVED and analysis`, async () => {
    const ui = await load(async url => url === '/submissions' ? ok([record]) : url.endsWith('/audits') ? ok([]) : ok([{ ...summary, latest_revision: { ...revision, status: state } }]));
    const row = ui.get('#manuscript-list').children[0];
    assert.match(row.textContent, /Questão ITA2025Q1.*Recebida pelo ConfIA/);
    assert(row.textContent.includes(label));
    assert.match(row.textContent, /Análise ConfIA: Não executada.*Abrir/);
    assert.doesNotMatch(row.textContent, /sub_|tr_|SHA-256|RECEIVED|NEEDS_REVIEW|ACCEPTED|solução aprovada/);
    assert(row.attributes['aria-label'].includes(label));
    assert(ui.calls.every(call => !call.options.method));
  });
}

test('received solution without transcription has only the receipt stage completed', async () => {
  const ui = await open();
  const steps = descendants(byClass(ui, 'teacher-workflow-stages')).filter(n => n.tag === 'li');
  assert.deepEqual(steps.map(n => n.dataset.complete), ['true', 'false', 'false', 'false']);
  assert.match(steps[1].textContent, /Ainda não criada/);
  assert.match(byClass(ui, 'manuscript-analysis-panel').textContent, /Não executada.*ainda não foi encaminhada para análise matemática/);
  assert.equal(ui.get('#manuscript-queue').hidden, true);
});

test('original precedes the complementary workflow and page navigation preserves original URLs', async () => {
  const data = detailData();
  data.submission = { ...record, page_images: [...record.page_images, { filename: 'page_2.png', page_index: 1 }] };
  data.integrity = [...data.integrity, { filename: 'page_2.png', matches: true }];
  const base = transportFor();
  const ui = await open(async url => url === `/submissions/${id}` ? ok(data) : base(url));
  const workspace = byClass(ui, 'transcription-workspace');
  assert.equal(workspace.children[0].className, 'original-manuscript-panel');
  assert.equal(workspace.children[1].className, 'transcription-panel');
  const detail = ui.get('#manuscript-detail');
  assert(detail.children.indexOf(byClass(ui, 'manuscript-analysis-panel')) > detail.children.indexOf(workspace));
  assert.match(primaryText(workspace.children[0]), /Solução do aluno.*Manuscrito original.*conferidos e preservados/);
  await tree(ui).find(n => n.tag === 'button' && n.textContent === 'Próxima página').click();
  assert.equal(tree(ui).find(n => n.tag === 'img').src, `/submissions/${id}/pages/1`);
  assert.match(primaryText(workspace.children[0]), /Página 2 de 2/);
  const pageStatus = tree(ui).find(n => n.textContent === 'Página 2 de 2');
  assert.equal(pageStatus.attributes['aria-live'], 'polite');
});

test('accepted fidelity completes only transcription; no audit, grade or institutional decision', async () => {
  const latest = { ...revision, status: 'ACCEPTED' };
  const base = transportFor(true, true);
  const ui = await open(async url => url === `/transcriptions/${transcriptionId}` ? ok({ ...history, revisions: [latest] }) : base(url));
  const steps = descendants(byClass(ui, 'teacher-workflow-stages')).filter(n => n.tag === 'li');
  assert.deepEqual(steps.map(n => n.dataset.complete), ['true', 'true', 'false', 'false']);
  const evaluation = byClass(ui, 'teacher-evaluation-panel');
  assert.match(evaluation.textContent, /integração em desenvolvimento/);
  assert.equal(descendants(evaluation).some(n => ['button', 'input', 'select'].includes(n.tag)), false);
  assert.equal(ui.calls.some(c => c.url === '/audit' || /decision|grade/.test(c.url) || c.options.method), false);
});

test('IDs, hashes and enums stay in closed disclosures and acceptance history remains available', async () => {
  const accepted = { revision_number: 1, accepted_at: revision.created_at, reviewer_reference: 'professor-teste-01', acceptance_note: 'Conferida visualmente.' };
  const base = transportFor(true, true);
  const ui = await open(async url => url === `/transcriptions/${transcriptionId}` ? ok({ ...history, acceptances: [accepted] }) : base(url));
  assert.doesNotMatch(primaryText(ui.get('#manuscript-detail')), /sub_|tr_|SHA-256|snapshot:|NEEDS_REVIEW|initial_transcription/);
  assert.match(byClass(ui, 'transcription-history').textContent, /Histórico da transcrição.*Revisão 1.*Conferência da revisão 1.*Conferida visualmente/s);
  const technical = byClass(ui, 'disclosure submission-technical');
  assert.equal(technical.children[0].textContent, 'Detalhes técnicos');
  assert(technical.textContent.includes(id));
  assert.equal(Boolean(technical.open), false);
});

test('production has no recognition controls; persisted fake transcription remains explicitly artificial', async () => {
  const fake = { ...revision, source: 'automatic', provider: 'fake_test', recognizer_run_id: 'run_' + 'c'.repeat(32), provenance: { adapter: 'confia_fake_test', input_hash: 'abc' } };
  const base = transportFor(true, true);
  const ui = await open(async url => url === '/submissions/recognition-providers' ? ok([]) : url === `/transcriptions/${transcriptionId}` ? ok({ ...history, revisions: [fake] }) : base(url));
  assert.equal(tree(ui).some(n => n.tag === 'button' && /Gerar transcrição automática/.test(n.textContent)), false);
  assert.match(primaryText(ui.get('#manuscript-detail')), /Transcrição de teste artificial.*não é OCR real/);
  assert.doesNotMatch(primaryText(ui.get('#manuscript-detail')), /fake_test|run_|input_hash/);
  assert.match(ui.get('#manuscript-detail').textContent, /Detalhes do reconhecimento.*input_hash/s);
});

test('transcription filters operate on the same queue and preserve the selected workspace', async () => {
  const idB = 'sub_' + 'c'.repeat(32);
  const idC = 'sub_' + 'd'.repeat(32);
  const base = transportFor(true, true);
  const ui = await load(async url => {
    if (url === '/submissions') return ok([record, { ...record, submission_id: idB }, { ...record, submission_id: idC }]);
    if (url === `/submissions/${idB}/transcriptions`) return ok([{ ...summary, latest_revision: { ...revision, status: 'ACCEPTED' } }]);
    if (url === `/submissions/${idC}/transcriptions`) return ok([]);
    return base(url);
  });
  await ui.get('#manuscript-list').children[0].click();
  const workspace = byClass(ui, 'transcription-workspace');
  const count = ui.calls.length;
  ui.get('#transcription-filter').value = 'accepted'; await ui.get('#transcription-filter').emit('change');
  assert.equal(ui.get('#manuscript-list').children.length, 1);
  assert.match(ui.get('#manuscript-list').textContent, /Transcrição conferida/);
  assert.equal(byClass(ui, 'transcription-workspace'), workspace);
  assert.equal(ui.calls.length, count);
  ui.get('#transcription-filter').value = 'uncreated'; await ui.get('#transcription-filter').emit('change');
  assert.equal(ui.get('#manuscript-list').children.length, 1);
  assert.match(ui.get('#manuscript-list').textContent, /Ainda não criada/);
});

test('failure to consult a transcription never looks like an absent transcription or completed analysis', async () => {
  const ui = await load(async url => url === '/submissions' ? ok([record]) : { ok: false, status: 503, json: async () => ({ detail: 'internal_error' }) });
  assert.match(ui.get('#manuscript-list').textContent, /Transcrição: Não foi possível consultar/);
  assert.doesNotMatch(ui.get('#manuscript-list').textContent, /Ainda não criada|internal_error|HTTP/);
  assert.match(ui.get('#manuscript-message').textContent, /Alguns estados de transcrição/);
});

test('Portuguese integrity conflict is translated and unsaved transcription survives', async () => {
  const base = transportFor(true, true);
  const ui = await open(async (url, options) => options.method === 'POST' ? { ok: false, status: 409, json: async () => ({ detail: 'Integridade da submissão original inválida; revisão não publicada.' }) } : base(url));
  const latex = tree(ui).find(n => n.tag === 'textarea' && /LaTeX/.test(n.placeholder));
  latex.value = 'alteração de teste'; await latex.emit('input');
  await tree(ui).find(n => n.tag === 'button' && n.textContent === 'Salvar como nova revisão').click();
  assert.match(primaryText(ui.get('#manuscript-detail')), /Os arquivos originais desta solução precisam ser conferidos/);
  assert.doesNotMatch(primaryText(ui.get('#manuscript-detail')), /Existe uma revisão mais recente|HTTP/);
  assert.equal(latex.value, 'alteração de teste');
});

test('return to queue respects unsaved changes and does not discard them implicitly', async () => {
  const ui = await open(transportFor(true, true));
  const latex = tree(ui).find(n => n.tag === 'textarea' && /LaTeX/.test(n.placeholder));
  const back = tree(ui).find(n => n.tag === 'button' && n.textContent === 'Voltar à fila de soluções');
  latex.value = 'nova leitura'; await latex.emit('input'); await back.click();
  assert.equal(ui.get('#manuscript-queue').hidden, true);
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.equal(latex.value, 'nova leitura');
  await tree(ui).find(n => n.tag === 'button' && n.textContent === 'Descartar alterações não salvas').click();
  await back.click();
  assert.equal(ui.get('#manuscript-queue').hidden, false);
  assert.equal(ui.get('#manuscript-detail').hidden, true);
});
