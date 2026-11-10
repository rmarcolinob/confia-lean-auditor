const test = require('node:test');
const assert = require('node:assert/strict');
const { File } = require('node:buffer');
const { pilot, walk, text } = require('./tme-dom.cjs');
const { flush } = require('./capture-dom.cjs');
const {backend,eid,aid,reply}=require('./exam-fixture.cjs');
const field=(ui,name)=>walk(ui.root).find(n=>n.dataset.examField===name);
async function input(ui, files){
  field(ui,'assessment').value=aid;field(ui,'assessment').handlers.change();
  field(ui,'participant').value='PROVA-1';field(ui,'participant').handlers.input();
  field(ui,'files').files=files;field(ui,'files').handlers.change();await flush();
}

test('production module receives a whole PDF, maps many-to-many and opens persisted question URLs',async()=>{
  const server=backend(),ui=await pilot({fullExam:true,mockFetch:server.mockFetch});
  await ui.nav[1].click();await flush();
  assert.match(text(ui.root),/Avaliação configurada pelo backend/);
  await input(ui,[new File(['%PDF-original'], 'original.pdf',{type:'application/pdf'})]);
  await ui.click('Receber prova');
  const payload=JSON.parse(ui.calls.find(c=>c.url==='/tme/exam-submissions'&&c.options.method==='POST').options.body);
  assert.equal(Buffer.from(payload.original_documents[0].content_base64,'base64').toString(),'%PDF-original');
  assert.equal(payload.external_participant_code,'PROVA-1');
  assert.match(ui.window.location.search,/exam_submission_id/);
  assert.equal(walk(ui.root).filter(n=>n.tag==='img').length,4);
  const checks=walk(ui.root).filter(n=>n.type==='checkbox');
  for(const i of [0,1,5]){checks[i].checked=true;checks[i].handlers.change();}
  await ui.click('Abrir Q1');assert.match(text(ui.root),/Salve as associações/);
  await ui.click('Salvar associações');
  assert.deepEqual(server.detail.mapping.bindings.map(b=>b.order),[1,2,1]);
  await ui.click('Abrir Q1');assert.match(ui.window.location.search,/question_attempt_id/);
  assert.equal(walk(ui.root).filter(n=>n.tag==='img').length,2);
  assert.match(text(ui.root),/Pontuação máxima: 20/);
  await ui.window.history.back();assert.match(text(ui.root),/Questões e páginas/);
  assert.equal(walk(ui.root).filter(n=>n.type==='checkbox'&&n.checked).length,3);
  await ui.nav[0].click();await flush();assert.match(text(ui.root),/Provas recebidas/);
});

test('image reorder and rotation preserve original bytes; legacy digital path remains reachable',async()=>{
  const server=backend(),ui=await pilot({fullExam:true,mockFetch:server.mockFetch});
  await ui.nav[1].click();await flush();
  await input(ui,[new File(['first'],'1.png',{type:'image/png'}),new File(['second'],'2.png',{type:'image/png'})]);
  await ui.click('Mover depois');await ui.click('Girar 90° · 0°');await ui.click('Receber prova');
  const payload=JSON.parse(ui.calls.find(c=>c.url==='/tme/exam-submissions'&&c.options.method==='POST').options.body);
  assert.deepEqual(payload.original_documents.map(d=>Buffer.from(d.content_base64,'base64').toString()),['second','first']);
  assert.deepEqual(payload.original_documents.map(d=>d.rotation_degrees),[90,0]);
  await ui.nav[1].click();await flush();await ui.click('Corrigir questão avulsa / escrita digital');
  assert.match(text(ui.root),/Selecione uma questão/);assert.match(text(ui.root),/Escrever no tablet/);
});

test('upload failure retains files and stable idempotency key for retry',async()=>{
  const server=backend({failUpload:true}),ui=await pilot({fullExam:true,mockFetch:server.mockFetch});
  await ui.nav[1].click();await flush();await input(ui,[new File(['bad'],'invalid.pdf',{type:'application/pdf'})]);
  await ui.click('Receber prova');assert.match(text(ui.root),/Confira o código e os arquivos/);assert.match(text(ui.root),/invalid.pdf/);
  await ui.click('Receber prova');
  const attempts=ui.calls.filter(c=>c.url==='/tme/exam-submissions'&&c.options.method==='POST').map(c=>JSON.parse(c.options.body));
  assert.equal(attempts.length,2);assert.deepEqual(attempts[0],attempts[1]);
});

test('question deep link restores mapped original; late new-capture fetch cannot replace navigation',async()=>{
  const server=backend();server.detail.mapping.bindings=[{question_attempt_id:server.detail.question_attempts[0].case_id,exam_page_id:server.detail.submission.pages[2].exam_page_id,order:1}];
  const ui=await pilot({fullExam:true,mockFetch:server.mockFetch,initialSearch:`?exam_submission_id=${eid}&question_attempt_id=${server.detail.question_attempts[0].case_id}`});
  assert.match(text(ui.root),/Questão 1/);assert.equal(walk(ui.root).filter(n=>n.tag==='img')[0].alt,'Página 3 da prova');
  let release;const late=await pilot({fullExam:true,mockFetch:async(u,o)=>u==='/tme/assessments'?new Promise(resolve=>release=()=>resolve(reply([server.detail.assessment]))):server.mockFetch(u,o)});
  const pending=late.nav[1].click();await flush();await late.nav[2].click();await flush();
  release();await pending;await flush();assert.match(text(late.root),/Distribuição atual/);assert.doesNotMatch(text(late.root),/Código pseudônimo/);
});
