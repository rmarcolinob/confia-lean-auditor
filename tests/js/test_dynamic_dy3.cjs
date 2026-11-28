const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {flush}=require('./ui-dom.cjs');
const pid='dyn_'+'d'.repeat(32),cid='case_'+'a'.repeat(32),reply=data=>({ok:true,json:async()=>data});
const current={case_id:cid,source_mode:'TEXT',submission_id:'sub_'+'b'.repeat(32),problem_id:pid,external_candidate_ref:'PROVA-1',dynamic_context:{statement_version:1}};
const doc={revision:1,problem:{problem_id:pid,correction_mode:'DYNAMIC'},statements:[{title:'Questão inédita',statement:'Resolva nos reais: 2y²-14y+24=0.',max_score:'10',version_number:1}],rubrics:[],preparation_history:[],current_preparation:null,current_configuration:{package:{package_version:1}},correction_available:true};
const result=(review=false)=>({engine_mode:'DYNAMIC',problem_id:pid,score:review?1.5:10,max_score:10,review_required:review,verdict:review?'inconclusivo':'concluido',feedback:'Sugestão provisória',uncertainty:review?['Interpretação requer revisão.']:[],analysis:{claims:[{claim_id:'c1',text:'S={3,4}',verification_status:'VERIFIED',verification_detail:'Checagem exata.'}]},rubric_assessment:{assessment_status:review?'partial':'complete',items:[{id:'roots',description:'Obter as raízes corretas.',points:review?1.5:10,max_points:10,mathematical_status:'supported',verification_status:'verified_in_scope',evidence:'S={3,4}',assessment_note:'Conjunto verificado.'}]}});
function mock(url,options){
 if(url===`/tme/cases/${cid}`||url==='/tme/direct-solutions')return reply(current);
 if(url.endsWith('/original-text'))return reply({text:'S={3,4}'});
 if(url.endsWith('/submission'))return reply({submission:{page_images:[]}});
 if(url===`/dynamic/problems/${pid}`||url.endsWith('/attempts'))return reply(url.endsWith('/attempts')?current:doc);
 if(url==='/dynamic/problems')return reply([doc]);
}
for(const review of [false,true])test(`shared Dynamic workspace renders score, rubric, evidence and review=${review}`,async()=>{
 const run={audit_run_id:'audit_dynamic',transcription_id:'tr_demo',revision_number:1,acceptance_id:'accept_auto',status:'COMPLETED',stale:false,result:result(review)};
 const ui=await pilot({mode:'TEXT',automatic:true,auditRun:run,mockFetch:mock});await ui.click('Abrir');
 assert.equal(ui.root.dataset.view,'workspace');assert.doesNotMatch(text(ui.root),/Não foi possível carregar a solução/);
 assert.match(text(ui.root),/Modo: Correção dinâmica/);assert.match(text(ui.root),review?/1,5 \/ 10/:/10 \/ 10/);
 assert.match(text(ui.root),/Obter as raízes corretas/);assert.match(text(ui.root),/S=\{3,4\}/);assert.match(text(ui.root),/Verificado no escopo exato/);
 if(review)assert.match(text(ui.root),/Revisão necessária/);
 assert(ui.statements.some(s=>s.source.includes('2y²-14y+24')));
 for(const tab of ['Transcrição','Comparar','Original'])await ui.click(tab);
 assert.equal(walk(ui.root).find(e=>e.attributes['aria-label']==='Comandos do original')?.hidden,true);
 await ui.nav[0].click();await flush();assert.equal(ui.root.dataset.view,'cases');
});
test('receiving a Dynamic solution opens the existing workspace and preserves explicit review consent',async()=>{
 const ui=await pilot({automatic:true,initialSearch:`?view=new&mode=dynamic&problem_id=${pid}`,mockFetch:mock});
 const fields=walk(ui.root);fields.find(e=>e.attributes['aria-label']==='Código pseudônimo da resolução').value='DY3-S1';fields.find(e=>e.attributes['aria-label']==='Resolução digitada').value='S={3,4}';fields.find(e=>e.attributes['aria-label']==='Permitir análise com preparação pendente').checked=true;
 await fields.find(e=>e.tag==='form'&&walk(e).some(c=>c.textContent==='Conferir transcrição')).handlers.submit({preventDefault(){}});await flush();
 const call=ui.calls.find(c=>c.url==='/tme/direct-solutions');assert.deepEqual(JSON.parse(call.options.body),{problem_id:pid,external_candidate_ref:'DY3-S1',solution:'S={3,4}',allow_preparation_review:true,policy_profile:'SCHOOL_EXAM'});
 assert.equal(ui.window.history.url,`/tme?case_id=${cid}`);assert.equal(ui.root.dataset.view,'workspace');assert.match(text(ui.root),/Resolução textual/);
});
