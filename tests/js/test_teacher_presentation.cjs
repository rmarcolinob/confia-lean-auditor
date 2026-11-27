const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {element, descendants, flush, deferred} = require('./ui-dom.cjs');
const source = name => fs.readFileSync(`app/confia_lean_auditor/static/${name}`, 'utf8');
const summary = count => ({counts:{pending:count,inconclusive:0,finalized:0,in_progress:0},priority_cases:[],exam_progress:[]});
function mount(fetcher = async () => ({ok:true,json:async()=>summary(7)})) {
  const make = tag => {
    const e=element(tag); e.append=(...items)=>items.forEach(x=>e.appendChild(x)); e.classList.add=()=>{};
    e.querySelector=selector => selector==='.home-overview h2' ? descendants(e).find(x=>x.className==='home-overview')?.querySelector('h2') : descendants(e).find(x=>x.tag===selector);
    return e;
  };
  const nodes=Object.fromEntries(['teacher-home','teacher-modern-header','teacher-bottom-nav','teacher-home-styles','teacher-avatar','teacher-modern-logout','auth-logout','teacher-modern-session','teacher-demo-profiles'].map(id=>[id,make('div')]));
  nodes['teacher-modern-header'].append(make('details'));
  const calls=[],routes=[],exits=[],body=make('body'); let allowed=true;
  const window={location:{assign:url=>exits.push(url)},ConfIATeacher:{canLeave:()=>allowed},ConfIAShell:{navigate:(...args)=>routes.push(args)}};
  const context={window,URLSearchParams,document:{body,createElement:make,querySelector:s=>nodes[s.slice(1)]},fetch:(url,options)=>{calls.push({url,options});return fetcher(url);}};
  vm.createContext(context);
  vm.runInContext(source('tme/home.js'),context);
  vm.runInContext(source('teacher-presentation.js'),context);
  return {nodes,body,calls,routes,exits,window,show:window.ConfIATeacherPresentation.show,block(){allowed=false;},
    all:()=>descendants(nodes['teacher-home']),button:action=>descendants(nodes['teacher-home']).find(x=>x.dataset.action===action)};
}
test('teacher uses real TME components and server counts with six existing destinations',async()=>{
  const ui=mount();ui.show('teacher','home');await flush();
  assert.equal(ui.all().filter(x=>x.className==='home-action').length,6);
  assert.equal(ui.all().find(x=>x.className==='home-metric blue').children[1].textContent,'7');
  assert.deepEqual(ui.calls.map(x=>x.url),['/tme/home-summary?period=today']);
  assert.equal(ui.calls[0].options.credentials,'same-origin');
  await ui.button('specialized').click();await ui.button('dynamic').click();
  assert.deepEqual(ui.exits,['/tme?view=new&mode=specialized','/tme?view=new&mode=dynamic']);
  await ui.button('activities').click();await ui.button('received').click();
  assert.deepEqual(ui.routes,[['teacher','exams'],['teacher','submissions']]);
  ui.block();await ui.button('cases').click();assert.equal(ui.exits.length,2);
});
test('failed summary keeps working shortcuts and never displays fabricated zero metrics',async()=>{
  const ui=mount(async()=>({ok:false,status:401}));ui.show('teacher','home');await flush();
  assert(ui.all().some(x=>x.className==='home-error'));
  assert(!ui.all().some(x=>x.className?.startsWith('home-metric ')));
  await ui.button('results').click();assert.equal(ui.exits[0],'/tme?view=results');
});
test('overlapping loads ignore an older response and leaving Teacher disables its presentation',async()=>{
  const older=deferred(),newer=deferred();let count=0;
  const ui=mount(()=> (++count===1?older:newer).promise);ui.show('teacher','home');
  assert(ui.all().some(x=>x.className==='home-loading'));
  ui.window.ConfIATeacherPresentation.refresh();
  newer.resolve({ok:true,json:async()=>summary(12)});await flush();
  older.resolve({ok:true,json:async()=>summary(99)});await flush();
  assert.equal(ui.all().find(x=>x.className==='home-metric blue').children[1].textContent,'12');
  ui.show('student','home');const requests=ui.calls.length;await ui.window.ConfIATeacherPresentation.refresh();
  assert.equal(ui.calls.length,requests);assert.equal(ui.nodes['teacher-home-styles'].media,'not all');
  assert.equal(ui.nodes['teacher-modern-header'].hidden,true);assert.equal(ui.nodes['teacher-bottom-nav'].hidden,true);
});
test('student and management do not load teacher data or activate its stylesheet',async()=>{
  const ui=mount();for(const profile of ['student','management']){ui.show(profile,'home');await flush();assert.equal(ui.calls.length,0);assert.equal(ui.nodes['teacher-home-styles'].media,'not all');}
});
test('teacher profile menu delegates logout to the existing authenticated handler',async()=>{
  const ui=mount();let logout=0;ui.nodes['auth-logout'].addEventListener('click',()=>logout++);
  ui.window.ConfIAAuthUser={display_name:'Docente'};ui.show('teacher','exams');
  assert.equal(ui.nodes['teacher-demo-profiles'].hidden,true);assert.equal(ui.nodes['teacher-modern-logout'].hidden,false);
  await ui.nodes['teacher-modern-logout'].click();assert.equal(logout,1);assert.equal(ui.calls.length,0);
});
