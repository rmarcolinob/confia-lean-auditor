const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {element,descendants}=require('./ui-dom.cjs');
const source=name=>fs.readFileSync(`app/confia_lean_auditor/static/${name}`,'utf8');
function page({login=false,profile=null}={}) {
 const make=tag=>{
  const n=element(tag);n.append=(...items)=>items.forEach(x=>n.appendChild(x));
  Object.defineProperty(n,'lastChild',{get(){return n.children.at(-1);}});
  n.querySelector=s=>descendants(n).find(x=>s.startsWith('.')?x.className?.split(' ').includes(s.slice(1)):x.tag===s);
  return n;
 };
 const ids=['platform-home','platform-header','platform-navigation','platform-home-styles','platform-avatar','platform-logout','auth-logout','platform-session','platform-brand-context','student-home-name','student-institutional-context','student-home','management-home'];
 if(login)ids.push('login-form','login');
 const nodes=Object.fromEntries(ids.map(id=>[id,make('div')]));nodes['platform-header'].append(make('details'));
 nodes['student-home-name'].textContent='Aluno';nodes['student-institutional-context'].textContent='Escola da sessão';
 const routes=[],body=make('body'),window={ConfIAShell:{navigate:(...args)=>routes.push(args)}};
 if(profile){window.ConfIAAuthUser={display_name:'Pessoa de teste'};window.ConfIAAuthProfile=profile;}
 const ctx={window,document:{body,querySelector:s=>nodes[s.slice(1)],createElement:make},fetch:()=>{throw Error('presentation must not fetch or mutate data');}};
 vm.createContext(ctx);vm.runInContext(source('tme/home.js'),ctx);vm.runInContext(source('platform-presentation.js'),ctx);
 return {nodes,body,window,routes,show:window.ConfIAPlatformPresentation?.show,
  actions:id=>descendants(nodes[id]).filter(x=>x.className==='home-action')};
}
test('local platform entry uses TME cards and existing routes without granting roles',async()=>{
 const ui=page();ui.show('platform','home');
 assert.match(ui.nodes['platform-home'].textContent,/Ambiente de demonstração local/);
 const actions=ui.actions('platform-home');assert.equal(actions.length,3);
 for(const b of actions)await b.click();
 assert.deepEqual(ui.routes,[['student','home'],['teacher','home'],['management','home']]);
 assert.equal(ui.window.ConfIAAuthUser,undefined);
});
test('authenticated entry exposes only the server authorized module',async()=>{
 for(const profile of ['student','teacher','management']) {
  const ui=page({profile});ui.show('platform','home');
  const cards=ui.actions('platform-home');assert.equal(cards.filter(x=>!x.disabled).length,1);
  for(const b of cards)await b.click();assert.deepEqual(ui.routes,[[profile,'home']]);
  assert.match(ui.nodes['platform-home'].textContent,/Sessão institucional/);
 }
});
test('unauthenticated institutional module cards focus existing login without assigning a role',async()=>{
 const ui=page({login:true});
 for(const b of ui.actions('platform-home'))await b.click();
 assert.equal(ui.nodes.login.focused,true);assert.deepEqual(ui.routes,[]);
 assert.equal(ui.window.ConfIAAuthProfile,undefined);assert.match(ui.nodes['platform-home'].textContent,/Acesso institucional/);
});
test('student home preserves live identity and enrollment nodes and routes to existing learning features',async()=>{
 const ui=page({profile:'student'}),name=ui.nodes['student-home-name'],context=ui.nodes['student-institutional-context'];
 ui.show('student','home');ui.show('platform','home');ui.show('student','home');
 const content=descendants(ui.nodes['student-home']);assert(content.includes(name));assert(content.includes(context));
 assert.equal(content.filter(x=>x===context).length,1);
 assert.equal(ui.actions('student-home').length,6);
 await content.find(x=>x.className==='home-primary').click();
 assert.deepEqual(ui.routes,[['student','tutoria/practice']]);
});
test('management presentation does not fabricate metrics or replace the operational panel',()=>{
 const ui=page({profile:'management'});ui.show('management','home');
 assert.match(ui.nodes['management-home'].textContent,/Uma visão clara/);
 assert(!descendants(ui.nodes['management-home']).some(x=>x.className?.startsWith('home-metric')));
});
test('approved Teacher disables the new presentation and logout delegates to existing handler',async()=>{
 const ui=page({profile:'student'});let count=0;ui.nodes['auth-logout'].addEventListener('click',()=>count++);
 ui.show('student','home');await ui.nodes['platform-logout'].click();assert.equal(count,1);
 ui.show('teacher','home');assert.equal(ui.nodes['platform-header'].hidden,true);
 assert.equal(ui.nodes['platform-home-styles'].media,'not all');assert.equal(ui.body.dataset.platformProfile,'');
});
