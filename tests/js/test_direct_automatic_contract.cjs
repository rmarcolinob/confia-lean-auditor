// Future capture integration: server transcription transport, never a mock OCR implementation.
const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const {element,descendants}=require('./ui-dom.cjs');
const node=tag=>{const el=element(tag);el.append=(...children)=>children.forEach(child=>el.appendChild(child));return el;};
const source=fs.readFileSync(path.join(__dirname,'../../app/confia_lean_auditor/static/teacher-direct.js'),'utf8');
async function screen({origin='automatic',problem='TME2026P1',issues=[]}={}){
 const host=node('div'),calls=[],window={crypto:require('node:crypto').webcrypto,ConfIAReport:{render(){}}};let version=1,failAudit=false;
 const c={case_id:'case_server',problem_id:problem,source_mode:'IMAGE_SCAN'};
 const history=()=>({transcription:{transcription_id:'tr_server',source:origin,recognizer_run_id:'run_server'},revisions:[{revision_number:version,input_issues:issues,segments:[{kind:'text',text:'[a]\n731-137=594'}]}],acceptances:[]});
 const fetch=async(url,options={})=>{calls.push({url,options});let data;
  if(url==='/tme/cases/case_server')data=c;
  else if(url.endsWith('/transcriptions'))data=[{transcription:{transcription_id:'tr_server'}}];
  else if(url.endsWith('/transcriptions/tr_server'))data=history();
  else if(url.endsWith('/submission'))data={submission:{page_images:[{page_index:0}]}};
  else if(url.endsWith('/accept'))data={acceptance:{acceptance_id:'a_server'}};
  else if(url.endsWith('/audits')){if(failAudit)throw Error('Falha de rede');data={status:'FAILED',audit_run_id:'aud_server'};}
  else throw Error('Unexpected '+url);
  return {ok:true,json:async()=>data};
 };
 vm.runInNewContext(source,{window,document:{createElement:node},fetch,URL:{revokeObjectURL(){}}});
 const component=window.ConfIATeacherDirect.create({host,problemId:'TME2026P1'});
 return {host,calls,component,nodes:()=>descendants(host),revise:()=>version++,fail:value=>failAudit=value};
}
test('server automatic source keeps case, transcription and revision; explicit confirmation still required',async()=>{
 const ui=await screen();await ui.component.loadAutomaticCase('case_server');const nodes=ui.nodes();const solution=nodes.find(n=>n.getAttribute('aria-label')==='Solução já digital');assert(solution.readOnly);assert.equal(solution.value,'[a]\n731-137=594');
 const submit=nodes.find(n=>n.textContent==='Corrigir solução');assert(submit.disabled);assert.equal(nodes.find(n=>n.tag==='img').src,'/tme/cases/case_server/originals/0');
 const check=nodes.find(n=>n.getAttribute('aria-label')==='Confirmo o texto da solução');check.checked=true;await check.emit('change');await nodes.find(n=>n.tag==='form').emit('submit',{preventDefault(){}});
 assert(!ui.calls.some(c=>c.url==='/tme/direct-solutions'));const request=JSON.parse(ui.calls.find(c=>c.url.endsWith('/audits')).options.body);assert.equal(request.transcription_id,'tr_server');assert.equal(request.revision_number,1);assert.equal(request.acceptance_id,'a_server');
 assert.match(ui.host.textContent,/Falha técnica/);
});
test('manual, wrong-problem or ambiguous sources cannot masquerade as automatic recognition',async()=>{
 for(const options of [{origin:'manual'},{problem:'TME2026P2'},{issues:[{requires_review:true,code:'AMBIGUOUS_SYMBOL'}]}]){
  const ui=await screen(options);await assert.rejects(ui.component.loadAutomaticCase('case_server'));assert(!ui.calls.some(c=>c.options.method));
 }
});
test('a changed automatic revision cannot inherit confirmation of the previous text',async()=>{
 const ui=await screen();await ui.component.loadAutomaticCase('case_server');const check=ui.nodes().find(n=>n.getAttribute('aria-label')==='Confirmo o texto da solução');check.checked=true;await check.emit('change');ui.revise();await ui.nodes().find(n=>n.tag==='form').emit('submit',{preventDefault(){}});
 assert.match(ui.host.textContent,/leitura automática mudou/);assert(!ui.calls.some(c=>c.options.method));
});
test('a lost audit response retries the same execution identity rather than charging for a new run',async()=>{
 const ui=await screen();await ui.component.loadAutomaticCase('case_server');const check=ui.nodes().find(n=>n.getAttribute('aria-label')==='Confirmo o texto da solução');check.checked=true;await check.emit('change');ui.fail(true);await ui.nodes().find(n=>n.tag==='form').emit('submit',{preventDefault(){}});ui.fail(false);await ui.nodes().find(n=>n.tag==='form').emit('submit',{preventDefault(){}});
 const audits=ui.calls.filter(c=>c.url.endsWith('/audits'));assert.equal(audits.length,2);assert.equal(JSON.parse(audits[0].options.body).execution_key,JSON.parse(audits[1].options.body).execution_key);
});
