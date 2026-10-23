const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk}=require('./tme-dom.cjs');
const find=(ui,cls)=>walk(ui.root).find(e=>e.className===cls);
async function setup() {
  const ui=await pilot({automatic:true,desktop:true});await ui.click('Abrir');
  const viewport=find(ui,'original-document'),page=find(ui,'page-review'),surface=find(ui,'manuscript-surface');
  const image=walk(page).find(e=>e.tag==='img');image.naturalWidth=3024;image.naturalHeight=4032;
  viewport.clientWidth=814;viewport.clientHeight=204;
  return {ui,viewport,page,surface,image,layout:ui.window.ConfiaCorrectionWorkspace.layoutOriginal};
}

test('Original uses the full available width even in a short desktop window',async()=>{
  const {viewport,page,surface,image,layout}=await setup();
  assert.equal(viewport.dataset.layout,'full-page');
  layout(page,image,viewport,{zoom:1,rotation:0,fitMode:'page'});
  assert.equal(surface.style.width,'810px');assert.equal(surface.style.height,'1080px');
  assert.equal(page.style.paddingTop,'');
  viewport.clientHeight=1080;layout(page,image,viewport,{zoom:1,rotation:0,fitMode:'page'});
  assert.equal(surface.style.width,'810px');assert.equal(surface.style.height,'1080px');
});

test('Original follows splitter width and accommodates a rotated full sheet',async()=>{
  const {viewport,page,surface,image,layout}=await setup();
  const state={zoom:1,rotation:0,fitMode:'page'};
  viewport.clientWidth=910;layout(page,image,viewport,state);
  assert.equal(surface.style.width,'906px');assert.equal(surface.style.height,'1208px');
  state.rotation=90;layout(page,image,viewport,state);
  assert.equal(surface.style.width,'906px');assert.equal(surface.style.height,'679.5px');
  assert.match(image.style.transform,/translate\(906px, 0px\)/);
});

test('tabs restore wide Original after bounded comparison without requests or duplicate images',async()=>{
  const {ui,viewport,image,surface}=await setup();const calls=ui.calls.length;
  const fit=find(ui,'viewer-fit');fit.handlers.change();
  assert.equal(surface.style.width,'810px');
  await ui.click('Comparar');assert.equal(viewport.dataset.layout,'bounded');
  assert.ok(parseFloat(surface.style.height)<=200);
  await ui.click('Transcrição');assert.equal(viewport.hidden,true);
  await ui.click('Original');assert.equal(viewport.hidden,false);
  assert.equal(viewport.dataset.layout,'full-page');assert.equal(surface.style.width,'810px');
  assert.equal(surface.style.height,'1080px');assert.equal(walk(ui.root).find(e=>e.tag==='img'),image);
  assert.equal(ui.calls.length,calls);assert.equal(find(ui,'correction-workspace').dataset.solutionTab,'original');
});
