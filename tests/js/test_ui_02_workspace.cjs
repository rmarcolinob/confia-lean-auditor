const test = require('node:test');
const assert = require('node:assert/strict');
const { page } = require('./workspace-dom.cjs');
const { page: capturePage } = require('./capture-dom.cjs');
const { flush, deferred } = require('./ui-dom.cjs');
const Model = require('../../app/confia_lean_auditor/static/capture/ink-model.js');
const fs = require('node:fs');
const path = require('node:path');
const report = id => ({ ok:true, json:async () => ({ problem_id:id, pedagogical_report: { summary:`Feedback ${id}` } }) });

test('Resolver opens the one notebook for the selected problem; both purposes reuse its frame', async () => {
  const ui = await page(); await ui.select('B'); await ui.start();
  assert.match(ui.frame.src, /\/capture\?embedded=1&problem_id=B&mode=practice/);
  assert.equal(ui.get('#notebook-surface').hidden,false);
  const source = ui.frame.src;
  await ui.get('#submission-mode').click(); ui.notebook();
  assert.equal(ui.frame.src,source);
  assert.deepEqual(JSON.parse(JSON.stringify(ui.commands.at(-1).message)), { type:'confia-workspace-command',action:'configure',problem_id:'B',mode:'submission' });
  assert.equal(ui.get('#resolution-title').textContent,'Solução para envio');
  assert.equal(ui.get('#practice-response').hidden,true);
  assert.equal(ui.calls.some(c => c.options?.method === 'POST'),false);
});

test('practice audits only explicitly typed text, with a frozen problem/draft/presentation context', async () => {
  const pending=deferred(); const ui=await page(() => pending.promise); await ui.start();
  await ui.write('Texto explícito do aluno'); await ui.get('#audit-button').click();
  assert.deepEqual(JSON.parse(ui.calls.at(-1).options.body),{problem_id:'A',solution:'Texto explícito do aluno'});
  await ui.write('Texto alterado'); pending.resolve(report('A')); await flush();
  assert.match(ui.get('#result-panel').textContent,/Análise de versão anterior.*Questão analisada: A.*Texto explícito do aluno/);
  const analysis=vmValue(ui,'studentAnalysis');
  assert.equal(analysis.context.mode,'practice'); assert.equal(analysis.context.draft_id,'draft:A');
  assert.equal(analysis.context.question_presentation_version,1);
  assert.equal(ui.calls.some(c => c.url==='/submissions'),false);
});
function vmValue(ui,expression) { return require('node:vm').runInContext(expression,ui.context); }

test('handwriting does not create text or trigger analysis; ink edits mark an earlier analysis stale', async () => {
  const ui=await page(); await ui.start(); ui.notebook({ink_version:'1:1:1'});
  assert.equal(ui.get('#solution-input').value,'');
  assert.equal(ui.calls.some(c => c.url==='/audit'),false);
  await ui.get('#audit-button').click(); assert.equal(ui.calls.some(c => c.url==='/audit'),false);
  await ui.write('Minha solução'); await ui.get('#audit-button').click(); await flush();
  ui.notebook({ink_version:'2:1:2'});
  assert.match(ui.get('#result-panel').textContent,/Análise de versão anterior/);
  assert.equal(ui.calls.filter(c => c.url==='/audit').length,1);
});

test('changing question/draft keeps explicit text, analysis and receipts in their own contexts', async () => {
  const ui=await page((url,options) => report(JSON.parse(options.body).problem_id)); await ui.start();
  await ui.write('Texto A'); await ui.get('#audit-button').click(); await flush();
  await ui.select('B'); await ui.start(); ui.notebook({draft_id:'draft:B'});
  assert.equal(ui.get('#solution-input').value,''); assert.doesNotMatch(ui.get('#result-panel').textContent,/Texto A|Feedback A/);
  await ui.write('Texto B');
  await ui.select('A'); await ui.start(); ui.notebook({draft_id:'draft:A'});
  assert.equal(ui.get('#solution-input').value,'Texto A'); assert.match(ui.get('#result-panel').textContent,/Questão analisada: A/);
  ui.notebook({draft_id:'draft:new-A'});
  assert.equal(ui.get('#solution-input').value,''); assert.doesNotMatch(ui.get('#result-panel').textContent,/Texto A|Feedback A/);
});

