const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {element,descendants}=require('./ui-dom.cjs');const {flush}=require('./capture-dom.cjs');
function fixture(){return {context:'SELF_STUDY',study_id:'study_test',source:{submission_id:'s1',revision_number:1,revision_sha256:'a'.repeat(64),confirmed:true,automatic:false,pages:[],originals:[],segments:[{page_index:0,text:'Resolva 2x=12.'}]},packages:[{package_id:'p1',version:1,sha256:'b'.repeat(64),status:'AWAITING_CONFIRMATION',interpretation:'Resolva 2x=12.',uncertainties:[],objectives:[],confirmed:true}],attempts:[{attempt_id:'t1',number:1,source:{submission_id:'s2',revision_number:1,revision_sha256:'c'.repeat(64),confirmed:true,pages:[],originals:[],segments:[{page_index:0,text:'Divido por 2.'}]},report:{findings:[{criterion_id:'method',objective:'Método',state:'PARTIAL',guidance:'Explique o passo.',evidence:[{text:'Divido por 2.'}]}],uncertainties:['Análise semântica.'],comparison:[],score:9},help:[]}]};}
async function mount(data=fixture()){
 const calls=[],window={crypto:{randomUUID:()=> 'test-key'}},make=tag=>{const e=element(tag);e.append=(...c)=>c.forEach(x=>e.appendChild(x));e.focus=()=>{window.focused=e;};return e;},host=make('section');
 const fetch=async(url,opts={})=>{calls.push({url,opts});const body=opts.body?JSON.parse(opts.body):null;
  if(url.endsWith('/help')){const a=data.attempts[0];a.help.push({level:body.level,content:{items:[{message:'Pista solicitada'}],limitations:[]}});}
  return {ok:true,json:async()=>url==='/dynamic/self-study'&&!body?{catalog:[],studies:[{study_id:data.study_id,statement:'Meu problema'}]}:data};};
 vm.runInNewContext(fs.readFileSync('app/confia_lean_auditor/static/dynamic-self-study.js','utf8'),{window,document:{createElement:make},fetch,FileReader:class{}});
 const app=window.ConfIASelfStudy.create(host);await flush();await descendants(host).find(n=>n.textContent==='Meu problema').click();await flush();return {host,window,calls,app,nodes:()=>descendants(host)};
}
test('self study renders qualitative evidence and never a supplied numerical grade',async()=>{
 const ui=await mount();assert.match(ui.host.textContent,/sem nota/);assert.match(ui.host.textContent,/Divido por 2/);assert.match(ui.host.textContent,/Desenvolvimento a completar/);
 assert.doesNotMatch(ui.host.textContent,/Nota:|9\s*\/|score/);assert(ui.window.focused);assert(ui.nodes().find(n=>n.getAttribute('role')==='status'));
 assert(!ui.calls.some(c=>c.url.startsWith('/tme')||c.url.startsWith('/assessments')));
});
test('progressive guidance requires each explicit step and complete-development consent',async()=>{
 const ui=await mount();assert(!ui.nodes().some(n=>n.textContent==='Mostrar desenvolvimento orientado'));
 await ui.nodes().find(n=>n.textContent==='Quero uma pista matemática').click();await flush();
 await ui.nodes().find(n=>n.textContent==='Explique o conceito').click();await flush();
 await ui.nodes().find(n=>n.textContent==='Mostrar desenvolvimento orientado').click();await flush();
 assert.equal(ui.calls.filter(c=>c.url.endsWith('/help')).length,2);
 const consent=ui.nodes().find(n=>n.getAttribute('aria-label')==='Solicito o desenvolvimento orientado completo');consent.checked=true;
 await ui.nodes().find(n=>n.textContent==='Mostrar desenvolvimento orientado').click();await flush();
 assert.equal(JSON.parse(ui.calls.filter(c=>c.url.endsWith('/help')).at(-1).opts.body).request_complete_solution,true);
});
test('unsaved reading cannot be confirmed or discarded by a new analysis operation',async()=>{
 const data=fixture();data.attempts=[];const ui=await mount(data);
 const area=ui.nodes().find(n=>n.tag==='textarea');area.value='Nova condição';await area.emit('input');
 const consent=ui.nodes().find(n=>n.getAttribute('aria-label')==='Conferi o enunciado');consent.checked=true;
 await ui.nodes().find(n=>n.textContent==='Confirmar leitura').click();await flush();
 assert(!ui.calls.some(c=>c.url.endsWith('/confirm-reading')));assert.match(ui.host.textContent,/Salve as alterações/);
 await ui.nodes().find(n=>n.textContent==='Interpretar enunciado e preparar critérios').click();await flush();
 assert(!ui.calls.some(c=>c.url.endsWith('/prepare')));
});

test('partial mathematical error remains explicit and safe fallback is identified',async()=>{
 const data=fixture();data.attempts[0].report.findings[0].mathematical_finding='MATHEMATICAL_ERROR';
 data.attempts[0].report.findings[0].guidance='Há etapas aproveitáveis e um possível erro matemático no trecho citado.';
 data.attempts[0].help=[{level:2,status:'SAFE_FALLBACK',content:{items:[{message:'Retome a regra usada no trecho.'}],limitations:['Nenhum novo julgamento.']}}];
 const ui=await mount(data);assert.match(ui.host.textContent,/erro matemático/);assert.match(ui.host.textContent,/orientação segura/);assert.match(ui.host.textContent,/Divido por 2/);
});
