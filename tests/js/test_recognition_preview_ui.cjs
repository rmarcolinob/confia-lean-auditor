const test = require('node:test');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const Model = require('../../app/confia_lean_auditor/static/capture/ink-model.js');
const { page, deferred, flush } = require('./capture-dom.cjs');
const { page: workspace } = require('./workspace-dom.cjs');
const { page: teacher, transportFor, history, revision, summary, transcriptionId, descendants } = require('./teacher-dom.cjs');
const fs = require('node:fs');
const path = require('node:path');

function snapshot() {
  const draft = Model.createDraft('ITA2025Q1');
  return Model.freeze(Model.addStroke(draft, { page_id: draft.pages[0].page_id, pointer_type: 'pen',
    points: [{x:10,y:20,t_ms:0,pressure_reported:0.5}] }));
}
function reply(init) {
  const raw = JSON.parse(init.body).snapshot_json;
  const source = JSON.parse(raw);
  return { ok:true, json:async () => ({ client_preview_id:JSON.parse(init.body).client_preview_id,
    problem_id:source.problem_id, snapshot_id:source.local_snapshot_id,
    snapshot_sha256:createHash('sha256').update(raw).digest('hex'), page_count:source.pages.length,
    active_stroke_count:source.active_stroke_ids.length,
    result:{segments:[{page_index:0,order:0,kind:'mixed',text:'2 + 2 = 5',latex:'2 + 2 = 5'}]} }) };
}

test('standalone preview uses frozen strokes before send, renders KaTeX unchanged, and creates no official run', async () => {
  const calls=[];
  const ui=await page({sender:{send:async()=>{ throw Error('send not used'); }},
    fetch:async (url,init) => { calls.push({url,init}); return reply(init); }});
  const frozen=snapshot(); await ui.recover(frozen);
  assert.equal(ui.get('#preview-writing').disabled,false);
  assert.equal(ui.get('#send-solution').disabled,true);
  await ui.click('preview-writing');
  assert.equal(calls.length,1);
  assert.equal(calls[0].url,'/submissions/recognition-preview');
  assert.equal(JSON.parse(calls[0].init.body).snapshot_json,JSON.stringify(Model.exportClone(frozen),null,2));
  assert.equal(ui.get('#preview-result').children[0].children[1].textContent,'rendered:2 + 2 = 5');
  assert.equal(ui.get('#preview-result').children[0].children[2].children[1].textContent,'2 + 2 = 5');
  assert.equal(ui.get('#send-solution').disabled,false);
  assert(calls.every(c => !/\/recognitions|\/audits|\/transcriptions|\/lean/.test(c.url)));
  assert.equal(JSON.stringify(calls).includes('CONFIA_MATHPIX_APP_KEY'),false);
  const revised=Model.freeze(Model.createDraft(frozen.problem_id,frozen));
  await ui.recover(revised);
  assert.equal(ui.get('#preview-result').children.length,0);
  assert.equal(ui.get('#send-solution').disabled,true);
});

test('late preview is discarded after continuing the draft; error never shows a successful preview', async () => {
  const pending=deferred();
  const frozen=snapshot();
  const ui=await page({initialDocument:frozen,
    fetch:async (_url,init) => pending.promise});
  // Load a known frozen version through the explicit recovery path.
  await ui.recover(frozen);
  const reading=ui.click('preview-writing'); await flush();
  assert.equal(ui.get('#preview-message').textContent,'Reconhecendo...');
  await ui.click('continue-draft');
  pending.resolve({ok:false,status:503}); await reading;
  assert.equal(ui.get('#preview-result').children.length,0);
  assert.match(ui.get('#preview-message').textContent,/Prepare uma versão/);
  let sent=0;
  const failedUi=await page({initialDocument:frozen,sender:{send:async()=>{sent+=1;}},
    fetch:async()=>({ok:false,status:503})});
  await failedUi.recover(frozen);
  await failedUi.click('preview-writing');
  assert.equal(failedUi.get('#preview-result').children.length,0);
  assert.match(failedUi.get('#preview-message').textContent,/Não foi possível reconhecer/);
  assert.equal(failedUi.get('#send-solution').disabled,true);
  await failedUi.click('send-solution');
  assert.equal(sent,0);
});

