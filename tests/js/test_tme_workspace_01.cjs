const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {flush} = require('./capture-dom.cjs');
const {pilot, walk, text} = require('./tme-dom.cjs');
const fixture = require('../fixtures/rich_audit_response.json');
const run = score => ({audit_run_id:'aud_'+'e'.repeat(64),status:'COMPLETED',stale:false,acceptance_id:'acc_auto',result:{...structuredClone(fixture),score}});
const input = (ui,name,value) => {const control=walk(ui.root).find(e=>e.name===name);control.value=value;control.handlers.input();return control;};
const component = (ui,cls) => walk(ui.root).find(e=>e.className===cls);
const writes = ui => ui.calls.filter(c=>c.options.method==='POST');
const base = {case_id:'case_'+'a'.repeat(32),external_candidate_ref:'PROVA-1',problem_id:'ITA2025F2Q1',source_mode:'IMAGE_SCAN',submission_id:'sub_'+'b'.repeat(32)};

test('case_id deep link opens the same workspace, statement and only actual related questions',async()=>{
  const sibling={...base,case_id:'case_'+'c'.repeat(32),problem_id:'ITA2025F2Q3'};
  const ui=await pilot({deepLink:true,auditRun:run(7.5),homeCases:[base,sibling,{...base,case_id:'case_other',external_candidate_ref:'OTHER'},{...base,case_id:'case_phase',problem_id:'ITA2026F2Q2'}],catalog:[{problem_id:base.problem_id,statement:'Calcule $x^2$.'}]});
  assert.match(ui.window.history.url,/case_id=case_a/);
  const nav=component(ui,'question-navigator');assert.deepEqual(nav.children.map(e=>e.textContent),['Q1 ●','Q3 ○']);
  assert.match(text(ui.root),/2 questões disponíveis/);assert.doesNotMatch(text(nav),/Q2|Q4|Q5/);
  assert.ok(ui.statements.some(s=>s.source==='Calcule $x^2$.'));
  const count=ui.calls.length;await ui.click('Ver enunciado completo');assert.equal(ui.calls.length,count);
  assert.equal(walk(ui.root).find(e=>e.textContent==='Recolher enunciado').attributes['aria-expanded'],'true');
  await nav.children[1].click();await flush();assert.match(ui.window.history.url,/case_id=case_c/);
  assert.match(text(component(ui,'case-information')),/Questão 3/);
  await ui.click('Voltar para fila');assert.match(text(ui.root),/Fila de correções/);assert.equal(ui.window.history.url,'/tme?view=queue');
});

test('null score retains an enabled human decision and does not become zero',async()=>{
  const ui=await pilot({auditRun:run(null)});await ui.click('Abrir');
  assert.match(text(component(ui,'review-outcome')),/Pontuação não determinada/);
  assert.doesNotMatch(text(component(ui,'review-outcome')),/null|0 \/ 10|Inconclusiva \/ 10/);
  assert.equal(walk(ui.root).find(e=>e.textContent==='Finalizar correção').disabled,false);
  input(ui,'final','6');await ui.click('Finalizar correção');
  const payload=JSON.parse(writes(ui).find(c=>c.url.endsWith('/decision')).options.body);
  assert.equal(payload.final_points,6);assert.equal(payload.override_reason,null);
  assert.match(text(ui.root),/Correção registrada/);assert.ok(walk(ui.root).some(e=>e.textContent==='Corrigir próxima'));
});

test('override reveals a reason and blocks submission until provided, using the unchanged payload',async()=>{
  const audit=run(7.5);audit.result.rubric_assessment.items[2].verification_status='not_available';audit.result.pedagogical_report.verification_status='not_available';
  const ui=await pilot({auditRun:audit});await ui.click('Abrir');input(ui,'final','8');
  assert.equal(component(ui,'decision-observation').open,true);
  await ui.click('Finalizar correção');assert.equal(writes(ui).length,0);assert.match(text(ui.root),/Informe o motivo/);
  input(ui,'reason','Revisão humana da etapa final');await ui.click('Finalizar correção');
  const payload=JSON.parse(writes(ui).find(c=>c.url.endsWith('/decision')).options.body);
  assert.equal(payload.audit_run_id,'aud_'+'e'.repeat(64));assert.equal(payload.override_reason,'Revisão humana da etapa final');assert.equal(payload.final_points,8);
});

