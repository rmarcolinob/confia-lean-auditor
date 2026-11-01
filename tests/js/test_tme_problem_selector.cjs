const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pilot,walk,text} = require('./tme-dom.cjs');
const problemRoot=path.join(__dirname,'../../problems');
const catalog=fs.readdirSync(problemRoot).filter(id=>/^(ITA2025(?:F2)?Q\d+|TME2026P\d+)$/.test(id)).map(id=>{
  const p=JSON.parse(fs.readFileSync(path.join(problemRoot,id,'problem.json'),'utf8'));
  return {...p,problem_id:id,statement:p.statement||p.statement_blocks.filter(b=>b.type==='text').map(b=>b.text).join('\n\n')};
});
const expected=[
  ['ITA 2025 — 1ª fase',[1,3,4,5,8].map(n=>[`ITA2025Q${n}`,`Questão ${n}`])],
  ['ITA 2025 — 2ª fase',[1,3,5,6,8].map(n=>[`ITA2025F2Q${n}`,`Questão ${n}`])],
  ['TME² 2026 — 2ª fase',[1,2,3,4,5].map(n=>[`TME2026P${n}`,`Problema ${n}`])],
];

for(const desktop of [true,false]) test(`native grouped selector preserves all 15 IDs and short labels (desktop=${desktop})`,async()=>{
  const before=JSON.stringify(catalog);
  const ui=await pilot({catalog:[...catalog].reverse(),desktop});
  await ui.nav.find(n=>n.dataset.view==='new').click();
  const select=walk(ui.root).find(e=>e.tag==='select');
  assert.equal(select.required,true);
  assert.deepEqual(select.children.filter(e=>e.tag==='optgroup').map(g=>[g.label,g.children.map(o=>[o.value,o.textContent])]),expected);
  assert.equal(walk(select).filter(e=>e.tag==='option'&&e.value).length,15);
  for(const p of catalog) assert.ok(!text(select).includes(p.title));
  assert.equal(JSON.stringify(catalog),before);
});

for(const p of catalog) test(`${p.problem_id}: selection submits original ID and preserves its statement/figures`,async()=>{
  const ui=await pilot({catalog});
  await ui.nav.find(n=>n.dataset.view==='new').click();
  const select=walk(ui.root).find(e=>e.tag==='select');select.value=p.problem_id;
  walk(ui.root).find(e=>e.tag==='input').value='SELECTOR-CONTROL';
  await ui.click('Escrever no tablet');await ui.click('Continuar');
  const call=ui.calls.find(c=>c.url==='/tme/cases'&&c.options.method==='POST');
  assert.equal(JSON.parse(call.options.body).problem_id,p.problem_id);
  const frame=walk(ui.root).find(e=>e.tag==='iframe');
  assert.equal(new URL(frame.src,'https://confia.test').searchParams.get('problem_id'),p.problem_id);
  const section=ui.window.ConfiaCorrectionWorkspace.ProblemStatement(p,{statementOpen:true},[]);
  for(const part of p.statement_blocks?.filter(b=>b.type==='text').map(b=>b.text)||[p.statement]) assert.ok(text(section).includes(part));
  assert.deepEqual(walk(section).filter(e=>e.tag==='img').map(e=>e.src),(p.figures||[]).map(f=>f.src));
});