test('late practice analysis cannot appear in submission and returns only to its original draft', async () => {
  const pending=deferred(); const ui=await page(() => pending.promise); await ui.start(); await ui.write('Texto A');
  await ui.get('#audit-button').click(); await ui.get('#submission-mode').click(); ui.notebook();
  pending.resolve(report('A')); await flush();
  assert.equal(vmValue(ui,'studentAnalysis'),null); assert.equal(ui.get('#student-feedback').hidden,true);
  await ui.get('#audit-button').click(); assert.equal(ui.calls.filter(c => c.url==='/audit').length,1);
  await ui.get('#practice-mode').click(); ui.notebook();
  assert.match(ui.get('#result-panel').textContent,/Questão analisada: A.*Texto A/);
});

test('late analysis for A cannot replace solution or feedback for B', async () => {
  const pending=deferred(); const ui=await page(() => pending.promise); await ui.start(); await ui.write('Texto A'); await ui.get('#audit-button').click();
  await ui.select('B'); await ui.start(); ui.notebook({draft_id:'draft:B'}); await ui.write('Texto B');
  pending.resolve(report('A')); await flush();
  assert.equal(ui.get('#solution-input').value,'Texto B'); assert.equal(vmValue(ui,'studentAnalysis'),null);
  assert.doesNotMatch(ui.get('#result-panel').textContent,/Texto A|Feedback A/);
});

test('Feedback is current session context; Envios uses session receipts and never loads general server history', async () => {
  const ui=await page(); ui.visit('feedback'); assert.equal(ui.get('#student-workspace').hidden,true);
  await ui.start('submission');
  const receipt={submission_id:'sub_test',snapshot_id:'snapshot:A',problem_id:'A',received_at:'2026-10-03T12:00:00Z'};
  ui.notebook({local_snapshot_id:'snapshot:B',receipt});
  assert.doesNotMatch(ui.get('#student-receipt-list').textContent,/sub_test/);
  ui.notebook({local_snapshot_id:'snapshot:A',receipt}); ui.visit('submissions');
  assert.match(ui.get('#student-receipt-list').textContent,/Número do envio: sub_test.*Versão enviada: snapshot:A/);
  assert.equal(ui.calls.some(c => c.url==='/submissions'),false);
});

test('messages from unrelated windows or origins cannot switch notebook context', async () => {
  const ui=await page(); await ui.start();
  const data={type:'confia-notebook-context',context:{problem_id:'B',draft_id:'draft:other',mode:'practice'}};
  ui.events.message({origin:'http://other.test',source:ui.frame.contentWindow,data});
  ui.events.message({origin:ui.location.origin,source:{},data});
  assert.equal(ui.window.ConfIAWorkspace.analysisContext().draft_id,'draft:A');
});

test('practice notebook preserves writing/pages/autosave but cannot prepare or send a submission', async () => {
  let sends=0;
  const ui=await capturePage({embedded:true,autoSave:true,sender:{send() { sends++; }}});
  assert.equal(ui.messages.at(-1).context.problem_id,'ITA2025Q1');
  assert.equal(ui.messages.at(-1).context.mode,'practice');
  ui.click('add-page'); await flush(); assert.equal(ui.saves.at(-1).document.pages.length,2);
  await ui.click('prepare-snapshot'); await ui.click('send-solution'); assert.equal(sends,0);
  assert.equal(ui.saves.some(s => s.document.document_kind==='local_snapshot'),false);
  await ui.command({problem_id:'ITA2025Q1',mode:'submission'});
  const preparing=ui.click('prepare-snapshot'); await preparing;
  assert.equal(ui.messages.at(-1).context.local_snapshot_id,ui.saves.at(-1).document.local_snapshot_id);
});

test('notebook entry resolves correct problem and serial question changes never mix drafts', async () => {
  const ui=await capturePage({embedded:true,autoSave:true,problems:[{problem_id:'A',statement:'A'},{problem_id:'B',statement:'B'}],search:'?embedded=1&problem_id=B&mode=practice'});
  const first=ui.messages.at(-1).context;
  assert.equal(first.problem_id,'B');
  await ui.command({problem_id:'A',mode:'practice'});
  const second=ui.messages.at(-1).context; assert.equal(second.problem_id,'A'); assert.notEqual(second.draft_id,first.draft_id);
  assert.equal(ui.saves.at(-1).document.problem_id,'B');
  assert.equal(ui.saves.at(-1).document.draft_id,first.draft_id);
});

