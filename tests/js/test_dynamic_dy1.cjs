const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { element, descendants } = require('./ui-dom.cjs');
const source = fs.readFileSync(path.join(__dirname, '../../app/confia_lean_auditor/static/dynamic.js'), 'utf8');
const pid = 'dyn_' + 'a'.repeat(32), rid = 'drub_' + 'b'.repeat(32);
const criteria = [3,3,4].map((p,i) => ({criterion_id:`c${i}`, title:['Estrutura','Raízes','Conclusão'][i], description:`Descrição ${i}`, max_points:String(p), order:i+1}));
function doc(stage = 'new') {
  return {revision: stage === 'new' ? 1 : stage === 'draft' ? 2 : 3, problem:{problem_id:pid},
    statements:[{version_number:1,title:'Equação',statement:'Resolva x² - 5x + 6 = 0',max_score:'10'}],
    rubrics:stage === 'new' ? [] : [{rubric_id:rid,version_number:1,statement_version:1,max_score:'10',criteria,
      status:stage === 'approved' ? 'APPROVED' : 'DRAFT_TEACHER',is_current:stage === 'approved',
      approved_at:stage === 'approved' ? '2026-11-11T18:00:00Z' : null, approved_by:{kind:'TEACHER',actor_id:'teacher'}}],
    current_configuration:stage === 'approved' ? {package:{package_version:2,statement_version:1,rubric_version:1}} : null};
}
async function page(initial, mutation) {
  const panel = element('section'), calls = [];
  const window = {};
  const document = {querySelector:() => panel,createElement:element};
  const fetch = async (url, options) => {
    calls.push({url,options,body:options?.body ? JSON.parse(options.body) : null});
    const result = options?.method ? mutation?.(url,JSON.parse(options.body),options.method) : url === '/dynamic/problems' ? (initial ? [initial] : []) : initial;
    return {ok:true,json:async () => result};
  };
  vm.runInNewContext(source, {window,document,fetch,Set,Number,String,Error,Math});
  await window.ConfIADynamic.load();
  const nodes = () => descendants(panel);
  const button = label => nodes().find(n => n.tag === 'button' && n.textContent === label);
  if (initial) await nodes().find(n => n.tag === 'button' && n.textContent.includes('Enunciado V1')).click();
  return {panel,calls,nodes,button};
}

test('create an explicit Dynamic problem; AI suggestion cannot send a request', async () => {
  const ui = await page(null, () => doc());
  const form = ui.nodes().find(n => n.tag === 'form');
  const fields = descendants(form);
  fields.find(n => n.name === 'Enunciado').value = 'Resolva x² - 5x + 6 = 0';
  await form.emit('submit',{preventDefault(){}});
  const sent = ui.calls.find(c => c.options?.method);
  assert.equal(sent.body.correction_mode,'DYNAMIC');
  assert.equal(sent.body.max_score,'10');
  assert.equal(ui.button('Sugerir rubrica por IA').disabled,true);
  await ui.button('Sugerir rubrica por IA').click();
  assert(!ui.calls.some(c => c.url.includes('suggestion')));
  assert.match(ui.panel.textContent,/Disponível no próximo estágio/);
});

test('manual criteria total, editing, stable IDs and approval only after saved draft', async () => {
  const ui = await page(doc(), (url,body) => {
    assert.equal(body.expected_revision,1);
    assert.equal(body.criteria.length,3);
    assert.equal(body.criteria.reduce((a,c) => a + Number(c.max_points),0),10);
    return doc('draft');
  });
  for (let i = 0; i < 3; i++) {
    await ui.button('Adicionar critério').click();
    const fieldset = ui.nodes().filter(n => n.tag === 'fieldset').at(-1);
    const fields = descendants(fieldset).filter(n => n.name);
    fields.find(n => n.name.includes('título')).value = ['Estrutura','Raízes','Conclusão'][i];
    fields.find(n => n.name.includes('descrição')).value = 'Justificar a etapa.';
    const points = fields.find(n => n.name.includes('pontos')); points.value = String([3,3,4][i]);
    await points.emit('input');
  }
  assert.equal(ui.button('Salvar rubrica draft').disabled,false);
  assert.equal(ui.button('Aprovar rubrica').disabled,true);
  await ui.button('Salvar rubrica draft').click();
  assert.equal(ui.button('Aprovar rubrica').disabled,false);
  const description = ui.nodes().find(n => n.name?.includes('descrição')); description.value='Nova descrição';
  await description.emit('input');
  assert.equal(ui.button('Aprovar rubrica').disabled,true);
  assert.match(ui.panel.textContent,/Total dos critérios: 10 \/ 10/);
});

test('approval uses saved revision; history remains visible after statement change', async () => {
  let approvals = 0;
  const ui = await page(doc('draft'), (url,body) => {
    if (url.endsWith('/approve')) { approvals++; assert.equal(body.expected_revision,2); return doc('approved'); }
    assert(url.endsWith('/statements')); assert.equal(body.expected_revision,3);
    const changed = doc('approved'); changed.revision=4; changed.current_configuration=null;
    changed.statements.push({...changed.statements[0],version_number:2,statement:body.statement});
    changed.rubrics[0].status='SUPERSEDED'; changed.rubrics[0].is_current=false;
    return changed;
  });
  await ui.button('Aprovar rubrica').click();
  assert.equal(approvals,1); assert.match(ui.panel.textContent,/Rubrica V1 · APPROVED/);
  assert.match(ui.panel.textContent,/Pacote ativo V2/);
  const form = ui.nodes().filter(n => n.tag === 'form').at(-1);
  descendants(form).find(n => n.name === 'Enunciado').value='Resolva em R: x² - 5x + 6 = 0';
  await form.emit('submit',{preventDefault(){}});
  assert.match(ui.panel.textContent,/Enunciado V2/);
  assert.match(ui.panel.textContent,/Rubrica V1 · SUPERSEDED · Enunciado V1/);
  assert.match(ui.panel.textContent,/Sem pacote ativo/);
  assert.equal(ui.button('Aprovar rubrica').disabled,true);
});

test('invalid total blocks save, removal updates total, texts render without HTML injection', async () => {
  const value = doc('draft'); value.rubrics[0].criteria = criteria.map(c=>({...c}));
  value.rubrics[0].criteria[0].title='<img onerror=alert(1)>';
  const ui = await page(value);
  const points = ui.nodes().find(n => n.name?.includes('pontos')); points.value='2'; await points.emit('input');
  assert.equal(ui.button('Salvar como nova versão da rubrica').disabled,true);
  assert.equal(ui.button('Aprovar rubrica').disabled,true);
  assert(!ui.nodes().some(n=>n.tag==='img'));
  await ui.button('Remover critério').click();
  assert.match(ui.panel.textContent,/Total dos critérios: 7 \/ 10/);
});


test('removed criterion IDs are not reused for a different criterion in later edits', async () => {
  const value = doc('draft');
  value.rubrics[0].criteria = criteria.map((c,i)=>({...c,criterion_id:`criterion_${i+1}`}));
  const ui = await page(value);
  await ui.button('Remover critério').click();
  await ui.button('Adicionar critério').click();
  assert(ui.nodes().some(n=>n.name==='Critério criterion_4: título'));
  assert(!ui.nodes().some(n=>n.name==='Critério criterion_1: título'));
});
