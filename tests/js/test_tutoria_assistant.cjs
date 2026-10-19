const test = require('node:test');
const assert = require('node:assert/strict');
const { page } = require('./workspace-dom.cjs');
const { descendants, flush } = require('./ui-dom.cjs');
const drawer = ui => ui.get('#tutoria-assistant-drawer');
const host = ui => ui.get('#tutoria-assistant-content');
const nodes = ui => descendants(host(ui));
const input = ui => nodes(ui).find(node => node.tag === 'textarea');
const button = (ui, label) => nodes(ui).find(node => node.tag === 'button' && node.textContent === label);
const open = ui => ui.get('#tutoria-assistant-toggle').click();
const close = ui => ui.get('#tutoria-assistant-close').click();

test('floating assistant opens in place on TutorIA overview with accessible nonmodal controls and Escape', async () => {
  const ui = await page(); ui.visit('tutoria'); const calls = ui.calls.length;
  assert.equal(ui.get('#tutoria-assistant-rail').hidden, false);
  await open(ui);
  assert.equal(ui.location.hash, '#student/tutoria'); assert.equal(drawer(ui).hidden, false);
  assert.equal(drawer(ui).getAttribute('aria-modal'), 'false');
  assert.equal(ui.get('#tutoria-assistant-toggle').getAttribute('aria-expanded'), 'true');
  assert.match(host(ui).textContent, /Como posso ajudar nos seus estudos/);
  assert.equal(ui.get('#tutoria-root').hidden, false);
  await drawer(ui).emit('keydown', {key:'Escape', preventDefault() {}});
  assert.equal(drawer(ui).hidden, true); assert.equal(host(ui).textContent, '');
  assert.equal(ui.get('#tutoria-assistant-toggle').focused, true);
  assert.equal(ui.calls.length, calls);
});

test('opening, messaging and collapsing preserves notebook identity, question, ink, snapshot and draft', async () => {
  const ui = await page(); ui.visit('tutoria/practice'); ui.window.ConfIAWorkspace.practiceProblem('B');
  ui.notebook({problem_id:'B',draft_id:'draft:B',local_snapshot_id:'snapshot:unchanged',ink_version:'3:7:12',controls:{document_id:'draft:B',can_tutor_preview:true,tutor_preview_segments:[{page_index:0,order:0,kind:'math',text:'2+2=5',latex:'2+2=5'}],persistence:'Rascunho salvo neste dispositivo',persistence_kind:'success'}});
  await ui.write('Minha solução permanece');
  const before = JSON.stringify(ui.window.ConfIAWorkspace.analysisContext()), src = ui.frame.src;
  const commands = ui.commands.length, calls = ui.calls.length, frame = ui.frame;
  const preview = ui.get('#workspace-tutor-result').textContent, autosave = ui.get('#workspace-draft-persistence').textContent;
  assert.match(preview, /2\+2=5/);
  assert.equal(autosave, 'Rascunho salvo neste dispositivo');
  for (let n = 0; n < 2; n++) {
    await open(ui); assert.match(host(ui).textContent, /Você está trabalhando na questão B/);
    assert.equal(ui.get('#notebook-surface').hidden, false);
    await button(ui, 'Me dê uma pista').click(); await flush(); await close(ui);
  }
  assert.equal(ui.location.hash, '#student/tutoria/practice');
  assert.equal(ui.frame, frame); assert.equal(ui.frame.src, src);
  assert.equal(JSON.stringify(ui.window.ConfIAWorkspace.analysisContext()), before);
  assert.equal(ui.get('#solution-input').value, 'Minha solução permanece');
  assert.equal(ui.commands.length, commands); assert.equal(ui.calls.length, calls);
  assert.equal(ui.get('#workspace-tutor-result').textContent, preview);
  assert.equal(ui.get('#workspace-draft-persistence').textContent, autosave);
});

test('repeated notebook layout updates keep composer identity and draft; selected questions isolate conversations', async () => {
  const ui = await page(); ui.visit('tutoria/practice'); ui.window.ConfIAWorkspace.practiceProblem('A'); ui.notebook();
  await open(ui); const field = input(ui); field.value = 'Pergunta ainda em edição'; await field.emit('input');
  ui.notebook(); ui.window.ConfIATutoriaAssistant.sync();
  assert.equal(input(ui), field); assert.equal(input(ui).value, 'Pergunta ainda em edição');
  ui.window.ConfIAWorkspace.practiceProblem('B'); ui.notebook({draft_id:'draft:B'});
  assert.match(host(ui).textContent, /Você está trabalhando na questão B/); assert.equal(input(ui).value, '');
  ui.window.ConfIAWorkspace.practiceProblem('A'); ui.notebook();
  assert.equal(input(ui).value, 'Pergunta ainda em edição');
});

test('context updates in the same drawer through lesson, attempt and overview navigation', async () => {
  const ui = await page(); ui.visit('tutoria'); await open(ui); ui.visit('tutoria/content');
  let content = descendants(ui.get('#tutoria-content'));
  let card = content.find(node => node.tag === 'article' && node.textContent.startsWith('Funções'));
  await descendants(card).find(node => node.tag === 'button').click();
  content = descendants(ui.get('#tutoria-content'));
  card = content.find(node => node.tag === 'article' && node.textContent.startsWith('Funções do 1º grau'));
  await descendants(card).find(node => node.tag === 'button').click();
  assert.match(host(ui).textContent, /Você está estudando: Funções do 1º grau/);
  ui.visit('tutoria/feedback'); assert.match(host(ui).textContent, /Você está revisando uma tentativa/);
  ui.visit('tutoria'); assert.match(host(ui).textContent, /Como posso ajudar nos seus estudos/);
  assert.doesNotMatch(host(ui).textContent, /Funções do 1º grau|Ver tentativa/);
});

