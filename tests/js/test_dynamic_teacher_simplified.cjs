const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {element,descendants,deferred}=require('./ui-dom.cjs');
const source=name=>fs.readFileSync(path.join(__dirname,'../../app/confia_lean_auditor/static',name),'utf8');
function node(tag){const e=element(tag),query=e.querySelectorAll;e.append=(...c)=>c.forEach(x=>e.appendChild(x));e.querySelectorAll=function(selector){return selector==='[role=status]'?descendants(this).slice(1).filter(n=>n.getAttribute('role')==='status'):query.call(this,selector);};return e;}
const response=data=>({ok:true,json:async()=>data});
const doc=(ready=false)=>({assessment:{assessment_id:'a',title:'Matemática • 8º ano',status:ready?'PUBLISHED':'DRAFT'},dynamic_revision:3,readiness:{state:ready?'ACTIVE':'DRAFT',ready,questions:[{order:1,title:'Frações',problem_id:'p',max_score:2,statement:'Explique três quartos de 24.',rubric_status:ready?'APPROVED':'MISSING'}],total_questions:1},events:[]});
async function screen(initial,failWrite=false){
 const host=node('div'),window={},calls=[],selected=[],uploads=[];let value=initial;
 const fetch=async(url,options={})=>{calls.push({url,options});if(failWrite&&options.method)throw Error('Falha simulada de rede');if(url==='/dynamic/capabilities')return response({});if(url==='/dynamic/assessments')return response(value?[value]:[]);if(url==='/tme/exam-submissions')return response([{assessment_id:'a',submission_id:'exam1',participant_code:'SINTETICO-01',page_count:2,status:'RECEIVED'}]);return response(value);};
 vm.runInNewContext(source('dynamic-assessment.js'),{window,fetch,document:{createElement:node},console});
 const component=window.ConfIADynamicAssessment.create({host,simplified:true,onSelect:(...x)=>selected.push(x),onUpload:id=>uploads.push(id)});
 await component.load(initial?'a':null);
 return {host,component,calls,selected,uploads,nodes:()=>descendants(host),click:async title=>{const b=descendants(host).find(n=>n.tag==='button'&&(n.textContent===title||n.getAttribute('aria-label')===title));assert(b,title);await b.click();}};
}
test('three teacher actions are real buttons and no provider is fabricated',async()=>{
 const ui=await screen();for(const t of ['Cadastrar avaliação','Enviar provas respondidas','Consultar correções'])assert(ui.nodes().some(n=>n.tag==='button'&&n.getAttribute('aria-label')===t));
 assert.match(ui.host.textContent,/Sugestão por IA indisponível/);assert.match(ui.host.textContent,/Reconhecimento automático indisponível/);
 await ui.click('Cadastrar avaliação');assert(ui.nodes().some(n=>n.getAttribute('aria-label')==='Tipo da avaliação'));
 assert(ui.calls.every(c=>!c.options.method));
});
test('draft cannot activate without approved ready rubric; upload keeps assessment context',async()=>{
 const ui=await screen(doc());const save=ui.nodes().find(n=>n.textContent==='Salvar avaliação aprovada');assert(save.disabled);await save.click();assert(ui.calls.every(c=>!c.options.method));
 const active=await screen(doc(true));await active.click('Enviar provas respondidas');assert.match(active.host.textContent,/um participante|participantes diferentes/);await active.click('Enviar fotografias ou PDF');assert.deepEqual(active.uploads,['a']);
});
test('received list identifies pseudonym, pending status and separate teacher decision',async()=>{
 const ui=await screen(doc(true));assert.match(ui.host.textContent,/SINTETICO-01/);assert.match(ui.host.textContent,/não são notas finais/);assert.match(ui.host.textContent,/Conferência ou correção pendente/);assert(ui.nodes().some(n=>n.tag==='summary'&&n.textContent==='Auditoria e evidências'));
});
function pipeline(){const window={};vm.runInNewContext(source('dynamic-correction.js'),{window,encodeURIComponent,Error});return window.ConfIADynamicCorrection.complete;}
const run={engine_mode:'DYNAMIC',status:'COMPLETED',audit_run_id:'aud_test',stale:false};
test('teacher correction chains reviewer/reconciliation and resumes without duplicate review',async()=>{
 const complete=pipeline(),writes=[];let review=null,rec=null;
 const api=async url=>url.endsWith('/independent-reviews')?(review?[review]:[]):rec?[rec]:[];
 const post=async(url,body)=>{writes.push({url,body});if(url.endsWith('/independent-reviews'))return review={review:{review_id:'r'},stale:false};return rec={reconciliation:{reconciled_suggested_score:null,review_required:true},stale:false};};
 await complete({caseId:'case',run,api,post});assert.equal(writes.length,2);assert.equal(writes[0].body.execution_key,'teacher-simplified');assert.equal(writes[1].body.independent_review_id,'r');
 await complete({caseId:'case',run,api,post});assert.equal(writes.length,2);assert.equal(rec.reconciliation.reconciled_suggested_score,null);
});
test('interrupted response retries same key; never confirms human decision',async()=>{
 const complete=pipeline(),keys=[];let failed=true;
 const api=async()=>[];const post=async(url,body)=>{assert(!/human|finalize|release/.test(url));if(url.endsWith('/independent-reviews')){keys.push(body.execution_key);if(failed){failed=false;throw Error('network');}return {review:{review_id:'r'}};}return {reconciliation:{}};};
 await assert.rejects(complete({caseId:'c',run,api,post}),/network/);await complete({caseId:'c',run,api,post});assert.equal(keys[0],keys[1]);
});
test('failed, stale or Specialized runs do not start semantic review',async()=>{
 for(const change of [{status:'FAILED'},{stale:true},{engine_mode:'TME'}]){const result=await pipeline()({caseId:'c',run:{...run,...change},api:()=>assert.fail(),post:()=>assert.fail()});assert.equal(result,null);}
});
test('failed read is not mistaken for missing reviews and causes no new mutation',async()=>{
 await assert.rejects(pipeline()({caseId:'c',run,api:async()=>{throw Error('integrity');},post:()=>assert.fail()}),/integrity/);
});