test('receipt arriving after a mode/question change remains attached to the submitted snapshot', async () => {
  const pending=deferred(); let sent;
  const ui=await capturePage({embedded:true,autoSave:true,search:'?embedded=1&problem_id=ITA2025Q1&mode=submission',sender:{send(snapshot) {sent=snapshot;return pending.promise;}}});
  await ui.click('prepare-snapshot'); const sending=ui.click('send-solution');
  await ui.command({problem_id:'ITA2025Q1',mode:'practice'}); ui.click('continue-draft');
  const receipt={submission_id:'sub_test',snapshot_id:sent.local_snapshot_id,problem_id:sent.problem_id,received_at:'2026-10-03T12:00:00Z'};
  pending.resolve(receipt); await sending;
  const result=ui.messages.find(m => m.context.receipt?.submission_id==='sub_test');
  assert.equal(result.context.local_snapshot_id,sent.local_snapshot_id); assert.equal(result.context.mode,'submission');
  assert.equal(ui.receipt.hidden,true); assert.notEqual(ui.messages.at(-1).context.draft_id,sent.draft_id);
});

test('typed alternative preserves the selected statement, text, analysis and the same notebook', async () => {
  const ui=await page(); await ui.select('B'); await ui.start(); await ui.write('Texto B');
  const source=ui.frame.src;
  await ui.get('#typed-response').click();
  assert.equal(ui.get('#typed-problem-context').hidden,false);
  assert.equal(ui.get('#typed-problem-title').textContent,'B · Questão B');
  assert.equal(ui.get('#typed-problem-statement').textContent,'Enunciado B');
  assert.equal(ui.get('#solution-input').value,'Texto B');
  assert.equal(ui.get('#notebook-surface').hidden,true);
  await ui.get('#notebook-response').click();
  assert.equal(ui.get('#typed-problem-context').hidden,true);
  assert.equal(ui.frame.src,source); assert.equal(ui.get('#solution-input').value,'Texto B');
});

test('teacher link leaves the embedded notebook through the institutional shell and preserves context', async () => {
  const ui=await page(); await ui.start('submission');
  ui.events.message({origin:ui.location.origin,source:ui.frame.contentWindow,data:{type:'confia-workspace-navigation',destination:'teacher-submissions'}});
  assert.equal(ui.location.hash,'#teacher/submissions');
  assert.equal(ui.document.body.dataset.resolutionActive,'false');
  assert.equal(ui.get('#student-area').hidden,true);
  ui.visit('resolve');
  assert.equal(ui.window.ConfIAWorkspace.mode,'submission');
  assert.equal(ui.document.body.dataset.resolutionActive,'true');
});

test('recovery rejects documents from another question instead of mixing strokes', async () => {
  const ui=await capturePage({embedded:true,problems:[{problem_id:'ITA2025Q1',statement:'A'},{problem_id:'B',statement:'B'}]});
  const initial=ui.messages.at(-1).context;
  await ui.recover(Model.createDraft('B'));
  assert.equal(ui.messages.at(-1).context.draft_id,initial.draft_id);
  assert.match(ui.get('#status-message').textContent,/pertence a outra questão/);
});

test('direct compatibility entry does not leave the notebook if migration saving fails', async () => {
  const ui=await capturePage({embedded:true});
  const opening=ui.click('direct-practice'); await flush();
  ui.saves.at(-1).reject(new Error('Quota excedida')); await opening;
  assert.equal(ui.context.location.href,undefined);
  assert.match(ui.get('#status-message').textContent,/Não foi possível salvar localmente/);
});

test('analysis starts closed, and opening or closing it never audits or loses text/context', async () => {
  const ui=await page(); await ui.start();
  const disclosure=ui.get('#practice-response');
  const context=JSON.stringify(ui.window.ConfIAWorkspace.analysisContext());
  const source=ui.frame.src;
  assert.equal(disclosure.open,false);
  assert.equal(ui.get('#prepare-analysis-label').textContent,'Preparar análise');
  assert.equal(ui.get('#prepare-analysis-note').hidden,false);
  disclosure.open=true; await disclosure.emit('toggle');
  await ui.write('Representação explícita');
  ui.notebook({ink_version:'1:1:1'});
  assert.equal(disclosure.open,true); // Autosave/ink notifications must not close the editor.
  disclosure.open=false; await disclosure.emit('toggle');
  ui.notebook({ink_version:'0:1:0'});
  assert.equal(disclosure.open,false);
  assert.equal(ui.get('#solution-input').value,'Representação explícita');
  assert.equal(JSON.stringify(ui.window.ConfIAWorkspace.analysisContext()),context);
  assert.equal(ui.frame.src,source);
  assert.equal(ui.calls.some(c=>c.options?.method==='POST'),false);
  await ui.get('#submission-mode').click(); ui.notebook();
  await ui.get('#practice-mode').click(); ui.notebook();
  assert.equal(disclosure.open,false);
  assert.equal(ui.get('#solution-input').value,'Representação explícita');
});

