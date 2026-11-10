const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {backend,eid}=require('./exam-fixture.cjs');
const {flush}=require('./capture-dom.cjs');
async function open(){
  const server=backend(),[q1,q2]=server.detail.question_attempts;
  server.detail.mapping={version:2,bindings:[...server.detail.submission.pages.map((p,i)=>({question_attempt_id:q1.case_id,exam_page_id:p.exam_page_id,order:i+1})),{question_attempt_id:q2.case_id,exam_page_id:server.detail.submission.pages[1].exam_page_id,order:1}]};
  const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${q1.case_id}`});
  return {server,ui,q1,q2};
}
const byClass=(ui,name)=>walk(ui.root).find(n=>n.className.split(' ').includes(name));
const areas=ui=>walk(ui.root).filter(n=>n.tag==='textarea');
function edit(area,value){area.value=value;area.handlers.input();}

test('question uses existing workspace, three tabs, splitter and real empty analysis without grading controls',async()=>{
  const {ui}=await open();
  assert.ok(byClass(ui,'correction-workspace'));assert.ok(walk(ui.root).find(n=>n.id==='solution-pane'));assert.ok(byClass(ui,'analysis-column'));
  assert.ok(byClass(ui,'pane-splitter'));assert.ok(byClass(ui,'problem-statement'));
  assert.deepEqual(walk(ui.root).filter(n=>n.attributes.role==='tab').map(n=>n.textContent),['Original','Transcrição','Comparar']);
  assert.match(text(ui.root),/Aguardando análise/);
  assert.equal(walk(ui.root).some(n=>n.tag==='button'&&['Analisar com ConfIA','Usar sugestão','Finalizar correção'].includes(n.textContent)),false);
  await ui.click('Transcrição');assert.equal(byClass(ui,'original-document').hidden,true);
  await ui.click('Comparar');assert.equal(byClass(ui,'original-document').hidden,false);assert.equal(byClass(ui,'transcript-document').hidden,false);
  await ui.click('Original');assert.equal(byClass(ui,'transcript-document').hidden,true);
});

test('four associated pages retain proportions/layout controls and current page across question navigation',async()=>{
  const {ui}=await open();
  const pages=walk(ui.root).filter(n=>n.className==='page-review');assert.equal(pages.length,4);
  const originalURLs=walk(ui.root).filter(n=>n.tag==='img').map(n=>n.src);
  assert.match(originalURLs[0],/preview_0001$/);
  await ui.click('Próxima');assert.match(byClass(ui,'page-position').textContent,/Página 2\/4 · folha 2/);
  await ui.click('Q2 · Pendente');assert.equal(walk(ui.root).filter(n=>n.className==='page-review').length,1);
  assert.equal(walk(ui.root).find(n=>n.tag==='img').src,originalURLs[1]);
  await ui.click('Q1 · Pendente');assert.match(byClass(ui,'page-position').textContent,/Página 2\/4 · folha 2/);
});

test('capture import then human correction appends a version, preserves history and signals reanalysis without executing audit',async()=>{
  const {ui,server,q1}=await open();
  await ui.click('Importar leitura da captura');assert.match(text(ui.root),/Versão 1 · Automática · captura importada/);
  await ui.click('Corrigir leitura');assert.equal(areas(ui)[0].value,'x = 1');edit(areas(ui)[0],'x = 2');
  await ui.click('Salvar nova revisão');assert.match(text(ui.root),/Versão 2 · Humana/);assert.match(text(ui.root),/Reanálise necessária/);
  assert.equal(server.histories.get(q1.case_id).revisions[0].segments[0].text,'x = 1');
  assert.equal(server.histories.get(q1.case_id).revisions[1].segments[0].text,'x = 2');
  assert.match(text(ui.root),/Versão 1 .*preservada/);
  await ui.click('Q2 · Pendente');await ui.click('Q1 · Revisão necessária');
  assert.match(text(ui.root),/Versão 2 · Humana/);
  assert.equal(server.histories.get(q1.case_id).revisions.length,2);
  assert.equal(ui.calls.some(c=>c.options.method==='POST'&&c.url.endsWith('/audits')),false);
});

test('unsaved draft stays with its question, cancel discards it and unchanged save creates no version',async()=>{
  const {ui,server,q1}=await open();await ui.click('Importar leitura da captura');await ui.click('Corrigir leitura');
  edit(areas(ui)[0],'rascunho não salvo');assert.match(text(ui.root),/Rascunho não salvo/);
  await ui.click('Q2 · Pendente');await ui.click('Q1 · Revisão necessária');
  assert.equal(areas(ui)[0].value,'rascunho não salvo');
  await ui.click('Cancelar edição');await ui.click('Corrigir leitura');assert.equal(areas(ui)[0].value,'x = 1');
  await ui.click('Salvar nova revisão');assert.match(text(ui.root),/Nenhuma versão adicional/);
  assert.equal(server.histories.get(q1.case_id).revisions.length,1);
});

test('typed first reading, conflict retains draft and current revision is never silently overwritten',async()=>{
  const {ui,server,q1}=await open();await ui.click('Digitar transcrição');edit(areas(ui)[0],'texto digitado');
  await ui.click('Salvar nova revisão');assert.match(text(ui.root),/Versão 1 · Humana/);
  await ui.click('Corrigir leitura');edit(areas(ui)[0],'rascunho local');
  const history=server.histories.get(q1.case_id);history.revisions.push({...history.revisions[0],revision_number:2,segments:[{...history.revisions[0].segments[0],text:'outra sessão'}]});
  await ui.click('Salvar nova revisão');assert.match(text(ui.root),/rascunho foi mantido/);assert.equal(areas(ui)[0].value,'rascunho local');
  assert.equal(history.revisions.length,2);assert.equal(history.revisions[1].segments[0].text,'outra sessão');
  await ui.click('Cancelar edição');assert.match(text(ui.root),/Versão 2 · Humana/);
});
