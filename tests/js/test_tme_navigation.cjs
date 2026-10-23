const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {flush}=require('./capture-dom.cjs');
const metadataOnly=calls=>assert.ok(calls.every(c=>!(/\/cases\/[^/?]+\/(audits|submission|transcriptions|originals|recognition)/.test(c.url))),JSON.stringify(calls));
const click=async(ui,label)=>{const b=walk(ui.root).find(n=>n.tag==='button'&&(n.textContent===label||n.attributes['aria-label']===label||walk(n).some(c=>c.textContent===label)));if(b)await b.click();else await ui.click(label);await flush();};
const modern=ui=>{assert.ok(walk(ui.root).some(n=>n.className==='tme-page')||ui.root.dataset.view==='home'||ui.root.dataset.view==='workspace');assert.doesNotMatch(text(ui.root),/Sessão do avaliador|Atualizar fila|Recentes/);};

for(const [action,view,url]of [['Ver fila','cases','queue'],['Ver fila completa','cases','queue'],['Nova correção','new','new'],['Resultados','results','results'],['Ver todas','exams','exams']])test(`Home → ${action} keeps modern shell and a restorable URL`,async()=>{
  const ui=await pilot({startHome:true});await click(ui,action);assert.equal(ui.root.dataset.view,view);assert.equal(ui.window.history.url,`/tme?view=${url}`);modern(ui);metadataOnly(ui.calls);
});

test('queue → workspace → back retains filters and browser back/forward restores views',async()=>{
  const ui=await pilot({startHome:true,automatic:true});await click(ui,'Ver fila');
  const search=walk(ui.root).find(n=>n.type==='search');search.value='PROVA';search.handlers.change();await flush();
  const queueURL=ui.window.history.url;await click(ui,'Abrir');assert.equal(ui.root.dataset.view,'workspace');const caseURL=ui.window.history.url;
  await ui.window.history.back();assert.equal(ui.root.dataset.view,'cases');assert.equal(ui.window.history.url,queueURL);
  await ui.window.history.forward();assert.equal(ui.root.dataset.view,'workspace');assert.equal(ui.window.history.url,caseURL);
  await click(ui,'Voltar para fila');assert.equal(ui.window.history.url,queueURL);assert.equal(walk(ui.root).find(n=>n.type==='search').value,'PROVA');modern(ui);
});

test('progress → exam questions → workspace only requests heavy data at the last step',async()=>{
  const ui=await pilot({startHome:true,automatic:true});await click(ui,'Ver todas');await click(ui,'Ver questões da prova PROVA-1');
  assert.match(ui.window.history.url,/view=queue&exam=PROVA-1/);assert.match(text(ui.root),/Questões da prova Prova 1/);metadataOnly(ui.calls);
  await click(ui,'Abrir');assert.equal(ui.root.dataset.view,'workspace');assert.ok(ui.calls.some(c=>c.url.endsWith('/submission')));
  await click(ui,'Voltar para fila');assert.match(ui.window.history.url,/exam=PROVA-1/);
});

for(const mode of ['Foto / scan','Escrever no tablet'])test(`new → ${mode} reuses the case and capture flow`,async()=>{
  const ui=await pilot({startHome:true});await click(ui,'Nova correção');const code=walk(ui.root).find(n=>n.tag==='input');code.value='EXAM-NEW';const question=walk(ui.root).find(n=>n.tag==='select');question.value='ITA2025F2Q1';await click(ui,mode);await click(ui,'Continuar');assert.equal(ui.root.dataset.view,'workspace');assert.match(ui.window.history.url,/case_id=case_c/);assert.equal(ui.calls.filter(c=>c.options.method==='POST').length,1);modern(ui);
  if(mode==='Escrever no tablet')assert.match(walk(ui.root).find(n=>n.tag==='iframe').src,/\/capture\?embedded=1/);else assert.match(text(ui.root),/Fotografar página/);
});

for(const view of ['queue','new','results','exams'])test(`reload/deep link view=${view}`,async()=>{
  const ui=await pilot({initialSearch:`?view=${view}`});assert.equal(ui.root.dataset.view,view==='queue'?'cases':view);modern(ui);metadataOnly(ui.calls);
});

test('case_id takes precedence over view and direct workspace back falls back to queue',async()=>{
  const ui=await pilot({initialSearch:'?view=results&case_id=case_'+'a'.repeat(32),automatic:true});assert.equal(ui.root.dataset.view,'workspace');await click(ui,'Voltar para fila');assert.equal(ui.root.dataset.view,'cases');
});

test('queue paginates at 50, preserves filters and never hydrates list rows',async()=>{
  const rows=Array.from({length:123},(_,i)=>({case_id:'case_'+i.toString(16).padStart(32,'0'),external_candidate_ref:`EXAM-${i}`,problem_id:'ITA2025F2Q1',source_mode:'IMAGE_SCAN'}));
  const ui=await pilot({homeCases:rows});assert.equal(walk(ui.root).filter(n=>n.className==='tme-queue-row').length,50);await click(ui,'Próxima');assert.match(ui.window.history.url,/page=2/);assert.equal(walk(ui.root).filter(n=>n.className==='tme-queue-row').length,50);await click(ui,'Próxima');assert.equal(walk(ui.root).filter(n=>n.className==='tme-queue-row').length,23);metadataOnly(ui.calls);
});

test('queue next uses exactly the server priority used by Home',async()=>{
  const ui=await pilot({startHome:true,homeSummary:{counts:{},priority_cases:[{case_id:'case_'+'a'.repeat(32)}],exam_progress:[]}});await click(ui,'Ver fila');await click(ui,'Corrigir próxima');assert.match(ui.window.history.url,/case_id=case_a/);assert.equal(ui.calls.filter(c=>c.url==='/tme/home-summary?period=all').length,1);
});

for(const [view,message]of [['queue','Não foi possível carregar a fila.'],['exams','Não foi possível carregar o progresso das provas.'],['results','Não foi possível carregar os resultados.']])test(`${view} has a domain error and retry without technical data`,async()=>{
  const ui=await pilot({initialSearch:`?view=${view}`,listingError:true});assert.ok(text(ui.root).includes(message));assert.doesNotMatch(text(ui.root),/private stack/);assert.ok(walk(ui.root).some(n=>n.textContent==='Tentar novamente'));modern(ui);
});

for(const [view,message]of [['queue','Nenhuma correção encontrada.'],['exams','Nenhuma prova disponível.'],['results','Ainda não há dados suficientes.']])test(`${view} empty state uses real zero data`,async()=>{
  const ui=await pilot({initialSearch:`?view=${view}`,homeCases:[]});assert.ok(text(ui.root).includes(message));modern(ui);
});

test('full queue link clears an earlier exam filter',async()=>{
  const ui=await pilot({initialSearch:'?view=queue&exam=PROVA-1'});await ui.shell['home-bottom-nav'].children[0].click();await flush();await click(ui,'Ver fila completa');assert.equal(ui.window.history.url,'/tme?view=queue');
});

test('one mount fetches one metadata page and repeated pending navigation shares work',async()=>{
  const ui=await pilot({startHome:true});const nav=ui.shell['home-bottom-nav'].children[1];await Promise.all([nav.click(),nav.click()]);await flush();assert.equal(ui.calls.filter(c=>c.url.startsWith('/tme/cases?')).length,1);metadataOnly(ui.calls);
});
