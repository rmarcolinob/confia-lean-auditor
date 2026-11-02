const test=require('node:test');
const assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {flush}=require('./capture-dom.cjs');

test('synthetic queue labels, sample marks and filter deep links',async()=>{
  const rows=[{case_id:'case_'+'a'.repeat(32),external_candidate_ref:'TME2026P1_01',problem_id:'TME2026P1',source_mode:'DIGITAL_INK',data_origin:'synthetic_demo',demo_sample_groups:['alta indeterminação']}];
  const ui=await pilot({homeCases:rows,initialSearch:'?view=queue&origin=synthetic_demo&sample=selected'});
  assert.match(text(ui.root),/CASO SINTÉTICO/);
  assert.match(text(ui.root),/AMOSTRA VISUAL/);
  assert.ok(ui.calls.some(c=>c.url.includes('origin=synthetic_demo')&&c.url.includes('sample=selected')));
  const select=walk(ui.root).find(e=>e.dataset.filter==='origin');
  assert.equal(select.value,'synthetic_demo');
  assert.deepEqual(select.children.map(o=>o.textContent),['Todos','Sintéticos','Reais']);
  select.value='real';await select.handlers.change();await flush();
  assert.match(ui.window.history.url,/origin=real/);
});

test('synthetic case header exposes provenance and inspection group',async()=>{
  const rows=[{case_id:'case_'+'f'.repeat(32),submission_id:'sub_'+'b'.repeat(32),external_candidate_ref:'TME2026P2_01',problem_id:'TME2026P2',source_mode:'DIGITAL_INK',data_origin:'synthetic_demo',demo_sample_groups:['alta indeterminação']}];
  const view=await pilot({homeCases:rows,automatic:true,initialSearch:'?case_id='+rows[0].case_id});
  assert.match(text(view.root),/CASO SINTÉTICO/);
  assert.match(text(view.root),/AMOSTRA VISUAL/);
  assert.match(text(view.root),/Transcrição importada/);
  assert.doesNotMatch(text(view.root),/Reprocessar/);
  assert.equal(view.calls.some(c=>c.url.endsWith('/recognition-status')),false);
});
