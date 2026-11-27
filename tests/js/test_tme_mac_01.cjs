const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk}=require('./tme-dom.cjs');
const find=(ui,cls)=>walk(ui.root).find(e=>e.className===cls);

async function setup(pageCount=1) {
  const ui=await pilot({automatic:true,desktop:true,pageCount});await ui.click('Abrir');
  const viewport=find(ui,'original-document'),pages=walk(ui.root).filter(e=>e.className==='page-review');
  viewport.clientWidth=805;viewport.clientHeight=204;
  for(const page of pages){const image=walk(page).find(e=>e.tag==='img');image.naturalWidth=3024;image.naturalHeight=4032;}
  const fit=find(ui,'viewer-fit');fit.handlers.change();
  return {ui,viewport,pages,fit,surface:find(ui,'manuscript-surface')};
}

test('desktop single sheet uses document flow at approved width and natural height',async()=>{
  const {viewport,surface}=await setup();
  assert.equal(viewport.dataset.scrollMode,'document');
  assert.equal(surface.style.width,'801px');assert.equal(surface.style.height,'1068px');
  assert.ok(parseFloat(surface.style.height)>viewport.clientHeight);
});

test('manual enlargement keeps panning, and normal fit restores document flow',async()=>{
  const {ui,viewport,fit,surface}=await setup();
  await ui.click('Zoom +');assert.equal(viewport.dataset.scrollMode,'viewer');
  assert.equal(surface.style.width,'1001.25px');
  fit.value='width';fit.handlers.change();assert.equal(viewport.dataset.scrollMode,'document');
  assert.equal(surface.style.width,'801px');
  await ui.click('Comparar');assert.equal(viewport.dataset.scrollMode,'viewer');
  await ui.click('Original');assert.equal(viewport.dataset.scrollMode,'document');
});

test('two pages retain navigation and use their own ratio after rotation without requests',async()=>{
  const {ui,viewport,pages}=await setup(2),calls=ui.calls.length;
  const second=walk(pages[1]).find(e=>e.tag==='img'),surface=walk(pages[1]).find(e=>e.className==='manuscript-surface');
  second.naturalWidth=4032;second.naturalHeight=3024;
  await ui.click('Próxima');assert.equal(pages[0].hidden,true);assert.equal(pages[1].hidden,false);
  assert.equal(surface.style.width,'801px');assert.equal(surface.style.height,'600.75px');
  for(const rotation of [90,180,270,0]) {
    await ui.click('Rotacionar');assert.equal(viewport.dataset.scrollMode,'document');
    assert.equal(surface.style.width,'801px');
    assert.equal(surface.style.height,rotation===90||rotation===270?'1068px':'600.75px');
  }
  await ui.click('Anterior');assert.equal(pages[0].hidden,false);assert.equal(pages[1].hidden,true);
  // An inactive landscape sheet cannot override the visible portrait's overflow
  // policy when a manually frozen base no longer fits after rotation/resize.
  const layout=ui.window.ConfiaCorrectionWorkspace.layoutOriginal;
  const state={rotation:90,zoom:1,fitMode:'custom',customWidth:801};
  layout(pages[0],walk(pages[0]).find(e=>e.tag==='img'),viewport,state);
  assert.equal(viewport.dataset.scrollMode,'viewer');
  layout(pages[1],second,viewport,state);
  assert.equal(viewport.dataset.scrollMode,'viewer');
  assert.equal(ui.calls.length,calls);
});

test('leaving desktop restores existing tablet/mobile viewport sizing',async()=>{
  const {ui,viewport,pages}=await setup(),layout=ui.window.ConfiaCorrectionWorkspace.layoutOriginal;
  const image=walk(pages[0]).find(e=>e.tag==='img'),surface=find(ui,'manuscript-surface');
  ui.window.matchMedia=()=>({matches:false});
  for(const width of [679,935,357]) {
    viewport.clientWidth=width;layout(pages[0],image,viewport,{zoom:1,rotation:0,fitMode:'page'});
    assert.equal(viewport.dataset.scrollMode,'viewer');
    assert.equal(surface.style.width,`${width-4}px`);
    assert.ok(Math.abs(parseFloat(surface.style.height)-(width-4)*4/3)<1e-8);
  }
  ui.window.matchMedia=()=>({matches:true});
  layout(pages[0],image,viewport,{zoom:1,rotation:0,fitMode:'page'});
  assert.equal(viewport.dataset.scrollMode,'document');
});