test('typed entry and feedback editing expose the textarea; notebook/new drafts start closed', async () => {
  const ui=await page(); await ui.start(); await ui.write('Solução');
  const disclosure=ui.get('#practice-response');
  await ui.get('#typed-response').click();
  assert.equal(disclosure.open,true);
  assert.equal(ui.get('#prepare-analysis-label').textContent,'Solução digitada');
  assert.equal(ui.get('#solution-input').focused,true);
  await ui.get('#notebook-response').click();
  assert.equal(disclosure.open,false);
  ui.visit('feedback'); await ui.get('#edit-solution').click();
  assert.equal(disclosure.open,true);
  assert.equal(ui.get('#solution-input').value,'Solução');
  await ui.get('#continue-solving').click();
  assert.equal(disclosure.open,false);
  disclosure.open=true;
  ui.notebook({draft_id:'draft:new'});
  assert.equal(disclosure.open,false);
  assert.equal(ui.get('#solution-input').value,'');
});

test('embedded sticky question starts compact and expands; standalone entry retains its statement', async () => {
  const embedded=await capturePage({embedded:true});
  assert.equal(embedded.get('#toggle-problem').getAttribute('aria-expanded'),'false');
  assert.equal(embedded.statementWrap.hidden,true);
  const context=JSON.stringify(embedded.messages.at(-1).context);
  embedded.click('toggle-problem');
  assert.equal(embedded.get('#toggle-problem').getAttribute('aria-expanded'),'true');
  assert.equal(embedded.statementWrap.hidden,false);
  assert.equal(embedded.statement.textContent,'Enunciado');
  assert.equal(JSON.stringify(embedded.messages.at(-1).context),context);
  const standalone=await capturePage();
  assert.equal(standalone.get('#toggle-problem').getAttribute('aria-expanded'),'true');
  assert.equal(standalone.statementWrap.hidden,false);
});

test('existing draft with handwriting recovers unchanged inside the taller notebook', async () => {
  let saved=Model.createDraft('ITA2025Q1');
  saved=Model.addStroke(saved,{stroke_id:'stroke:saved',page_id:saved.pages[0].page_id,pointer_type:'pen',
    color:'#17355c',width:4,points:[{x:100,y:350,t_ms:0,pressure_reported:.2},{x:800,y:1400,t_ms:20,pressure_reported:.8}]});
  const persisted=JSON.stringify(saved);
  const ui=await capturePage({embedded:true});
  await ui.recover(JSON.parse(persisted));
  const restored=ui.canvasRenders.at(-1).document;
  assert.equal(JSON.stringify(restored),persisted);
  assert.equal(ui.messages.at(-1).context.draft_id,saved.draft_id);
  assert.equal(ui.messages.at(-1).context.ink_version,'1:1:1');
  ui.click('toggle-problem'); ui.click('toggle-problem');
  assert.equal(JSON.stringify(ui.canvasRenders.at(-1).document),persisted);
});

test('parent question precedes the notebook in both modes; practice focus and typed view keep their behavior', async () => {
  const ui=await page();
  const question=ui.get('#notebook-problem-context');
  assert.equal(question.hidden,true);
  await ui.start();
  const source=ui.frame.src;
  assert.equal(question.hidden,false);
  assert.equal(ui.document.body.dataset.handwritingFocus,'true');
  assert.equal(ui.get('#practice-response').open,false);
  assert.equal(ui.get('#typed-problem-context').hidden,true);
  await ui.write('Solução preservada');
  await ui.get('#typed-response').click();
  assert.equal(question.hidden,true);
  assert.equal(ui.document.body.dataset.handwritingFocus,'false');
  assert.equal(ui.get('#typed-problem-context').hidden,false);
  assert.equal(ui.get('#notebook-surface').hidden,true);
  assert.equal(ui.get('#practice-response').open,true);
  assert.equal(ui.get('#solution-input').focused,true);
  assert.equal(ui.get('#solution-input').value,'Solução preservada');
  assert.equal(ui.get('#typed-problem-title').textContent,'A · Questão A');
  assert.equal(ui.get('#typed-problem-statement').textContent,'Enunciado A');
  await ui.get('#notebook-response').click();
  assert.equal(question.hidden,false);
  assert.equal(ui.get('#practice-response').open,false);
  await ui.get('#submission-mode').click(); ui.notebook();
  assert.equal(question.hidden,false);
  assert.equal(ui.document.body.dataset.handwritingFocus,'false');
  await ui.get('#practice-mode').click(); ui.notebook();
  ui.visit('feedback');
  assert.equal(question.hidden,true);
  assert.equal(ui.document.body.dataset.handwritingFocus,'false');
  ui.visit('resolve');
  assert.equal(question.hidden,false);
  await ui.get('#change-question').click();
  assert.equal(ui.get('#question-picker').hidden,false);
  assert.equal(question.hidden,true);
  assert.equal(ui.document.body.dataset.handwritingFocus,'false');
  assert.equal(ui.frame.src,source);
  assert.equal(ui.calls.some(c=>c.options?.method==='POST'),false);
});

