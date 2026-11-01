const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pilot, walk, text} = require('./tme-dom.cjs');
const catalog = [1,2,3,4,5].map(n => {
  const p = JSON.parse(fs.readFileSync(path.join(__dirname, `../../problems/TME2026P${n}/problem.json`), 'utf8'));
  return {...p, statement:p.statement_blocks.filter(b=>b.type==='text').map(b=>b.text).join('\n\n')};
});

test('existing TME selector lists all five official problems', async () => {
  const ui = await pilot({catalog});
  await ui.nav.find(n => n.dataset.view === 'new').click();
  const options = walk(ui.root).filter(e=>e.tag==='option' && e.value);
  assert.deepEqual(options.map(e=>e.value), catalog.map(p=>p.problem_id));
  for (const p of catalog) assert.ok(options.some(e=>e.textContent.includes(p.title)));
});

for (const p of catalog) test(`${p.problem_id}: complete statement and figures in existing collapsible panel`, async () => {
  const ui=await pilot({catalog});
  const saved={statementOpen:true};
  const section=ui.window.ConfiaCorrectionWorkspace.ProblemStatement(p,saved,[]);
  for (const block of p.statement_blocks.filter(b=>b.type==='text')) assert.ok(text(section).includes(block.text));
  const imgs=walk(section).filter(e=>e.tag==='img');
  assert.deepEqual(imgs.map(e=>e.src),p.figures.map(f=>f.src));
  assert.deepEqual(imgs.map(e=>e.alt),p.figures.map(f=>f.alt));
  const toggle=walk(section).find(e=>e.tag==='button');
  assert.equal(toggle.attributes['aria-expanded'],'true');
  const before=JSON.stringify(imgs.map(e=>[e.src,e.alt]));
  await toggle.click(); assert.equal(saved.statementOpen,false);
  await toggle.click(); assert.equal(saved.statementOpen,true);
  assert.equal(JSON.stringify(walk(section).filter(e=>e.tag==='img').map(e=>[e.src,e.alt])),before);
});

test('legacy ITA rendering and fallback still use the complete original string', async () => {
  const ui=await pilot();
  const statement='Enunciado ITA original, sem blocos.';
  const section=ui.window.ConfiaCorrectionWorkspace.ProblemStatement({problem_id:'ITA2025Q1',statement},{},[]);
  assert.ok(text(section).includes(statement));
  assert.equal(walk(section).filter(e=>e.tag==='img').length,0);
});

test('catalog image URL cannot load external content', async () => {
  const ui=await pilot();
  const p=JSON.parse(JSON.stringify(catalog[2]));p.figures[0].src='https://example.invalid/picture.png';
  const section=ui.window.ConfiaCorrectionWorkspace.ProblemStatement(p,{},[]);
  assert.equal(walk(section).filter(e=>e.tag==='img').length,0);
  assert.ok(text(section).includes(p.statement_blocks[0].text));
});

test('official mathematical notation parses with the bundled KaTeX renderer', () => {
  const katex=require('../../app/confia_lean_auditor/static/capture/vendor/katex-0.18.9/katex.min.js');
  let formulas=0;
  for (const p of catalog) for (const match of p.statement.matchAll(/\\\((.*?)\\\)/g)) {
    assert.doesNotThrow(()=>katex.renderToString(match[1],{throwOnError:true,trust:false}));formulas++;
  }
  assert.ok(formulas>20);
});
