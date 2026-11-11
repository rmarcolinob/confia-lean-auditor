const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
// Product-contract fixtures only: real-engine parity and scoring are Python tests.
function result(body,id,extra={}){return {audit_run_id:'aud_'+body.execution_key,question_attempt_id:id,transcription_version_id:`${body.transcription_id}:${body.revision_number}`,revision_number:body.revision_number,status:'COMPLETED',suggested_score:body.revision_number===1?12:16,max_score:20,review_required:false,review_reasons:[],warnings:[],rubric_items:[],evidences:[],checker_summary:[],engine_mode:'TME_CURRENT',engine_version:'test',completed_at:'2026-11-10T14:00:00Z',...extra};}
async function open(responder){const server=backend({auditResponder:responder}),[q1,q2]=server.detail.question_attempts;server.detail.mapping={version:2,bindings:server.detail.submission.pages.map((p,i)=>({question_attempt_id:i<2?q1.case_id:q2.case_id,exam_page_id:p.exam_page_id,order:i%2+1}))};const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${q1.case_id}`});return {ui,server,q1,q2};}
const audits=ui=>ui.calls.filter(c=>c.url.endsWith('/audits')&&c.options.method==='POST');
async function edit(ui){await ui.click('Comparar');await ui.click('Corrigir leitura');const area=walk(ui.root).find(n=>n.tag==='textarea');area.value='Leitura corrigida';area.handlers.input();await ui.click('Salvar nova revisão');}

test('D4 stale Q1 navigates independently of Q2 and reanalysis updates comparison and partial total',async()=>{
 const {ui,server,q1,q2}=await open(result);
 await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');
 await ui.click('Q2 · Pendente');await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');
 const q2before=JSON.stringify(server.audits.get(q2.case_id));
 await ui.click('Q1 · Pronta');await edit(ui);
 assert.match(text(ui.root),/Leitura alterada — reanálise necessária/);
 assert.match(text(ui.root),/Sugestão anterior: 12 \/ 20/);
 assert.match(text(ui.root),/Sugestão ConfIA parcial: 12 \/ 40/);
 assert.equal(audits(ui).length,2);
 await ui.click('Q2 · Pronta');assert.match(text(ui.root),/12 \/ 20/);
 await ui.click('Q1 · Revisão necessária');assert.match(text(ui.root),/Reanalisar questão/);
 await ui.click('Reanalisar questão');
 assert.match(text(ui.root),/Atualizado após correção da leitura/);
 assert.doesNotMatch(text(ui.root),/Aguardando análise/);
 assert.match(text(ui.root),/Sugestão anterior: 12 \/ 20/);assert.match(text(ui.root),/Sugestão atual: 16 \/ 20/);
 assert.match(text(ui.root),/Sugestão ConfIA: 28 \/ 40/);
 assert.match(text(ui.root),/Versão 1 .* preservada/);assert.match(text(ui.root),/Versão 2 .* corrente/);
 assert.match(text(ui.root),/x = 1/);assert.match(text(ui.root),/Leitura corrigida/);
 assert.equal(server.audits.get(q1.case_id).length,2);assert.equal(JSON.stringify(server.audits.get(q2.case_id)),q2before);
 assert.equal(audits(ui).length,3);
 assert.ok(walk(ui.root).some(n=>n.className==='correction-workspace'));
 assert.ok(walk(ui.root).some(n=>n.id==='tab-original'));
 assert.ok(walk(ui.root).some(n=>n.className==='pane-splitter'));
});

test('D4 reanalysis loading disables repeated click and keeps previous suggestion historical',async()=>{
 let release;const pending=new Promise(r=>release=r);
 const {ui}=await open(async(body,id)=>{if(body.revision_number===2)await pending;return result(body,id);});
 await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');await edit(ui);
 const trigger=walk(ui.root).find(n=>n.tag==='button'&&n.textContent==='Reanalisar questão');
 const first=trigger.click();await flush();await trigger.click();await flush();
 assert.match(text(ui.root),/Analisando matemática/);assert.equal(audits(ui).length,2);
 assert.ok(walk(ui.root).find(n=>n.tag==='button'&&n.textContent==='Reanalisar questão').disabled);
 assert.match(text(ui.root),/Sugestão anterior: 12 \/ 20/);
 release();await first;await flush();assert.match(text(ui.root),/Sugestão atual: 16 \/ 20/);
});

test('D4 failed reanalysis preserves null current and old score, explicit retry gets a new run',async()=>{
 let attempts=0;
 const {ui,server,q1}=await open((body,id)=>result(body,id,body.revision_number===2&&++attempts===1?{status:'FAILED',suggested_score:null,review_required:true,technical_uncertainty:true}:{}));
 await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');await edit(ui);await ui.click('Reanalisar questão');
 assert.match(text(ui.root),/Não foi possível concluir a reanálise/);
 assert.match(text(ui.root),/Pontuação não determinada/);assert.match(text(ui.root),/Sugestão atual: não determinada/);
 assert.match(text(ui.root),/Sugestão anterior: 12 \/ 20/);
 assert.match(text(ui.root),/Sugestão ConfIA parcial: 0 \/ 40/);
 assert.equal(server.audits.get(q1.case_id)[0].suggested_score,null);
 await ui.click('Tentar novamente');assert.match(text(ui.root),/Sugestão atual: 16 \/ 20/);
 const requests=audits(ui).map(c=>JSON.parse(c.options.body));assert.notEqual(requests[1].execution_key,requests[2].execution_key);
 assert.equal(server.audits.get(q1.case_id).length,3);
 assert.equal(server.audits.get(q1.case_id)[1].status,'FAILED');
});
