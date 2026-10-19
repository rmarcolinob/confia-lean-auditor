const test = require('node:test');
const assert = require('node:assert/strict');
const { page } = require('./workspace-dom.cjs');
const { descendants, flush } = require('./ui-dom.cjs');
const host = ui => ui.get(ui.get('#tutoria-assistant-drawer').hidden ? '#tutoria-content' : '#tutoria-assistant-content');
const nodes = ui => descendants(host(ui));
const button = (ui, label) => nodes(ui).find(node => node.tag === 'button' && node.textContent === label);
const byId = (ui, id) => nodes(ui).find(node => node.id === id);
const log = ui => nodes(ui).find(node => node.getAttribute('role') === 'log');
const history = ui => log(ui).children.map(node => node.textContent);
const forbidden = /Lean|Mathlib|AuditRun|TeacherDecision|claims|verificado|refutado|formalmente provado|pontuação ConfIA/i;
async function type(ui, text) {
  const input = nodes(ui).find(node => node.tag === 'textarea'); input.value = text; await input.emit('input'); return input;
}
async function send(ui, text) {
  const input = await type(ui, text);
  await input.emit('keydown', { key: 'Enter', preventDefault() {} }); await flush();
}

test('assistant is a drawer tool, without a card, tab or separate chat page', async () => {
  const ui = await page(); ui.visit('tutoria');
  assert(!nodes(ui).some(node => node.dataset.module === 'chat'));
  assert(!descendants(ui.get('#tutoria-navigation')).some(node => node.textContent === 'Assistente'));
  await ui.get('#tutoria-assistant-toggle').click();
  assert.equal(ui.location.hash, '#student/tutoria');
  assert.equal(ui.get('#tutoria-assistant-drawer').hidden, false);
  assert.equal(log(ui).getAttribute('aria-live'), 'polite');
  assert.equal(log(ui).getAttribute('aria-relevant'), 'additions');
  assert.equal(log(ui).tabIndex, 0);
  assert.equal(history(ui).length, 1); assert.match(history(ui)[0], /Como posso ajudar/);
  assert.equal(button(ui, 'Enviar').disabled, true);
  assert.doesNotMatch(host(ui).textContent, forbidden);
  ui.location.hash = '#student/tutoria/chat'; await ui.events.hashchange();
  assert.equal(ui.location.hash, '#student/tutoria');
  assert.equal(ui.get('#page-title').textContent, 'TutorIA');
});

test('all four quick prompts append a student message and a short response; hints progress', async () => {
  const ui = await page(); ui.visit('tutoria'); await ui.get('#tutoria-assistant-toggle').click();
  const originalCalls = ui.calls.length;
  for (const label of ['Explique de outro jeito', 'Me dê uma pista', 'Como começo?', 'Meu raciocínio faz sentido?']) {
    const before = history(ui).length;
    await button(ui, label).click(); await flush();
    assert.equal(history(ui).length, before + 2);
    assert.equal(log(ui).children.at(-2).dataset.origin, 'REAL');
    assert.match(history(ui).at(-2), new RegExp(label.replace('?', '\\?')));
    assert.equal(log(ui).children.at(-1).dataset.origin, 'DEMO');
    assert(history(ui).at(-1).length < 400);
    assert.match(history(ui).at(-1), /\?/);
  }
  await button(ui, 'Me dê uma pista').click(); await flush();
  assert.match(history(ui).at(-1), /exemplo pequeno/);
  assert.equal(ui.calls.length, originalCalls);
});

test('typed messages stay literal, render math and cannot become executable HTML or institutional output', async () => {
  const ui = await page(); ui.visit('tutoria'); await ui.get('#tutoria-assistant-toggle').click(); const calls = ui.calls.length;
  await send(ui, String.raw`Minha ideia: \(2+2=5\)
<img src=x onerror=alert(1)>`);
  assert.match(history(ui).at(-2), /rendered:2\+2=5.*<img src=x onerror=alert\(1\)>/s);
  assert.equal(nodes(ui).filter(node => node.tag === 'img').length, 0);
  assert.equal(ui.calls.length, calls);
  assert.equal(ui.get('#student-feedback').hidden, true);
  await send(ui, 'Não entendi o coeficiente angular.');
  assert.match(history(ui).at(-1), /coeficiente angular.*aumenta uma unidade/);
  assert.doesNotMatch(history(ui).at(-1), forbidden);
});

test('composer rejects empty/oversize input and respects multiline editing and composition', async () => {
  const ui = await page(); ui.visit('tutoria'); await ui.get('#tutoria-assistant-toggle').click(); const initial = history(ui).length;
  await send(ui, '   '); assert.equal(history(ui).length, initial);
  await send(ui, 'a'.repeat(2001)); assert.equal(history(ui).length, initial);
  assert.match(byId(ui, 'tutoria-drawer-chat-message-status').textContent, /2000 caracteres/);
  const input = await type(ui, 'Uma dúvida');
  await input.emit('keydown', { key:'Enter', shiftKey:true, preventDefault() { throw Error('Must preserve newline'); } });
  await input.emit('keydown', { key:'Enter', isComposing:true, preventDefault() { throw Error('Must preserve composition'); } });
  assert.equal(history(ui).length, initial);
  await nodes(ui).find(node => node.tag === 'form').emit('submit', {preventDefault() {}}); await flush();
  assert.equal(history(ui).length, initial + 2);
});

