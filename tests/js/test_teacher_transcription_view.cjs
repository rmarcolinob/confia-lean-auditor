const test = require('node:test');
const assert = require('node:assert/strict');
const { id, record, detailData, revision, history, transcriptionId, page, transportFor, descendants, primaryText } = require('./teacher-dom.cjs');

const mixed = { ...revision.segments[0], kind: 'mixed',
  text: 'Primeira linha.\nSegunda linha: 1/2 = 0.5.', latex: 'Primeira linha.\nSegunda linha: \\(\\frac{1}{2} = 0.5\\).',
  confidence: 0.91, source_region: { x: 1, y: 2, width: 100, height: 50, coordinate_system: 'top_left_css_pixels' },
  source_stroke_refs: ['stroke:1'] };
async function open(segments = [mixed], pageCount = 1) {
  const saved = { ...revision, source: 'automatic', provider: 'mathpix', recognizer_run_id: 'run_' + 'c'.repeat(32),
    provenance: { input_hash: 'preserved' }, segments };
  const originalJSON = JSON.stringify(saved);
  const versions = [saved], acceptances = [];
  const original = detailData();
  const submission = { ...record, page_images: Array.from({ length: pageCount }, (_, page_index) => ({ page_index, filename: `page_${page_index + 1}.png` })) };
  const base = transportFor(true, true);
  const ok = value => ({ ok: true, json: async () => value });
  const ui = page(async (url, options) => {
    if (url.endsWith('/revisions') && options.method === 'POST') {
      const body = JSON.parse(options.body);
      assert.equal(body.based_on_revision_number, versions.at(-1).revision_number);
      const next = { ...saved, ...body, revision_number: versions.length + 1 };
      versions.push(next);
      return ok(next);
    }
    if (url.endsWith('/accept') && options.method === 'POST') {
      const body = JSON.parse(options.body);
      acceptances.push({ ...body, accepted_at: '2026-10-19T12:00:00Z', acceptance_id: `acc:${body.revision_number}` });
      return ok({ revision: versions.find(v => v.revision_number === body.revision_number), acceptance: acceptances.at(-1) });
    }
    if (url === `/transcriptions/${transcriptionId}` && !options.method) {
      return ok({ ...history, revisions: versions.map(v => ({ ...v,
        status: acceptances.some(a => a.revision_number === v.revision_number) ? 'ACCEPTED' : v.status })), acceptances });
    }
    if (url === `/submissions/${id}`) return ok({ ...original, submission,
      integrity: [...original.integrity, ...submission.page_images.slice(1).map(image => ({ ...original.integrity[1], filename: image.filename }))] });
    return base(url, options);
  });
  await ui.get('#refresh-manuscripts').click();
  await ui.get('#manuscript-list').children[0].click();
  const nodes = () => descendants(ui.get('#manuscript-detail'));
  const section = name => nodes().find(node => node.className === name);
  const button = text => nodes().find(node => node.tag === 'button' && node.textContent === text);
  const edit = async value => {
    await button('Editar transcrição').click();
    section('transcription-source').value = value;
    await section('transcription-source').emit('input');
  };
  return { ...ui, saved, originalJSON, versions, acceptances, nodes, section, button, edit };
}

test('main column is one white reading document, with source and metadata collapsed', async () => {
  const ui = await open();
  const column = ui.section('transcription-panel');
  assert.equal(column.children[0].textContent, 'Transcrição reconhecida');
  assert.equal(column.children[1], ui.section('transcription-visual'));
  assert.equal(ui.section('transcription-visual').children.length, 1);
  assert.equal(ui.section('transcription-document').attributes.role, 'document');
  assert.doesNotMatch(primaryText(column), /Misto|mixed|Texto reconhecido|LaTeX reconhecido|Texto-fonte|provider|confidence|OCR|Mathpix|input_hash|não significa/);
  assert.equal(ui.section('transcription-document').textContent, 'Primeira linha.\nSegunda linha: rendered:\\frac{1}{2} = 0.5.');
  assert.equal(ui.section('transcription-editor').hidden, true);
  assert.equal(ui.section('transcription-visual').hidden, false);
  assert.match(ui.button('Conferir transcrição').title, /somente a fidelidade ao manuscrito; não significa solução correta/);
  const original = ui.section('original-manuscript-panel');
  const titleIndex = original.children.findIndex(n => n.textContent === 'Manuscrito original');
  assert.equal(original.children[titleIndex + 1].textContent, 'Solução enviada pelo aluno.');
  assert.doesNotMatch(original.textContent, /O arquivo original permanece preservado/);
  assert.match(column.textContent, /input_hash.*preserved/s);
  assert.equal(JSON.stringify(ui.saved), ui.originalJSON);
  assert.equal(ui.calls.some(call => call.options.method === 'POST'), false);
});

