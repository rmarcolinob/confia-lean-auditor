const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const Home = require('../../app/confia_lean_auditor/static/tme/home.js');
const {pilot,walk,text} = require('./tme-dom.cjs');
const {flush} = require('./capture-dom.cjs');
const sample = (i,status='pending') => ({case_id:'case_'+String(i).padStart(32,'0'),exam_code:'prova-'+i,problem_id:`ITA2025F2Q${i}`,question_label:`Q${i}`,source_mode:'IMAGE_SCAN',operational_status:status,updated_at:'2026-10-22T12:00:00Z'});
const summary = () => ({period:'today',counts:{pending:128,inconclusive:24,finalized:318,in_progress:12},
  priority_cases:[sample(3,'inconclusive'),sample(1),sample(2,'in_progress')],
  exam_progress:[{exam_code:'prova-2',known_items:5,completed_items:2,percent:40},{exam_code:'prova-8',known_items:6,completed_items:3,percent:50}],
  generated_at:'2026-10-22T12:00:00Z'});
const find = (ui,cls) => walk(ui.root).find(n=>n.className===cls);
const button = (ui,label) => walk(ui.root).find(n=>n.tag==='button' && text(n).includes(label));
const metrics = ui => walk(ui.root).filter(n=>n.className.startsWith('home-metric ')).map(n=>n.children[1].textContent);

test('Home requests one aggregate without fetching case lists or artifacts',async()=>{
  const ui=await pilot({startHome:true,homeSummary:summary()});
  assert.equal(ui.root.dataset.view,'home'); assert.match(text(ui.root),/Olá, avaliador!.*Vamos continuar\?/);
  assert.deepEqual(ui.calls.map(c=>c.url).sort(),['/auth/me','/tme/home-summary?period=today']);
  assert.equal(walk(ui.root).filter(n=>n.tag==='table'||n.tag==='img'||n.tag==='textarea').length,0);
  assert.doesNotMatch(text(ui.root),/AuditRun|RecognitionRun|Lean|rubrica|hash|JSON/);
  assert.equal(find(ui,'home-primary').disabled,false);
});

test('overview displays exact server counts including real inconclusive and numeric zero',async()=>{
  const data=summary(), ui=await pilot({startHome:true,homeSummary:data});
  assert.deepEqual(metrics(ui),['128','24','318','12']);
  data.counts={pending:0,inconclusive:0,finalized:0,in_progress:0};
  await ui.shell['home-bottom-nav'].children[0].click();
  assert.deepEqual(metrics(ui),['0','0','0','0']);
  assert.doesNotMatch(text(ui.root),/contagem indisponível/);
});

test('primary CTA uses first server case without creating a correction or sorting in browser',async()=>{
  const ui=await pilot({startHome:true});
  await find(ui,'home-primary').click(); await flush();
  assert.equal(ui.root.dataset.view,'workspace');
  assert.ok(ui.calls.some(c=>c.url==='/tme/cases/'+ui.snapshot.case_id));
  assert.equal(ui.calls.filter(c=>c.options.method==='POST').length,0);
  const opened=[], node=ui.window.ConfiaTmeHome.TmeHome({summary:summary(),navigate(){},open:id=>opened.push(id)});
  await walk(node).find(n=>n.className==='home-primary').click();
  assert.deepEqual(opened,[sample(3).case_id]);
});

test('priority queue preserves server order, uses operational labels, and renders three cases',async()=>{
  const ui=await pilot({startHome:true,homeSummary:summary()});
  const rows=walk(find(ui,'home-priority')).filter(n=>n.className==='home-case');
  assert.equal(rows.length,3); assert.match(text(rows[0]),/prova-3.*ITA2025F2Q3.*Inconclusiva/);
  assert.match(text(rows[1]),/Pendente/); assert.match(text(rows[2]),/Em andamento/);
  assert.equal(find(ui,'home-count').textContent,'3');
  assert.equal(Home.status({status:'DECIDED'}),'Finalizada'); // Existing queue component compatibility.
  assert.equal(Home.status({status:'UNKNOWN'}),'Não informado');
  assert.equal(walk(rows[0]).find(n=>n.className==='home-status').dataset.status,'Inconclusiva');
});

test('progress uses actual server denominators and accessible counts',async()=>{
  const ui=await pilot({startHome:true,homeSummary:summary()});
  const bars=walk(find(ui,'home-progress')).filter(n=>n.tag==='progress');
  assert.equal(bars.length,2); assert.equal(bars[0].max,5); assert.equal(bars[0].value,2);
  assert.equal(bars[1].max,6); assert.equal(bars[1].value,3);
  assert.match(bars[1].attributes['aria-label'],/3 de 6 questões finalizadas/);
});

