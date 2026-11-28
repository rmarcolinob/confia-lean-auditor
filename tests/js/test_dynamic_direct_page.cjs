// Synthetic transport/state responses only; these tests do not evaluate mathematics.
const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const pid='dyn_'+'d'.repeat(32),cid='case_'+'a'.repeat(32),reply=data=>({ok:true,json:async()=>data});
const field=(ui,label)=>walk(ui.root).find(n=>n.attributes['aria-label']===label);
const button=(ui,label)=>walk(ui.root).find(n=>n.tag==='button'&&n.textContent===label);
function fill(ui,label,value){const el=field(ui,label);assert(el,label);el.value=value;el.handlers.input?.();return el;}
async function screen({existing=null,failure=false}={}){
 let doc=existing,accepted=false;const writes=[];
 const ui=await pilot({initialSearch:'?view=new&mode=dynamic'+(existing?'&problem_id='+pid:''),mockFetch:async(url,options)=>{
  if(url==='/dynamic/capabilities')return reply({rubric_suggestion_configured:false});
  if(url.startsWith('/dynamic/problems')){
   if(!options.body)return reply(doc);const body=JSON.parse(options.body);writes.push({url,body,method:options.method});
   if(failure)return {ok:false,json:async()=>({detail:'Falha de armazenamento'})};
   if(url==='/dynamic/problems')doc={revision:1,problem:{problem_id:pid},statements:[{...body,version_number:1}],rubrics:[],current_configuration:null};
   else if(url.endsWith('/statements')){assert.equal(body.expected_revision,doc.revision);doc={...doc,revision:doc.revision+1,statements:[...doc.statements,{...body,version_number:doc.statements.length+1}],current_configuration:null};}
   else if(url.endsWith('/approve')){assert.equal(body.expected_revision,doc.revision);assert.equal(body.acknowledge_warnings,true);doc={...doc,revision:doc.revision+1,current_configuration:{package:{package_id:'pkg'}},rubrics:doc.rubrics.map((r,i)=>i===doc.rubrics.length-1?{...r,status:'APPROVED'}:r)};}
   else {assert.equal(body.expected_revision,doc.revision);doc={...doc,revision:doc.revision+1,rubrics:[...doc.rubrics,{rubric_id:'r'+doc.revision,statement_version:doc.statements.at(-1).version_number,status:'DRAFT_TEACHER',criteria:body.criteria.map(c=>({...c,dependencies:c.dependencies||[],notes:c.notes||''})),review_warnings:[{requires_review:true,message:'Preparação pendente; revisão docente necessária.'}]}]};}
   return reply(doc);
  }
  if(url==='/tme/direct-solutions'){writes.push({url,body:JSON.parse(options.body)});return reply({case_id:cid,problem_id:pid});}
  if(url.endsWith('/transcriptions'))return reply([{transcription:{transcription_id:'tr_demo'}}]);
  if(url.endsWith('/transcriptions/tr_demo'))return reply({transcription:{transcription_id:'tr_demo'},revisions:[{revision_number:1,segments:[{kind:'text',text:'x=5'}]}],acceptances:accepted?[{revision_number:1,acceptance_id:'accepted'}]:[]});
  if(url.endsWith('/accept')){accepted=true;return reply({acceptance:{acceptance_id:'accepted'}});}
  if(url.endsWith('/audits')&&options.body)return reply({engine_mode:'DYNAMIC',audit_run_id:'audit',status:'COMPLETED',stale:false,result:{engine_mode:'DYNAMIC',problem_id:pid,score:null,max_score:10,review_required:true,analysis:{claims:[]},uncertainty:['Provider desligado'],rubric_assessment:{items:[]}}});
  if(url.endsWith('/independent-reviews'))return reply(options.body?{review:{review_id:'review'},stale:false}:[]);
  if(url.endsWith('/reconciliations'))return reply(options.body?{reconciliation:{reconciled_suggested_score:null,review_required:true,criteria:[]},stale:false}:[]);
 }});
 return {ui,writes,getDoc:()=>doc};
}
function draft(ui){fill(ui,'Enunciado do problema','Resolva 3x+7=22.');fill(ui,'Critério criterion_1: título','Equivalência');fill(ui,'Critério criterion_1: descrição','Isolar a incógnita por operações equivalentes.');fill(ui,'Critério criterion_1: pontos','10');}
async function approve(ui){await ui.click('Aprovar rubrica');const ack=field(ui,'Li os avisos da rubrica');ack.checked=true;ack.handlers.change();await ui.click('Aprovar rubrica');}
test('all sections exist on first page; points and explicit version approval gate correction',async()=>{
 const {ui,writes,getDoc}=await screen();
 for(const label of ['Título (opcional)','Enunciado do problema','Pontuação total','Critério criterion_1: título','Critério criterion_1: descrição','Critério criterion_1: pontos','Fazer upload da solução'])assert(field(ui,label),label);
 assert(button(ui,'Corrigir solução').disabled);assert(button(ui,'Sugerir rubrica com IA').disabled);assert(!writes.length);
 draft(ui);fill(ui,'Critério criterion_1: pontos','9.99');assert(button(ui,'Aprovar rubrica').disabled);assert.match(text(ui.root),/9,99 \/ 10/);
 fill(ui,'Critério criterion_1: pontos','10');await ui.click('Aprovar rubrica');assert.equal(writes.length,2);assert(!writes.some(w=>w.url.endsWith('/approve')));assert.match(text(ui.root),/Preparação pendente/);
 const ack=field(ui,'Li os avisos da rubrica');ack.checked=true;ack.handlers.change();await ui.click('Aprovar rubrica');assert.equal(writes.length,3);assert.equal(getDoc().rubrics.at(-1).status,'APPROVED');
 fill(ui,'Critério criterion_1: descrição','Nova descrição explícita.');assert.match(text(ui.root),/Aprovação pendente/);assert(button(ui,'Corrigir solução').disabled);
 await approve(ui);assert.equal(getDoc().rubrics.length,2);assert.equal(getDoc().rubrics[0].criteria[0].description,'Isolar a incógnita por operações equivalentes.');
 assert(!writes.some(w=>/assessments|publish|release/.test(w.url)));
});
test('digital DYNAMIC executes shared pipeline and shows pending result on the same page',async()=>{
 const {ui,writes}=await screen();draft(ui);await approve(ui);await ui.click('Solução já digital');fill(ui,'Solução já digital','x=5');
 const check=field(ui,'Confirmo o texto da solução');check.checked=true;check.handlers.change();assert(!button(ui,'Corrigir solução').disabled);
 await walk(ui.root).find(n=>n.tag==='form').handlers.submit({preventDefault(){}});
 assert.equal(ui.root.dataset.view,'new');assert.equal(ui.window.history.url,`/tme?view=new&mode=dynamic&problem_id=${pid}`);
 assert(ui.calls.some(c=>c.url.endsWith('/audits')&&c.options.method==='POST'));
 assert(ui.calls.some(c=>c.url.endsWith('/independent-reviews')&&c.options.method==='POST'));
 assert(ui.calls.some(c=>c.url.endsWith('/reconciliations')&&c.options.method==='POST'));
 assert.match(text(ui.root),/Resultado da correção/);assert.match(text(ui.root),/Provider desligado/);assert(ui.reports.some(r=>r.data.score===null));
 assert(!ui.calls.some(c=>c.options.method==='POST'&&/decision|release|publish/.test(c.url)));
 const input=writes.find(w=>w.url==='/tme/direct-solutions').body;assert.equal(input.solution,'x=5');assert(!input.original);
});
test('photo/upload never becomes a correction even with pre-existing digital text',async()=>{
 const {ui}=await screen();draft(ui);await approve(ui);await ui.click('Solução já digital');fill(ui,'Solução já digital','x=5');field(ui,'Confirmo o texto da solução').checked=true;
 await ui.click('Foto ou upload');const file=field(ui,'Fazer upload da solução');file.files=[{name:'resposta.png',type:'image/png',size:42}];await file.handlers.change();
 assert(button(ui,'Corrigir solução').disabled);assert.match(text(ui.root),/visualização local/);assert.match(text(ui.root),/nenhum texto ou nota foi gerado/);
 assert.equal(field(ui,'Tirar foto da solução').attributes.capture,'environment');
 await walk(ui.root).find(n=>n.tag==='form').handlers.submit({preventDefault(){}});assert(!ui.calls.some(c=>c.url==='/tme/direct-solutions'));
});
test('editing basic criteria preserves hidden scientific fields and prevents dangling dependencies',async()=>{
 const criteria=[{criterion_id:'first',title:'Método',description:'Justificar',max_points:'6',order:1,credit_levels:[{level_id:'partial',points:'3',description:'Etapa justificada'}],notes:'Preservar nota',teacher_guidance:'Preservar orientação'}, {criterion_id:'second',title:'Resultado',description:'Concluir',max_points:'4',order:2,dependencies:['first'],dependency_rules:[{criterion_id:'first',kind:'MATHEMATICAL',condition:'Transformação válida',minimum_points:'3'}]}];
 const doc={problem:{problem_id:pid},revision:3,statements:[{statement:'Resolva x+1=6.',max_score:'10',version_number:1}],rubrics:[{rubric_id:'original',statement_version:1,status:'APPROVED',criteria,review_warnings:[]}],current_configuration:{package:{}}};
 const {ui,writes}=await screen({existing:doc});await ui.click('Remover critério');assert.match(text(ui.root),/pré-requisito/);assert(field(ui,'Critério first: título'));
 fill(ui,'Critério first: descrição','Justificar cada transformação.');await ui.click('Aprovar rubrica');const saved=writes.find(w=>w.method==='PATCH');assert(saved);
 assert.deepEqual(saved.body.criteria[0].credit_levels,criteria[0].credit_levels);assert.equal(saved.body.criteria[0].notes,criteria[0].notes);assert.deepEqual(saved.body.criteria[1].dependency_rules,criteria[1].dependency_rules);
 assert.equal(criteria[0].description,'Justificar');
});
test('failed persistence retains all entered fields and does not approve',async()=>{
 const {ui}=await screen({failure:true});draft(ui);await ui.click('Aprovar rubrica');assert.match(text(ui.root),/Falha de armazenamento/);assert.equal(field(ui,'Enunciado do problema').value,'Resolva 3x+7=22.');assert.equal(field(ui,'Critério criterion_1: pontos').value,'10');assert(button(ui,'Corrigir solução').disabled);
});

test('an approved rubric does not override server correction unavailability',async()=>{
 const existing={problem:{problem_id:pid},revision:3,statements:[{statement:'Resolva x+1=6.',max_score:'10',version_number:1}],rubrics:[{rubric_id:'r',statement_version:1,status:'APPROVED',criteria:[{criterion_id:'c',title:'Método',description:'Justificar',max_points:'10',order:1}],review_warnings:[]}],current_configuration:{package:{}},correction_available:false};
 const {ui}=await screen({existing});assert.match(text(ui.root),/não está disponível para esta configuração/);await ui.click('Solução já digital');fill(ui,'Solução já digital','x=5');field(ui,'Confirmo o texto da solução').checked=true;field(ui,'Confirmo o texto da solução').handlers.change();assert(button(ui,'Corrigir solução').disabled);assert(!ui.calls.some(c=>c.options.method));
});