test('equivalent text and latex with different spacing or notation render exactly one solution', async () => {
  for (const [text, latex, rendered] of [
    ['2 + 2 = 5', '2+2=5', 'rendered:2+2=5'],
    ['x² = 9', 'x^2 = 9', 'rendered:x^2 = 9'],
    ['Seja x² + 1.\nLogo, y = 2.', 'Seja \\(x^2 + 1\\).\nLogo, \\(y = 2\\).', 'Seja rendered:x^2 + 1.\nLogo, rendered:y = 2.'],
  ]) {
    const ui = await open([{ ...mixed, text, latex }]);
    assert.equal(ui.section('transcription-document').textContent, rendered);
    assert.equal(JSON.stringify(ui.saved), ui.originalJSON);
    assert.equal(ui.section('transcription-source').value, latex.includes('\\(') ? latex : `\\[${latex}\\]`);
  }
});

test('canonical source is latex when populated, otherwise text; fields are never concatenated', async () => {
  const ui = await open([
    { ...mixed, text: 'Representação alternativa', latex: 'x=1' },
    { ...mixed, segment_id: 'seg:2', order: 1, text: 'Texto comum\ncom continuação.', latex: '  ' },
  ]);
  assert.equal(ui.section('transcription-document').children[0].textContent, 'rendered:x=1');
  assert.equal(ui.section('transcription-document').children[1].textContent, 'Texto comum\ncom continuação.');
  assert.doesNotMatch(ui.section('transcription-source').value, /Representação alternativa/);
});

test('inline/display math, prose, paragraphs and intentional repetitions retain their order', async () => {
  const source = 'Antes $x_1$.\n\\[a-b=-3\\]\n\nDepois $$2+2=5$$\nFim \\(y=2\\).';
  const ui = await open([{ ...mixed, text: source, latex: source },
    { ...mixed, segment_id: 'seg:2', order: 1, text: 'Outra linha\ncom continuação.', latex: null },
    { ...mixed, segment_id: 'seg:3', order: 2, text: '\\(x=1\\)\n\\(x=1\\)', latex: null }]);
  const document = ui.section('transcription-document');
  assert.equal(document.children[0].textContent, 'Antes rendered:x_1.\nrendered:a-b=-3\n\nDepois rendered:2+2=5\nFim rendered:y=2.');
  assert.equal(document.children[1].textContent, 'Outra linha\ncom continuação.');
  assert.equal(document.children[2].textContent, 'rendered:x=1\nrendered:x=1');
  assert.deepEqual(descendants(document).filter(n => n.className?.startsWith('recognized-')).map(n => n.className),
    ['recognized-inline-math', 'recognized-math', 'recognized-math', 'recognized-inline-math', 'recognized-inline-math', 'recognized-inline-math']);
});

test('edit opens one source textarea; save returns to the new persisted document without modifying revision 1', async () => {
  const ui = await open();
  await ui.button('Editar transcrição').click();
  const editor = ui.section('transcription-editor');
  assert.equal(editor.hidden, false);
  assert.equal(ui.section('transcription-visual').hidden, true);
  assert.equal(ui.button('Editar transcrição').attributes['aria-expanded'], 'true');
  assert.equal(descendants(editor).filter(n => n.tag === 'textarea').length, 1);
  assert.equal(ui.section('transcription-source').value, mixed.latex);
  assert(ui.section('transcription-source').focused);
  assert.match(primaryText(editor), /Editar transcrição.*Cancelar.*Salvar nova versão/);
  const source = 'Leitura corrigida: \\(x^2 = 9\\).\n\nSem avaliar a matemática.';
  ui.section('transcription-source').value = source; await ui.section('transcription-source').emit('input');
  assert.equal(ui.button('Conferir transcrição').disabled, true);
  assert.equal(ui.calls.some(call => call.options.method === 'POST'), false);
  await ui.button('Salvar nova versão').click();
  assert.equal(ui.section('transcription-editor').hidden, true);
  assert.equal(ui.section('transcription-visual').hidden, false);
  assert.equal(ui.section('transcription-document').textContent, 'Leitura corrigida: rendered:x^2 = 9.\n\nSem avaliar a matemática.');
  assert.equal(ui.button('Conferir transcrição').disabled, false);
  assert.equal(ui.versions.length, 2);
  const next = ui.versions[1];
  assert.equal(next.segments[0].text, source);
  assert.equal(next.segments[0].latex, null);
  assert.equal(next.segments[0].kind, 'mixed');
  assert.equal(next.status, 'NEEDS_REVIEW');
  assert.equal(next.based_on_revision_number, 1);
  assert.equal(JSON.stringify(ui.saved), ui.originalJSON);
});

