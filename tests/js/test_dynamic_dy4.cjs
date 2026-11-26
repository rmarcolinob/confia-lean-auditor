const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {flush,deferred}=require('./ui-dom.cjs');
const cid='case_'+'a'.repeat(32),pid='dyn_'+'d'.repeat(32),reply=data=>({ok:true,json:async()=>data});
const current={case_id:cid,source_mode:'TEXT',submission_id:'sub_'+'b'.repeat(32),problem_id:pid,external_candidate_ref:'PROVA-1',dynamic_context:{statement_version:1}};
const run={audit_run_id:'aud_dy4',transcription_id:'tr_demo',revision_number:1,acceptance_id:'accept_auto',status:'COMPLETED',stale:false,result:{engine_mode:'DYNAMIC',score:10,max_score:10,verdict:'concluido',review_required:false,analysis:{claims:[]},decisions:[{criterion_id:'roots',description:'Obter as raízes corretas.'}],rubric_assessment:{assessment_status:'complete',items:[{id:'roots',description:'Obter as raízes corretas.',points:10,max_points:10,mathematical_status:'supported',verification_status:'verified_in_scope'}]}}};
function review(disagreement=false,failed=false){return {stale:false,review_required:disagreement||failed,reconciliation:null,review:{status:failed?'FAILED':'COMPLETED',phase_a:{warnings:[],criterion_reviews:[{criterion_id:'roots',explanation:'Fonte e conjunto de raízes conferidos.',evidence:['S={3,4}'],uncertainty:[]}]},comparison:failed?null:{exact_agreement:!disagreement,agreement_count:disagreement?0:1,conflicting_criteria:disagreement?['roots']:[],criteria:[{criterion_id:'roots',grader_points:10,reviewer_points:disagreement?3:10,reason:disagreement?'Crédito excessivo requer atenção.':'Concordância no escopo verificado.'}]}}};}
async function dynamic({value=[],post}={}){
 let reviews=value;
 return pilot({mode:'TEXT',automatic:true,auditRun:run,mockFetch:async(url,options)=>{
  if(url.endsWith('/independent-reviews')){if(options.method==='POST'){const result=post?await post(options):review();reviews=[result];return reply(result);}return reply(reviews);}
  if(url===`/tme/cases/${cid}`)return reply(current);
  if(url.endsWith('/original-text'))return reply({text:'S={3,4}'});
  if(url.endsWith('/submission'))return reply({submission:{page_images:[]}});
  if(url===`/dynamic/problems/${pid}`)return reply({statements:[{version_number:1,statement:'Resolva nos reais: y-3=0.',title:'Dynamic',max_score:'10'}]});
 }});
}
test('review agreement lives in the shared workspace without changing the suggested score',async()=>{
 const ui=await dynamic({value:[review()]});await ui.click('Abrir');
 assert.match(text(ui.root),/Concordância: 1\/1 critérios/);assert.match(text(ui.root),/10 \/ 10/);
 assert.match(text(ui.root),/Concordância não é prova matemática/);
 const row=walk(ui.root).find(e=>e.tag==='summary'&&e.textContent.includes('Grader:'));assert.match(row.textContent,/Grader: 10 · Reviewer: 10/);
 const disclosure=walk(ui.root).find(e=>e.tag==='details'&&e.children.includes(row));disclosure.open=true;assert.match(text(disclosure),/Fonte e conjunto de raízes conferidos/);
 for(const tab of ['Transcrição','Comparar','Original'])await ui.click(tab);
 await ui.nav[0].click();await flush();assert.equal(ui.root.dataset.view,'cases');
});
test('material divergence is visible but original score and human decision stay unchanged',async()=>{
 const ui=await dynamic({value:[review(true)]});await ui.click('Abrir');
 assert.match(text(ui.root),/1 divergência requer atenção/);assert.match(text(ui.root),/Revisão necessária/);assert.match(text(ui.root),/Grader: 10 · Reviewer: 3/);
 assert.match(text(ui.root),/10 \/ 10/);assert(!ui.calls.some(c=>c.options.method==='POST'));
});
test('explicit request blocks duplicate action while pending and renders completion',async()=>{
 const pending=deferred();const ui=await dynamic({post:()=>pending.promise});await ui.click('Abrir');
 const request=ui.click('Solicitar revisão independente');await flush();
 assert(walk(ui.root).find(e=>e.textContent==='Revisando independentemente…').disabled);
 pending.resolve(review());await request;
 assert.match(text(ui.root),/Concordância: 1\/1 critérios/);
 const call=ui.calls.find(c=>c.url.endsWith('/independent-reviews')&&c.options.method==='POST');assert(JSON.parse(call.options.body).execution_key);
 assert(!ui.calls.some(c=>c.url.endsWith('/decision')&&c.options.method==='POST'));
});
test('failed review remains inconclusive and allows a new request',async()=>{
 const ui=await dynamic({value:[review(false,true)]});await ui.click('Abrir');
 assert.match(text(ui.root),/Revisão não concluída/);assert.doesNotMatch(text(ui.root),/Concordância:/);
 assert(walk(ui.root).some(e=>e.textContent==='Solicitar nova revisão independente'));
});
test('Specialized never requests or renders the Dynamic reviewer',async()=>{
 const ui=await pilot({automatic:true,auditRun:{...run,result:{...run.result,engine_mode:undefined}}});await ui.click('Abrir');
 assert.doesNotMatch(text(ui.root),/Revisão independente/);assert(!ui.calls.some(c=>c.url.includes('independent-reviews')));
});