test('drawer preserves conversation and draft across close, internal navigation and a visit outside TutorIA', async () => {
  const ui = await page(); ui.visit('tutoria'); await open(ui);
  input(ui).value = 'Minha dúvida de estudo'; await input(ui).emit('input');
  await input(ui).emit('keydown', {key:'Enter', preventDefault() {}}); await flush();
  input(ui).value = 'Próxima dúvida'; await input(ui).emit('input'); await close(ui); await open(ui);
  assert.equal(input(ui).value, 'Próxima dúvida');
  ui.visit('home'); assert.equal(drawer(ui).hidden, true); assert.equal(host(ui).textContent, '');
  ui.visit('tutoria'); await open(ui); assert.match(host(ui).textContent, /Minha dúvida de estudo/);
  assert.equal(input(ui).value, 'Próxima dúvida');
  assert.equal(ui.get('#tutoria-assistant-expand'), undefined);
});

test('exam route and mode block opening and stale message actions; leaving Exames restores the launcher', async () => {
  const ui = await page(); ui.visit('tutoria'); await open(ui); const oldHint = button(ui, 'Me dê uma pista');
  ui.visit('exams'); await flush(); const calls = ui.calls.length;
  assert.equal(drawer(ui).hidden, true); assert.equal(ui.get('#tutoria-assistant-rail').hidden, true);
  assert.equal(ui.window.ConfIATutoriaAssistant.open(), false); await oldHint.click(); await flush();
  assert.equal(host(ui).textContent, ''); assert.equal(ui.calls.length, calls);
  // Even an inconsistent route cannot bypass the EXAM mode guard.
  const shell = ui.window.ConfIAShell;
  ui.window.ConfIAShell = { current:{profile:'student',view:'tutoria'} };
  assert.equal(ui.window.ConfIATutoriaAssistant.open(), false);
  ui.window.ConfIAShell = shell; ui.visit('tutoria'); assert.equal(ui.get('#tutoria-assistant-rail').hidden, false);
});

test('legacy institutional submission mode, teacher, management and unresolved authentication cannot open pedagogy', async () => {
  const ui = await page(); await ui.start('submission');
  assert.equal(ui.window.ConfIATutoriaAssistant.open(), false);
  const fresh = await page(); fresh.visit('tutoria');
  for (const profile of ['teacher','management']) {
    fresh.window.ConfIAShell.navigate(profile, 'home');
    assert.equal(fresh.window.ConfIATutoriaAssistant.open(), false);
    assert.equal(fresh.get('#tutoria-assistant-rail').hidden, true);
  }
  fresh.visit('tutoria'); fresh.document.body.classList = { contains: name => name === 'auth-enabled' };
  fresh.window.ConfIATutoriaAssistant.sync();
  assert.equal(fresh.window.ConfIATutoriaAssistant.open(), false);
  fresh.window.ConfIAAuthProfile = 'teacher'; assert.equal(fresh.window.ConfIATutoriaAssistant.open(), false);
  fresh.window.ConfIAAuthProfile = 'student'; assert.equal(fresh.window.ConfIATutoriaAssistant.open(), true);
});

test('launcher is restricted to existing TutorIA views and never renders outside them', async () => {
  const ui = await page();
  for (const view of ['tutoria','tutoria/content','tutoria/questions','tutoria/practice','tutoria/feedback','tutoria/trails','tutoria/progress','tutoria/attempts']) {
    ui.visit(view);
    assert.equal(ui.get('#tutoria-assistant-rail').hidden, false, view);
    await open(ui); assert.equal(drawer(ui).hidden, false, view); await close(ui);
  }
  for (const view of ['home','submissions','exams','resolve','feedback']) {
    ui.visit(view); await flush();
    assert.equal(ui.get('#tutoria-assistant-rail').hidden, true, view);
    assert.equal(drawer(ui).hidden, true, view);
    assert.equal(ui.window.ConfIATutoriaAssistant.open(), false, view);
  }
});

test('bank context follows only real catalog theme filters, with no invented topic when absent', async () => {
  const ui = await page(undefined, {catalog:[
    {problem_id:'A',title:'A',statement:'Enunciado A',examples:[],theme:'Funções'},
    {problem_id:'B',title:'B',statement:'Enunciado B',examples:[],theme:'Geometria'},
  ]});
  ui.visit('tutoria/questions'); await open(ui);
  assert.match(host(ui).textContent, /Você está explorando o banco de questões/);
  const filter = descendants(ui.get('#tutoria-content')).find(node => node.tag === 'select' && node.name === 'theme');
  filter.value = 'Funções'; await filter.emit('change');
  assert.match(host(ui).textContent, /Você está explorando questões de Funções/);
  filter.value = 'Geometria'; await filter.emit('change');
  assert.match(host(ui).textContent, /Você está explorando questões de Geometria/);
  assert.doesNotMatch(host(ui).textContent, /Funções/);
  const missing = await page(); missing.visit('tutoria/questions'); await open(missing);
  assert.match(host(missing).textContent, /Você está explorando o banco de questões/);
});
