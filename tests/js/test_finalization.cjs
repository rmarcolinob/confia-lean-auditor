const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
const audit=(b,id)=>({audit_run_id:'aud_'+b.execution_key,question_attempt_id:id,transcription_version_id:`${b.transcription_id}:${b.revision_number}`,revision_number:b.revision_number,status:'COMPLETED',suggested_score:id.endsWith('2')?15:20,max_score:20,review_required:id.endsWith('2'),review_reasons:[],warnings:[],rubric_items:[],evidences:[],checker_summary:[],engine_mode:'TME_CURRENT',engine_version:'fixture'});
const button=(ui,label)=>walk(ui.root).find(n=>n.tag==='button'&&n.textContent===label);
const set=(ui,label,value)=>{const c=walk(ui.root).find(n=>n.tag==='label'&&n.textContent===label)?.children.at(-1);assert.ok(c);c.value=value;c.handlers.input();};
async function open(options={}){const server=backend({auditResponder:audit,...options}),[q1,q2]=server.detail.question_attempts;server.detail.mapping={version:2,bindings:server.detail.submission.pages.map((p,i)=>({question_attempt_id:i<2?q1.case_id:q2.case_id,exam_page_id:p.exam_page_id,order:i%2+1}))};const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${q1.case_id}`});return {ui,server,q1,q2};}
async function ready(options={}){const ctx=await open(options),{ui}=ctx;await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');await ui.click('Aceitar sugestão');await ui.click('Q2 · Pendente');await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');await ui.click('Ajustar nota');set(ui,'Nota final da questão','18');set(ui,'Motivo do ajuste','Crédito parcial.');await ui.click('Confirmar ajuste');await ui.click('Resumo da correção');return ctx;}

test('D6 summary names pending questions, incomplete totals and opens a blocker',async()=>{
 const {ui}=await open();await ui.click('Resumo da correção');
 assert.match(text(ui.root),/Não é possível finalizar/);assert.match(text(ui.root),/ConfIA parcial — incompleto: —/);assert.match(text(ui.root),/Q2: Questão ainda não confirmada/);
 assert.ok(button(ui,'Finalizar correção').disabled);await ui.click('Abrir Q2 pendente');assert.match(text(ui.root),/Questão 2/);
});

test('D6 preview separates totals, review and adjustment before explicit final confirmation',async()=>{
 const {ui,server}=await ready();assert.match(text(ui.root),/ConfIA: 35 \/ 40/);assert.match(text(ui.root),/Final humano: 38 \/ 40/);assert.match(text(ui.root),/Ajuste total: \+3/);assert.match(text(ui.root),/Confirmada após revisão/);assert.match(text(ui.root),/1 de 2 questões tiveram ajuste humano/);
 assert.equal(server.correction().current_final_correction,null);await ui.click('Finalizar correção');assert.equal(server.correction().current_final_correction,null);
 assert.match(text(ui.root),/Confirme o fechamento/);await ui.click('Confirmar finalização');assert.match(text(ui.root),/Correção finalizada/);assert.match(text(ui.root),/Histórico de fechamento \(1\)/);assert.ok(server.correction().current_final_correction);
});

test('D6 finalized question disables edits and audit; reopening preserves decisions and versions',async()=>{
 const {ui,server}=await ready();await ui.click('Finalizar correção');await ui.click('Confirmar finalização');
 await ui.click('Q1');assert.ok(button(ui,'Corrigir leitura').disabled);assert.ok(button(ui,'Executar nova análise').disabled);assert.equal(button(ui,'Reabrir questão'),undefined);
 await ui.click('Ver correção finalizada');await ui.click('Reabrir correção');await ui.click('Confirmar reabertura');assert.match(text(ui.root),/Correção reaberta/);assert.equal(server.correction().confirmed_question_count,2);
 await ui.click('Finalizar correção');await ui.click('Confirmar finalização');assert.match(text(ui.root),/Histórico de fechamento \(2\)/);assert.equal(server.correction().current_final_correction.version,2);
});

test('D6 double click is suppressed and stale finalization displays refreshed summary',async()=>{
 let release;const wait=new Promise(r=>release=r);const {ui}=await ready({finalizationResponder:async()=>{await wait;return {status:409};}});
 await ui.click('Finalizar correção');const trigger=button(ui,'Confirmar finalização');const first=trigger.click();await flush();await trigger.click();await flush();
 assert.equal(ui.calls.filter(c=>c.url.endsWith('/correction/finalize')).length,1);assert.ok(trigger.disabled);release();await first;await flush();
 assert.match(text(ui.root),/A prova mudou ou possui pendências/);assert.ok(button(ui,'Finalizar correção'));assert.equal(button(ui,'Reabrir correção'),undefined);
});

test('D6 finalized exam is visible on home with total and adjustment count',async()=>{
 const {ui}=await ready();await ui.click('Finalizar correção');await ui.click('Confirmar finalização');
 await ui.shell['home-bottom-nav'].children[0].click();await flush();assert.match(text(ui.root),/Finalizada · Final 38 · 1 ajustes/);
});
