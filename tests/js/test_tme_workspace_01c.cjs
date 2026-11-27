const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const find=(ui,cls)=>walk(ui.root).find(e=>e.className===cls);
async function setup(desktop=true) {
  const ui=await pilot({automatic:true,desktop,pageCount:2});await ui.click('Abrir');
  const viewport=find(ui,'original-document'),pages=walk(ui.root).filter(e=>e.className==='page-review');
  viewport.clientWidth=604;viewport.clientHeight=404;
  for(const page of pages){const img=walk(page).find(e=>e.tag==='img');img.naturalWidth=600;img.naturalHeight=1200;}
  const fit=find(ui,'viewer-fit');fit.handlers.change();
  return {ui,viewport,pages,fit,image:walk(pages[0]).find(e=>e.tag==='img'),surface:find(ui,'manuscript-surface')};
}

test('desktop defaults to page and mobile defaults to width',async()=>{
  const desktop=await setup(),mobile=await setup(false);
  assert.equal(desktop.fit.value,'page');assert.equal(desktop.surface.style.height,'1200px');
  assert.equal(mobile.fit.value,'width');assert.equal(mobile.surface.style.width,'600px');assert.equal(mobile.surface.style.height,'1200px');
  assert.equal(mobile.pages[0].style.paddingTop,'');
});

test('automatic page fit uses the smaller dimension and centers portrait and landscape',async()=>{
  const {ui,viewport,pages,image,surface}=await setup();const layout=ui.window.ConfiaCorrectionWorkspace.layoutOriginal;
  viewport.dataset.layout="bounded"; // Comparison keeps the bounded fit-page algorithm.
  const state={rotation:0,zoom:1};
  layout(pages[0],image,viewport,state);assert.equal(surface.style.width,'200px');assert.equal(surface.style.height,'400px');assert.equal(pages[0].style.paddingTop,'2px');
  image.naturalWidth=1200;image.naturalHeight=600;layout(pages[0],image,viewport,state);
  assert.equal(surface.style.width,'600px');assert.equal(surface.style.height,'300px');assert.equal(pages[0].style.paddingTop,'52px');
  viewport.clientHeight=204;layout(pages[0],image,viewport,state);assert.equal(surface.style.width,'400px');assert.equal(surface.style.height,'200px');
});

test('manual zoom becomes custom, freezes automatic base, and page fit restores framing',async()=>{
  const {ui,fit,image,surface,viewport}=await setup();const calls=ui.calls.length;
  await ui.click('Zoom +');assert.equal(fit.value,'custom');assert.equal(surface.style.height,'1500px');assert.match(text(ui.root),/125%/);
  viewport.clientHeight=604;await ui.click('Zoom +');assert.equal(surface.style.height,'1800px'); // Manual base stays wide when viewport height changes.
  fit.value='page';fit.handlers.change();assert.equal(surface.style.height,'1200px');assert.match(text(ui.root),/100%/);
  fit.value='width';fit.handlers.change();assert.equal(surface.style.height,'1200px');assert.equal(image.style.width,'600px');
  fit.value='page';fit.handlers.change();assert.equal(surface.style.height,'1200px');assert.equal(ui.calls.length,calls);
});

test('desktop rotation restores page fit after custom zoom and fits all four orientations',async()=>{
  const {ui,fit,surface}=await setup();await ui.click('Zoom +');assert.equal(fit.value,'custom');
  for(let i=0;i<4;i++) {
    await ui.click('Rotacionar');assert.equal(fit.value,'page');assert.match(text(ui.root),/100%/);
    assert.ok(parseFloat(surface.style.width)<=600);assert.ok(parseFloat(surface.style.height)<=1200);
  }
});

test('page navigation keeps the selected fit mode and uses each image dimensions',async()=>{
  const {ui,pages,fit}=await setup();const second=walk(pages[1]).find(e=>e.tag==='img'),surface=walk(pages[1]).find(e=>e.className==='manuscript-surface');
  second.naturalWidth=1200;second.naturalHeight=600;
  await ui.click('Próxima');assert.equal(fit.value,'page');assert.equal(surface.style.width,'600px');assert.equal(surface.style.height,'300px');
  fit.value='width';fit.handlers.change();await ui.click('Anterior');assert.equal(fit.value,'width');
  await ui.click('Zoom −');assert.equal(fit.value,'custom');await ui.click('Próxima');assert.equal(fit.value,'custom');
});

test('default follows breakpoint until the evaluator explicitly selects a mode',async()=>{
  const {ui}=await setup();const state={};
  assert.equal(ui.window.ConfiaCorrectionWorkspace.originalFitMode(state),'page');
  ui.window.matchMedia=()=>({matches:false});assert.equal(ui.window.ConfiaCorrectionWorkspace.originalFitMode(state),'width');
  state.fitMode='width';ui.window.matchMedia=()=>({matches:true});assert.equal(ui.window.ConfiaCorrectionWorkspace.originalFitMode(state),'width');
});
