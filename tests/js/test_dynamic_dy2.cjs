const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {element,descendants,deferred,flush} = require('./ui-dom.cjs');
const source=fs.readFileSync(path.join(__dirname,'../../app/confia_lean_auditor/static/dynamic.js'),'utf8');
const pid='dyn_'+'a'.repeat(32), prepId='dprep_'+'b'.repeat(32), rid='drub_'+'c'.repeat(32);
function documentValue(status=null,rubric=false) {
 const warning={code:'MISSING_DOMAIN',message:'Domínio ausente: confirme a interpretação.',requires_review:true};
 const prep=status ? {preparation_id:prepId,preparation_version:1,statement_version:1,status,effective_status:status,is_current:true,
  proposal:{mathematical_domain:'Álgebra',normalized_problem:'Equação quadrática',target:'Raízes',assumptions:[],
   candidate_reference_solutions:[{solution_id:'s1',strategy_label:'Fatoração',claims:[{text:'(x-2)(x-3)=0'}],final_result:{text:'{2,3}'}}],
   alternative_strategies:[{strategy_id:'formula',description:'Fórmula quadrática ou método equivalente'}],uncertainties:[]},
  analysis:{candidate_checks:[{solution_id:'s1',status:'PARTIALLY_VERIFIED'}],warnings:[warning],trust_state:'HUMAN_REVIEW_REQUIRED',
   verifier_plan:[{claim_id:'c1',capability:'DETERMINISTIC',status:'VERIFIED_WITHIN_SCOPE',formal_status:'FORMAL_NOT_ATTEMPTED',detail:'Conjunto completo',scope:'Somente polinômio'}]},
  provenance:{provider:'controlled-test',returned_model:'fixture',prompt_version:'test.v1'}} : null;
 return {revision:rubric?5:status?4:1,problem:{problem_id:pid},statements:[{version_number:1,title:'Equação DY2',statement:'Resolva x² - 5x + 6 = 0',max_score:'10'}],
  current_configuration:null,automatic_suggestion_available:true,current_preparation:prep,preparation_history:prep?[prep]:[],
  rubrics:rubric?[{rubric_id:rid,version_number:1,statement_version:1,status:'DRAFT_AI',generation:{},review_warnings:[warning],
   criteria:[{criterion_id:'c1',title:'Método equivalente',description:'Aceita fatoração ou fórmula.',max_points:'10',order:1}]}]:[]};
}
async function page(initial,mutation,simplified=false) {
 let current=initial;const panel=element('section'),calls=[],window={};
 const fetch=async(url,options)=>{const body=options?.body?JSON.parse(options.body):null;calls.push({url,body});
  if(body){const result=await mutation(url,body);if(result.error)return {ok:false,json:async()=>({detail:result.error})};current=result;}
  return {ok:true,json:async()=>url==='/dynamic/problems'?[current]:current};};
 vm.runInNewContext(source,{window,document:{querySelector:()=>panel,createElement:element},fetch,Set,Number,String,Error,Math});
 await window.ConfIADynamic.create({host:panel,simplified}).load(simplified?pid:null);
 const nodes=()=>descendants(panel),button=text=>nodes().find(n=>n.tag==='button'&&n.textContent===text);
 if(!simplified)await button(`Equação DY2 · Enunciado V${initial.statements.at(-1).version_number}`).click();return {panel,nodes,button,calls};
}

test('prepare shows loading, real request and checked evidence with no automatic rubric or approval',async()=>{
 const pending=deferred();const ui=await page(documentValue(),async(url,body)=>{assert(url.endsWith('/preparations'));assert.equal(body.expected_revision,1);await pending.promise;return documentValue('REVIEW_REQUIRED');});
 const action=ui.button('Preparar com ConfIA').click();await flush();assert.match(ui.panel.textContent,/Preparando com ConfIA/);
 assert.equal(ui.button('Preparar com ConfIA').disabled,true);pending.resolve();await action;
 assert.match(ui.panel.textContent,/Revisão necessária/);assert.match(ui.panel.textContent,/Solução de referência candidata/);assert.match(ui.panel.textContent,/Fórmula quadrática/);
 assert.match(ui.panel.textContent,/Verificação formal não executada/);assert.equal(ui.button('Gerar rubrica sugerida').disabled,false);
 assert(!ui.calls.some(c=>c.url.endsWith('/approve')));
});

test('AI draft warnings are visible and acknowledgement gates explicit approval; edits require save',async()=>{
 const ui=await page(documentValue('REVIEW_REQUIRED'),async(url,body)=>{
  if(url.endsWith('/rubric-suggestion')){assert.equal(body.preparation_id,prepId);return documentValue('REVIEW_REQUIRED',true);}
  assert(url.endsWith('/approve'));assert.equal(body.acknowledge_warnings,true);const d=documentValue('REVIEW_REQUIRED',true);d.rubrics[0].status='APPROVED';return d;
 });
 await ui.button('Gerar rubrica sugerida').click();assert.match(ui.panel.textContent,/Sugestão da IA/);assert.match(ui.panel.textContent,/Domínio ausente/);
 assert.equal(ui.button('Aprovar rubrica').disabled,true);
 const ack=ui.nodes().find(n=>n.type==='checkbox');ack.checked=true;await ack.emit('change');assert.equal(ui.button('Aprovar rubrica').disabled,false);
 await ui.button('Aprovar rubrica').click();assert.match(ui.panel.textContent,/Aprovada/);assert.match(ui.panel.textContent,/HUMAN_REVIEW_REQUIRED/);
});

