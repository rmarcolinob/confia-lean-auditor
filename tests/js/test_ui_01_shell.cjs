const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { element, descendants, flush } = require("./ui-dom.cjs");
const { summary, history: transcriptionHistory, revision } = require("./teacher-dom.cjs");
const staticDir = path.join(__dirname, "../../app/confia_lean_auditor/static");
const html = fs.readFileSync(path.join(staticDir, "index.html"), "utf8");
const submissionId = "sub_" + "a".repeat(32);
const record = { submission_id: submissionId, problem_id: "ITA2025Q1", snapshot_id: "snapshot:test",
  received_at: "2026-10-03T12:00:00Z", status: "RECEIVED", source: "tablet", capture_schema_version: "1.0",
  page_images: [{ filename: "page_1.png", page_index: 0 }] };
async function page({ hash = "", search = "", records = [], authRole = null, teacherReview = false,
  contextSchools = [{ school_id: 'school-a', name: 'Escola A' }],
  classroomsBySchool = { 'school-a': [{ classroom_id: 'class-a', school_id: 'school-a', name: 'Turma A' }] },
  recordsByClass = null } = {}) {
  const nodes = new Map(), links = [], menus = [], tabs = [], modes = [], calls = [], events = {}, store = new Map();
  let accepted = false;
  const acceptance = { submission_id: submissionId, transcription_id: summary.transcription.transcription_id,
    revision_number: 1, acceptance_id: 'acc_' + 'c'.repeat(32), accepted_at: revision.created_at,
    accepted_revision_sha256: 'd'.repeat(64) };
  function create(tag) {
    const n = element(tag);
    n.isConnected = true;
    n.remove = () => {
      n.isConnected = false;
      if (n.attributes.class === 'profile-switch') for (const tab of tabs) tab.isConnected = false;
    };
    n.removeAttribute = key => { delete n.attributes[key]; };
    n.getAttribute = key => n.attributes[key] ?? null;
    n.closest = () => n.inNav ? {} : null;
    return n;
  }
  let inNav = false;
  for (const match of html.matchAll(/<(\w+)([^>]*?)>/g)) {
    const [, tag, raw] = match;
    const attrs = Object.fromEntries([...raw.matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1], m[2]]));
    const n = create(tag);
    n.attributes = attrs; n.id = attrs.id; n.hidden = /\bhidden\b/.test(raw);
    if (attrs.id) nodes.set(`#${attrs.id}`, n);
    if (attrs.id === "profile-navigation") inNav = true;
    if (tag === "p" && attrs.class === "sidebar-note") inNav = false;
    if (/\bdata-shell-link\b/.test(raw)) { n.inNav = inNav; links.push(n); }
    if (attrs['data-profile-menu']) { n.dataset.profileMenu = attrs['data-profile-menu']; menus.push(n); }
    if (attrs['data-tab-target']) { n.dataset.tabTarget = attrs['data-tab-target']; tabs.push(n); nodes.set(`[data-tab-target="${n.dataset.tabTarget}"]`, n); }
    if (attrs['data-student-mode']) { n.dataset.studentMode = attrs['data-student-mode']; modes.push(n); }
    if (attrs.class) nodes.set(`.${attrs.class}`, n);
  }
  const get = selector => nodes.get(selector);
  const panels = ['student-area', 'teacher-area', 'management-area'].map(id => get(`#${id}`));
  const location = { hash, search, replace(url) { this.redirected = url; } };
  const bodyClasses = new Set(authRole ? ['auth-enabled', 'auth-loading'] : []);
  const body = { classList: { contains: value => bodyClasses.has(value), remove: value => bodyClasses.delete(value) } };
  const history = Object.fromEntries(['pushState', 'replaceState'].map(method => [method, (_a, _b, url) => { location.hash = url; }]));
  const window = { addEventListener: (name, handler) => { events[name] = handler; } };
  const context = vm.createContext({ document: { body,
    querySelector: get, createElement: create,
    querySelectorAll: selector => ({ '[data-tab-target]': tabs, '.tab-panel': panels, '[data-student-mode]': modes,
      '[data-shell-link]': links, '[data-profile-menu]': menus })[selector] || [],
  }, location, history, window, URLSearchParams, console,
    katex: { render(latex, target) { target.textContent = `rendered:${latex}`; } },
    localStorage: { getItem: key => store.get(key), setItem: (key, value) => store.set(key, value) },
    fetch: async (url, options) => {
      calls.push({ url, options });
      assert.notEqual(url, '/audit', 'Shell navigation must never trigger an audit');
      let data;
      if (url === '/auth/me') data = { user_id: 'usr_test', display_name: 'Pessoa Demo', role: authRole };
      else if (url === '/institutional/me/context') data = { academic_year: 2026,
        schools: contextSchools, classrooms: Object.values(classroomsBySchool).flat() };
      else if (url.startsWith('/institutional/schools/') && url.endsWith('/classrooms'))
        data = classroomsBySchool[url.split('/')[3]] || [];
      else if (url === '/institutional/classrooms/class-a/students') data = [{ user_id: 'usr_student', display_name: 'Aluno da turma A' }];
      else if (teacherReview && url.endsWith('/accept') && options?.method === 'POST') {
        accepted = true;
        data = { revision: { ...revision, status: 'ACCEPTED' }, acceptance };
      }
      else if (url === '/problems') data = [{ problem_id: 'ITA2025Q1', title: 'Questão de teste', statement: 'Enunciado', examples: [{ key: 'correct', label: 'Exemplo' }] }];
      else if (url === '/submissions' || url.startsWith('/submissions?'))
        data = recordsByClass ? (recordsByClass[new URLSearchParams(url.split('?')[1] || '').get('classroom_id')] || []) : records;
      else if (teacherReview && url.endsWith('/transcriptions')) data = [{ ...summary,
        latest_revision: { ...revision, status: accepted ? 'ACCEPTED' : 'NEEDS_REVIEW' } }];
      else if (teacherReview && url.startsWith('/transcriptions/')) data = { ...transcriptionHistory,
        revisions: [{ ...revision, status: accepted ? 'ACCEPTED' : 'NEEDS_REVIEW' }],
        acceptances: accepted ? [acceptance] : [] };
      else if (url === '/submissions/recognition-providers' || /\/(transcriptions|audits)$/.test(url)) data = [];
      else data = { submission: record, integrity: [{ filename: 'snapshot.json', matches: true }, { filename: 'page_1.png', matches: true }] };
      return { ok: true, json: async () => data };
    },
  });
  for (const file of ['recognition-view.js', 'app.js', 'submissions/teacher.js', 'shell.js']) vm.runInContext(fs.readFileSync(path.join(staticDir, file), 'utf8'), context);
  await flush();
  const visit = async href => {
    const link = links.find(link => link.inNav && link.getAttribute('href') === href);
    assert(link, `missing menu link ${href}`);
    await link.emit('click', { button: 0, preventDefault() {} }); await flush();
  };
  return { get, links, menus, tabs, modes, visit, location, window, events, calls, store, bodyClasses };
}

