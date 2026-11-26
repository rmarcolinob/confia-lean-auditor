const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid,reply}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
async function handwriting(){
 const server=backend({auditResponder:(b,id)=>({audit_run_id:'aud_test',question_attempt_id:id,transcription_version_id:`${b.transcription_id}:${b.revision_number}`,revision_number:b.revision_number,status:'COMPLETED',suggested_score:null,engine_mode:'DYNAMIC',review_required:true,rubric_items:[]})});
 const c=server.detail.question_attempts[0];c.dynamic_context={statement_version:1};c.problem_id='dyn_novel';let confirmed=0;
 server.detail.mapping.bindings=[{question_attempt_id:c.case_id,exam_page_id:server.detail.submission.pages[0].exam_page_id,order:1}];
 const mockFetch=async(url,options)=>{
  if(url==='/dynamic/problems/dyn_novel')return reply({statements:[{version_number:1,title:'Frações',statement:'Calcule três quartos de 24.',max_score:20}],rubrics:[]});
  if(url.endsWith('/confirm-reading')){const b=JSON.parse(options.body);assert.equal(b.confirmed,true);assert.equal(b.question_scope_confirmed,true);confirmed=b.revision_number;return reply({});}
  const response=await server.mockFetch(url,options);
  if(url.endsWith('/workspace')){const w=await response.json(),v=w.history?.revisions.at(-1);w.reading_review={required:true,shared_pages:[1],status:!v?'NO_TRANSCRIPTION':v.segments.some(s=>s.kind==='unknown')?'UNRESOLVED':confirmed===v.revision_number?'CONFIRMED':'NEEDS_CONFIRMATION',revision_number:v?.revision_number,revision_sha256:'a'.repeat(64),technically_accepted:Boolean(w.history?.acceptances.length)};return reply(w);}
  return response;
 };
 const ui=await pilot({fullExam:true,mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${c.case_id}`});
 await ui.click('Importar leitura da captura');return {ui,server,c};
}
test('handwritten Dynamic requires explicit scope confirmation before technical acceptance and analysis',async()=>{
 const {ui}=await handwriting();assert.match(text(ui.root),/ainda não conferida/);assert.match(text(ui.root),/compartilhada/);
 await ui.click('Analisar com ConfIA');assert(!ui.calls.some(c=>c.url.endsWith('/accept')));assert(!ui.calls.some(c=>c.url.endsWith('/audits')&&c.options.method==='POST'));
 await ui.click('Confirmar leitura desta questão');assert(!ui.calls.some(c=>c.url.endsWith('/confirm-reading')));
 const check=walk(ui.root).find(n=>n.getAttribute('aria-label')==='Conferi o texto com os originais e somente os trechos desta questão');assert(check);check.checked=true;check.handlers.change();
 await ui.click('Confirmar leitura desta questão');assert.match(text(ui.root),/conferidos explicitamente/);
 await ui.click('Analisar com ConfIA');assert(ui.calls.some(c=>c.url.endsWith('/accept')));assert(ui.calls.some(c=>c.url.endsWith('/audits')&&c.options.method==='POST'));
});
test('unreadable page remains explicitly pending after a saved revision',async()=>{
 const {ui,server,c}=await handwriting();await ui.click('Corrigir leitura');
 const flag=walk(ui.root).find(n=>n.dataset.unreadablePage==='0');assert(flag);flag.checked=true;flag.handlers.change();
 await ui.click('Salvar nova revisão');await flush();
 assert.equal(server.histories.get(c.case_id).revisions.at(-1).segments[0].kind,'unknown');
 assert.match(text(ui.root),/Há trechos ilegíveis/);
 const analyze=walk(ui.root).find(n=>n.tag==='button'&&/Analisar com ConfIA|Reanalisar questão/.test(n.textContent));assert(analyze.disabled);
});
test('active Dynamic activity exposes existing upload callback with its own assessment ID',async()=>{
 const {element,descendants}=require('./ui-dom.cjs');const n=t=>{const e=element(t);e.append=(...c)=>c.forEach(x=>e.appendChild(x));return e;};
 const host=n('section'),window={},uploads=[];
 const doc={assessment:{assessment_id:'asmt_a',title:'Ensino Fundamental',status:'PUBLISHED'},readiness:{state:'ACTIVE',ready_questions:3,total_questions:3,questions:[]}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../app/confia_lean_auditor/static/dynamic-assessment.js'),'utf8'),{window,document:{createElement:n},fetch:async url=>reply(url==='/tme/exam-submissions'?[]:doc)});
 await window.ConfIADynamicAssessment.create({host,onUpload:id=>uploads.push(id)}).load('asmt_a');
 const button=descendants(host).find(n=>n.textContent==='Enviar fotografias ou PDF');assert(button);await button.click();assert.deepEqual(uploads,['asmt_a']);
});
test('summary derives protected original route from IDs, not redacted artifact URLs',async()=>{
 const server=backend(),c=server.detail.question_attempts[0];
 const mockFetch=async(url,options)=>{
  const response=await server.mockFetch(url,options);
  if(url.endsWith('/correction')){const data=await response.json();data.questions[0].engine_mode='DYNAMIC';return reply(data);}
  if(url.endsWith('/workspace')){const w=await response.json();w.current_audit={rubric_items:[{rubric_item_id:'method',label:'Método',max_points:2,suggested_points:1,evidence_ids:['e1']}],evidences:[{evidence_id:'e1',text:'Passo do aluno',source_pages:[{page_number:2,original_asset_id:'original_0002',original_url:'[local path hidden]'}]}]};return reply(w);}
  return response;
 };
 const ui=await pilot({fullExam:true,mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${c.case_id}`});
 await ui.click('Resumo da correção');await ui.click('Ver critérios Q1');
 const link=walk(ui.root).find(n=>n.tag==='a'&&n.textContent==='Original · página 2');assert(link);assert.equal(link.href,`/tme/exam-submissions/${eid}/assets/original_0002`);
 assert.match(text(ui.root),/Passo do aluno/);
});
test('unsaved reading edit cannot confirm the preceding version',async()=>{
 const {ui}=await handwriting();
 const check=walk(ui.root).find(n=>n.getAttribute('aria-label')==='Conferi o texto com os originais e somente os trechos desta questão');check.checked=true;check.handlers.change();
 await ui.click('Corrigir leitura');await ui.click('Confirmar leitura desta questão');
 assert(!ui.calls.some(c=>c.url.endsWith('/confirm-reading')));
});
test('unchanged legacy TME reading preserves unknown segments without a fabricated revision',async()=>{
 const server=backend(),c=server.detail.question_attempts[0];
 server.detail.mapping.bindings=[{question_attempt_id:c.case_id,exam_page_id:server.detail.submission.pages[0].exam_page_id,order:1}];
 await server.mockFetch(`/tme/cases/${c.case_id}/transcriptions`,{method:'POST',body:JSON.stringify({origin:'manual',segments:[{segment_id:'unknown:0',page_index:0,order:0,kind:'unknown',text:'Trecho não resolvido'}]})});
 const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${c.case_id}`});
 await ui.click('Corrigir leitura');await ui.click('Salvar nova revisão');
 assert.equal(server.histories.get(c.case_id).revisions.length,1);assert.equal(server.histories.get(c.case_id).revisions[0].segments[0].kind,'unknown');
});