test('use suggestion scales only the displayed decision amount when maximum changes',async()=>{
  const ui=await pilot({auditRun:run(7.5)});await ui.click('Abrir');input(ui,'max','20');await ui.click('Usar sugestão');
  assert.equal(walk(ui.root).find(e=>e.name==='final').value,'15');
  assert.equal(walk(ui.root).find(e=>e.name==='reason').required,false);assert.equal(writes(ui).length,0);
});

test('human decision with no audit binds the exact revision without a compulsory review gate',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');input(ui,'final','6');await ui.click('Finalizar correção');
  assert.ok(writes(ui)[0].url.endsWith('/accept'));assert.ok(writes(ui)[1].url.endsWith('/decision'));
  assert.equal(JSON.parse(writes(ui)[0].options.body).reviewer_identity_verified,false);
  assert.equal(JSON.parse(writes(ui)[1].options.body).audit_run_id,null);
});

test('after finalization the next action uses the existing all-period queue and does not create a case',async()=>{
  const next={...base,case_id:'case_'+'c'.repeat(32),external_candidate_ref:'PROVA-2'};
  const ui=await pilot({auditRun:run(7.5),homeCases:[base,next],homeSummary:{counts:{},priority_cases:[next],exam_progress:[]}});
  await ui.click('Abrir');await ui.click('Usar sugestão');await ui.click('Finalizar correção');await ui.click('Corrigir próxima');
  assert.ok(ui.calls.some(c=>c.url==='/tme/home-summary?period=all'));assert.match(ui.window.history.url,/case_id=case_c/);
  assert.equal(writes(ui).filter(c=>c.url==='/tme/cases').length,0);
});

test('empty next queue returns to the queue with clear feedback',async()=>{
  const ui=await pilot({auditRun:run(7.5),homeSummary:{counts:{},priority_cases:[],exam_progress:[]}});await ui.click('Abrir');await ui.click('Usar sugestão');await ui.click('Finalizar correção');await ui.click('Corrigir próxima');
  assert.match(text(ui.root),/Não há outra correção pendente/);
});

test('failed decision retains draft and safely explains retry',async()=>{
  const ui=await pilot({auditRun:run(null),decisionError:true});await ui.click('Abrir');input(ui,'final','6');await ui.click('Finalizar correção');
  assert.equal(walk(ui.root).find(e=>e.name==='final').value,'6');assert.match(text(ui.root),/Não foi possível registrar a decisão/);assert.doesNotMatch(text(ui.root),/internal error/);
});

test('criteria and claims preserve refutation, uncertainty and technical errors with no manufactured evidence',async()=>{
  const audit=run(null);audit.result.rubric_assessment.items[0]={id:'refuted',description:'Resultado estabelecido',mathematical_status:'refuted',verification_status:'verified',points:0,max_points:2};
  audit.result.extracted_claims.claims[0]={id:'missing',text:'Passo sem evidência'};
  const original=JSON.stringify(audit),ui=await pilot({auditRun:audit});await ui.click('Abrir');
  const criteria=walk(ui.root).filter(e=>e.className==='audit-criterion');assert.equal(criteria[0].dataset.mathematicalStatus,'refuted');assert.match(text(criteria[0]),/0 \/ 2/);
  assert.match(text(criteria[0]),/Evidência textual não localizada/);
  const claims=walk(ui.root).filter(e=>e.className==='audit-claim');await claims[0].click();assert.match(text(component(ui,'claim-detail')),/Evidência textual não localizada/);
  assert.ok(claims.some(e=>e.dataset.formalStatus==='technical_error'));assert.ok(claims.some(e=>e.dataset.formalStatus==='unverified'));
  assert.equal(JSON.stringify(audit),original);
});

