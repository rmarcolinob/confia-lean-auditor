const test = require('node:test');
const assert = require('node:assert/strict');
const { page } = require('./workspace-dom.cjs');
const { descendants, flush, deferred } = require('./ui-dom.cjs');
const nodes = ui => descendants(ui.get('#tutoria-content'));
const click = node => node.emit('click', { button: 0, preventDefault() {} });
const button = (ui, label) => nodes(ui).find(node => node.tag === 'button' && node.textContent === label);
const link = (ui, label) => nodes(ui).find(node => node.tag === 'a' && node.textContent === label);
const forbidden = /Lean|Mathlib|claims|AuditRun|TeacherDecision|technical_error|Pontuação|Verificações formais/;
const institutionalCall = call => /\/audit$|\/audits(?:\/|$)|\/teacher-decisions|\/assessments|\/management|\/submissions(?:$|\?)/.test(call.url);

async function practice(ui, problem = 'A', solution = '2+2=5') {
  ui.visit('tutoria/questions');
  await nodes(ui).find(node => node.getAttribute('aria-label') === `Resolver ${problem}`).click();
  ui.notebook({ problem_id: problem, draft_id: `draft:${problem}`, controls: { document_id: `draft:${problem}`,
    tutor_preview_segments: [{ page_index: 0, order: 0, kind: 'math', text: solution, latex: solution }] } });
  await ui.get('#workspace-tutor-feedback').click(); await flush();
}

test('TutorIA landing page has six modules and never opens the notebook automatically', async () => {
  const ui = await page(); ui.visit('tutoria');
  assert.equal(ui.get('#tutoria-root').hidden, false);
  assert.equal(ui.get('#student-workspace').hidden, true);
  assert.equal(ui.frame.src, undefined);
  assert.equal(ui.document.body.dataset.resolutionActive, 'false');
  const modules = nodes(ui).filter(node => node.dataset.module);
  assert.deepEqual(modules.map(node => node.dataset.module), ['content', 'questions', 'practice', 'feedback', 'trails', 'progress']);
  assert.deepEqual(modules.map(node => node.dataset.state), ['DEMO', 'REAL', 'REAL', 'DEMO', 'DEMO', 'DEMO']);
  assert.match(ui.get('#page-description').textContent, /Aprendizagem assistida em matemática/);
  assert.match(ui.get('#tutoria-content').textContent, /Funções do 1º grau.*Recomendado para você.*Atividades recentes/s);
  assert(!ui.calls.some(institutionalCall));
});

test('all six modules navigate and secondary navigation keeps TutorIA selected', async () => {
  const ui = await page();
  for (const module of ['content', 'questions', 'practice', 'feedback', 'trails', 'progress']) {
    ui.visit('tutoria');
    const card = nodes(ui).find(node => node.dataset.module === module);
    await click(descendants(card).find(node => node.tag === 'a'));
    assert.equal(ui.location.hash, `#student/tutoria/${module}`);
    assert.equal(ui.get('#student-workspace').hidden, module !== 'practice');
    assert.equal(ui.get('#tutoria-navigation').children.length, 5);
    assert.equal(ui.get('#tutoria-navigation').children.filter(node => node.getAttribute('aria-current') === 'page').length, 1);
    assert.doesNotMatch(ui.get('#tutoria-content').textContent, forbidden);
  }
});

test('library provides navigable topics, sample lessons and math without fabricating catalog questions', async () => {
  const ui = await page(); ui.visit('tutoria/content');
  for (const title of ['Álgebra', 'Funções', 'Geometria', 'Trigonometria', 'Estatística e Probabilidade']) assert(ui.get('#tutoria-content').textContent.includes(title));
  const functions = nodes(ui).find(node => node.tag === 'article' && node.textContent.startsWith('Funções'));
  await descendants(functions).find(node => node.tag === 'button').click();
  assert.match(ui.get('#tutoria-content').textContent, /Funções.*Conceito de função.*Funções do 1º grau.*Interpretação de gráficos/);
  const affine = nodes(ui).find(node => node.tag === 'article' && node.textContent.startsWith('Funções do 1º grau'));
  await descendants(affine).find(node => node.tag === 'button').click();
  assert.match(ui.get('#tutoria-content').textContent, /Visão demonstrativa.*Para compreender.*Observe este exemplo.*rendered:f\(x\)=2x\+1/s);
  await click(link(ui, 'Praticar questões do catálogo'));
  assert.equal(ui.location.hash, '#student/tutoria/questions');
  assert.match(ui.get('#tutoria-content').textContent, /Questão A.*Questão B/);
});

