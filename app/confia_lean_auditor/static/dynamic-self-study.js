/* SELF_STUDY uses the authenticated DYNAMIC gateway. No grade rendering. */
(function(root){
 'use strict';
 const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;};
 const label=(text,control)=>{const e=node('label',text);e.append(control);return e;};
 const button=(text,fn)=>{const e=node('button',text,'button');e.type='button';e.addEventListener('click',fn);return e;};
 const states={SUPPORTED:'Passo apoiado pela análise',PARTIAL:'Desenvolvimento a completar',MATHEMATICAL_ERROR:'Possível erro matemático',NEEDS_EXPLANATION:'Explique este passo',UNCERTAIN:'Análise inconclusiva',TECHNICAL_ERROR:'Falha técnica'};
 const changes={ERROR_REVISED:'O erro apontado anteriormente não aparece na análise atual.',STILL_NEEDS_ATTENTION:'Este objetivo continua precisando de atenção.',NEW_EXPLANATION:'Você apresentou uma justificativa diferente.',UNCHANGED:'Este trecho permanece sem mudança.'};
 function create(host){
  let data=null,listing=null,busy=false,disposed=false,selected=null;const dirty=new Map();
  const status=node('p','','status-message');status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.tabIndex=-1;
  const request=async(path,body)=>{const r=await fetch('/dynamic/self-study'+path,{credentials:'same-origin',...(body!==undefined?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Não foi possível concluir. Confira os campos e sua sessão.');return d;};
  const key=()=>root.crypto.randomUUID();
  const pending=()=>{if(dirty.size)throw Error('Salve as leituras editadas antes de continuar.');};
  async function perform(fn){if(busy)return;busy=true;status.textContent='Aguarde…';try{await fn();if(!disposed){render();status.textContent='Operação concluída.';status.focus();}}catch(e){if(!disposed)status.textContent=e.message;}finally{busy=false;}}
  async function fileSource(input,text){
   if(!input.files?.length){if(!text.trim())throw Error('Digite seu texto ou selecione fotografias/PDF.');return {text};}
   if(text.trim())throw Error('Envie texto ou fotografias/PDF, separadamente.');
   const docs=[];for(const f of Array.from(input.files)){if(f.size>20*1024*1024)throw Error('Cada arquivo deve ter até 20 MiB.');const content=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(',')[1]);r.onerror=()=>reject(Error('Não foi possível ler o arquivo.'));r.readAsDataURL(f);});docs.push({media_type:f.type,content_base64:content});}return {original_documents:docs};
  }
  function inputForm(title,onSend,withGrade=false){
   const form=node('form',null,'card');form.append(node('h3',title));
   const area=node('textarea');area.rows=6;area.maxLength=20000;area.setAttribute('aria-label',title);form.append(label(title,area));
   const files=node('input');files.type='file';files.accept='image/png,image/jpeg,image/webp,application/pdf';files.multiple=true;form.append(label('Fotografias ou PDF (opcional; substituem o texto)',files));
   const grade=node('select');for(let n=6;n<=12;n++){const o=node('option',n<=9?n+'º ano do Fundamental':(n-9)+'ª série do Médio');o.value=String(n);grade.append(o);}grade.value='9';if(withGrade)form.append(label('Etapa escolar',grade));
   const send=node('button',withGrade?'Registrar enunciado':'Registrar nova tentativa','button button-primary');send.type='submit';form.append(send);
   form.addEventListener('submit',e=>{e.preventDefault();perform(async()=>{pending();await onSend(await fileSource(files,area.value),Number(grade.value));});});return {form,area};
  }
  function sourceEditor(source,aid=null,immutable=false){
   const base='/'+data.study_id+(aid?'/attempts/'+aid:'');const id=source.submission_id;
   const box=node('section',null,'card');box.append(node('h3',aid?'Sua resolução':'Enunciado original e leitura'));
   if(source.pages.length){const media=node('details');media.append(node('summary','Consultar páginas e originais'));for(const p of source.pages){const img=node('img');img.src=p.preview_url;img.alt='Página '+(p.page_index+1);img.style.maxWidth='100%';media.append(img);}for(const o of source.originals){const a=node('a','Abrir original');a.href=o.url;a.target='_blank';a.rel='noopener';media.append(a);}box.append(media);}
   box.append(node('p',source.confirmed?'Leitura conferida por você, vinculada a esta versão.':source.automatic?'Transcrição automática: confira com o original.':'Confira o texto antes de prosseguir.'));
   const pages=source.pages.length?source.pages.map(p=>p.page_index):[0];const areas=[];
   for(const p of pages){const original=source.segments.filter(s=>s.page_index===p).map(s=>[s.text,s.latex].filter(Boolean).join('\n')).join('\n');if(immutable){box.append(node('p',original,'study-original'));continue;}const area=node('textarea');area.rows=5;area.readOnly=immutable;area.setAttribute('aria-label',(aid?'Resolução':'Enunciado')+' — página '+(p+1));area.value=dirty.get(id+':'+p)??original;area.addEventListener('input',()=>{if(area.value===original)dirty.delete(id+':'+p);else dirty.set(id+':'+p,area.value);});areas.push({area,p,original});box.append(label('Página '+(p+1),area));}
   if(immutable)return box;
   if(source.pages.length)box.append(button('Reconhecer fotografias',()=>perform(async()=>{pending();data=await request(base+'/recognize',{});} )));
   box.append(node('p','Se um trecho estiver ilegível, escreva [ilegível]. A análise ficará bloqueada até esclarecer esse trecho.'));
   box.append(button('Salvar leitura',()=>perform(async()=>{const segments=areas.map(({area,p})=>({segment_id:'page:'+p,page_index:p,order:0,kind:'text',text:area.value}));data=await request(base+'/reading',{based_on_revision_number:source.revision_number,segments});for(const {p} of areas)dirty.delete(id+':'+p);} )));
   const consent=node('input');consent.type='checkbox';consent.setAttribute('aria-label',aid?'Conferi minha resolução':'Conferi o enunciado');box.append(label('Conferi o texto e, quando houver, sua correspondência com o original.',consent));
   box.append(button('Confirmar leitura',()=>perform(async()=>{if(!consent.checked)throw Error('Confirme que conferiu o texto.');if(areas.some(a=>a.area.value!==a.original))throw Error('Salve as alterações antes de confirmar.');data=await request(base+'/confirm-reading',{revision_number:source.revision_number,revision_sha256:source.revision_sha256,confirmed:true});} )));
   return box;
  }
  function reportView(a){
   const report=a.report,box=node('section',null,'card');box.append(node('h3','Orientações para aprender — sem nota'),node('p','Critérios provisórios e formativos. Avaliação automática; sem certificação Lean.'));
   for(const f of report.findings){const row=node('article');row.append(node('h4',f.objective+' · '+states[f.state]),node('p',f.guidance));for(const e of f.evidence)row.append(node('blockquote',e.text));box.append(row);}
   for(const u of report.uncertainties)box.append(node('p',u));
   for(const c of report.comparison)box.append(node('p',changes[c.change]||'Compare as justificativas entre tentativas.'));
   for(const h of a.help){box.append(node('h4','Nível '+h.level+(h.status==='SAFE_FALLBACK'?' · orientação segura':'')));for(const i of h.content.items)box.append(node('p',i.message));for(const l of h.content.limitations)box.append(node('p',l));}
   const next=a.help.length?Math.max(...a.help.map(h=>h.level))+1:2;
   if(next<=4&&report.findings.some(f=>f.evidence.length)){
    const consent=node('input');consent.type='checkbox';consent.setAttribute('aria-label','Solicito o desenvolvimento orientado completo');if(next===4)box.append(label('Quero consultar o desenvolvimento orientado ou a resolução completa.',consent));
    box.append(button({2:'Quero uma pista matemática',3:'Explique o conceito',4:'Mostrar desenvolvimento orientado'}[next],()=>perform(async()=>{pending();if(next===4&&!consent.checked)throw Error('Solicite explicitamente o desenvolvimento completo.');data=await request('/'+data.study_id+'/attempts/'+a.attempt_id+'/help',{level:next,request_complete_solution:next===4&&consent.checked});} )));
   }
   return box;
  }
  function render(){
   if(disposed)return;host.replaceChildren(status);
   if(!data){
    host.append(node('h2','Estudo autônomo'),node('p','Explore seu raciocínio, peça pistas e tente novamente. Este espaço não atribui notas.'));
    const f=inputForm('Seu enunciado',async(source,grade_year)=>{data=await request('',{source,grade_year,execution_key:key()});selected=null;},true);
    const choose=node('select');choose.setAttribute('aria-label','Escolher um problema');choose.append(node('option','Inserir outro enunciado'));for(const c of listing?.catalog||[]){const o=node('option',c.topic);o.value=c.id;choose.append(o);}choose.addEventListener('change',()=>{const c=listing.catalog.find(c=>c.id===choose.value);if(c)f.area.value=c.statement;});host.append(label('Problemas para estudar',choose),f.form,node('h3','Seu histórico'));
    for(const s of listing?.studies||[])host.append(button(s.statement,()=>perform(async()=>{data=await request('/'+s.study_id);selected=null;})));
    return;
   }
   host.append(button('Voltar ao histórico',()=>perform(async()=>{pending();data=null;listing=await request('');selected=null;})),node('h2','Seu estudo — DYNAMIC'),sourceEditor(data.source));
   host.append(button('Interpretar enunciado e preparar critérios',()=>perform(async()=>{pending();data=await request('/'+data.study_id+'/prepare',{});} )));
   const pack=data.packages.at(-1);
   if(pack){const box=node('section',null,'card');box.append(node('h3','Interpretação e critérios provisórios'),node('p',pack.interpretation||'Interpretação indisponível.'));
    for(const u of pack.uncertainties)box.append(node('p',u));for(const o of pack.objectives)box.append(node('p',o.title));
    if(pack.status==='TECHNICAL_ERROR')box.append(node('p','Falha técnica ao preparar. O enunciado foi preservado; tente novamente.'));
    else if(pack.status==='NEEDS_CLARIFICATION')box.append(node('p','Esclareça o enunciado antes de avaliar sua resolução.'));
    else if(!pack.confirmed){const c=node('input');c.type='checkbox';c.setAttribute('aria-label','A interpretação corresponde ao problema');box.append(label('A interpretação corresponde ao problema que quero estudar.',c),button('Confirmar interpretação',()=>perform(async()=>{pending();if(!c.checked)throw Error('Confira a interpretação primeiro.');data=await request('/'+data.study_id+'/confirm-interpretation',{package_id:pack.package_id,package_sha256:pack.sha256,confirmed:true});})));}
    else box.append(node('p','Interpretação conferida. Os critérios continuam provisórios, sem aprovação institucional.'));host.append(box);
    if(pack.confirmed&&pack.current_statement!==false){const f=inputForm('Sua nova resolução',async(source)=>{data=await request('/'+data.study_id+'/attempts',{source,package_id:pack.package_id,execution_key:key()});selected=data.attempts.at(-1).attempt_id;});host.append(f.form);}
   }
   host.append(node('h3','Tentativas e orientações'));
   for(const a of data.attempts)host.append(button('Tentativa '+a.number+(a.report?' · com análise':' · conferir leitura'),()=>{selected=a.attempt_id;render();}));
   const a=data.attempts.find(a=>a.attempt_id===selected)||data.attempts.at(-1);
   if(a){const pinned=data.packages.find(p=>p.package_id===a.package_id);if(pinned)host.append(node('h3','Tentativa '+a.number+' · critérios provisórios, versão '+pinned.version),node('p',pinned.statement||pinned.interpretation));host.append(sourceEditor(a.source,a.attempt_id,Boolean(a.report)));if(a.report)host.append(reportView(a));else host.append(button('Analisar minha resolução',()=>perform(async()=>{pending();data=await request('/'+data.study_id+'/attempts/'+a.attempt_id+'/analyze',{});})));}
  }
  perform(async()=>{listing=await request('');});
  return {dispose(){disposed=true;},reload(){return perform(async()=>{if(data)data=await request('/'+data.study_id);else listing=await request('');});}};
 }
 let mounted;
 root.ConfIASelfStudy={create,show(view){const host=document.querySelector('#student-self-study');if(!host)return;host.hidden=view!=='study';if(view==='study'&&!mounted)mounted=create(host);}};
})(window);
