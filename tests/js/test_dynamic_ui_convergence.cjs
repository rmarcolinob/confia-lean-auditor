const test=require('node:test'), assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pilot,walk,text}=require('./tme-dom.cjs');
const {deferred,flush}=require('./ui-dom.cjs');
const pid='dyn_'+'d'.repeat(32),prepId='dprep_'+'e'.repeat(32),rid='drub_'+'f'.repeat(32);
const reply=data=>({ok:true,json:async()=>data});
function fixture(){return {revision:1,problem:{problem_id:pid,correction_mode:'DYNAMIC'},statements:[{title:'Questão inédita',statement:'Resolva em R: x²-5x+6=0.',max_score:'10',version_number:1}],rubrics:[],preparation_history:[],current_preparation:null,current_configuration:null,automatic_suggestion_available:true};}
function prepared(doc){const prep={preparation_id:prepId,preparation_version:1,statement_version:1,status:'REVIEW_REQUIRED',effective_status:'REVIEW_REQUIRED',
 proposal:{mathematical_domain:'Álgebra',normalized_problem:'x²-5x+6=0',target:'Raízes reais',assumptions:[],candidate_reference_solutions:[{solution_id:'s1',strategy_label:'Fatoração',claims:[{text:'(x-2)(x-3)=0'}],final_result:{text:'2 e 3'}}],alternative_strategies:[{strategy_id:'s2',description:'Usar fórmula quadrática'}],uncertainties:['Confira a interpretação antes de aprovar.']},
 analysis:{candidate_checks:[{solution_id:'s1',status:'PARTIALLY_VERIFIED'}],warnings:[{message:'A verificação não cobre toda a justificativa.',requires_review:true}],trust_state:'HUMAN_REVIEW_REQUIRED',verifier_plan:[{claim_id:'c1',capability:'DETERMINISTIC',status:'VERIFIED_WITHIN_SCOPE',formal_status:'FORMAL_NOT_ATTEMPTED',detail:'Raízes verificadas',scope:'Polinômio declarado'}]}};
 return {...doc,revision:4,current_preparation:prep,preparation_history:[prep]};}
const field=(ui,name)=>walk(ui.root).find(n=>n.name===name);
const submit=ui=>walk(ui.root).find(n=>n.tag==='form').handlers.submit({preventDefault(){}});

test('Nova presents both routes in the existing shell; teacher preparation remains in the shared shell while student integration is separate',async()=>{
 const ui=await pilot({startHome:true});await walk(ui.root).find(n=>n.tag==='button' && walk(n).some(c=>c.textContent==='Nova correção')).click();await flush();
 assert.equal(ui.root.dataset.view,'new');assert.equal(ui.window.history.url,'/tme?view=new');
 assert.match(text(ui.root),/Avaliação preparada/);assert.match(text(ui.root),/Nova atividade ou prova/);
 assert.doesNotMatch(text(ui.root),/Gestão|Perfil de demonstração/);
 assert.match(text(ui.root),/SPECIALIZED/);assert.match(text(ui.root),/DYNAMIC/);
 await ui.click('Avaliação preparada');assert.match(text(ui.root),/Escrever no tablet/);
 assert.equal(ui.window.history.url,'/tme?view=new&mode=specialized');
 const staticDir=path.join(__dirname,'../../app/confia_lean_auditor/static');
 const legacy=fs.readFileSync(path.join(staticDir,'index.html'),'utf8'),shell=fs.readFileSync(path.join(staticDir,'shell.js'),'utf8');
 assert.match(legacy,/Gestão/);assert.doesNotMatch(legacy+shell,/teacher-dynamic|teacher\/dynamic|ConfIADynamic(?:Assessment)?\b|\/static\/dynamic(?:-assessment)?\.js/);
 assert.match(legacy,/\/static\/dynamic-student\.js/);
 const modern=fs.readFileSync(path.join(staticDir,'tme/index.html'),'utf8');
 assert.match(modern,/data-tme-shell="modern"/);assert.match(modern,/\/static\/dynamic.js/);assert.doesNotMatch(modern,/Gestão|Perfil de demonstração/);
 const css=fs.readFileSync(path.join(staticDir,'tme/secondary-views.css'),'utf8');
 assert.match(css,/\.top,\.sidebar\).*display:\s*none\s*!important/);
});