test('catalog search and metadata filters use only real API fields', async () => {
  const ui = await page(undefined, { catalog: [
    { problem_id: 'A', title: 'Álgebra', statement: 'Equação', origin: 'Catálogo da escola', difficulty: 'Inicial', examples: [] },
    { problem_id: 'B', title: 'Geometria', statement: 'Triângulo', examples: [] },
  ] }); ui.visit('tutoria/questions');
  const selects = nodes(ui).filter(node => node.tag === 'select');
  assert.equal(selects.find(node => node.name === 'theme').disabled, true);
  assert.equal(selects.find(node => node.name === 'grade').disabled, true);
  assert.equal(selects.find(node => node.name === 'difficulty').disabled, false);
  const origin = selects.find(node => node.name === 'origin');
  assert.deepEqual(origin.children.map(node => node.textContent), ['Todos', 'Catálogo da escola']);
  const input = nodes(ui).find(node => node.type === 'search');
  input.value = 'algebra'; await input.emit('input');
  let results = nodes(ui).find(node => node.id === 'tutoria-question-results');
  assert.match(results.textContent, /Álgebra/); assert.doesNotMatch(results.textContent, /Geometria/);
  input.value = ''; await input.emit('input'); origin.value = 'Catálogo da escola'; await origin.emit('change');
  assert.equal(results.children.length, 1);
  input.value = 'sem correspondência'; await input.emit('input'); assert.match(results.textContent, /Nenhuma questão corresponde/);
  assert.equal(ui.calls.filter(call => call.url === '/problems').length, 1);
});

test('question bank has loading, empty and failure states instead of fictional replacements', async () => {
  const pending = deferred();
  const ui = await page(undefined, { catalogResponse: pending.promise }); ui.visit('tutoria/questions');
  assert.match(ui.get('#tutoria-content').textContent, /Carregando questões/);
  pending.resolve({ ok: true, json: async () => [] }); await flush();
  assert.match(ui.get('#tutoria-content').textContent, /Nenhuma questão disponível/);
  const failed = await page(undefined, { catalogResponse: Promise.resolve({ ok: false }) }); failed.visit('tutoria/questions');
  assert.match(failed.get('#tutoria-content').textContent, /Não foi possível carregar o catálogo/);
  assert.equal(nodes(failed).filter(node => node.dataset.origin === 'REAL').length, 0);
});

test('Resolve reuses TUTOR notebook; feedback creates no audit or institutional submission', async () => {
  const ui = await page(); await practice(ui, 'B');
  assert.equal(ui.location.hash, '#student/tutoria/practice');
  assert.equal(ui.window.ConfIAWorkspace.mode, 'practice');
  assert.equal(ui.window.ConfIAWorkspace.experience, 'TUTOR');
  assert.match(ui.frame.src, /problem_id=B&mode=practice/);
  assert.equal(ui.get('#workspace-submission-actions').hidden, true);
  assert.equal(ui.get('#workspace-tutor-actions').hidden, false);
  assert(!ui.calls.some(institutionalCall));
  assert.match(ui.get('#result-panel').textContent, /Tentativa desta sessão.*2\+2=5.*Feedback demonstrativo.*sem análise automática/s);
  assert.doesNotMatch(ui.get('#result-panel').textContent, forbidden);
});