test('regeneration has reason and new version; own rubric sends teacher replacement flag',async()=>{
 let phase=0;const ui=await page(documentValue('REVIEW_REQUIRED',true),async(url,body)=>{
  const d=documentValue('REVIEW_REQUIRED',true);d.revision=6;
  if(phase++===0){assert(url.endsWith('/rubric-suggestion'));assert.equal(body.reason,'Melhorar parcialidade');d.rubrics[0].version_number=2;return d;}
  assert.equal(body.replace_with_teacher,true);assert.equal(body.criteria.length,0);d.rubrics[0].criteria=[];d.rubrics[0].generation=null;d.rubrics[0].status='TEACHER_EDITED';return d;
 });
 ui.nodes().find(n=>n.name==='Motivo da nova sugestão (opcional)').value='Melhorar parcialidade';
 await ui.button('Rejeitar e gerar nova sugestão').click();assert.match(ui.panel.textContent,/Rubrica V2/);
 await ui.button('Fornecer minha própria rubrica').click();assert.equal(ui.button('Aprovar rubrica').disabled,true);
 await ui.button('Salvar como nova versão da rubrica').click();assert.match(ui.panel.textContent,/Rubrica fornecida pelo professor/);
});

test('failed preparation offers retry and never fabricates a candidate',async()=>{
 const d=documentValue('FAILED');d.current_preparation.proposal=null;d.current_preparation.failure_code='PROVIDER_REQUEST_FAILED';
 const ui=await page(d);assert.match(ui.panel.textContent,/PROVIDER_REQUEST_FAILED/);assert(!ui.panel.textContent.includes('Resultado candidato'));
 assert.equal(ui.button('Gerar rubrica sugerida').disabled,true);assert.equal(ui.button('Gerar nova preparação').disabled,false);
});

test('historical preparation after statement change is visible but cannot enable suggestion',async()=>{
 const d=documentValue('REVIEW_REQUIRED');d.current_preparation=null;d.preparation_history[0].effective_status='SUPERSEDED';
 d.statements.push({...d.statements[0],version_number:2,statement:'Novo problema'});
 const ui=await page(d);assert.match(ui.panel.textContent,/Versão anterior/);assert.equal(ui.button('Gerar rubrica sugerida').disabled,true);
});

test('provider failure surfaces error with no phantom draft',async()=>{
 const ui=await page(documentValue('READY_FOR_REVIEW'),async()=>({error:{message:'Saída inválida; recarregue.'}}));
 await ui.button('Gerar rubrica sugerida').click();assert.match(ui.panel.textContent,/Saída inválida/);assert(!ui.panel.textContent.includes('DRAFT_AI'));
});


test('simplified rubric prepares behind the scenes, then suggests without approving or publishing',async()=>{
 const ui=await page(documentValue(),async(url,body)=>{
  if(url.endsWith('/preparations'))return documentValue('REVIEW_REQUIRED');
  assert(url.endsWith('/rubric-suggestion'));assert.equal(body.preparation_id,prepId);
  return documentValue('REVIEW_REQUIRED',true);
 },true);
 assert(ui.button('Gerar rubrica sugerida'));await ui.button('Gerar rubrica sugerida').click();
 const writes=ui.calls.filter(c=>c.body);assert.equal(writes.length,2);
 assert(writes[0].url.endsWith('/preparations'));assert(writes[1].url.endsWith('/rubric-suggestion'));
 assert.match(ui.panel.textContent,/Sugestão da IA/);assert.equal(ui.button('Aprovar rubrica').disabled,true);
 const title=ui.nodes().find(n=>n.name==='Critério c1: título');title.value='Critério revisado';await title.emit('input');
 assert.equal(ui.button('Aprovar rubrica').disabled,true);assert(ui.button('Salvar critérios'));
 await ui.button('Fornecer minha própria rubrica').click();assert.equal(ui.button('Salvar critérios').disabled,true);
 assert(!ui.calls.some(c=>/approve|activate|publish/.test(c.url)));
});

test('failed suggestion after automatic preparation retains current revision for a safe retry',async()=>{
 let prepared=0,suggestions=0;
 const ui=await page(documentValue(),async(url,body)=>{
  if(url.endsWith('/preparations')){prepared++;return documentValue('REVIEW_REQUIRED');}
  assert.equal(body.expected_revision,4);suggestions++;
  return suggestions===1?{error:'Provider temporariamente indisponível'}:documentValue('REVIEW_REQUIRED',true);
 },true);
 await ui.button('Gerar rubrica sugerida').click();assert.match(ui.panel.textContent,/Provider temporariamente indisponível/);
 await ui.button('Gerar rubrica sugerida').click();assert.equal(prepared,1);assert.equal(suggestions,2);
 assert.match(ui.panel.textContent,/Sugestão da IA/);assert(!ui.calls.some(c=>c.url.endsWith('/approve')));
});