test('completed reconciliation does not advertise unfinished pipeline; pending and historical states stay distinct',()=>{
 const window={ConfIAReport:{publicTechnicalValue:(k,v)=>v},ConfiaRecognitionView:{renderMathText:(el,text)=>{el.textContent=text;}}};
 vm.runInNewContext(source('tme/workspace-report.js'),{window,document:{createElement:node}});
 const host=node('div'),data={engine_mode:'DYNAMIC',workflow_actions:[{label:'Solicitar revisão independente'}],rubric_items:[]};
 const render=extra=>window.ConfiaWorkspaceReport.renderQuestion({...data,...extra},host,{simplified:true});
 render({});assert.match(host.textContent,/Concluir correção/);
 render({reconciliation:{criteria:[]}});assert(!host.textContent.includes('Concluir correção'));assert.match(host.textContent,/Auditoria e evidências/);
 render({stale:true});assert(!host.textContent.includes('Concluir correção'));
});

test('failed save preserves teacher input and restores controls without creating a phantom assessment',async()=>{
 const ui=await screen(null,true);await ui.click('Cadastrar avaliação');
 const title=ui.nodes().find(n=>n.getAttribute('aria-label')==='Título da avaliação');title.value='Prova ainda não salva';
 const form=ui.nodes().find(n=>n.tag==='form');await form.emit('submit',{preventDefault(){}});
 assert.equal(title.value,'Prova ainda não salva');assert(!title.disabled);assert(ui.nodes().includes(title));
 assert.match(ui.host.textContent,/Falha simulada de rede/);assert(!ui.nodes().some(n=>n.textContent==='Salvar avaliação aprovada'));
});
