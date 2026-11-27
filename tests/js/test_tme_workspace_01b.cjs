const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {flush}=require('./capture-dom.cjs');
const find=(ui,cls)=>walk(ui.root).find(e=>e.className===cls);

async function setup(desktop=true) {
  const ui=await pilot({automatic:true,desktop,pageCount:2});await ui.click('Abrir');
  const viewport=find(ui,'original-document'),page=find(ui,'page-review'),surface=find(ui,'manuscript-surface'),image=walk(page).find(e=>e.tag==='img');
  viewport.clientWidth=604;viewport.clientHeight=404;image.naturalWidth=600;image.naturalHeight=1200;
  return {ui,viewport,page,surface,image};
}

test('bounded desktop width and page fits preserve aspect ratio, zoom and rotated reachable bounds',async()=>{
  const {ui,viewport,page,surface,image}=await setup(),layout=ui.window.ConfiaCorrectionWorkspace.layoutOriginal;
  viewport.dataset.layout='bounded'; // Comparison retains a viewport with a bounded height.
  const state={zoom:1,rotation:0,fitMode:"width"};
  layout(page,image,viewport,state);assert.equal(surface.style.width,'600px');assert.equal(surface.style.height,'1200px');
  state.fitMode='page';layout(page,image,viewport,state);assert.equal(surface.style.width,'200px');assert.equal(surface.style.height,'400px');
  state.rotation=90;layout(page,image,viewport,state);assert.equal(surface.style.width,'600px');assert.equal(surface.style.height,'300px');
  assert.match(image.style.transform,/translate\(600px, 0px\)/);
  state.zoom=1.25;layout(page,image,viewport,state);assert.equal(surface.style.width,'750px');assert.equal(surface.style.height,'375px');
});

test('bounded fit page uses extra viewer height and avoids stretching a landscape page',async()=>{
  const {ui,viewport,page,surface,image}=await setup();
  viewport.dataset.layout='bounded';
  const layout=ui.window.ConfiaCorrectionWorkspace.layoutOriginal,state={zoom:1,rotation:0,fitMode:'page'};
  layout(page,image,viewport,state);const before=parseFloat(surface.style.height);
  viewport.clientHeight=704;layout(page,image,viewport,state);assert.ok(parseFloat(surface.style.height)>before);assert.equal(surface.style.height,'700px');
  image.naturalWidth=1200;image.naturalHeight=600;layout(page,image,viewport,state);assert.equal(surface.style.width,'600px');assert.equal(surface.style.height,'300px');
});

test('mobile retains existing width/rotation sizing even with a saved desktop page fit',async()=>{
  const {ui,viewport,page,surface,image}=await setup(false);
  ui.window.ConfiaCorrectionWorkspace.layoutOriginal(page,image,viewport,{zoom:1,rotation:0,fitMode:'page'});
  assert.equal(surface.style.width,'600px');assert.equal(surface.style.height,'1200px');
  assert.equal(find(ui,'transcription-status').textContent,'Transcrição disponível');
  assert.match(text(find(ui,'caption-compact')),/Transcrição automática/);
});

test('fit and expansion reuse image nodes and perform no new requests',async()=>{
  const {ui,image}=await setup();const calls=ui.calls.length,fit=find(ui,'viewer-fit');
  assert.equal(fit.value,'page');fit.value='page';fit.handlers.change();
  await ui.click('Expandir solução');assert.equal(find(ui,'correction-workspace').dataset.solutionExpanded,'true');
  await ui.click('Restaurar análise');assert.equal(find(ui,'correction-workspace').dataset.solutionExpanded,'false');
  assert.equal(walk(ui.root).find(e=>e.tag==='img'),image);assert.equal(ui.calls.length,calls);
  assert.equal(walk(ui.root).find(e=>e.attributes['aria-label']==='Expandir solução').attributes['aria-expanded'],'false');
});

test('page, zoom, rotation, fit, expansion and collapsed analysis survive workspace rerender',async()=>{
  const {ui}=await setup();const fit=find(ui,'viewer-fit');fit.value='page';fit.handlers.change();
  await ui.click('Próxima');await ui.click('Rotacionar');await ui.click('Zoom +');await ui.click('Recolher análise');await ui.click('Expandir solução');
  const images=walk(ui.root).filter(e=>e.tag==='img');await ui.nav[0].click();await flush();await ui.click('Abrir');
  assert.equal(find(ui,'viewer-fit').value,'custom');assert.match(text(ui.root),/125% · Página 2\/2/);
  assert.equal(find(ui,'correction-workspace').dataset.solutionExpanded,'true');
  assert.equal(walk(ui.root).find(e=>e.id==='analysis-content').hidden,true);
  assert.match(walk(ui.root).find(e=>e.tag==='img').style.transform,/scale\(1.25\) rotate\(90deg\)/);
  assert.deepEqual(walk(ui.root).filter(e=>e.tag==='img'),images);
  await ui.click('Restaurar análise');assert.equal(walk(ui.root).find(e=>e.id==='analysis-content').hidden,true);
  await ui.click('Expandir análise');assert.equal(walk(ui.root).find(e=>e.id==='analysis-content').hidden,false);
});

test('desktop tab metadata has a compact provider caption and history is closed initially',async()=>{
  const {ui}=await setup();const solution=walk(ui.root).find(e=>e.id==='solution-pane');
  assert.equal(solution.dataset.tab,'original');await ui.click('Transcrição');assert.equal(solution.dataset.tab,'transcript');
  assert.match(text(find(ui,'caption-compact')),/Transcrição automática.*revisão 1/);
  assert.equal(Boolean(find(ui,'transcription-metadata').open),false);
  assert.ok(walk(ui.root).some(e=>e.className==='desktop-original-link'&&e.href.endsWith('/originals/0')));
});