test('typed practice uses the same pedagogical path and keeps demo feedback explicit', async () => {
  const ui = await page(); ui.visit('tutoria/practice'); await ui.get('#resolve-question').click(); ui.notebook();
  await ui.get('#typed-response').click(); await ui.write('x = 3'); await ui.get('#audit-button').click(); await flush();
  assert.match(ui.get('#result-panel').textContent, /x = 3.*Feedback demonstrativo/);
  assert.doesNotMatch(ui.get('#result-panel').textContent, forbidden);
  assert.equal(ui.get('#audit-button').textContent, 'Pedir feedback');
  assert(!ui.calls.some(institutionalCall));
});

test('real session attempts replace illustrative activities and never become demo progress or management data', async () => {
  const ui = await page(); ui.visit('tutoria/attempts');
  assert.match(ui.get('#tutoria-content').textContent, /Atividades ilustrativas/);
  await practice(ui, 'A', 'MINHA_TENTATIVA <img src=x onerror=unsafe>');
  ui.visit('tutoria/attempts');
  assert.match(ui.get('#tutoria-content').textContent, /Nesta sessão.*Tentativa 1/);
  assert.doesNotMatch(ui.get('#tutoria-content').textContent, /Atividades ilustrativas/);
  await click(link(ui, 'Rever tentativa'));
  assert.match(ui.get('#tutoria-content').textContent, /MINHA_TENTATIVA/);
  assert(!nodes(ui).some(node => node.tag === 'img'));
  ui.visit('tutoria/progress');
  assert.match(ui.get('#tutoria-content').textContent, /Dados ilustrativos.*Não representam seu desempenho real/);
  assert.deepEqual(nodes(ui).filter(node => node.className === 'tutoria-metric-value').map(node => node.textContent), ['3', '8', '5']);
  assert(!ui.calls.some(institutionalCall));
  ui.window.ConfIAShell.navigate('management', 'home');
  assert.equal(ui.get('#tutoria-root').hidden, true);
  assert.equal(ui.get('#tutoria-content').textContent, '');
});

test('nested routes survive hash navigation and a return from Exames clears its binding before practice', async () => {
  const exam = { assessment: { assessment_id: 'exam-1', title: 'Avaliação', opens_at: '2026-01-01', closes_at: '2026-12-01' },
    items: [{ assessment_item_id: 'item-b', problem_id: 'B', order: 1, points: 5 }], availability: 'DISPONÍVEL', submitted_item_ids: [] };
  const ui = await page(undefined, { exams: [exam] });
  ui.location.hash = '#student/tutoria/trails'; await ui.events.hashchange();
  assert.equal(ui.location.hash, '#student/tutoria/trails'); assert.match(ui.get('#tutoria-content').textContent, /Fundamentos de Álgebra/);
  ui.visit('exams'); await flush();
  await descendants(ui.get('#student-exam-list')).find(node => node.tag === 'button').click();
  await descendants(ui.get('#student-exam-items')).find(node => node.tag === 'button').click();
  await ui.get('#resolve-question').click(); ui.notebook({ problem_id: 'B', controls: { document_id: 'draft:B' } });
  assert.equal(ui.window.ConfIAWorkspace.mode, 'submission');
  const frame = ui.frame;
  await practice(ui, 'A');
  assert.equal(ui.frame, frame);
  assert.equal(ui.window.ConfIAWorkspace.mode, 'practice');
  assert.equal(ui.window.ConfIAWorkspace.examSelected, false);
  assert.equal(ui.commands.at(-1).message.mode, 'practice');
  assert.equal(ui.commands.at(-1).message.submission_target, '/submissions');
  assert.equal(ui.get('#workspace-send-solution').disabled, true);
  ui.visit('exams'); await flush();
  assert.doesNotMatch(ui.get('#service-status').textContent, /Feedback demonstrativo/);
  assert.equal(ui.get('#student-feedback').hidden, true);
});

test('returning home preserves notebook identity without leaving the writing layout visible', async () => {
  const ui = await page(); await practice(ui);
  const frame = ui.frame;
  ui.visit('tutoria');
  assert.equal(ui.get('#student-workspace').hidden, true);
  assert.equal(ui.document.body.dataset.resolutionActive, 'false');
  ui.visit('tutoria/practice');
  assert.equal(ui.frame, frame); assert.equal(ui.window.ConfIAWorkspace.experience, 'TUTOR');
});