test('authenticated shell locks navigation to the server role and exposes logout', async () => {
  const student = await page({ hash: '#teacher/submissions', authRole: 'STUDENT' });
  assert.equal(student.location.hash, '#student/home');
  assert.equal(student.get('#auth-identity').textContent, 'Pessoa Demo / Aluno');
  assert.equal(student.get('#student-home-name').textContent, 'Pessoa Demo');
  assert.equal(student.get('#student-institutional-context').textContent, 'Escola: Escola A · Turma: Turma A');
  assert.equal(student.get('#auth-logout').hidden, false);
  assert.equal(student.get('#active-profile').textContent, 'Pessoa Demo / Aluno');
  assert.deepEqual(student.menus.filter(menu => menu.isConnected).map(menu => menu.dataset.profileMenu), ['student']);
  assert(student.links.some(link => link.isConnected && /^#student\//.test(link.getAttribute('href'))));
  assert(student.links.filter(link => link.isConnected).every(link => !/^#(teacher|management)\//.test(link.getAttribute('href'))));
  assert.equal(student.get('.profile-switch').isConnected, false);
  assert(student.tabs.every(tab => !tab.isConnected));
  assert.equal(student.get('#demo-profile-label').isConnected, false);
  assert.equal(student.get('.sidebar-note').isConnected, false);
  assert(student.calls.some(call => call.url === '/auth/me'));
  student.location.hash = '#student/resolve'; await student.events.hashchange();
  assert.equal(student.location.hash, '#student/tutoria');
  student.location.hash = '#management/overview'; await student.events.hashchange();
  assert.equal(student.location.hash, '#student/home');
  assert.equal(student.window.ConfIAShell.navigate('teacher', 'submissions'), true);
  assert.equal(student.location.hash, '#student/home');
  assert.equal(student.get('#teacher-area').hidden, true);
  await student.get('#auth-logout').click();
  assert.equal(student.calls.at(-1).url, '/auth/logout');
  assert.equal(student.location.redirected, '/');

  const teacher = await page({ hash: '#teacher/submissions', authRole: 'TEACHER' });
  assert.equal(teacher.location.hash, '#teacher/submissions');
  assert.deepEqual(teacher.menus.filter(menu => menu.isConnected).map(menu => menu.dataset.profileMenu), ['teacher']);
  assert(teacher.links.some(link => link.isConnected && /^#teacher\//.test(link.getAttribute('href'))));
  assert(teacher.links.filter(link => link.isConnected).every(link => !/^#(student|management)\//.test(link.getAttribute('href'))));
  assert.equal(teacher.get('.profile-switch').isConnected, false);
  assert(teacher.tabs.every(tab => !tab.isConnected));
  teacher.location.hash = '#student/resolve'; await teacher.events.hashchange();
  assert.equal(teacher.location.hash, '#teacher/home');
  const manager = await page({ authRole: 'SCHOOL_MANAGER' });
  assert.equal(manager.location.hash, '#management/overview');
  assert.deepEqual(manager.menus.filter(menu => menu.isConnected).map(menu => menu.dataset.profileMenu), ['management']);
  assert(manager.links.some(link => link.isConnected && /^#management\//.test(link.getAttribute('href'))));
  assert(manager.links.filter(link => link.isConnected).every(link => !/^#(student|teacher)\//.test(link.getAttribute('href'))));
  assert.equal(manager.get('.profile-switch').isConnected, false);
  assert(manager.tabs.every(tab => !tab.isConnected));
  manager.location.hash = '#teacher/analysis'; await manager.events.hashchange();
  assert.equal(manager.location.hash, '#management/home');
  const network = await page({ authRole: 'NETWORK_MANAGER' });
  assert.equal(network.location.hash, '#management/overview');
  assert.deepEqual(network.menus.filter(menu => menu.isConnected).map(menu => menu.dataset.profileMenu), ['management']);
  assert(network.links.filter(link => link.isConnected).every(link => !/^#(student|teacher)\//.test(link.getAttribute('href'))));
});

test('authenticated teacher opens the original and recognized transcription, then enables analysis after acceptance', async () => {
  const ui = await page({ hash: '#teacher/submissions', authRole: 'TEACHER', records: [record], teacherReview: true });
  await ui.get('#manuscript-list').children[0].click();
  let tree = descendants(ui.get('#manuscript-detail'));
  const workspace = tree.find(node => node.className === 'transcription-workspace');
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.deepEqual(workspace.children.map(node => node.className), ['original-manuscript-panel', 'transcription-panel']);
  assert(tree.some(node => node.tag === 'img' && node.src === `/submissions/${submissionId}/pages/0`));
  assert(tree.some(node => node.textContent === 'rendered:2 + 2 = 5'));
  assert.equal(tree.find(node => node.tag === 'button' && node.textContent === 'Executar Análise ConfIA').disabled, true);
  assert(ui.calls.some(call => call.url === '/submissions/recognition-providers'));
  await tree.find(node => node.tag === 'button' && node.textContent === 'Aceitar como fiel ao manuscrito').click();
  tree = descendants(ui.get('#manuscript-detail'));
  assert.equal(tree.find(node => node.tag === 'button' && node.textContent === 'Executar Análise ConfIA').disabled, false);
  assert(tree.some(node => node.className === 'transcription-history'));
});

test('teacher changes school and classroom without leaving the previous queue or detail visible', async () => {
  const other = { ...record, submission_id: 'sub_' + 'b'.repeat(32) };
  const ui = await page({ hash: '#teacher/submissions', authRole: 'TEACHER',
    contextSchools: [{ school_id: 'school-a', name: 'Escola A' }, { school_id: 'school-b', name: 'Escola B' }],
    classroomsBySchool: {
      'school-a': [{ classroom_id: 'class-a', school_id: 'school-a', name: 'Turma A' }],
      'school-b': [{ classroom_id: 'class-b', school_id: 'school-b', name: 'Turma B' }],
    }, recordsByClass: { 'class-a': [record], 'class-b': [other] } });
  assert.equal(ui.get('#teacher-school-select').value, '');
  ui.get('#teacher-school-select').value = 'school-a';
  await ui.get('#teacher-school-select').emit('change'); await flush();
  assert.equal(ui.get('#teacher-classroom-select').value, 'class-a');
  assert.equal(ui.get('#manuscript-list').children.length, 1);
  ui.get('#teacher-school-select').value = 'school-b';
  const changing = ui.get('#teacher-school-select').emit('change');
  assert.equal(ui.get('#manuscript-list').children.length, 0);
  assert.equal(ui.get('#manuscript-detail').hidden, true);
  await changing; await flush();
  assert.equal(ui.get('#teacher-classroom-select').value, 'class-b');
  assert.equal(ui.get('#manuscript-list').children.length, 1);
  assert(ui.calls.some(call => call.url === '/submissions?school_id=school-b&classroom_id=class-b'));
});

test('teacher Alunos view lists only the selected classroom and hides manuscript detail', async () => {
  const ui = await page({ hash: '#teacher/submissions', authRole: 'TEACHER', records: [record] });
  await ui.get('#manuscript-list').children[0].click();
  await ui.visit('#teacher/students'); await flush();
  assert.equal(ui.get('#teacher-students-panel').hidden, false);
  assert.equal(ui.get('#manuscript-detail').hidden, true);
  assert.equal(ui.get('#manuscript-queue').hidden, true);
  assert.equal(ui.get('#teacher-queue-header').hidden, true);
  assert.match(ui.get('#teacher-students-panel').textContent, /Aluno da turma A/);
  assert(ui.calls.some(call => call.url === '/institutional/classrooms/class-a/students'));
});

test('initial shell explicitly selects Aluno and shows only its home and menu', async () => {
  const ui = await page();
  assert.equal(ui.location.hash, '#student/home');
  assert.equal(ui.get('#active-profile').textContent, 'Perfil de demonstração: Aluno');
  assert.equal(ui.get('#student-home').hidden, false);
  assert.equal(ui.get('#student-workspace').hidden, true);
  assert.equal(ui.get('#teacher-area').hidden, true);
  assert.equal(ui.tabs[0].getAttribute('aria-pressed'), 'true');
  assert.equal(ui.menus.filter(m => !m.hidden).length, 1);
});

test('every existing destination stays reachable, and profile/current-page semantics follow navigation', async () => {
  const ui = await page();
  const routes = ['#student/tutoria', '#student/exams', '#student/submissions', '#teacher/home', '#teacher/submissions',
    '#teacher/transcriptions', '#teacher/analysis', '#management/home', '#management/overview'];
  for (const route of routes) {
    await ui.visit(route);
    assert.equal(ui.location.hash, route);
    const active = ui.links.filter(link => link.getAttribute('aria-current') === 'page');
    assert.equal(active.length, 1); assert.equal(active[0].getAttribute('href'), route);
    assert.equal(ui.tabs.filter(tab => tab.getAttribute('aria-pressed') === 'true').length, 1);
    assert.equal(ui.get('#page-title').focused, true);
  }
  assert.equal(ui.get('#management-overview').hidden, false);
  assert.match(ui.get('#page-description').textContent, /Dados agregados/);
});

test('teacher routes converge on the same solution and keep the local text demonstration separate', async () => {
  const ui = await page({ records: [record] });
  await ui.visit('#teacher/submissions');
  await ui.get('#manuscript-list').children[0].click();
  const originalDetail = ui.get('#manuscript-detail').children;
  await ui.visit('#teacher/transcriptions');
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.equal(ui.get('#manuscript-detail').children, originalDetail);
  assert(descendants(ui.get('#manuscript-detail')).some(n => n.className === 'transcription-workspace'));
  await ui.visit('#teacher/analysis');
  assert.equal(ui.get('#manuscript-inbox').hidden, false);
  assert.equal(ui.get('#teacher-text-prototype').hidden, true);
  assert.equal(ui.get('#manuscript-detail').children, originalDetail);
  await ui.get('#show-text-prototype').click(); await flush();
  assert.equal(ui.location.hash, '#teacher/text');
  assert.equal(ui.get('#manuscript-inbox').hidden, true);
  assert.equal(ui.get('#teacher-text-prototype').hidden, false);
});

test('UI-P0 dirty editor protects profile switches, shell links and browser history', async () => {
  const ui = await page({ records: [record] });
  await ui.visit('#teacher/transcriptions');
  await ui.get('#manuscript-list').children[0].click();
  const editor = descendants(ui.get('#manuscript-detail')).find(n => n.className === 'transcription-segment');
  editor.controls.text.value = 'Leitura ainda não salva'; await editor.controls.text.emit('input');
  await ui.tabs[0].click();
  assert.equal(ui.get('#teacher-area').hidden, false);
  assert.equal(ui.location.hash, '#teacher/transcriptions');
  await ui.visit('#teacher/analysis');
  assert.equal(ui.get('#teacher-text-prototype').hidden, true);
  assert.match(ui.get('#manuscript-message').textContent, /Alterações não salvas/);
  ui.location.hash = '#management/overview'; await ui.events.hashchange();
  assert.equal(ui.location.hash, '#teacher/transcriptions');
  assert.equal(editor.controls.text.value, 'Leitura ainda não salva');
  const discard = descendants(ui.get('#manuscript-detail')).find(n => n.tag === 'button' && n.textContent === 'Descartar alterações não salvas');
  await discard.click(); await ui.visit('#teacher/analysis');
  assert.equal(ui.location.hash, '#teacher/analysis');
});

test('Envios exposes session receipts and no legacy local submission editor', async () => {
  const ui = await page(); await ui.visit('#student/submissions');
  assert.equal(ui.get('#student-session-envios').hidden, false);
  assert.equal(ui.get('#student-workspace').hidden, true);
  assert.equal(ui.modes.length, 0);
  assert.equal(ui.calls.some(call => call.options?.method === 'POST'), false);
  ui.window.ConfIAShell.navigate('student', 'feedback');
  assert.equal(ui.get('#student-feedback').hidden, false);
  assert.equal(ui.get('#student-workspace').hidden, true);
});

test('capture return query, deep links, invalid links and skip link preserve consistent state', async () => {
  const ui = await page({ search: '?area=teacher' });
  assert.equal(ui.location.hash, '#teacher/submissions');
  assert.equal(ui.get('#manuscript-inbox').hidden, false);
  const direct = await page({ hash: '#management/overview' });
  assert.equal(direct.get('#management-overview').hidden, false);
  const invalid = await page({ hash: '#teacher/classes' });
  assert.equal(invalid.location.hash, '#student/home');
  ui.location.hash = '#app-root'; await ui.events.hashchange();
  assert.equal(ui.location.hash, '#app-root'); assert.equal(ui.get('#teacher-area').hidden, false);
});
