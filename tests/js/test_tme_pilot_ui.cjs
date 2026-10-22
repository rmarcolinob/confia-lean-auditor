const test = require('node:test');
const assert = require('node:assert/strict');
const { page, flush } = require('./capture-dom.cjs');
const Model = require('../../app/confia_lean_auditor/static/capture/ink-model.js');

const { pilot, walk, text } = require('./tme-dom.cjs');

test('photo states, retry and single transcription remain visible without exposing technical content', async () => {
  const ui = await pilot();
  assert.match(text(ui.root), /Correções/);
  assert.doesNotMatch(text(ui.root), /TME/);
  await ui.click('Abrir');
  assert.match(text(ui.root), /Aguardando reconhecimento/);
  assert.ok(walk(ui.root).some(e => e.tag === 'img' && e.src.endsWith('/originals/0')));
  await ui.click('Reconhecer');
  assert.match(text(ui.root), /Falha técnica/);
  assert.match(text(ui.root), /limite do serviço/);
  assert.ok(walk(ui.root).some(e => e.textContent === 'Voltar e ajustar páginas'));
  await ui.click('Tentar novamente');
  assert.match(text(ui.root), /Transcrição automática disponível/);

  assert.match(text(ui.root), /Original.*Transcrição/);
  assert.deepEqual(ui.rendered, ['x = 2']);
  assert.doesNotMatch(walk(ui.root).filter(e => e.tag !== "pre").map(e => e.textContent).join(" "), /mixed|PROVIDER_|recognizer_run_id/);
  assert.equal(walk(ui.root).find(e => e.tag === 'button' && e.textContent === 'Analisar com ConfIA').disabled, false);
  assert.doesNotMatch(text(ui.root), /Conferir transcrição/);
});

test('adjusting a saved photo recovers original bytes and timestamps and publishes a separate case', async () => {
  const ui = await pilot();
  await ui.click('Abrir');
  await ui.click('Voltar e ajustar páginas');
  assert.match(text(ui.root), /nova correção.*originais ficam preservados/);
  await ui.click('Girar 90°');
  await ui.click('Usar esta página');
  await ui.click('Continuar');
  const upload = ui.calls.find(c => c.url.endsWith('/scan') && c.options.method === 'POST');
  assert.ok(upload);
  assert.ok(!upload.url.includes(ui.snapshot.case_id));
  const page = JSON.parse(upload.options.body).pages[0];
  assert.equal(Buffer.from(page.original_base64, 'base64').toString(), 'original-bytes');
  assert.equal(page.captured_at, ui.acceptedAt);
  assert.equal(page.original_mime, 'image/png');
  assert.equal(page.rotation_degrees, 180);
  assert.ok(ui.calls.some(c => c.url === '/tme/cases' && c.options.method === 'POST'));
});

test('pilot notebook shows the selected statement, updates sticky offset, and reuses the five editing handlers', async () => {
  const ui = await page({ embedded: true, catalogPath: '/tme/problems',
    search: '?embedded=1&tme_case_id=case_' + 'a'.repeat(32) + '&problem_id=ITA2025Q1',
    problems: [{ problem_id: 'ITA2025Q1', title: 'Questão escolhida', statement: 'Enunciado escolhido' }],
  });
  assert.equal(ui.statement.textContent, 'Enunciado escolhido');
  assert.equal(ui.statementWrap.hidden, false);
  assert.equal(ui.get('#toggle-problem').attributes['aria-expanded'], 'true');
  assert.equal(ui.get('.notebook-card').nextElement, ui.get('#capture-recovery'));
  assert.equal(ui.get('.notebook-controls').nextElement, ui.get('.page-toolbar'));
  ui.get('#problem-dock').height = 65;
  await ui.click('toggle-problem');
  assert.equal(ui.context.document.body.style['--pilot-dock-height'], '65px');
  assert.equal(ui.statementWrap.hidden, true);
  ui.get('#problem-dock').height = 210;
  await ui.click('toggle-problem');
  assert.equal(ui.context.document.body.style['--pilot-dock-height'], '210px');
  await ui.click('pen-mode');
  assert.equal(ui.messages.at(-1).context.controls.input_mode, 'pen');
  await ui.click('erase-tool');
  assert.equal(ui.messages.at(-1).context.controls.active_tool, 'erase');
  await ui.click('draw-tool');
  assert.equal(ui.messages.at(-1).context.controls.active_tool, 'draw');
  const draft = Model.createDraft('ITA2025Q1');
  const ink = Model.addStroke(draft, { page_id: draft.pages[0].page_id, pointer_type: 'pen', points: [{ x: 1, y: 2, t_ms: 0, pressure_reported: .5 }] });
  // Recover the same real model used by the canvas; no new undo/redo implementation.
  await ui.recover(ink);
  assert.equal(ui.canvasRenders.at(-1).document.active_stroke_ids.length, 1);
  await ui.click('undo'); await flush();
  assert.equal(ui.canvasRenders.at(-1).document.active_stroke_ids.length, 0);
  ui.saves.at(-1).resolve(); await flush();
  await ui.click('redo'); await flush();
  assert.equal(ui.canvasRenders.at(-1).document.active_stroke_ids.length, 1);
  ui.saves.at(-1).resolve(); await flush();
});
