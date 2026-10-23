const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk}=require('./tme-dom.cjs');
const fixture=require('../fixtures/rich_audit_response.json');
const find=(ui,cls)=>walk(ui.root).find(e=>e.className===cls);

test('shared outline icons retain accessible action names and textual result states',async()=>{
  const ui=await pilot({desktop:true,auditRun:{audit_run_id:'aud_test',status:'COMPLETED',stale:false,result:structuredClone(fixture)}});
  await ui.click('Abrir');
  for(const name of ['Voltar para fila','Zoom +','Zoom −','Anterior','Próxima','Rotacionar','Expandir solução']) {
    const control=walk(ui.root).find(e=>e.attributes['aria-label']===name);
    const icon=control.children.find(e=>e.className==='home-icon');
    assert.equal(icon.attributes['aria-hidden'],'true');assert.match(icon.innerHTML,/stroke-width="1.7"/);
  }
  const statuses=walk(ui.root).filter(e=>e.className==='result-glyph');assert.ok(statuses.length>0);
  for(const icon of statuses){assert.equal(icon.attributes.role,'img');assert.ok(icon.attributes['aria-label']);}
  const technical=find(ui,'technical-details');assert.equal(Boolean(technical.open),false);
  const criterion=find(ui,'audit-criterion');criterion.open=true;criterion.handlers.toggle();
  assert.equal(criterion.open,true);
  assert.equal(walk(ui.root).find(e=>e.name==='final').value,''); // Placeholder never changes a score.
});

test('segmented tabs preserve keyboard focus, selection and request-free switching',async()=>{
  const ui=await pilot({automatic:true,desktop:true});await ui.click('Abrir');
  const tabs=find(ui,'solution-tabs').children,calls=ui.calls.length;
  let prevented=false;
  tabs[0].handlers.keydown({key:'ArrowRight',preventDefault(){prevented=true;}});
  assert.equal(prevented,true);assert.equal(tabs[1].focused,true);
  assert.equal(tabs[1].attributes['aria-selected'],'true');assert.equal(tabs[0].tabIndex,-1);
  tabs[1].handlers.keydown({key:'End',preventDefault(){}});
  assert.equal(tabs[2].attributes['aria-selected'],'true');
  tabs[2].handlers.keydown({key:'Home',preventDefault(){}});
  assert.equal(tabs[0].attributes['aria-selected'],'true');assert.equal(tabs[0].tabIndex,0);
  assert.equal(ui.calls.length,calls);
  assert.deepEqual(find(ui,'steps').children.map(e=>e.dataset.state),['complete','current','upcoming','upcoming']);
});
