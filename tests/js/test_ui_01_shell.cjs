const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { element, descendants, flush } = require("./ui-dom.cjs");
const staticDir = path.join(__dirname, "../../app/confia_lean_auditor/static");
const html = fs.readFileSync(path.join(staticDir, "index.html"), "utf8");
const submissionId = "sub_" + "a".repeat(32);
const record = { submission_id: submissionId, problem_id: "ITA2025Q1", snapshot_id: "snapshot:test",
  received_at: "2026-10-03T12:00:00Z", status: "RECEIVED", source: "tablet", capture_schema_version: "1.0",
  page_images: [{ filename: "page_1.png", page_index: 0 }] };
async function page({ hash = "", search = "", records = [] } = {}) {
  const nodes = new Map(), links = [], menus = [], tabs = [], modes = [], calls = [], events = {}, store = new Map();
  function create(tag) {
    const n = element(tag);
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
  const location = { hash, search };
  const history = Object.fromEntries(['pushState', 'replaceState'].map(method => [method, (_a, _b, url) => { location.hash = url; }]));
  const window = { addEventListener: (name, handler) => { events[name] = handler; } };
  const context = vm.createContext({ document: {
    querySelector: get, createElement: create,
    querySelectorAll: selector => ({ '[data-tab-target]': tabs, '.tab-panel': panels, '[data-student-mode]': modes,
      '[data-shell-link]': links, '[data-profile-menu]': menus })[selector] || [],
  }, location, history, window, URLSearchParams, console,
    localStorage: { getItem: key => store.get(key), setItem: (key, value) => store.set(key, value) },
    fetch: async (url, options) => {
      calls.push({ url, options });
      assert.notEqual(url, '/audit', 'Shell navigation must never trigger an audit');
      let data;
      if (url === '/problems') data = [{ problem_id: 'ITA2025Q1', title: 'Questão de teste', statement: 'Enunciado', examples: [{ key: 'correct', label: 'Exemplo' }] }];
      else if (url === '/submissions') data = records;
      else if (url === '/submissions/recognition-providers' || url.endsWith('/transcriptions')) data = [];
      else data = { submission: record, integrity: [{ filename: 'snapshot.json', matches: true }, { filename: 'page_1.png', matches: true }] };
      return { ok: true, json: async () => data };
    },
  });
  for (const file of ['app.js', 'submissions/teacher.js', 'shell.js']) vm.runInContext(fs.readFileSync(path.join(staticDir, file), 'utf8'), context);
  await flush();
  const visit = async href => {
    const link = links.find(link => link.inNav && link.getAttribute('href') === href);
    assert(link, `missing menu link ${href}`);
    await link.emit('click', { button: 0, preventDefault() {} }); await flush();
  };
  return { get, links, menus, tabs, modes, visit, location, window, events, calls, store };
}

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
  const routes = ['#student/resolve', '#student/feedback', '#student/submissions', '#teacher/home', '#teacher/submissions',
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
  assert.match(ui.get('#page-description').textContent, /Dados ilustrativos.*não são indicadores reais/);
});

test('teacher inbox and correction remain mutually exclusive and expose original/transcription together', async () => {
  const ui = await page({ records: [record] });
  await ui.visit('#teacher/submissions');
  await ui.get('#manuscript-list').children[0].click();
  const originalDetail = ui.get('#manuscript-detail').children;
  await ui.visit('#teacher/transcriptions');
  assert.equal(ui.get('#manuscript-detail').hidden, false);
  assert.equal(ui.get('#manuscript-detail').children, originalDetail);
  assert(descendants(ui.get('#manuscript-detail')).some(n => n.className === 'transcription-workspace'));
  await ui.visit('#teacher/analysis');
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

test('local submission mode and shell destination stay in sync without a server write', async () => {
  const ui = await page(); await ui.visit('#student/resolve');
  await ui.modes[1].click();
  assert.equal(ui.location.hash, '#student/submissions');
  assert.equal(ui.get('#student-name-field').hidden, false);
  ui.get('#student-name-input').value = 'Aluno fictício';
  ui.get('#solution-input').value = 'Solução de teste';
  await ui.get('#audit-button').click();
  assert.match(ui.get('#student-local-list').textContent, /Aluno fictício.*Registro local de demonstração/);
  assert.equal(ui.calls.some(call => call.options?.method === 'POST'), false);
  await ui.modes[0].click(); assert.equal(ui.location.hash, '#student/resolve');
  await ui.visit('#student/feedback'); assert.equal(ui.get('#result-panel').hidden, false);
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