test('Cancel is available even before changing the source; it restores the persisted document without requests', async () => {
  const ui = await open();
  const before = ui.section('transcription-document').textContent;
  await ui.button('Editar transcrição').click();
  assert.equal(ui.button('Cancelar').hidden, false);
  await ui.button('Cancelar').click();
  assert.equal(ui.section('transcription-editor').hidden, true);
  await ui.edit('Texto que será descartado');
  assert.equal(ui.section('transcription-message').textContent, '');
  await ui.button('Cancelar').click();
  assert.equal(ui.section('transcription-editor').hidden, true);
  assert.equal(ui.section('transcription-visual').hidden, false);
  assert.equal(ui.section('transcription-document').textContent, before);
  assert.equal(ui.section('transcription-source').value, mixed.latex);
  assert.equal(ui.button('Conferir transcrição').disabled, false);
  assert.equal(ui.calls.some(call => call.options.method === 'POST'), false);
});

test('acceptance targets the current revision; editing an accepted revision creates another requiring acceptance', async () => {
  const ui = await open();
  await ui.button('Conferir transcrição').click();
  const firstAcceptance = JSON.stringify(ui.acceptances[0]);
  assert.equal(ui.button('Conferir transcrição').disabled, true);
  for (let number = 2; number <= 3; number++) {
    await ui.edit(`Versão ${number}: \\(2+2=5\\).`);
    await ui.button('Salvar nova versão').click();
    assert.equal(ui.button('Conferir transcrição').disabled, false);
    assert.equal(ui.versions.at(-1).status, 'NEEDS_REVIEW');
    assert.equal(ui.versions.at(-1).revision_number, number);
    assert.match(ui.section('transcription-document').textContent, new RegExp(`Versão ${number}: rendered:2\\+2=5`));
    await ui.button('Conferir transcrição').click();
    assert.equal(ui.acceptances.at(-1).revision_number, number);
    assert.equal(ui.acceptances.at(-1).segments, undefined);
    assert.equal(ui.button('Conferir transcrição').disabled, true);
  }
  assert.equal(JSON.stringify(ui.acceptances[0]), firstAcceptance);
  assert.equal(JSON.stringify(ui.saved), ui.originalJSON);
  assert.equal(ui.versions[1].segments[0].text, 'Versão 2: \\(2+2=5\\).');
  assert.deepEqual(ui.calls.filter(c => c.options.method === 'POST').map(c => c.url.split('/').at(-1)),
    ['accept', 'revisions', 'accept', 'revisions', 'accept']);
});

test('history is compact and distinguishes automatic origin from subsequent manual corrections', async () => {
  const ui = await open();
  await ui.edit('Uma nova leitura.');
  await ui.button('Salvar nova versão').click();
  const history = ui.section('transcription-history');
  assert.equal(history.tag, 'details');
  assert.equal(history.open, undefined);
  assert.equal(history.children[0].textContent, 'Histórico da transcrição (2 revisões)');
  const articles = history.children.filter(n => n.tag === 'article');
  assert.match(primaryText(articles[0]), /Revisão 2 · Aguardando conferência.*Manual.*Ver revisão/);
  assert.match(primaryText(articles[1]), /Revisão 1 · Aguardando conferência.*Automática.*Ver revisão/);
  assert.doesNotMatch(primaryText(articles[0]), /Uma nova leitura|provider|input_hash/);
});

