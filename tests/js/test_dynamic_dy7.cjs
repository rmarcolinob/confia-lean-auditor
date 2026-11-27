const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid,aid,reply}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
function metrics(){const s={score:{N:2,MAE:'1',exact_score_agreement:'.5'},criterion:{false_credit_rate:'.1',missed_credit_rate:'.2'},review_rate:'.5',automation_coverage:'.5',unsafe_automation_rate:'0'};
return {N:2,strata:[{profile:'SCHOOL_EXAM',split:'HOLDOUT',source_kind:'SYNTHETIC',metrics:{N:2,stages:{G0:s,G1:s,G2:s,G3:s},human_override:{rate:'.5'},technical_failure_cases:1,exclusions:{RUBRIC_MISMATCH:1}}}]};}
test('DY7 shared certification shows separate stages, provenance strata and frozen exports',async()=>{
 const server=backend(),comparison={N:2,MAE:'1',exact_score_agreement:'.5'},base=`/tme/assessments/${aid}/certification`;
 const ui=await pilot({fullExam:true,initialSearch:`?exam_submission_id=${eid}`,mockFetch:async(url,options)=>{
 if(url===`/tme/exam-submissions/${eid}/correction`)return reply({...server.correction(),assessment_id:aid,certification_available:true});
 if(url===base+'/runs')return reply([{id:'run_1',verdict:{status:'PILOT_METRICS_AVAILABLE'}}]);
 if(url===base+'/runs/run_1')return reply({metrics:metrics(),verdict:{status:'PILOT_METRICS_AVAILABLE'}});
 if(url.startsWith(base))return reply({manifest:{counts:{proofs:2,questions:2,records:2,gold_available:2},gold:null},gold_history:[],dynamic_metrics:metrics(),
 metrics:{confia_vs_gold:comparison,confia_vs_human_decision:comparison,human_decision_vs_gold:comparison,stages:{audit:{review_rate:'.5'},human_adjustment:{adjustment_rate:'.5'}}}});
 return server.mockFetch(url,options);}});
 await ui.click('Resumo da correção');await ui.click('Certificação');
 assert.match(text(ui.root),/G0 · N: 2/);assert.match(text(ui.root),/G1 · N: 2/);assert.match(text(ui.root),/G2 · N: 2/);
 assert.match(text(ui.root),/SCHOOL_EXAM · HOLDOUT · SYNTHETIC/);assert.match(text(ui.root),/Falso crédito: 10.0%/);
 assert.match(text(ui.root),/RUBRIC_MISMATCH: 1/);assert.match(text(ui.root),/Falhas técnicas: 1/);
 assert.match(text(ui.root),/SHADOW_EVALUATION/);assert.doesNotMatch(text(ui.root),/PRODUCTION_READY|CERTIFIED/);
 await ui.click('Execuções experimentais');await flush();assert.match(text(ui.root),/PILOT_METRICS_AVAILABLE/);
 const links=walk(ui.root).filter(n=>n.tag==='a'&&n.href.includes('/runs/run_1/'));
 assert.equal(links.length,3);assert.ok(links.some(n=>n.href.endsWith('/export.csv')));
 await ui.click('Ver métricas da execução');await flush();assert.match(text(ui.root),/Crédito perdido: 20.0%/);
});