test('formal verified label requires execution and an artifact, while empty claims have an explicit state',async()=>{
  const audit=run(null);audit.result.student_claim_checks[0].compiled=false;
  const ui=await pilot({auditRun:audit});await ui.click('Abrir');
  assert.match(text(component(ui,'coverage')),/0 claims formalmente verificados/);
  assert.equal(walk(ui.root).find(e=>e.dataset.claimId==='claim_1').dataset.formalStatus,'unverified');
  const empty=run(null);empty.result.extracted_claims={claims:[]};empty.result.student_claims=[];empty.result.student_claim_checks=[];
  const noClaims=await pilot({auditRun:empty});await noClaims.click('Abrir');assert.match(text(noClaims.root),/Nenhum passo matemático estruturado foi identificado nesta análise/);
});

test('technical provenance is closed and original images are reused across review rerenders',async()=>{
  const ui=await pilot({auditRun:run(null)});await ui.click('Abrir');
  const image=walk(ui.root).find(e=>e.tag==='img');const technical=walk(ui.root).filter(e=>e.tag==='details'&&/technical/.test(e.className));assert.ok(technical.length>0);assert.ok(technical.every(e=>!e.open));
  await ui.click('Editar');const area=walk(component(ui,'transcription-editor')).find(e=>e.tag==='textarea');area.value='x = 3';area.handlers.input();await ui.click('Salvar nova revisão');
  assert.equal(walk(ui.root).find(e=>e.tag==='img'),image);
});

test('digital writing uses preserved page rendering without recreating strokes',async()=>{
  const ui=await pilot({automatic:true,mode:'DIGITAL_INK'});await ui.click('Abrir');
  assert.ok(walk(ui.root).some(e=>e.tag==='img'&&e.src.endsWith('/pages/0')));assert.equal(writes(ui).length,0);
});

test('original pan moves the viewport and rotation reserves reachable nonnegative bounds',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');await ui.click('Zoom +');await ui.click('Rotacionar');
  const original=component(ui,'original-document');original.scrollLeft=40;original.scrollTop=30;
  original.handlers.pointerdown({button:0,pointerId:1,clientX:100,clientY:100,preventDefault(){}});original.handlers.pointermove({clientX:70,clientY:80});
  assert.equal(original.scrollLeft,70);assert.equal(original.scrollTop,50);original.handlers.pointerup();
  assert.match(walk(ui.root).find(e=>e.tag==='img').style.transform,/translate\([\d.]+px, 0px\) scale\(1.25\) rotate\(90deg\)/);
});