test('empty and all-finalized states disable next correction and keep creation available',async()=>{
  for(const finalized of [0,1]) {
    const data={...summary(),counts:{pending:0,in_progress:0,inconclusive:0,finalized},priority_cases:[],exam_progress:[]};
    const ui=await pilot({startHome:true,homeSummary:data});
    assert.match(text(ui.root),/Nenhuma correção pendente/); assert.equal(find(ui,'home-primary').disabled,true);
    assert.match(text(ui.root),/Suas provas aparecerão aqui/); assert.ok(button(ui,'Nova correção'));
  }
});

test('aggregate error has safe text, retry and usable quick actions',async()=>{
  const ui=await pilot({startHome:true,homeError:true});
  assert.match(text(ui.root),/Não foi possível carregar os indicadores\./); assert.doesNotMatch(text(ui.root),/private stack trace/);
  assert.equal(find(ui,'home-primary').disabled,true);
  await ui.click('Tentar novamente'); await flush();
  assert.equal(ui.calls.filter(c=>c.url.startsWith('/tme/home-summary')).length,2);
  assert.ok(button(ui,'Ver fila')); assert.equal(ui.calls.filter(c=>/audits|transcriptions|submission/.test(c.url)).length,0);
  await button(ui,'Nova correção').click(); assert.equal(ui.root.dataset.view,'new');
});

test('quick actions and bottom navigation preserve existing flows',async()=>{
  const ui=await pilot({startHome:true});
  const bottom=ui.shell['home-bottom-nav'];
  assert.deepEqual(bottom.children.map(n=>n.dataset.view),['home','cases','new','results']);
  for(const [label,view] of [['Nova correção','new'],['Ver fila','cases'],['Resultados','results']]) {
    await button(ui,label).click(); await flush(); assert.equal(ui.root.dataset.view,view);
    await bottom.children[0].click(); await flush(); assert.equal(ui.root.dataset.view,'home');
  }
});

test('loading skeletons keep navigation available',async()=>{
  const ui=await pilot({startHome:true});
  const loading=ui.window.ConfiaTmeHome.TmeHome({state:'loading',navigate(){}});
  assert.equal(walk(loading).filter(n=>n.className==='home-skeleton').length,9);
  assert.equal(walk(loading).find(n=>n.className==='home-primary').disabled,true);
  assert.equal(walk(loading).find(n=>n.className==='home-action').disabled,undefined);
});

test('period options each query server and render returned counts',async()=>{
  const ui=await pilot({startHome:true,homeSummary:period=>({...summary(),period,counts:{pending:period==='today'?1:7,inconclusive:2,finalized:3,in_progress:4}})});
  assert.equal(metrics(ui)[0],'1');
  for(const period of ['7d','30d','all','today']) {
    const select=walk(find(ui,'home-overview')).find(n=>n.tag==='select');
    assert.deepEqual(select.children.map(n=>n.value),['today','7d','30d','all']);
    select.value=period; await select.handlers.change(); await flush();
    assert.equal(ui.calls.at(-1).url,`/tme/home-summary?period=${period}`);
    assert.equal(metrics(ui)[0],period==='today'?'1':'7');
  }
});

test('mobile shell retains safe areas, touch targets and focus',()=>{
  const css=fs.readFileSync('app/confia_lean_auditor/static/tme/home.css','utf8');
  const html=fs.readFileSync('app/confia_lean_auditor/static/tme/index.html','utf8');
  assert.match(css,/\.sidebar \{ display: none !important/); assert.match(css,/\.queue-scroll \{ display: none/);
  assert.match(css,/safe-area-inset-bottom/); assert.match(css,/position: fixed; z-index: 60; bottom: 0/);
  assert.match(css,/min-height: var\(--confia-control-height\)/); assert.match(css,/:focus-visible/);
  assert.match(html,/viewport-fit=cover/);
});

test('progress cards open the existing queue once and retain readable progress semantics',async()=>{
  const ui=await pilot({startHome:true,homeSummary:summary()});
  const open=walk(ui.root).find(n=>n.attributes['aria-label']==='Ver correções da prova prova-2');
  assert.equal(open.tag,'button');
  assert.equal(walk(ui.root).find(n=>n.tag==='progress').attributes['aria-label'],'prova-2: 2 de 5 questões finalizadas');
  await open.click(); await flush();
  assert.equal(ui.root.dataset.view,'cases');
  assert.equal(ui.calls.filter(c=>c.url==='/tme/cases').length,1);
  assert.equal(ui.calls.filter(c=>c.options.method==='POST').length,0);
});