test('multiple pages share one editor and retain drafts, ordering and untouched page provenance', async () => {
  const untouched = { ...mixed, segment_id: 'seg:page2', page_index: 1, text: 'Outra representação', latex: 'Página 2: \\(y=3\\).', confidence: 0.7 };
  const ui = await open([untouched, mixed], 2);
  await ui.edit('Página 1 editada: \\(x=2\\).');
  const selection = ui.section('transcription-source-page');
  selection.value = '1'; await selection.emit('change');
  assert.equal(ui.section('transcription-source').value, untouched.latex);
  selection.value = '0'; await selection.emit('change');
  assert.equal(ui.section('transcription-source').value, 'Página 1 editada: \\(x=2\\).');
  await ui.button('Salvar nova versão').click();
  assert.deepEqual(ui.versions[1].segments[1], untouched);
  assert.equal(ui.versions[1].segments[0].page_index, 0);
  assert.equal(ui.versions[1].segments[0].confidence, undefined);
  assert.equal(ui.versions[1].segments[0].source_region, undefined);
  assert.equal(JSON.stringify(ui.saved), ui.originalJSON);
  assert.equal(ui.section('transcription-document').children[0].textContent, 'Página 1 editada: rendered:x=2.');
  assert.equal(ui.section('transcription-document').children[1].textContent, 'Página 2: rendered:y=3.');
});

test('page selection alone does not dirty a revision; Cancel discards drafts on every page', async () => {
  const other = { ...mixed, segment_id: 'seg:page2', page_index: 1, latex: 'y=3' };
  const ui = await open([mixed, other], 2);
  await ui.button('Editar transcrição').click();
  const selection = ui.section('transcription-source-page');
  selection.value = '1'; await selection.emit('change');
  assert.equal(ui.button('Conferir transcrição').disabled, false);
  ui.section('transcription-source').value = 'Mudança na página 2'; await ui.section('transcription-source').emit('input');
  selection.value = '0'; await selection.emit('change');
  ui.section('transcription-source').value = 'Mudança na página 1'; await ui.section('transcription-source').emit('input');
  await ui.button('Cancelar').click();
  await ui.button('Editar transcrição').click();
  assert.equal(ui.section('transcription-source').value, mixed.latex);
  selection.value = '1'; await selection.emit('change');
  assert.equal(ui.section('transcription-source').value, '\\[y=3\\]');
  assert.equal(ui.button('Conferir transcrição').disabled, false);
});

test('unchanged sources preserve exact strings, CRLF, types and segment provenance in the revision payload', async () => {
  const original = { ...mixed, text: '  Primeiro\r\n\r\nSegundo  ', latex: '  2 + 2 = 5\r\n' };
  const ui = await open([original]);
  await ui.button('Editar transcrição').click();
  assert.equal(ui.section('transcription-source').value.includes('\r'), false);
  await ui.button('Salvar nova versão').click();
  assert.deepEqual(ui.versions[1].segments, [original]);
  assert.equal(ui.versions[1].status, 'NEEDS_REVIEW');
  assert.equal(JSON.stringify(ui.saved), ui.originalJSON);
});

test('oversized edits keep the draft and explain the existing segment limit before sending', async () => {
  const ui = await open();
  await ui.edit('a'.repeat(20001));
  await ui.button('Salvar nova versão').click();
  assert.match(ui.section('transcription-message').textContent, /página 1.*20.000 caracteres/);
  assert.equal(ui.section('transcription-editor').hidden, false);
  assert.equal(ui.section('transcription-source').value.length, 20001);
  assert.equal(ui.calls.some(call => call.options.method === 'POST'), false);
});

test('malformed delimiters and HTML-looking text remain literal; a single source does not remove repetitions', async () => {
  const ui = await open([
    { ...mixed, text: '<img src=x onerror=unsafe>\nTexto', latex: null, kind: 'text' },
    { ...mixed, segment_id: 'seg:2', order: 1, text: 'alternativa', latex: '\\(z=3' },
    { ...mixed, segment_id: 'seg:3', order: 2, text: null, latex: 'y=2' },
    { ...mixed, segment_id: 'seg:4', order: 3, text: null, latex: 'y=2' },
  ]);
  const document = ui.section('transcription-document');
  assert.equal(document.children[0].textContent, '<img src=x onerror=unsafe>\nTexto');
  assert.equal(document.children[1].textContent, '\\(z=3');
  assert.equal((document.textContent.match(/rendered:y=2/g) || []).length, 2);
  assert.equal(descendants(document).some(node => ['img', 'script', 'textarea', 'pre', 'code'].includes(node.tag) || node.contentEditable), false);
});