test('shared theme is extracted verbatim and responsive layout uses Home tokens and semantic tabs',async()=>{
  const css=fs.readFileSync('app/confia_lean_auditor/static/tme/correction-workspace.css','utf8'),theme=fs.readFileSync('app/confia_lean_auditor/static/tme/tme-theme.css','utf8');
  assert.doesNotMatch(css, /#[0-9a-f]{3,8}\b/i);assert.match(css,/min-width: 1100px/);assert.match(css,/safe-area-inset-bottom/);assert.match(css,/var\(--confia-control-height\)/);assert.match(theme,/--status-error: var\(--confia-rose-ink\)/);
  const ui=await pilot({automatic:true});await ui.click('Abrir');
  assert.equal(walk(ui.root).filter(e=>e.attributes.role==='tablist').length,1);assert.equal(walk(ui.root).filter(e=>e.attributes.role==='tab'&&e.attributes['aria-selected']==='true').length,1);
  assert.equal(component(ui,'question-navigator').attributes['aria-label'],'Questões disponíveis desta prova');
});

test('a technical failure does not impose an override reason absent from the existing server rule',async()=>{
  const ui=await pilot({auditRun:run(7.5)});await ui.click('Abrir');input(ui,'final','8');
  assert.equal(Boolean(walk(ui.root).find(e=>e.name==='reason').required),false);await ui.click('Finalizar correção');
  assert.ok(writes(ui).some(c=>c.url.endsWith('/decision')));
});

test('failed analysis stays technical and exposes retry while a decision remains possible',async()=>{
  const audit=run(null);audit.status='FAILED';audit.result=null;
  const ui=await pilot({auditRun:audit});await ui.click('Abrir');
  assert.match(text(ui.root),/Falha técnica/);assert.match(text(ui.root),/Não foi possível concluir a análise/);
  assert.ok(walk(ui.root).some(e=>e.textContent==='Analisar com ConfIA'&&!e.disabled));
  assert.equal(walk(ui.root).filter(e=>e.dataset.mathematicalStatus==='refuted').length,0);
  assert.equal(walk(ui.root).find(e=>e.textContent==='Finalizar correção').disabled,false);
});

test('two finalize activations cannot create duplicate decisions',async()=>{
  const ui=await pilot({auditRun:run(null)});await ui.click('Abrir');input(ui,'final','6');
  const submit=walk(ui.root).find(e=>e.textContent==='Finalizar correção');
  await Promise.all([submit.click(),submit.click()]);await flush();
  assert.equal(writes(ui).filter(c=>c.url.endsWith('/decision')).length,1);
});

test('statement receives the shared registry once and expands the same rendered subtree',async()=>{
  const problem=require('../../problems/ITA2025F2Q1/problem.json');
  const ui=await pilot({automatic:true,catalog:[problem]});await ui.click('Abrir');
  const statement=ui.statements.at(-1), rich=component(ui,'problem-rich-text');
  assert.equal(statement.source,problem.statement);
  assert.equal(statement.options.problemId,problem.id);
  assert.ok(statement.options.registry.some(p=>p.problem_id==='ITA2025F2Q3'));
  const count=ui.statements.length;
  await ui.click('Ver enunciado completo');
  assert.equal(walk(ui.root).find(e=>e.textContent==='Recolher enunciado').attributes['aria-expanded'],'true');
  assert.equal(component(ui,'problem-rich-text'),rich);
  await ui.click('Recolher enunciado');
  assert.equal(walk(ui.root).find(e=>e.textContent==='Ver enunciado completo').attributes['aria-expanded'],'false');
  assert.equal(ui.statements.length,count);
  await ui.click('Transcrição');
  assert.equal(ui.calls.filter(c=>c.url==='/static/problem-presentations/registry.json').length,1);
});

test('missing presentation asset retains the statement without blocking the workspace',async()=>{
  const problem=require('../../problems/ITA2025F2Q1/problem.json');
  const ui=await pilot({automatic:true,catalog:[problem],presentationError:true});await ui.click('Abrir');
  assert.equal(component(ui,'problem-rich-text').textContent,problem.statement);
  assert.equal(ui.statements.at(-1).options.registry.length,0);
  assert.ok(walk(ui.root).some(e=>e.id==='solution-pane'));
  assert.doesNotMatch(text(ui.root),/unavailable/);
});

test('compact layout moves its boundary before a fraction and expanded layout retains full content',async()=>{
  const ui=await pilot({automatic:true});await ui.click('Abrir');
  const section=component(ui,'problem-statement'),content=component(ui,'problem-content'),rich=component(ui,'problem-rich-text');
  content.isConnected=true;ui.window.getComputedStyle=()=>({fontSize:'16px'});
  rich.getBoundingClientRect=()=>({top:200,height:160});
  rich.querySelectorAll=()=>[{getBoundingClientRect:()=>({top:270,bottom:310})}];
  section.updateStatementLayout();
  assert.equal(content.style.maxHeight,'70px');assert.equal(content.dataset.clipped,'true');
  await ui.click('Ver enunciado completo');
  assert.equal(content.style.maxHeight,'none');assert.equal(content.dataset.clipped,'false');
  assert.equal(component(ui,'problem-rich-text'),rich);
});