test('workspace renders capture status and routes actions through the existing notebook frame', async () => {
  const ui=await page(); await ui.start('submission');
  ui.notebook({local_snapshot_id:'snap:A',content_height:1120,controls:{
    document_id:'snap:A', frozen:true, document_state:'Cópia local congelada', storage_state:'Salvo neste dispositivo',
    persistence:'Cópia local salva neste dispositivo', persistence_kind:'saved', status:'Versão recuperada', status_kind:'saved',
    saved_documents:[{id:'snap:A',label:'cópia congelada'}], can_prepare:false, can_send:true, send_label:'Enviar solução',
    can_recognize:false, snapshot_message:'Versão preparada localmente.', submission_message:'Envie para receber confirmação.',
    submission_receipt:'', recognition_message:'Envie a versão preparada.', recognition_segments:[],
  }});
  assert.equal(ui.get('#workspace-draft-persistence').textContent,'Cópia local salva neste dispositivo');
  assert.equal(ui.frame.style.height,'1120px');
  assert.equal(ui.get('#workspace-submission-actions').hidden,false);
  assert.equal(ui.get('#workspace-recognition-actions').hidden,false);
  assert.equal(ui.get('#workspace-continue-draft').hidden,false);
  assert.equal(ui.get('#workspace-send-solution').disabled,false);
  await ui.get('#workspace-send-solution').click();
  assert.deepEqual(JSON.parse(JSON.stringify(ui.commands.at(-1).message)),{
    type:'confia-workspace-command',action:'send-solution',problem_id:'A',mode:'submission',document_id:'snap:A',
  });
  const select=ui.get('#workspace-saved-document');
  select.value='snap:A'; await select.emit('change');
  await ui.get('#workspace-open-document').click();
  assert.equal(ui.commands.at(-1).message.action,'open-document');
  assert.equal(ui.commands.at(-1).message.saved_document_id,'snap:A');
  ui.notebook({local_snapshot_id:'snap:A',controls:{
    document_id:'snap:A', frozen:true, saved_documents:[], can_send:false, can_recognize:true,
    submission_receipt:'submission_id: sub_test', recognition_message:'Confira a leitura.',
    recognition_segments:[{page_index:0,text:'<script>texto</script>',latex:'x^2'}],
  }});
  assert.equal(ui.get('#workspace-submission-receipt').hidden,false);
  assert.equal(ui.get('#workspace-recognition-preview').children[0].children[1].textContent,'rendered:x^2');
  assert.equal(ui.get('#workspace-recognition-preview').children[0].children[2].children[1].textContent,'<script>texto</script>');
  assert.equal(ui.get('#workspace-recognize-writing').disabled,false);
  await ui.get('#workspace-recognize-writing').click();
  assert.equal(ui.commands.at(-1).message.action,'recognize-writing');
  await ui.get('#practice-mode').click(); ui.notebook();
  assert.equal(ui.get('#workspace-submission-actions').hidden,true);
  assert.equal(ui.get('#workspace-recognition-actions').hidden,true);
  assert.equal(ui.get('#workspace-send-solution').disabled,true);
});

