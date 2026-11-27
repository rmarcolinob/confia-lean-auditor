const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const find=(ui,cls)=>walk(ui.root).find(e=>e.className===cls);

test('exam names are formatted for display without rewriting the stored code',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');
  const format=ui.window.ConfiaCorrectionWorkspace.displayExamName;
  for(const [code,label] of [['prova2','Prova 2'],['prova00231','Prova 00231'],['PROVA-1','Prova 1'],['ABC-7','Prova ABC-7'],['','Prova']]) assert.equal(format(code),label);
  assert.equal(ui.calls.find(c=>c.url==='/tme/cases').options.method,undefined);
  assert.equal(walk(ui.root).find(e=>e.tag==='h1').textContent,'Prova 1');
  assert.equal(ui.calls.filter(c=>c.options.method==='POST').length,0);
});

test('only Transcrição exposes compact transcription metadata; tab navigation preserves the image',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');
  const caption=find(ui,'transcription-caption'),status=find(ui,'transcription-status'),image=walk(ui.root).find(e=>e.tag==='img');
  assert.equal(caption.hidden,true);assert.equal(status.hidden,true);
  const calls=ui.calls.length;
  await ui.click('Transcrição');assert.equal(caption.hidden,false);assert.match(text(caption),/Transcrição automática.*revisão 1/);
  assert.equal(find(ui,'caption-full'),undefined);
  await ui.click('Comparar');assert.equal(caption.hidden,true);
  await ui.click('Original');assert.equal(caption.hidden,true);assert.equal(status.hidden,true);
  assert.equal(walk(ui.root).find(e=>e.tag==='img'),image);assert.equal(ui.calls.length,calls);
  assert.equal(find(ui,'viewer-fit').value,'width');
  assert.equal(find(ui,'case-context').dataset.questionCount,'1');
});

test('mobile statement moves the compact boundary before a fraction and expands the same content',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');
  const statement=find(ui,'problem-statement'),content=find(ui,'problem-content'),rich=find(ui,'problem-rich-text');
  ui.window.matchMedia=q=>({matches:q.includes('max-width')});ui.window.getComputedStyle=()=>({fontSize:'14px'});content.isConnected=true;
  rich.getBoundingClientRect=()=>({top:200,height:130});
  rich.querySelectorAll=()=>[{getBoundingClientRect:()=>({top:250,bottom:280})}];
  statement.updateStatementLayout();assert.equal(content.style.maxHeight,'50px');assert.equal(content.dataset.clipped,'true');
  await ui.click('Ver enunciado completo');assert.equal(content.style.maxHeight,'none');assert.equal(find(ui,'problem-rich-text'),rich);
  await ui.click('Recolher enunciado');assert.equal(content.style.maxHeight,'50px');
});

test('decision clearance follows measured bar heights including wrapping and safe-area padding',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');
  const reserve=ui.window.ConfiaCorrectionWorkspace.reserveDecisionSpace;
  const decision={getBoundingClientRect:()=>({height:60.2})},action={getBoundingClientRect:()=>({height:99})};
  reserve(ui.root,decision,action);
  assert.equal(ui.root.style['--decision-clearance'],'61px');assert.equal(ui.root.style['--action-clearance'],'99px');
  decision.getBoundingClientRect=()=>({height:104});reserve(ui.root,decision,action);
  assert.equal(ui.root.style['--decision-clearance'],'104px');
});