test('unified creation → preparation → suggestion → edit → explicit approval retains provenance and history',async()=>{
 let saved=null;const writes=[];
 const ui=await pilot({startHome:true,mockFetch:async(url,options)=>{
  if(!url.startsWith('/dynamic/problems'))return;
  if(!options.body)return reply(url==='/dynamic/problems'?(saved?[saved]:[]):saved);
  const body=JSON.parse(options.body);writes.push({url,body,method:options.method});
  if(url==='/dynamic/problems'){assert.equal(body.correction_mode,'DYNAMIC');saved=fixture();}
  else {
   assert.equal(body.expected_revision,saved.revision);
   if(url.endsWith('/preparations'))saved=prepared(saved);
   else if(url.endsWith('/rubric-suggestion')){
    assert.equal(body.preparation_id,prepId);saved={...saved,revision:5,rubrics:[{rubric_id:rid,version_number:1,statement_version:1,status:'DRAFT_AI',generation:{},review_warnings:saved.current_preparation.analysis.warnings,criteria:[{criterion_id:'c1',title:'Método',description:'Justificar as raízes.',max_points:'10',order:1}]}]};
   } else if(options.method==='PATCH')saved={...saved,revision:6,rubrics:[...saved.rubrics,{...saved.rubrics[0],version_number:2,rubric_id:rid+'2',status:'TEACHER_EDITED',criteria:body.criteria}]};
   else if(url.endsWith('/approve')){assert.equal(body.acknowledge_warnings,true);saved={...saved,revision:7,current_configuration:{package:{package_version:2,statement_version:1,rubric_version:2}},rubrics:[saved.rubrics[0],{...saved.rubrics[1],status:'APPROVED'}]};}
   else assert.fail('Unexpected mutation '+url);
  }
  return reply(saved);
 }});
 await walk(ui.root).find(n=>n.tag==='button' && walk(n).some(c=>c.textContent==='Nova correção')).click();await flush();await ui.click('Nova atividade ou prova');
 assert.match(text(ui.root),/Forneça sua rubrica/);assert.equal(ui.window.history.url,'/tme?view=new&mode=dynamic');
 field(ui,'Título').value='Questão inédita';field(ui,'Enunciado').value='Resolva em R: x²-5x+6=0.';await submit(ui);
 assert.equal(ui.window.history.url,`/tme?view=new&mode=dynamic&problem_id=${pid}`);
 await ui.click('Preparar com ConfIA');assert.equal(writes.length,2);
 assert.match(text(ui.root),/Verificação parcial/);assert.match(text(ui.root),/Usar fórmula quadrática/);assert.match(text(ui.root),/Verificação formal não executada/);
 await ui.click('Gerar rubrica sugerida');assert.match(text(ui.root),/Sugestão da IA/);
 field(ui,'Critério c1: descrição').value='Aceitar qualquer método matemático equivalente.';field(ui,'Critério c1: descrição').handlers.input();
 assert.equal(walk(ui.root).find(n=>n.textContent==='Aprovar rubrica').disabled,true);
 await ui.click('Salvar como nova versão da rubrica');assert.match(text(ui.root),/Revisada pelo professor/);
 assert.equal(walk(ui.root).find(n=>n.textContent==='Aprovar rubrica').disabled,true);
 const ack=field(ui,'Li os avisos e assumo a revisão docente');ack.checked=true;ack.handlers.change();await ui.click('Aprovar rubrica');
 assert.equal(writes.length,5);assert.match(text(ui.root),/Rubrica V2 ·\s+Aprovada/);assert.match(text(ui.root),/Rubrica V1 · Sugestão da IA/);
 assert.match(text(ui.root),/Original \/ Transcrição \/ Comparar/);assert.equal(saved.current_preparation.status,'REVIEW_REQUIRED');
 assert(!ui.calls.some(c=>c.url.endsWith('/corrections')));assert.doesNotMatch(text(ui.root),/Gestão|teacher-dynamic/);
 for(const [index,view,url] of [[3,'home','/tme'],[0,'cases','/tme?view=queue'],[2,'results','/tme?view=results']]){await ui.nav[index].click();await flush();assert.equal(ui.root.dataset.view,view);assert.equal(ui.window.history.url,url);}
 await ui.window.history.back();await ui.window.history.back();await ui.window.history.back();
 assert.equal(ui.root.dataset.view,'new');assert.match(text(ui.root),/Rubrica V2 ·\s+Aprovada/);
});

