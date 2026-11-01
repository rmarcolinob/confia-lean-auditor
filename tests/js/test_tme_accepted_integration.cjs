const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
function result(){
  const statuses=['supported','refuted','indeterminate','technical_error'];
  const obligations=statuses.map((status,i)=>({obligation_id:`a.o${i}`,effective_status:status,source_claim_ids:[`r${i}`],verification_source:i<2?'student_lean':'deterministic'}));
  return {schema_version:'tme-audit-result.v1',problem_id:'TME2026P2',score:null,max_score:20,needs_review:true,
    pauta:{obligations:statuses.map((_,i)=>({id:`a.o${i}`,description:`Etapa matemática ${i+1}`})),items:[{id:'a',children:[]}]},
    assessment:{needs_review:true,items:[{item_id:'a',status:'technical_error',points_awarded:null,max_points:5,known_points:1,possible_points:5,needs_review:true,obligations,children:[],carry_forward_applied:true}]},
    bridge:{auditor:{records:statuses.map((_,i)=>({record_id:`r${i}`,source:{raw_text:`expressão aceita ${i+1}`}})),facts:[
      {source_claim_ids:['r0'],student_check:{status:'verified',compiled:true,lean_file:'proof.lean'}},
      {source_claim_ids:['r1'],student_check:{status:'refuted',refutation_verified:true,refutation_lean_file:'negative.lean'}}]}}};
}
test('pauta workspace preserves pending score, four statuses, source evidence and local formal labels',async()=>{
  const data=result(),before=JSON.stringify(data);
  const ui=await pilot({auditRun:{audit_run_id:'aud_'+'a'.repeat(64),status:'COMPLETED',stale:false,result:data}});await ui.click('Abrir');
  const report=walk(ui.root).find(e=>e.className==='workspace-report');
  const visible=report.children.filter(e=>e.className!=='technical-details').map(text).join('\n');
  assert.match(visible,/Pontuação não determinada/);assert.match(visible,/Item \(a\) — Pendente \/ 5/);
  for(const label of ['Atendido','Afirmação refutada','Não foi possível determinar com segurança','Erro técnico','expressão aceita 1','Verificação formal com Lean: confirmada (etapa local).','Verificação formal: afirmação incompatível (etapa local).','continuidade coerente']) assert.ok(visible.includes(label),label);
  assert.doesNotMatch(visible,/MathClaimRecord|FactResult|PautaEvidence|canonicalization|a\.o0|r0|checker/);
  assert.equal(JSON.stringify(data),before);
  assert.equal(walk(ui.root).find(e=>e.textContent==='Usar sugestão').disabled,true);
});
test('uncompiled check does not advertise a Lean confirmation',async()=>{
  const data=result();data.bridge.auditor.facts[0].student_check.compiled=false;
  const ui=await pilot({auditRun:{audit_run_id:'aud_'+'b'.repeat(64),status:'COMPLETED',stale:false,result:data}});await ui.click('Abrir');
  const criteria=walk(ui.root).find(e=>e.className==='dense-criteria');assert.doesNotMatch(text(criteria),/Lean: confirmada/);
});
test('P5 labels are pedagogical rather than internal obligation identifiers',async()=>{
  const data=result();data.problem_id='TME2026P5';data.pauta.obligations[0]={id:'a.product',description:'a.product'};
  data.assessment.items[0].obligations[0].obligation_id='a.product';
  const ui=await pilot({auditRun:{audit_run_id:'aud_'+'c'.repeat(64),status:'COMPLETED',stale:false,result:data}});await ui.click('Abrir');
  const criteria=walk(ui.root).find(e=>e.className==='dense-criteria');assert.match(text(criteria),/Calcula o produto da decomposição/);assert.doesNotMatch(text(criteria),/a\.product/);
});