test('embedded parent orders prepare, preview, send and displays only the current preview', async () => {
  const ui=await workspace(); await ui.start('submission');
  ui.notebook({local_snapshot_id:'snapshot:1',controls:{document_id:'snapshot:1',frozen:true,
    can_preview:true,can_send:true,preview_message:'Prévia transitória.',
    preview_segments:[{page_index:0,kind:'math',latex:'2 + 2 = 5'}]}});
  const html=fs.readFileSync(path.join(__dirname,'../../app/confia_lean_auditor/static/index.html'),'utf8');
  assert(html.indexOf('id="workspace-prepare-snapshot"') < html.indexOf('id="workspace-preview-writing"'));
  assert(html.indexOf('id="workspace-preview-writing"') < html.indexOf('id="workspace-send-solution"'));
  assert.equal(ui.get('#workspace-preview-result').children[0].children[1].textContent,'rendered:2 + 2 = 5');
  await ui.get('#workspace-preview-writing').click();
  assert.equal(ui.commands.at(-1).message.action,'preview-writing');
  ui.notebook({local_snapshot_id:null,controls:{document_id:'draft:2',frozen:false,can_preview:false,preview_segments:[]}});
  assert.equal(ui.get('#workspace-preview-result').children.length,0);
});

test('teacher shows rendered persisted math beside intact original and analysis below, including legacy revisions', async () => {
  const base=transportFor(true,true);
  const ui=teacher(async url => url===`/transcriptions/${transcriptionId}` ? {ok:true,json:async()=>({
    ...history,revisions:[{...revision,provider:null,segments:[
      {page_index:0,order:0,kind:'math',latex:'2 + 2 = 5'},
      {page_index:0,order:1,kind:'text',text:'<script>literal</script>'},
      {page_index:0,order:2,kind:'unknown',text:'?'},
    ]}]})} : base(url));
  await ui.get('#refresh-manuscripts').click(); await ui.get('#manuscript-list').children[0].click();
  const detail=ui.get('#manuscript-detail');
  const grid=detail.children.find(n=>n.className==='transcription-workspace');
  assert.equal(grid.children[0].className,'original-manuscript-panel');
  assert.equal(grid.children[1].className,'transcription-panel');
  assert(detail.children.indexOf(grid)<detail.children.findIndex(n=>n.className==='manuscript-analysis-panel'));
  const tree=descendants(grid);
  assert(tree.some(n=>n.tag==='img' && n.src?.includes('/pages/0')));
  assert(tree.some(n=>n.textContent==='rendered:2 + 2 = 5'));
  assert(tree.some(n=>n.textContent==='<script>literal</script>'));
  assert(tree.some(n=>n.textContent==='?'));
  assert(tree.some(n=>n.title?.includes('não significa solução correta')));
  const css=fs.readFileSync(path.join(__dirname,'../../app/confia_lean_auditor/static/submissions/teacher.css'),'utf8');
  assert.match(css,/\.transcription-workspace\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1\.15fr\) minmax\(0, 1fr\)/);
  assert.match(css,/@media \(max-width: 760px\)\s*\{[^}]*\.transcription-workspace\s*\{ grid-template-columns: minmax\(0, 1fr\)/);
});