test('deep link restores selected preparation; Nova questão clears it without discarding stored versions',async()=>{
 const d=prepared(fixture()),ui=await pilot({initialSearch:`?view=new&mode=dynamic&problem_id=${pid}`,mockFetch:async(url)=>url.startsWith('/dynamic/problems')?reply(url==='/dynamic/problems'?[d]:d):undefined});
 assert.match(text(ui.root),/Questão inédita/);assert.match(text(ui.root),/Revisão necessária/);
 await ui.click('Nova questão');assert.equal(ui.window.history.url,'/tme?view=new&mode=dynamic');
 assert.doesNotMatch(text(ui.root),/Histórico de versões/);assert(!ui.calls.some(c=>c.options.method));
 await ui.click('Questão inédita · Enunciado V1');assert.match(text(ui.root),/Histórico de versões/);
});

test('late document read cannot restore a previous preparation over Home or change its URL',async()=>{
 const wait=deferred();const ui=await pilot({initialSearch:`?view=new&mode=dynamic&problem_id=${pid}`,mockFetch:async(url)=>url==='/dynamic/problems'?reply([fixture()]):url===`/dynamic/problems/${pid}`?wait.promise:undefined});
 await ui.nav[3].click();await flush();wait.resolve(reply(prepared(fixture())));await flush();
 assert.equal(ui.root.dataset.view,'home');assert.equal(ui.window.history.url,'/tme');assert.match(text(ui.root),/Visão geral/);assert.doesNotMatch(text(ui.root),/Rubrica/);
});

test('in-flight preparation blocks navigation and preserves route until response; then navigation resumes',async()=>{
 const wait=deferred(),d=fixture();const ui=await pilot({initialSearch:`?view=new&mode=dynamic&problem_id=${pid}`,mockFetch:async(url,options)=>url.startsWith('/dynamic/problems')?(options.body?wait.promise:reply(url==='/dynamic/problems'?[d]:d)):undefined});
 const pending=ui.click('Preparar com ConfIA');await flush();await ui.nav[3].click();assert.equal(ui.root.dataset.view,'new');
 wait.resolve(reply(prepared(d)));await pending;await ui.nav[3].click();await flush();assert.equal(ui.root.dataset.view,'home');
});

test('unauthorized or missing preparation stays in the same shell with a recoverable error',async()=>{
 const ui=await pilot({initialSearch:`?view=new&mode=dynamic&problem_id=${pid}`,mockFetch:async(url)=>url==='/dynamic/problems'?reply([]):url===`/dynamic/problems/${pid}`?{ok:false,json:async()=>({detail:'Questão não encontrada.'})}:undefined});
 assert.match(text(ui.root),/Questão não encontrada/);assert.equal(ui.root.dataset.view,'new');await ui.click('Voltar às opções');assert.match(text(ui.root),/Avaliação preparada/);
});

test('Nova questão invalidates an initial pending selection and cannot be overwritten by its response',async()=>{
 const wait=deferred(),ui=await pilot({initialSearch:`?view=new&mode=dynamic&problem_id=${pid}`,mockFetch:async(url)=>url==='/dynamic/problems'?reply([]):url===`/dynamic/problems/${pid}`?wait.promise:undefined});
 await ui.click('Nova questão');wait.resolve(reply(prepared(fixture())));await flush();
 assert.equal(ui.window.history.url,'/tme?view=new&mode=dynamic');assert.doesNotMatch(text(ui.root),/Histórico de versões/);
});


test('a restored workspace invalidates a pending Dynamic read before it can rewrite the URL',async()=>{
 const wait=deferred();const ui=await pilot({startHome:true,mockFetch:async(url)=>url==='/dynamic/problems'?reply([]):url===`/dynamic/problems/${pid}`?wait.promise:undefined});
 const caseURL='/tme?case_id=case_'+'a'.repeat(32);
 ui.window.history.pushState({tme:true},'',caseURL);
 ui.window.history.pushState({tme:true},'',`/tme?view=new&mode=dynamic&problem_id=${pid}`);
 await ui.window.history.back();const pending=ui.window.history.forward();await flush();
 await ui.window.history.back();wait.resolve(reply(prepared(fixture())));await pending;await flush();
 assert.equal(ui.root.dataset.view,'workspace');assert.equal(ui.window.history.url,caseURL);
});
