const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {element,descendants}=require('./ui-dom.cjs');
const {flush}=require('./capture-dom.cjs');
const fixture=()=>({assessment_id:'asmt_school',title:'Matemática 9º ano',purpose:'SCHOOL_EXAM',availability:'DISPONÍVEL',definition_sha256:'a'.repeat(64),policy:{max_attempts:2,allowed_inputs:['TEXT'],feedback:'TEACHER_RELEASE'},questions:[1,2,3].map(order=>({order,item_id:'i'+order,statement:'Enunciado '+order,max_points:2})),attempts:[]});
async function mount(data=fixture(),mutate){
 const calls=[],window={crypto:{randomUUID:()=> 'test-key'}},n=tag=>{const e=element(tag);e.append=(...c)=>c.forEach(x=>e.appendChild(x));e.focus=()=>{window.focused=e;};return e;},host=n('section');
 const fetch=async(url,options={})=>{calls.push({url,options});const body=options.body?JSON.parse(options.body):undefined;const result=body?mutate?.(url,body):data;return {ok:true,json:async()=>result||{}};};
 vm.runInNewContext(fs.readFileSync('app/confia_lean_auditor/static/dynamic-student.js','utf8'),{window,document:{createElement:n},fetch,FileReader:class{}});
 const app=window.ConfIADynamicStudent.create(host,data.assessment_id);await flush();return {host,window,calls,app,nodes:()=>descendants(host)};
}
test('student text submission uses institutional gateway, current hash and session-owned actors',async()=>{
 const data=fixture();const ui=await mount(data,(url,body)=>{
  assert(url.endsWith('/attempts'));assert.equal(body.definition_sha256,data.definition_sha256);assert.equal(body.mode,'TEXT');assert(!('student_user_id' in body));
  const a={attempt_id:'exam_x',attempt_number:1,status:'DRAFT',submitted:false,pages:[],questions:[{case_id:'case_x',order:1,status:'DRAFT',segments:[{text:body.solutions[0]}]}],result:null};data.attempts.push(a);return a;
 });
 const areas=ui.nodes().filter(n=>n.tag==='textarea');assert.equal(areas.length,3);areas.forEach((a,i)=>a.value='Solução '+i);
 const form=ui.nodes().find(n=>n.tag==='form');form.emit("submit",{preventDefault(){}});await flush();await flush();
 assert.equal(ui.calls.filter(c=>c.options.body).length,1);assert.match(ui.host.textContent,/Enviar tentativa para avaliação/);assert(ui.window.focused);
 assert(!ui.calls.some(c=>c.url.startsWith('/tme/')||c.url.startsWith('/submissions')));
});
test('held result never appears as zero or an official automatic grade',async()=>{
 const data=fixture();data.attempts=[{attempt_id:'exam_x',attempt_number:1,status:'SUBMITTED',submitted:true,pages:[],questions:[{case_id:'c',order:1,status:'TECHNICAL_ERROR',segments:[]}],result:null}];
 const ui=await mount(data);await ui.nodes().find(n=>n.tag==='button'&&n.textContent.startsWith('Tentativa 1')).click();
 assert.match(ui.host.textContent,/Falha técnica/);assert.match(ui.host.textContent,/resultado ainda não foi divulgado/);assert.doesNotMatch(ui.host.textContent,/Nota confirmada:/);
 assert(ui.nodes().filter(n=>n.tag==='button').every(n=>n.type==='button'));
});
test('only explicitly released result and teacher feedback are rendered',async()=>{
 const data=fixture();data.attempts=[{attempt_id:'exam_x',attempt_number:1,status:'RELEASED',submitted:true,pages:[],questions:[],result:{final_total:3.5,max_total:6,questions:[{order:1,final_points:2,max_points:2}],teacher_feedback:'Confira os quatro lados.'}}];
 const ui=await mount(data);await ui.nodes().find(n=>n.tag==='button'&&n.textContent.startsWith('Tentativa 1')).click();
 assert.match(ui.host.textContent,/Nota confirmada: 3.5 \/ 6/);assert.match(ui.host.textContent,/Confira os quatro lados/);
});
test('school manuscript requires explicit student attestation and preserves per-question page order',async()=>{
 const data=fixture();data.policy.allowed_inputs=['IMAGES'];const a={attempt_id:'exam_x',attempt_number:1,status:'DRAFT',submitted:false,pages:[{page_id:'p1',page_number:1},{page_id:'p2',page_number:2}],mapping:{version:1,bindings:[]},questions:[{case_id:'c',order:1,status:'DRAFT',revision_number:1,segments:[{text:'Minha resposta',page_index:0}],pages:[{page_number:2}],reading_review:{status:'NEEDS_CONFIRMATION',revision_sha256:'b'.repeat(64)}}]};data.attempts=[a];
 const ui=await mount(data,()=>({}));await ui.nodes().find(n=>n.tag==='button'&&n.textContent.startsWith('Tentativa 1')).click();
 await ui.nodes().find(n=>n.textContent==='Confirmar minha leitura da questão 1').click();await flush();assert.equal(ui.calls.filter(c=>c.url.endsWith('/confirm-reading')).length,0);
 const consent=ui.nodes().find(n=>n.tag==='input'&&n.getAttribute('aria-label').startsWith('Conferi'));consent.checked=true;
 await ui.nodes().find(n=>n.textContent==='Confirmar minha leitura da questão 1').click();await flush();
 const request=ui.calls.find(c=>c.url.endsWith('/confirm-reading'));assert(request);assert.equal(JSON.parse(request.options.body).question_scope_confirmed,true);
});

test('unsaved manuscript edits cannot be sent with an earlier attestation',async()=>{
 const data=fixture();data.policy.allowed_inputs=['IMAGES'];data.attempts=[{attempt_id:'exam_x',attempt_number:1,status:'DRAFT',submitted:false,pages:[{page_id:'p1',page_number:1}],mapping:{version:1,bindings:[]},questions:[{case_id:'c',order:1,status:'DRAFT',revision_number:1,segments:[{text:'Texto salvo',page_index:0}],pages:[{page_number:1}],reading_review:{status:'CONFIRMED',revision_sha256:'b'.repeat(64)}}]}];
 const ui=await mount(data,()=>({}));await ui.nodes().find(n=>n.tag==='button'&&n.textContent.startsWith('Tentativa 1')).click();
 const area=ui.nodes().find(n=>n.tag==='textarea');area.value='Outra leitura ainda não salva';await area.emit('input');
 await ui.nodes().find(n=>n.textContent==='Enviar tentativa para avaliação').click();await flush();
 assert(!ui.calls.some(c=>c.url.endsWith('/submit')));assert.match(ui.host.textContent,/Salve e confira/);
});
