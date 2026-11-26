const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {page} = require('./capture-dom.cjs');
const catalog = [1,2,3,4,5].map(n => {
  const p = JSON.parse(fs.readFileSync(path.join(__dirname, `../../problems/TME2026P${n}/problem.json`), 'utf8'));
  return {...p, statement:p.statement_blocks.filter(b=>b.type==='text').map(b=>b.text).join('\n\n')};
});
const walk = e => [e, ...e.children.flatMap(walk)];
const open = p => page({embedded:true, catalogPath:'/tme/problems', problems:[p],
  search:`?embedded=1&tme_case_id=case_${'a'.repeat(32)}&problem_id=${p.problem_id}`});

for (const p of catalog) test(`${p.problem_id}: actual notebook renders all declared figures in statement order`, async () => {
  const ui = await open(p);
  const images = walk(ui.statement).filter(e=>e.tag==='img');
  assert.deepEqual(images.map(e=>e.src),p.figures.map(f=>f.src));
  assert.deepEqual(images.map(e=>e.alt),p.figures.map(f=>f.alt));
  assert.equal(ui.statementWrap.dataset.hasFigures,p.figures.length?'true':undefined);
  for (const [i,img] of images.entries()) {
    assert.equal(img.width,p.figures[i].width); assert.equal(img.height,p.figures[i].height);
    assert.ok(img.src && img.alt);
  }
  if (p.figures.length) {
    assert.deepEqual(ui.statement.children.map(e=>e.tag),p.statement_blocks.map(b=>b.type==='text'?'p':'figure'));
    assert.deepEqual(ui.mathRenders,p.statement_blocks.filter(b=>b.type==='text').map(b=>b.text));
  } else assert.equal(ui.statement.textContent,p.statement);
  ui.click('toggle-problem'); assert.equal(ui.statementWrap.hidden,true);
  ui.click('toggle-problem'); assert.equal(ui.statementWrap.hidden,false);
  assert.deepEqual(walk(ui.statement).filter(e=>e.tag==='img'),images);
});

for (const src of ['/Users/local/figure.png','https://example.invalid/figure.png','/static/problem-assets/TME2026P4/triangulo.png']) {
  test(`notebook rejects nonlocal or mismatched figure: ${src}`,async()=>{
    const p=JSON.parse(JSON.stringify(catalog[2]));p.figures[0].src=src;
    const ui=await open(p);
    assert.equal(walk(ui.statement).filter(e=>e.tag==='img').length,0);
    assert.equal(ui.statementWrap.dataset.hasFigures,undefined);
    assert.deepEqual(ui.mathRenders,p.statement_blocks.filter(b=>b.type==='text').map(b=>b.text));
  });
}

test('ITA retains its existing string/curated presentation even when extra metadata is present',async()=>{
  const p={...catalog[2],problem_id:'ITA2025Q1',statement:'Texto ITA original'};
  const ui=await open(p);
  assert.equal(walk(ui.statement).filter(e=>e.tag==='img').length,0);
  assert.equal(ui.statement.textContent,p.statement);
  assert.deepEqual(ui.mathRenders,[p.statement]);
});
