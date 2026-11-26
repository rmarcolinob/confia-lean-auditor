const test=require('node:test'),assert=require('node:assert/strict');
const {flush}=require('./capture-dom.cjs');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid}=require('./exam-fixture.cjs');
const input=(ui,label)=>walk(ui.root).find(n=>n.tag==='label'&&n.textContent===label)?.children.at(-1);
function set(control,value){assert.ok(control);control.value=value;control.handlers.input();}
async function open(){
 const server=backend({auditResponder:(body,id)=>({audit_run_id:'aud_'+body.execution_key,question_attempt_id:id,transcription_version_id:`${body.transcription_id}:${body.revision_number}`,revision_number:body.revision_number,status:'COMPLETED',suggested_score:null,suggestion_ready:false,max_score:20,review_required:true,review_reasons:['Divergência entre avaliadores.'],warnings:[],engine_mode:'DYNAMIC',engine_version:'test',reconciliation_id:'rec-test',reconciliation:{reconciliation_id:'rec-test',context:{rubric_sha256:'a'.repeat(64)},criteria:[{criterion_id:'area',status:'REVIEW_REQUIRED',reason:'Divergência.'}]},rubric_items:[{rubric_item_id:'area',label:'Área',max_points:20,suggested_points:null,grader_explanation:'Cálculo parcial.',dependencies:['base'],evidence_ids:[],children:[]}],independent_review:{phase_a:{criterion_reviews:[{criterion_id:'area',explanation:'Justificativa insuficiente.',evidence:['Texto do aluno.']}]}}})});
 const [q1,q2]=server.detail.question_attempts;
 server.detail.mapping={version:2,bindings:server.detail.submission.pages.map((p,i)=>({question_attempt_id:i<2?q1.case_id:q2.case_id,exam_page_id:p.exam_page_id,order:i%2+1}))};
 const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${q1.case_id}`});
 await ui.click('Importar leitura da captura');await ui.click('Analisar com ConfIA');return {ui,server};
}
const posts=ui=>ui.calls.filter(c=>c.url.endsWith('/decision')&&c.options.method==='POST');
test('inconclusive Dynamic displays separate opinions and blank explicit human inputs',async()=>{
 const {ui}=await open();const t=text(ui.root);
 for(const label of ['Parecer do Grader','Parecer do Reviewer','Resultado da Reconciliation','Cálculo parcial.','Justificativa insuficiente.','Divergência.'])assert(t.includes(label),label);
 assert.equal(input(ui,'Área · pontos (máximo 20)').value,'');
 assert(!walk(ui.root).some(n=>n.tag==='button'&&n.textContent==='Aceitar sugestão'));
 await ui.click('Confirmar adjudicação humana');assert.equal(posts(ui).length,0);
 assert.match(text(ui.root),/Decida todos os critérios/);
});
for(const points of ['0','10','20'])test(`explicit human ${points}, per-criterion justification and rubric binding`,async()=>{
 const {ui}=await open();set(input(ui,'Área · pontos (máximo 20)'),points);set(input(ui,'Área · justificativa'),'Resolução conferida.');
 await ui.click('Confirmar adjudicação humana');assert.equal(posts(ui).length,0);
 set(input(ui,'Área · aplicação das dependências (base)'),'Dependência conferida na resolução.');
 await ui.click('Confirmar adjudicação humana');assert.equal(posts(ui).length,0);
 set(input(ui,'Justificativa da adjudicação humana'),'Conferência docente por critério.');
 const form=walk(ui.root).find(n=>n.tag==='form'&&n.getAttribute('aria-label')==='Adjudicação humana por critério');
 assert(form);await form.handlers.submit({preventDefault(){}});await flush();await flush();
 const body=JSON.parse(posts(ui)[0].options.body);assert.equal(Number(body.final_points),Number(points));assert.equal(body.adjudication.criteria[0].final_points,points);assert.equal(body.adjudication.rubric_sha256,'a'.repeat(64));
 assert.match(text(ui.root),/Decisão humana por critério/);assert.match(text(ui.root),/ConfIA: Não determinada/);
});
test('human bounds are enforced before posting',async()=>{const {ui}=await open();set(input(ui,'Área · pontos (máximo 20)'),'21');await ui.click('Confirmar adjudicação humana');assert.equal(posts(ui).length,0);});