test('teacher receives the official Mathpix NEEDS_REVIEW revision and can confer fidelity before analysis', async () => {
  const recognized={...revision,source:'automatic',provider:'mathpix',recognizer_run_id:'run_'+'a'.repeat(32),
    status:'NEEDS_REVIEW',segments:[{page_index:0,order:0,kind:'math',latex:'2 + 2 = 5'}]};
  const automatic={...summary,transcription:{...summary.transcription,source:'automatic',provider:'mathpix'},latest_revision:recognized};
  const base=transportFor();
  const ui=teacher(async url => url.endsWith('/transcriptions') ? {ok:true,json:async()=>[automatic]}
    : url===`/transcriptions/${transcriptionId}` ? {ok:true,json:async()=>({
      ...history,transcription:automatic.transcription,revisions:[recognized],acceptances:[]})}
      : base(url));
  await ui.get('#refresh-manuscripts').click();
  await ui.get('#manuscript-list').children[0].click();
  const tree=descendants(ui.get('#manuscript-detail'));
  assert(tree.some(n=>n.className==='transcription-visual' && n.textContent.includes('rendered:2 + 2 = 5')));
  assert(tree.some(n=>n.tag==='img' && n.src?.endsWith('/pages/0')));
  const accept=tree.find(n=>n.tag==='button' && n.textContent==='Conferir transcrição');
  assert.equal(accept.disabled,false);
  assert(tree.some(n=>n.className==='manuscript-analysis-panel' && n.textContent.includes('transcrição precisa ser conferida')));
  assert(ui.calls.every(call=>call.options?.method!=='POST'));
});

test('recognition UI keeps Mathpix credentials server side and uses safe DOM rendering', () => {
  const root=path.join(__dirname,'../../app/confia_lean_auditor/static');
  for (const file of ['capture/tablet.js','resolution-workspace.js','submissions/teacher.js','recognition-view.js']) {
    const source=fs.readFileSync(path.join(root,file),'utf8');
    assert.doesNotMatch(source,/CONFIA_MATHPIX_APP_(ID|KEY)|app_key|app_id/);
  }
  const renderer=fs.readFileSync(path.join(root,'recognition-view.js'),'utf8');
  assert.match(renderer,/trust:\s*false/);
  assert.doesNotMatch(renderer,/innerHTML|insertAdjacentHTML/);
});

test('tablet Mathpix prose with inline TeX renders consistently in student preview and teacher view', async () => {
  const recognized = String.raw`Seja \(p(x)=x^{57}+a x^{14}+b x^7+1\)`;
  const calls = [];
  const student = await page({ sender: { send: async () => { throw Error('preview must not send'); } },
    fetch: async (url, init) => {
      calls.push(url);
      const body = JSON.parse(init.body), snapshot = JSON.parse(body.snapshot_json);
      return { ok: true, json: async () => ({ client_preview_id: body.client_preview_id,
        problem_id: snapshot.problem_id, snapshot_id: snapshot.local_snapshot_id,
        snapshot_sha256: createHash('sha256').update(body.snapshot_json).digest('hex'),
        page_count: snapshot.pages.length, active_stroke_count: snapshot.active_stroke_ids.length,
        result: { segments: [{ page_index: 0, order: 0, kind: 'text', text: recognized }] } }) };
    } });
  await student.recover(snapshot());
  await student.click('preview-writing');
  const preview = student.get('#preview-result').children[0].children[1];
  assert.equal(preview.children[0].textContent, 'Seja ');
  assert.equal(preview.children[1].textContent, 'rendered:p(x)=x^{57}+a x^{14}+b x^7+1');
  assert.deepEqual(calls, ['/submissions/recognition-preview']);

  const base = transportFor(true, true);
  const persisted = { ...revision, source: 'automatic', provider: 'mathpix', segments: [
    { page_index: 0, order: 0, kind: 'text', text: recognized, latex: null }] };
  const professor = teacher(async url => url === `/transcriptions/${transcriptionId}`
    ? { ok: true, json: async () => ({ ...history, revisions: [persisted] }) } : base(url));
  await professor.get('#refresh-manuscripts').click();
  await professor.get('#manuscript-list').children[0].click();
  const tree = descendants(professor.get('#manuscript-detail'));
  const visual = tree.find(node => node.className === 'transcription-visual');
  assert(visual.textContent.includes('rendered:p(x)=x^{57}+a x^{14}+b x^7+1'));
  assert(!visual.textContent.includes(String.raw`\(`));
  const sourceField = tree.find(node => node.tag === 'textarea' && node.value === recognized);
  assert(sourceField);
  assert.equal(persisted.segments[0].text, recognized);
});