test('parent sticky updates with the selected problem and its disclosure preserves notebook/text', async () => {
  const ui=await page(); await ui.select('B'); await ui.start();
  const source=ui.frame.src, draft=ui.window.ConfIAWorkspace.analysisContext().draft_id;
  assert.equal(ui.get('#notebook-problem-code').textContent,'B');
  assert.equal(ui.get('#notebook-problem-title'),undefined);
  assert.equal(ui.get('#notebook-problem-statement').textContent,'Enunciado B');
  await ui.write('Texto B');
  await ui.get('#toggle-notebook-problem').click();
  assert.equal(ui.get('#notebook-problem-body').hidden,true);
  assert.equal(ui.get('#toggle-notebook-problem').getAttribute('aria-expanded'),'false');
  assert.equal(ui.get('#toggle-notebook-problem').textContent,'Expandir enunciado');
  ui.notebook({ink_version:'1:1:1'});
  assert.equal(ui.get('#notebook-problem-body').hidden,true);
  await ui.get('#toggle-notebook-problem').click();
  assert.equal(ui.get('#notebook-problem-body').hidden,false);
  assert.equal(ui.get('#toggle-notebook-problem').getAttribute('aria-expanded'),'true');
  assert.equal(ui.get('#solution-input').value,'Texto B');
  assert.equal(ui.window.ConfIAWorkspace.analysisContext().draft_id,draft);
  await ui.get('#toggle-notebook-problem').click();
  await ui.get('#change-question').click(); await ui.select('A'); await ui.start();
  assert.equal(ui.get('#notebook-problem-code').textContent,'A');
  assert.equal(ui.get('#notebook-problem-statement').textContent,'Enunciado A');
  assert.equal(ui.get('#notebook-problem-body').hidden,false);
  assert.equal(ui.frame.src,source);
});

test('every catalog question shows only its ID above its complete statement in the parent notebook', async () => {
  const root=path.join(__dirname,'../../problems');
  const catalog=fs.readdirSync(root).flatMap(id => {
    const file=path.join(root,id,'problem.json');
    if (!fs.existsSync(file)) return [];
    const problem=JSON.parse(fs.readFileSync(file,'utf8'));
    return [{problem_id:id,title:problem.title,statement:problem.statement,examples:[]}];
  });
  assert.ok(catalog.some(problem => problem.problem_id==='ITA2025F2Q5'));
  for (const problem of catalog) {
    const ui=await page(undefined,{catalog});
    await ui.select(problem.problem_id); await ui.start('submission');
    assert.equal(ui.get('#notebook-problem-code').textContent,problem.problem_id);
    assert.equal(ui.get('#notebook-problem-title'),undefined);
    assert.equal(ui.get('#notebook-problem-statement').textContent,problem.statement);
    assert.equal(ui.get('#notebook-problem-context').hidden,false);
    assert.equal(ui.get('#workspace-submission-actions').hidden,false);
  }
});

test('parent question uses the same renderer, registry and fallback message as the approved typed statement', async () => {
  const registry=require('../../app/confia_lean_auditor/static/problem-presentations/registry.json');
  const entry=registry.find(p=>p.problem_id==='ITA2025F2Q1');
  const rendered=[];
  const ui=await page(undefined,{registry,catalog:[{problem_id:entry.problem_id,title:'Polinômio',statement:entry.source_statement,examples:[]}],
    mathRenderer:{render(element,message,options) { rendered.push({element,message,options,source:element.textContent}); }} });
  await ui.start();
  const parent=rendered.filter(r=>r.element===ui.get('#notebook-problem-statement')).at(-1);
  const typed=rendered.filter(r=>r.element===ui.get('#typed-problem-statement')).at(-1);
  assert.equal(parent.source,entry.source_statement);
  assert.equal(parent.options.problemId,entry.problem_id);
  assert.equal(parent.options.registry,registry);
  assert.equal(parent.options,typed.options);
  assert.equal(parent.message,ui.get('#notebook-math-message'));
  assert.equal(ui.calls.filter(c=>c.url.endsWith('registry.json')).length,1);
});

test('embedded practice hides its question presentation without hiding autosave or changing standalone/submission', async () => {
  const embedded=await capturePage({embedded:true,autoSave:true});
  assert.equal(embedded.context.document.body.dataset.workspaceMode,'practice');
  assert.equal(embedded.indicator.hidden,false);
  assert.equal(embedded.get('#problem-dock').hidden,false);
  await embedded.command({problem_id:'ITA2025Q1',mode:'submission'});
  assert.equal(embedded.context.document.body.dataset.workspaceMode,'submission');
  await embedded.command({problem_id:'ITA2025Q1',mode:'practice'});
  assert.equal(embedded.context.document.body.dataset.workspaceMode,'practice');
  const standalone=await capturePage();
  assert.equal(standalone.context.document.body.dataset.workspaceMode,undefined);
  assert.equal(standalone.get('#toggle-problem').getAttribute('aria-expanded'),'true');
  assert.equal(standalone.statementWrap.hidden,false);
});
