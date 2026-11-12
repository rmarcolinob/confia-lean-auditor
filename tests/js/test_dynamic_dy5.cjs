const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {flush,deferred}=require('./ui-dom.cjs');
const cid='case_'+'a'.repeat(32),pid='dyn_'+'d'.repeat(32),rid='drec_'+'c'.repeat(64),reply=data=>({ok:true,json:async()=>data});
const current={case_id:cid,source_mode:'TEXT',submission_id:'sub_'+'b'.repeat(32),problem_id:pid,external_candidate_ref:'PROVA-1',dynamic_context:{statement_version:1}};
const run={audit_run_id:'aud_dy5',transcription_id:'tr_demo',revision_number:1,acceptance_id:'accept_auto',status:'COMPLETED',stale:false,result:{engine_mode:'DYNAMIC',score:6,max_score:10,verdict:'concluido',review_required:false,analysis:{claims:[]},decisions:[{criterion_id:'method',description:'Justificar o método.'}],rubric_assessment:{assessment_status:'complete',items:[{id:'method',description:'Justificar o método.',points:0,max_points:4,mathematical_status:'supported',verification_status:'verified_in_scope'}]}}};
const review={stale:false,review_required:true,review:{review_id:'drev_'+'e'.repeat(64),status:'COMPLETED',phase_a:{warnings:[],criterion_reviews:[]},comparison:{exact_agreement:false,agreement_count:0,conflicting_criteria:['method'],criteria:[{criterion_id:'method',grader_points:0,reviewer_points:4,reason:'Método equivalente.'}]}}};
function reconciled(exam=false){return {reconciliation_id:rid,grader_audit_run_id:run.audit_run_id,policy_profile:exam?'SCHOOL_EXAM':'FORMATIVE_LIST',grader_score_snapshot:'6',reconciled_suggested_score:exam?'6':'10',max_score:'10',review_required:exam,review_reasons:exam?['Divergência exige homologação.']:[],criteria:[{criterion_id:'method',grader_points:'0',reviewer_points:'4',reconciled_points:exam?'0':'4',max_points:'4',automation:exam?'REVIEW_ONLY':'AUTO_ADJUST_UP',reason:exam?'Perfil exige revisão; pontos provisórios preservados.':'Evidência equivalente verificada e suficiente.'}]};}
async function dynamic({record=reconciled(),pending=null}={}){
 let value=record,decision=null;
 return pilot({mode:'TEXT',automatic:true,auditRun:run,mockFetch:async(url,options)=>{
  if(url.endsWith('/policy'))return reply({policy_profile:value?.policy_profile||'FORMATIVE_LIST'});
  if(url.endsWith('/reconciliations')){if(options.method==='POST'){if(pending)await pending;value=reconciled();return reply({reconciliation:value,stale:false});}return reply(value?[{reconciliation:value,stale:false}]:[]);}
  if(url.endsWith('/human-decisions'))return reply([]);
  if(url.endsWith('/independent-reviews'))return reply([review]);
  if(url===`/tme/cases/${cid}`)return reply(current);
  if(url.endsWith('/decision')){if(options.method==='POST'){const body=JSON.parse(options.body);decision={...body,suggested_points:value?.reconciled_suggested_score};}return reply(decision);}
  if(url.endsWith('/original-text'))return reply({text:'S={3,4}'});
  if(url.endsWith('/submission'))return reply({submission:{page_images:[]}});
  if(url===`/dynamic/problems/${pid}`)return reply({statements:[{version_number:1,statement:'Resolva nos reais: y-3=0.',title:'Dynamic',max_score:'10'}]});
 }});
}
test('reconciled score is shown while original and reviewer remain inspectable',async()=>{
 const ui=await dynamic();await ui.click('Abrir');
 assert.match(text(ui.root),/10 \/ 10/);assert.match(text(ui.root),/Primeira análise preservada: 6 \/ 10/);
 assert.match(text(ui.root),/1 divergência resolvida/);assert.match(text(ui.root),/Primeira análise: 0 · Revisão: 4 · Reconciliação: 4/);
 const row=walk(ui.root).find(e=>e.tag==='summary'&&e.textContent.includes('Reconciliação: 4'));
 const details=walk(ui.root).find(e=>e.tag==='details'&&e.children.includes(row));details.open=true;assert.match(text(details),/Evidência equivalente verificada/);
 for(const tab of ['Comparar','Transcrição','Original'])await ui.click(tab);assert.match(text(ui.root),/10 \/ 10/);
 await ui.nav[0].click();await flush();assert.equal(ui.root.dataset.view,'cases');
});
test('exam REVIEW_ONLY preserves grader points and exposes required review',async()=>{
 const ui=await dynamic({record:reconciled(true)});await ui.click('Abrir');
 assert.match(text(ui.root),/6 \/ 10/);assert.match(text(ui.root),/1 critério requer revisão/);
 assert.match(text(ui.root),/Pontos provisórios preservados/);assert.match(text(ui.root),/Perfil: Prova escolar/);
});
test('confirmation submits reconciliation reference and uses reconciled score',async()=>{
 const ui=await dynamic();await ui.click('Abrir');await ui.click('Usar sugestão');await ui.click('Finalizar correção');
 const call=ui.calls.find(c=>c.url.endsWith('/decision')&&c.options.method==='POST');assert(call);
 const body=JSON.parse(call.options.body);assert.equal(body.reconciliation_id,rid);assert.equal(body.final_points,10);assert.equal(body.audit_run_id,'aud_dy5');
 assert.match(text(ui.root),/Correção registrada/);assert.equal(run.result.score,6);
});
test('no confirmation before current reconciliation; explicit request blocks repeats',async()=>{
 const gate=deferred();const ui=await dynamic({record:null,pending:gate.promise});await ui.click('Abrir');
 assert.match(text(ui.root),/Conclua a revisão independente e a reconciliação corrente/);
 assert(!walk(ui.root).some(e=>e.tag==='button'&&e.textContent==='Finalizar correção'));
 const action=ui.click('Reconciliar sugestão');await flush();assert(walk(ui.root).find(e=>e.textContent==='Reconciliando…').disabled);
 gate.resolve();await action;assert.match(text(ui.root),/1 divergência resolvida/);
 assert(!ui.calls.some(c=>c.url.endsWith('/decision')&&c.options.method==='POST'));
});
test('Specialized never requests or renders Dynamic reconciliation',async()=>{
 const ui=await pilot({automatic:true,auditRun:{...run,result:{...run.result,engine_mode:undefined}}});await ui.click('Abrir');
 assert.doesNotMatch(text(ui.root),/Reconciliação ·/);assert(!ui.calls.some(c=>c.url.includes('reconciliations')||c.url.endsWith('/policy')));
});
