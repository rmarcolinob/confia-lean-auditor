const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
function audit(body,id){return {audit_run_id:'aud_'+body.execution_key,question_attempt_id:id,transcription_version_id:`${body.transcription_id}:${body.revision_number}`,revision_number:body.revision_number,status:'COMPLETED',suggested_score:id.endsWith('2')?15:20,max_score:20,review_required:id.endsWith('2'),review_reasons:id.endsWith('2')?['Confira o crédito parcial.']:[],warnings:[],rubric_items:[],evidences:[],checker_summary:[],engine_mode:'TME_CURRENT',engine_version:'fixture'};}
async function open(options={}){const server=backend({auditResponder:audit,...options}),[q1,q2]=server.detail.question_attempts;server.detail.mapping={version:2,bindings:server.detail.submission.pages.map((p,i)=>({question_attempt_id:i<2?q1.case_id:q2.case_id,exam_page_id:p.exam_page_id,order:i%2+1}))};const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${q1.case_id}`});await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');return {ui,server,q1,q2};}
const posts=ui=>ui.calls.filter(c=>c.url.endsWith('/decision')&&c.options.method==='POST');
const buttons=ui=>walk(ui.root).filter(n=>n.tag==='button');
const input=(ui,label)=>walk(ui.root).find(n=>n.tag==='label'&&n.textContent===label)?.children.at(-1);
function set(control,value){assert.ok(control);control.value=value;control.handlers.input();}

test('D5 accepts suggestion separately, confirms question, preserves audit and reopens with history',async()=>{
 const {ui,server,q1}=await open();const before=JSON.stringify(server.audits.get(q1.case_id));
 await ui.click('Aceitar sugestão');assert.match(text(ui.root),/✓ Confirmada/);assert.match(text(ui.root),/Nota final: 20 \/ 20/);assert.match(text(ui.root),/Sugestão aceita/);
 assert.match(text(ui.root),/Confirmado: 20 \/ 20/);assert.match(text(ui.root),/Histórico de decisões humanas \(1\)/);
 assert.equal(JSON.stringify(server.audits.get(q1.case_id)),before);assert.equal(posts(ui).length,1);
 assert.equal(buttons(ui).some(n=>n.textContent==='Aceitar sugestão'),false);
 await ui.click('Reabrir questão');assert.match(text(ui.root),/Confirmado: 0 \/ 0/);assert.match(text(ui.root),/Decisão histórica/);
 assert.ok(buttons(ui).some(n=>n.textContent==='Aceitar sugestão'));
 await ui.click('Aceitar sugestão');assert.equal(server.decisions.get(q1.case_id).length,2);
 assert.match(text(ui.root),/Histórico de decisões humanas \(2\)/);
});

test('D5 adjusts total with bounds and reason while keeping agent suggestion and review flag',async()=>{
 const {ui,server,q1,q2}=await open();await ui.click('Aceitar sugestão');
 await ui.click('Q2 · Pendente');await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');
 assert.match(text(ui.root),/Confira os alertas antes de homologar/);await ui.click('Ajustar nota');
 const score=input(ui,'Nota final da questão'),reason=input(ui,'Motivo do ajuste');
 set(score,'21');await ui.click('Confirmar ajuste');assert.match(text(ui.root),/entre 0 e 20/);assert.equal(posts(ui).length,1);
 set(score,'18');await ui.click('Confirmar ajuste');assert.match(text(ui.root),/Informe o motivo do ajuste/);assert.equal(posts(ui).length,1);
 set(reason,'Estratégia alternativa correta.');await ui.click('Confirmar ajuste');
 assert.match(text(ui.root),/Nota final: 18 \/ 20/);assert.match(text(ui.root),/Ajuste: \+3/);assert.match(text(ui.root),/ConfIA: 15 \/ 20/);
 assert.match(text(ui.root),/Confirmado: 38 \/ 40/);
 assert.equal(server.decisions.get(q2.case_id)[0].review_required_snapshot,true);
 await ui.click('Q1 · Confirmada · Final: 20/20');assert.match(text(ui.root),/Nota final: 20 \/ 20/);
 assert.equal(server.decisions.get(q1.case_id).length,1);
});

test('D5 editing confirmed reading invalidates it, reanalysis requires new confirmation and keeps Q2 isolated',async()=>{
 const {ui,server,q1}=await open();await ui.click('Aceitar sugestão');
 await ui.click('Corrigir leitura');set(walk(ui.root).find(n=>n.tag==='textarea'),'leitura nova');await ui.click('Salvar nova revisão');
 assert.match(text(ui.root),/reanálise necessária/);assert.match(text(ui.root),/Decisão histórica/);assert.match(text(ui.root),/Confirmado: 0 \/ 0/);
 assert.equal(buttons(ui).some(n=>n.textContent==='Aceitar sugestão'),false);
 await ui.click('Reanalisar questão');assert.ok(buttons(ui).some(n=>n.textContent==='Aceitar sugestão'));
 assert.match(text(ui.root),/Confirmado: 0 \/ 0/);await ui.click('Aceitar sugestão');assert.equal(server.decisions.get(q1.case_id).length,2);
 await ui.click('Executar nova análise');assert.match(text(ui.root),/Confirmado: 0 \/ 0/);assert.ok(buttons(ui).some(n=>n.textContent==='Aceitar sugestão'));
});

test('D5 confirmation processing prevents double click and stale conflict refreshes without confirming',async()=>{
 let release;const pending=new Promise(r=>release=r);
 const {ui,server,q1}=await open({decisionResponder:async()=>{await pending;return {status:409};}});
 const trigger=buttons(ui).find(n=>n.textContent==='Aceitar sugestão');const first=trigger.click();await flush();await trigger.click();await flush();
 assert.match(text(ui.root),/Registrando decisão/);assert.equal(posts(ui).length,1);assert.ok(buttons(ui).find(n=>n.textContent==='Aceitar sugestão').disabled);
 release();await first;await flush();assert.match(text(ui.root),/A análise, leitura ou decisão mudou/);assert.equal(server.decisions.has(q1.case_id),false);
});

test('D5 failed or absent suggestion cannot be accepted or adjusted',async()=>{
 const {ui}=await open({auditResponder:(body,id)=>({...audit(body,id),status:'FAILED',suggested_score:null,review_required:true})});
 assert.equal(buttons(ui).some(n=>['Aceitar sugestão','Ajustar nota'].includes(n.textContent)),false);
 assert.match(text(ui.root),/análise atual com pontuação disponível/);assert.match(text(ui.root),/Pontuação não determinada/);
});
