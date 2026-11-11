const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid,aid,reply}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
function dataset(gold=false){const comparison={N:gold?3:0,MAE:gold?'1.333333333333':null,exact_score_agreement:gold?'0.333333333':null};return {
 manifest:{counts:{proofs:1,questions:3,records:3,gold_available:gold?3:0},gold:gold?{source_id:'external',dataset_version:'v1',version:1}:null},gold_history:gold?[{version:1,dataset_version:'v1'}]:[],
 metrics:{confia_vs_gold:comparison,confia_vs_human_decision:{N:3,MAE:'1.333'},human_decision_vs_gold:comparison,stages:{audit:{review_rate:'0.3333'},human_adjustment:{adjustment_rate:'0.6666'}}}};}
async function open({gold=false,enabled=true,fail=false}={}){const server=backend();let imported=gold;const ui=await pilot({fullExam:true,initialSearch:`?exam_submission_id=${eid}`,mockFetch:async(url,options)=>{
 if(url===`/tme/exam-submissions/${eid}/correction`)return reply({...server.correction(),assessment_id:aid,certification_available:enabled});
 if(url.startsWith(`/tme/assessments/${aid}/certification`)){
   if(options.method==='POST'){if(fail)return {ok:false,status:409,json:async()=>({})};imported=true;return reply({version:1});}return reply(dataset(imported));}
 return server.mockFetch(url,options);
 }});await ui.click('Resumo da correção');if(enabled)await ui.click('Certificação');return ui;}
const control=(ui,label)=>walk(ui.root).find(n=>n.attributes?.['aria-label']===label||n.getAttribute?.('aria-label')===label);

test('D7 opt-in area no gold and explicit SHADOW, never fabricated zero MAE',async()=>{
 const ui=await open();assert.match(text(ui.root),/Gold humano ainda não importado/);assert.match(text(ui.root),/SHADOW_EVALUATION/);assert.match(text(ui.root),/não alteram a correção oficial/);assert.match(text(ui.root),/N: 0 · MAE: —/);assert.match(text(ui.root),/Provas: 1 · Questões: 3/);
 await ui.click('Voltar ao resumo');assert.match(text(ui.root),/Resumo da correção/);
 const disabled=await open({enabled:false});assert.ok(!walk(disabled.root).some(n=>n.textContent==='Certificação'));
});
test('D7 gold metrics and CSV JSON links preserve cohort filters',async()=>{
 const ui=await open({gold:true});assert.match(text(ui.root),/Gold importado: external \/ v1/);assert.match(text(ui.root),/MAE: 1,333/);assert.match(text(ui.root),/Concordância exata: 33.3%/);assert.match(text(ui.root),/Questões ajustadas: 66.7%/);
 const links=walk(ui.root).filter(n=>n.tag==='a');assert.equal(links.length,2);assert.ok(links.every(n=>n.href.endsWith('?selection=finalized')));
 const select=control(ui,'Seleção das provas');select.value='current';await select.handlers.change();await flush();assert.ok(walk(ui.root).filter(n=>n.tag==='a').every(n=>n.href.endsWith('?selection=current')));
 const version=control(ui,'Versão do gold');version.value='1';await version.handlers.change();await flush();assert.ok(walk(ui.root).filter(n=>n.tag==='a').every(n=>n.href.includes('gold_version=1')));
 const mode=control(ui,'Motor');mode.value='DYNAMIC';await ui.click('Aplicar motor');assert.ok(walk(ui.root).filter(n=>n.tag==='a').every(n=>n.href.includes('engine_mode=DYNAMIC')));
});
test('D7 import CSV refreshes independent gold metrics and asks no student identity',async()=>{
 const ui=await open();control(ui,'Fonte do gold').value='external';control(ui,'Versão do dataset').value='v1';control(ui,'Conteúdo do gold').value='assessment_id,participant_code,question_id,gold_score,max_score\na,p,q,1,2';
 await walk(ui.root).find(n=>n.tag==='form').handlers.submit({preventDefault(){}});await flush();
 assert.match(text(ui.root),/Gold importado. Histórico preservado/);const call=ui.calls.find(c=>c.url.includes('/gold?'));
 assert.equal(call.options.headers['Content-Type'],'text/csv');assert.ok(call.url.includes('expected_version=0'));
 assert.doesNotMatch(text(ui.root),/CPF|e-mail|Nome do estudante/);
});
test('D7 JSON import envelope and conflict feedback preserve input',async()=>{
 const ui=await open({fail:true});control(ui,'Formato do gold').value='JSON';control(ui,'Fonte do gold').value='external';control(ui,'Versão do dataset').value='v1';control(ui,'Conteúdo do gold').value='[]';
 await walk(ui.root).find(n=>n.tag==='form').handlers.submit({preventDefault(){}});await flush();assert.match(text(ui.root),/O gold mudou/);
 const call=ui.calls.find(c=>c.url.endsWith('/gold'));assert.equal(JSON.parse(call.options.body).source_id,'external');assert.equal(control(ui,'Conteúdo do gold').value,'[]');
});
