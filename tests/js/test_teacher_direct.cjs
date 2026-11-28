// UI transport/state tests use synthetic replies, not mathematical evaluations.
const test=require('node:test'),assert=require('node:assert/strict');
const {pilot,walk,text}=require('./tme-dom.cjs');
const reply=data=>({ok:true,json:async()=>data});
const cid='case_'+'a'.repeat(32),tid='tr_demo';
test('SPECIALIZED direct intake sends typed original without assessment or automatic audit',async()=>{
 const ui=await pilot({initialSearch:'?view=new&mode=specialized',mockFetch:(url)=>url==='/tme/direct-solutions'?reply({case_id:cid}):undefined});
 const select=walk(ui.root).find(n=>n.attributes['aria-label']==='Problema preparado');select.value='ITA2025F2Q1';await select.handlers.change();
 const nodes=walk(ui.root);nodes.find(n=>n.attributes['aria-label']==='Resolução digitada').value='x = 2';
 const form=nodes.find(n=>n.tag==='form');await form.handlers.submit({preventDefault(){}});
 const call=ui.calls.find(c=>c.url==='/tme/direct-solutions');assert(call);
 assert.equal(JSON.parse(call.options.body).problem_id,'ITA2025F2Q1');assert.equal(JSON.parse(call.options.body).solution,'x = 2');
 assert(!ui.calls.some(c=>c.options.method==='POST'&&/audits|assessments|release|publish/.test(c.url)));
});
test('direct workspace blocks analysis until explicit transcription confirmation',async()=>{
 const ui=await pilot({mode:'TEXT',automatic:true,mockFetch:(url)=>url.endsWith('/original-text')?reply({text:'x = 2',teacher_confirmation_required:true}):undefined});
 await ui.click('Abrir');assert.match(text(ui.root),/Confirmar transcrição/);
 const audit=walk(ui.root).filter(n=>n.tag==='button'&&n.textContent==='Analisar com ConfIA');assert(audit.length);assert(audit.every(n=>n.disabled));
 await audit[0].click();assert(!ui.calls.some(c=>c.options.method==='POST'&&c.url.endsWith('/audits')));
 const check=walk(ui.root).find(n=>n.attributes['aria-label']==='Conferi a transcrição com o original');check.checked=true;check.handlers.change();await ui.click('Confirmar transcrição');
 const call=ui.calls.find(c=>c.options.method==='POST'&&c.url.endsWith('/accept'));assert(call);
 assert.equal(JSON.parse(call.options.body).acceptance_note,ui.window.ConfIATeacherDirect.confirmation);
 assert(!ui.calls.some(c=>c.options.method==='POST'&&c.url.endsWith('/audits')));
});
test('direct intake keeps typed work on backend failure and labels OCR unavailable',async()=>{
 const ui=await pilot({initialSearch:'?view=new&mode=specialized',mockFetch:url=>url==='/tme/direct-solutions'?{ok:false,json:async()=>({detail:'Falha de armazenamento'})}:undefined});
 const select=walk(ui.root).find(n=>n.attributes['aria-label']==='Problema preparado');select.value='ITA2025F2Q1';await select.handlers.change();
 const solution=walk(ui.root).find(n=>n.attributes['aria-label']==='Resolução digitada');solution.value='Texto a preservar';
 await walk(ui.root).find(n=>n.tag==='form').handlers.submit({preventDefault(){}});
 assert.equal(solution.value,'Texto a preservar');assert.equal(solution.disabled,false);assert.match(text(ui.root),/Falha de armazenamento/);assert.match(text(ui.root),/nenhum OCR/);
});
