const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
function result(body,id,extra={}){
  return {schema_version:'question-audit.v1',audit_run_id:'aud_'+body.execution_key,question_attempt_id:id,
    transcription_version_id:`${body.transcription_id}:${body.revision_number}`,revision_number:body.revision_number,
    status:'COMPLETED',analysis_status:'COMPLETED',stale:false,engine_mode:'TME_CURRENT',engine_version:'test-contract.v1',engine_config:{use_lean:false},
    suggested_score:16,max_score:20,review_required:false,review_reasons:[],warnings:[],technical_uncertainty:false,
    rubric_items:[{rubric_item_id:'criterion-a',label:'Critério vindo do backend',suggested_points:2,max_points:2,status:'decided',status_label:'Verificado',evidence_ids:['e1'],checker_ids:['check1'],children:[]}],
    evidences:[{evidence_id:'e1',text:'731 - 137 = 594',exam_page_id:'page_'+'1'.repeat(32),page_number:2,page_reference_scope:'item_page'}],
    checker_summary:[{checker_id:'check1',status:'verified',status_label:'Verificação formal deste passo concluída'}],...extra};
}
async function open(responder){
  const server=backend({auditResponder:responder}),[q1,q2]=server.detail.question_attempts;
  server.detail.mapping={version:2,bindings:[...server.detail.submission.pages.map((p,i)=>({question_attempt_id:q1.case_id,exam_page_id:p.exam_page_id,order:i+1})),{question_attempt_id:q2.case_id,exam_page_id:server.detail.submission.pages[1].exam_page_id,order:1}]};
  const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${q1.case_id}`});
  return {server,ui,q1,q2};
}
const buttons=ui=>walk(ui.root).filter(n=>n.tag==='button');
const postAudits=ui=>ui.calls.filter(c=>c.url.endsWith('/audits')&&c.options.method==='POST');

test('question analysis loading prevents double submit and renders backend score criteria evidence and page action',async()=>{
  let resolve;const pending=new Promise(r=>resolve=r);
  const {ui}=await open(async(body,id)=>{await pending;return result(body,id);});
  await ui.click('Importar leitura da captura');
  const trigger=buttons(ui).find(n=>n.textContent==='Analisar com ConfIA');
  const first=trigger.click();await flush();await trigger.click();await flush();
  assert.match(text(ui.root),/Analisando matemática/);assert.equal(postAudits(ui).length,1);
  assert.ok(buttons(ui).find(n=>n.textContent==='Analisar com ConfIA').disabled);
  resolve();await first;await flush();
  assert.match(text(ui.root),/Sugestão ConfIA/);assert.match(text(ui.root),/16 \/ 20/);
  assert.match(text(ui.root),/Critério vindo do backend/);assert.match(text(ui.root),/731 - 137 = 594/);
  assert.match(text(ui.root),/Verificação formal deste passo concluída/);
  assert.equal(buttons(ui).some(n=>n.textContent==='Finalizar correção'),false);
  assert.equal(walk(ui.root).find(n=>n.className==='workspace-actions').dataset.quiet,'false');
  await ui.click('Ver no original · página 2');
  assert.match(text(ui.root),/Página 2\/4/);
  assert.equal(walk(ui.root).find(n=>n.id==='tab-original').attributes['aria-selected'],'true');
});

test('Q1 Q2 preserve separate audit runs, new explicit analysis preserves history, editing makes old audit historical',async()=>{
  const {ui,server,q1,q2}=await open((body,id)=>result(body,id,{suggested_score:id.endsWith('2')?8:16}));
  await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');
  const old=server.audits.get(q1.case_id)[0].audit_run_id;
  await ui.click('Executar nova análise');assert.equal(server.audits.get(q1.case_id).length,2);
  assert.match(text(ui.root),/Histórico de análises \(1\)/);
  await ui.click('Q2 · Pendente');assert.match(text(ui.root),/Aguardando análise/);
  await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');assert.match(text(ui.root),/8 \/ 20/);
  await ui.click('Q1 · Pronta');assert.match(text(ui.root),/16 \/ 20/);assert.equal(postAudits(ui).length,3);
  assert.ok(server.audits.get(q1.case_id).some(r=>r.audit_run_id===old));
  await ui.click('Corrigir leitura');const area=walk(ui.root).find(n=>n.tag==='textarea');area.value='texto corrigido';area.handlers.input();
  assert.ok(buttons(ui).find(n=>n.textContent==='Executar nova análise').disabled);
  await ui.click('Salvar nova revisão');assert.match(text(ui.root),/Reanálise necessária/);
  assert.match(text(ui.root),/Sugestão ConfIA anterior/);assert.match(text(ui.root),/Histórico de análises \(2\)/);
  assert.match(text(ui.root),/Aguardando análise/);assert.equal(postAudits(ui).length,3);
});

test('technical failure has no numerical fallback and warning/review stays readable without unsupported original action',async()=>{
  const {ui}=await open((body,id)=>result(body,id,{status:'FAILED',suggested_score:null,review_required:true,technical_uncertainty:true,
    review_reasons:['A análise não foi concluída por uma falha técnica.'],warnings:['Trecho sem identificação de item.'],rubric_items:[],evidences:[],checker_summary:[]}));
  await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');
  assert.match(text(ui.root),/Pontuação não determinada/);assert.match(text(ui.root),/Revisar/);
  assert.match(text(ui.root),/falha técnica/);assert.match(text(ui.root),/Trecho sem identificação/);
  assert.doesNotMatch(text(ui.root),/0 \/ 20/);assert.equal(buttons(ui).some(n=>n.textContent.startsWith('Ver no original')),false);
});

test('ambiguous network result retries the same key, then a new requested analysis receives a new key',async()=>{
  let count=0;const {ui}=await open((body,id)=>++count===1?{httpError:true}:result(body,id));
  await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');
  assert.match(text(ui.root),/Não foi possível concluir/);await ui.click('Analisar com ConfIA');
  await ui.click('Executar nova análise');
  const keys=postAudits(ui).map(c=>JSON.parse(c.options.body).execution_key);
  assert.equal(keys[0],keys[1]);assert.notEqual(keys[1],keys[2]);
});