test('session history and draft survive navigation; reset and reload are explicit', async () => {
  const ui = await page(); ui.visit('tutoria'); await ui.get('#tutoria-assistant-toggle').click();
  await send(ui, 'Quero aprender com uma tabela.'); await type(ui, 'Minha próxima pergunta');
  ui.visit('tutoria/questions'); assert.doesNotMatch(log(ui).textContent, /Quero aprender/);
  ui.visit('tutoria'); assert.match(log(ui).textContent, /Quero aprender com uma tabela/);
  assert.equal(byId(ui, 'tutoria-drawer-chat-input').value, 'Minha próxima pergunta');
  await button(ui, 'Nova conversa').click(); assert.equal(history(ui).length, 1);
  assert.equal(byId(ui, 'tutoria-drawer-chat-input').value, '');
  const fresh = await page(); fresh.visit('tutoria'); await fresh.get('#tutoria-assistant-toggle').click(); assert.equal(history(fresh).length, 1);
});

test('practice entry carries only the selected question and resumes the identical notebook and draft', async () => {
  const ui = await page(); ui.visit('tutoria/practice'); ui.window.ConfIAWorkspace.practiceProblem('B');
  ui.notebook({ problem_id:'B', draft_id:'draft:B' });
  await ui.write('Meu rascunho preservado');
  const frame = ui.frame, commandCount = ui.commands.length, calls = ui.calls.length;
  await ui.get('#tutoria-assistant-toggle').click();
  assert.equal(ui.location.hash, '#student/tutoria/practice');
  assert.equal(ui.get('#tutoria-assistant-drawer').hidden, false);
  assert.match(host(ui).textContent, /Contexto desta sessão.*B · Questão B.*Você está estudando esta questão/);
  assert.doesNotMatch(ui.get('#tutoria-content').textContent, /Meu rascunho preservado|Porcentagem|15%|Questão A/);
  assert.equal(history(ui).length, 1);
  await button(ui, 'Me dê uma pista').click(); await flush();
  assert.match(history(ui).at(-1), /informação do enunciado/);
  await ui.get('#tutoria-assistant-close').click();
  assert.equal(ui.frame, frame); assert.equal(ui.commands.length, commandCount);
  assert.equal(ui.get('#solution-input').value, 'Meu rascunho preservado');
  assert.equal(ui.calls.length, calls);
  assert.equal(ui.window.ConfIAWorkspace.experience, 'TUTOR');
});

test('content entry uses the selected lesson context instead of an unrelated question', async () => {
  const ui = await page(); ui.visit('tutoria/content');
  let card = nodes(ui).find(node => node.tag === 'article' && node.textContent.startsWith('Geometria'));
  await descendants(card).find(node => node.tag === 'button').click();
  card = nodes(ui).find(node => node.tag === 'article' && node.textContent.startsWith('Ângulos'));
  await descendants(card).find(node => node.tag === 'button').click();
  await ui.get('#tutoria-assistant-toggle').click();
  assert.match(host(ui).textContent, /Contexto ilustrativo.*Geometria.*Ângulos/);
  await button(ui, 'Explique de outro jeito').click(); await flush();
  assert.doesNotMatch(history(ui).at(-1), /y=2x|Funções|Questão/);
});

test('attempt context comes from feedback on opening the drawer and remains faithful without an automatic correctness claim', async () => {
  const ui = await page(); ui.visit('tutoria/practice'); ui.window.ConfIAWorkspace.practiceProblem('A'); ui.notebook();
  await ui.get('#typed-response').click(); await ui.write(String.raw`Meu passo: \(2+2=5\)`);
  await ui.get('#audit-button').click(); await flush(); ui.visit('tutoria/feedback');
  await ui.get('#tutoria-assistant-toggle').click();
  assert.match(host(ui).textContent, /Ver tentativa compartilhada.*rendered:2\+2=5/);
  await send(ui, 'Esse passo está certo?');
  assert.match(history(ui).at(-1), /Qual operação foi aplicada/);
  assert.doesNotMatch(history(ui).at(-1), /coerente|correto|nota/);
  assert(!ui.calls.some(call => /audit|submissions|management/.test(call.url)));
});

test('Exames never offers the chat shortcut or inherits chat content; pending demo replies cannot reopen it', async () => {
  const ui = await page(); ui.visit('tutoria'); await ui.get('#tutoria-assistant-toggle').click();
  const input = await type(ui, 'Me dê uma pista');
  const pending = input.emit('keydown', {key:'Enter',preventDefault() {}});
  ui.visit('exams'); await pending; await flush();
  assert.equal(ui.get('#tutoria-root').hidden, true); assert.equal(ui.get('#tutoria-content').textContent, '');
  assert.equal(ui.get('#tutoria-assistant-rail').hidden, true);
  assert.equal(ui.window.ConfIATutoriaAssistant.open(), false);
  assert.equal(ui.location.hash, '#student/exams');
  assert(!ui.calls.some(call => /audit|submissions|teacher-decision|management/.test(call.url)));
  assert(!ui.calls.some(call => /^https?:/.test(call.url)));
  ui.visit('tutoria/progress');
  assert.deepEqual(nodes(ui).filter(node => node.className === 'tutoria-metric-value').map(node => node.textContent), ['3', '8', '5']);
});

test('context boundary excludes unrelated institutional records', async () => {
  const ui = await page(); ui.visit('tutoria/practice'); ui.window.ConfIAWorkspace.practiceProblem('A'); ui.notebook();
  ui.window.ConfIAWorkspace.studyContext = () => ({kind:'question',origin:'REAL',problemId:'A',problemTitle:'Questão A',
    student_id:'PRIVATE_STUDENT',auditRun:'PRIVATE_AUDIT',claims:'PRIVATE_CLAIMS',submission:'PRIVATE_SUBMISSION'});
  await ui.get('#tutoria-assistant-toggle').click();
  assert.doesNotMatch(host(ui).textContent, /PRIVATE_/);
  assert.match(log(ui).textContent, /Você está trabalhando na questão A/);
});
