const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, flush } = require('./ui-dom.cjs');
const staticDir = path.join(__dirname, '../../app/confia_lean_auditor/static');
const html = fs.readFileSync(path.join(staticDir, 'index.html'), 'utf8');
const catalog = ['A', 'B'].map(id => ({ problem_id: id, title: `Questão ${id}`, statement: `Enunciado ${id}`, examples: [{key:'example',label:'Exemplo'}] }));
async function page(transport = async () => ({ ok: true, json: async () => ({ problem_id: 'A', pedagogical_report: { summary: 'Feedback A' } }) }), options = {}) {
  const nodes = new Map(), events = {}, links = [], menus = [], tabs = [], calls = [], commands = [];
  const create = tag => {
    const node = element(tag);
    node.getAttribute = key => node.attributes[key] ?? null;
    node.removeAttribute = key => { delete node.attributes[key]; };
    node.closest = () => node.inNav ? {} : null;
    return node;
  };
  let inNav = false;
  for (const match of html.matchAll(/<(\w+)([^>]*?)>/g)) {
    const [,tag,raw] = match;
    const attrs = Object.fromEntries([...raw.matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1],m[2]]));
    const n = create(tag); n.attributes = attrs; n.id = attrs.id; n.hidden = /\bhidden\b/.test(raw);
    if (tag === 'details') n.open = /\bopen\b/.test(raw);
    if (attrs.id) nodes.set(`#${attrs.id}`, n);
    if (attrs.id === 'profile-navigation') inNav = true;
    if (attrs.class === 'sidebar-note') inNav = false;
    if (/\bdata-shell-link\b/.test(raw)) { n.inNav = inNav; links.push(n); }
    if (attrs['data-profile-menu']) { n.dataset.profileMenu = attrs['data-profile-menu']; menus.push(n); }
    if (attrs['data-tab-target']) { n.dataset.tabTarget = attrs['data-tab-target']; tabs.push(n); }
    if (attrs.class) nodes.set(`.${attrs.class}`, n);
  }
  const get = selector => nodes.get(selector);
  const frame = get('#resolution-notebook');
  frame.style = {};
  frame.contentWindow = { postMessage: (message, origin) => commands.push({message,origin}) };
  const window = { addEventListener(name, callback) { events[name] = callback; }, ConfIATeacher: { canLeave: () => true, showText() {}, showView() {} } };
  const location = { hash: '#student/resolve', search: '', origin: 'http://confia.test' };
  const document = { body: { dataset: {} }, querySelector: get, createElement: create,
    querySelectorAll: selector => ({ '[data-tab-target]': tabs, '.tab-panel': ['student-area','teacher-area','management-area'].map(id => get(`#${id}`)),
      '[data-student-mode]': [], '[data-shell-link]': links, '[data-profile-menu]': menus })[selector] || [] };
  const context = vm.createContext({ window, document, location, URLSearchParams, console,
    localStorage: { getItem: () => null, setItem() { throw Error('Workspace must never submit to localStorage'); } },
    history: { pushState: (_a,_b,url) => { location.hash=url; }, replaceState: (_a,_b,url) => { location.hash=url; } },
    ConfiaProblemMath: options.mathRenderer,
    fetch: async (url, request) => {
      calls.push({url,options:request});
      if (url === '/problems') return options.catalogResponse || { ok:true, json:async () => options.catalog || catalog };
      if (url.endsWith('registry.json')) return { ok:true, json:async () => options.registry || [] };
      if (url === '/assessments') return { ok:true, json:async () => options.exams || [] };
      return transport(url,request);
    },
  });
  context.katex = { render(latex, target) { target.textContent = `rendered:${latex}`; } };
  for (const file of ['recognition-view.js','app.js','resolution-workspace.js','shell.js']) vm.runInContext(fs.readFileSync(path.join(staticDir,file),'utf8'),context);
  await flush();
  const notebook = (values = {}) => {
    const current = window.ConfIAWorkspace;
    const message = { problem_id: get('#problem-select').value, draft_id:'draft:A', mode:current.mode, local_snapshot_id:null, ink_version:'0:1:0', question_presentation_version:1, receipt:null, ...values };
    events.message({ origin:location.origin, source:frame.contentWindow, data: { type:'confia-notebook-context',context:message } });
    return message;
  };
  return {get, frame, context, window, document, calls, commands, events, location, notebook,
    async start(mode='practice') { await get('#resolve-question').click(); await get(`#${mode}-mode`).click(); notebook(); },
    async write(value) { get('#solution-input').value=value; await get('#solution-input').emit('input'); },
    async select(value) { get('#problem-select').value=value; await get('#problem-select').emit('change'); },
    visit: (view) => window.ConfIAShell.navigate('student',view),
  };
}
module.exports = { page, catalog };
