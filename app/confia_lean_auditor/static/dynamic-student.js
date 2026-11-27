/* Institutional student adapter. Scoring and capture remain server-owned. */
(function(root){
  const labels={DRAFT:'Em preparação',SUBMITTED:'Enviada',RELEASED:'Resultado divulgado',AWAITING_EVALUATION:'Aguardando avaliação',TECHNICAL_ERROR:'Falha técnica — aguarda retomada docente',REVIEW_PENDING:'Aguardando revisão',AWAITING_TEACHER:'Aguardando confirmação docente',TEACHER_CONFIRMED:'Confirmada pelo professor'};
  const node=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
  const field=(parent,label,element)=>{const l=node('label',label);l.append(element);parent.append(l);element.setAttribute('aria-label',label);return element;};
  const button=(parent,text,action)=>{const b=node('button',text,'button button-primary');b.type='button';b.addEventListener('click',action);parent.append(b);return b;};
  async function request(url,body,method='POST'){
    const r=await fetch(url,{credentials:'same-origin',...(body===undefined?{}:{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
    const data=await r.json();if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:data.detail?.message||'Não foi possível concluir. Confira o estado da atividade.');return data;
  }
  async function fileData(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve({media_type:file.type,content_base64:String(r.result).split(',')[1]});r.onerror=()=>reject(Error('Não foi possível ler o arquivo.'));r.readAsDataURL(file);});}
  function create(host,id){
    let data,selected=null,busy=false,disposed=false;
    const drafts=new Map();
    const dirty=id=>Array.from(drafts.keys()).some(k=>k.startsWith(id+':'));
    const panel=node('section',undefined,'dynamic-workflow');host.replaceChildren(panel);
    const message=node('p','Carregando atividade…','status');message.setAttribute('role','status');message.setAttribute('aria-live','polite');panel.append(message);
    async function perform(action){if(busy||disposed)return;busy=true;panel.setAttribute('aria-busy','true');panel.querySelectorAll('button').forEach(b=>b.disabled=true);try{await action();if(!disposed){await load();message.textContent='Dados atualizados.';message.tabIndex=-1;message.focus();}}catch(e){message.textContent=e.message;}finally{busy=false;panel.setAttribute('aria-busy','false');panel.querySelectorAll('button').forEach(b=>b.disabled=b.dataset.unavailable==='true');}}
    async function load(){data=await request('/dynamic/student/activities/'+id);if(!disposed)render();}
    function render(){
      panel.replaceChildren(message);message.textContent='';
      panel.append(node('h3',data.title),node('p',`${data.purpose==='SCHOOL_EXAM'?'Prova':'Atividade formativa'} DYNAMIC · ${data.availability} · até ${data.policy.max_attempts} tentativa(s)`),node('p','A avaliação automática é uma sugestão. A nota escolar depende de confirmação e divulgação pelo professor.'));
      if(data.policy.feedback==='GUIDANCE')panel.append(node('p','Orientações formativas disponíveis após o envio.'));
      for(const q of data.questions){const c=node('article',undefined,'exam-item-card');c.append(node('h4',`Questão ${q.order} · ${q.max_points} pontos`),node('p',q.statement));panel.append(c);}
      const history=node('section');history.append(node('h3','Minhas tentativas'));panel.append(history);
      for(const a of data.attempts)button(history,`Tentativa ${a.attempt_number} — ${labels[a.status]||a.status}`,()=>{selected=a.attempt_id;render();});
      const attempt=data.attempts.find(a=>a.attempt_id===selected);
      if(attempt){renderAttempt(attempt);button(panel,'Voltar às tentativas',()=>{selected=null;render();});return;}
      const available=data.availability==='DISPONÍVEL'&&data.attempts.length<data.policy.max_attempts;
      if(!available){panel.append(node('p','Novos envios indisponíveis: confira o prazo e o limite de tentativas.'));return;}
      panel.append(node('p','Iniciar uma tentativa registra seu uso. Confira o conteúdo antes de continuar.'));
      if(data.policy.allowed_inputs.includes('TEXT')){
        const form=node('form',undefined,'tme-new-form');form.append(node('h3','Resolução digitada'));
        const areas=data.questions.map(q=>{const a=field(form,`Solução da questão ${q.order}`,node('textarea'));a.rows=7;a.required=true;a.maxLength=20000;return a;});
        const b=node('button','Registrar tentativa textual','button button-primary');b.type='submit';form.append(b);
        const key=root.crypto.randomUUID();form.addEventListener('submit',e=>{e.preventDefault();perform(async()=>{const a=await request(`/dynamic/student/activities/${id}/attempts`,{definition_sha256:data.definition_sha256,mode:'TEXT',solutions:areas.map(a=>a.value),execution_key:key});selected=a.attempt_id;});});panel.append(form);
      }
      if(data.policy.allowed_inputs.some(x=>x==='IMAGES'||x==='PDF')){
        const form=node('form',undefined,'tme-new-form');form.append(node('h3','Fotografias ou PDF'));
        const f=field(form,'Originais da resolução',node('input'));f.type='file';f.multiple=true;f.required=true;f.accept=[...(data.policy.allowed_inputs.includes('IMAGES')?['image/png','image/jpeg','image/webp']:[]),...(data.policy.allowed_inputs.includes('PDF')?['application/pdf']:[])].join(',');
        form.append(node('p','Envie fotografias ou um PDF. Associe páginas, confira a leitura de cada questão e só então autorize o envio.'));
        const b=node('button','Registrar originais','button button-primary');b.type='submit';form.append(b);const key=root.crypto.randomUUID();
        form.addEventListener('submit',e=>{e.preventDefault();perform(async()=>{const documents=await Promise.all(Array.from(f.files).map(fileData));const a=await request(`/dynamic/student/activities/${id}/attempts`,{definition_sha256:data.definition_sha256,mode:documents[0].media_type==='application/pdf'?'PDF':'IMAGES',original_documents:documents,execution_key:key});selected=a.attempt_id;});});panel.append(form);
      }
    }
    function renderAttempt(a){
      const section=node('section');section.append(node('h3',`Tentativa ${a.attempt_number} — ${labels[a.status]||a.status}`));panel.append(section);
      const base='/dynamic/student/attempts/'+a.attempt_id;
      for(const p of a.pages){const link=node('a',`Consultar original — página ${p.page_number}`);link.href=p.original_url;link.target='_blank';link.rel='noopener';const image=node('img');image.src=p.preview_url;image.alt=`Resolução original, página ${p.page_number}`;image.style.maxWidth='100%';image.style.maxHeight='420px';section.append(link,image);}
      if(!a.submitted&&a.pages.length){
        const form=node('form',undefined,'tme-new-form'),checks=[];form.append(node('h4','Associar páginas às questões'),node('p','Uma página pode conter mais de uma resposta. Na transcrição, mantenha apenas o trecho da questão indicada. A associação é fixada ao iniciar a leitura.'));
        for(const q of a.questions){const group=node('fieldset');group.append(node('legend',`Questão ${q.order}`));for(const p of a.pages){const c=field(group,`Q${q.order}: página ${p.page_number}`,node('input'));c.type='checkbox';c.checked=a.mapping.bindings.some(b=>b.question_attempt_id===q.case_id&&b.exam_page_id===p.page_id);checks.push({c,q,p});}form.append(group);}
        const b=node('button','Salvar associação de páginas','button');b.type='submit';form.append(b);form.addEventListener('submit',e=>{e.preventDefault();perform(()=>{if(dirty(a.attempt_id))throw Error('Salve as leituras antes de alterar a associação.');return request(base+'/page-mapping',{expected_version:a.mapping.version,bindings:checks.filter(x=>x.c.checked).map(({q,p})=>({question_attempt_id:q.case_id,exam_page_id:p.page_id,order:checks.filter(x=>x.c.checked&&x.q.case_id===q.case_id).findIndex(x=>x.p.page_id===p.page_id)+1}))},'PUT');});});section.append(form);
      }
      for(const q of a.questions){
        const card=node('article',undefined,'exam-item-card');card.append(node('h4',`Questão ${q.order} — ${labels[q.status]||q.status}`));section.append(card);
        if(q.guidance)for(const g of q.guidance)card.append(node('p',g.message));
        if(!a.submitted&&a.pages.length){
          button(card,`Reconhecer escrita da questão ${q.order}`,()=>perform(()=>{if(drafts.has(a.attempt_id+':'+q.case_id))throw Error('Salve a leitura editada antes de reconhecer novamente.');return request(`${base}/questions/${q.case_id}/recognize`,{});}));
          const key=a.attempt_id+':'+q.case_id;const form=node('form',undefined,'tme-new-form');const areas=q.pages.map((p,i)=>{const t=field(form,`Texto da questão ${q.order}, página ${p.page_number}`,node('textarea'));t.rows=6;t.value=q.segments.filter(s=>s.page_index===i).map(s=>s.text||s.latex||'').join('\n');const original=t.value;t.value=drafts.get(key)?.[i]??original;t.addEventListener('input',()=>{if(areas.every(x=>x.t.value===x.original))drafts.delete(key);else drafts.set(key,areas.map(x=>x.t.value));});return {t,i,original};});
          form.append(node('p','Transcreva somente esta resposta. Use [Trecho ilegível] quando necessário; não complete conteúdo matemático por suposição.'));
          const save=node('button',`Salvar leitura da questão ${q.order}`,'button');save.type='submit';form.append(save);form.addEventListener('submit',e=>{e.preventDefault();perform(async()=>{await request(`${base}/questions/${q.case_id}/reading`,{based_on_revision_number:q.revision_number,segments:areas.map(({t,i})=>({segment_id:'page:'+i,page_index:i,order:0,kind:'text',text:t.value}))});drafts.delete(key);});});card.append(form);
          const reading=q.reading_review;
          card.append(node('p',reading?.status==='CONFIRMED'?'Leitura conferida — autoria registrada.':'Leitura ainda não conferida.'));
          if(reading?.revision_sha256&&reading.status!=='CONFIRMED'){
            const consent=field(card,`Conferi o texto salvo da questão ${q.order} com os originais; contém apenas esta resposta`,node('input'));consent.type='checkbox';
            button(card,`Confirmar minha leitura da questão ${q.order}`,()=>perform(async()=>{if(areas.some(x=>x.t.value!==x.original))throw Error('Salve as alterações da leitura antes de confirmar.');if(!consent.checked)throw Error('Confira os originais e marque a confirmação explícita.');await request(`${base}/questions/${q.case_id}/confirm-reading`,{revision_number:q.revision_number,revision_sha256:reading.revision_sha256,confirmed:true,question_scope_confirmed:true});}));
          }
        }else if(q.segments.length){const details=node('details');details.append(node('summary','Consultar texto utilizado'));for(const s of q.segments)details.append(node('p',s.text||s.latex||''));card.append(details);}
      }
      if(!a.submitted)button(section,'Enviar tentativa para avaliação',()=>perform(()=>{if(dirty(a.attempt_id))throw Error('Salve e confira as leituras editadas antes de enviar.');return request(base+'/submit',{});}));
      else button(section,'Atualizar andamento',()=>perform(async()=>{}));
      if(a.result){if(a.result.final_total!==undefined){section.append(node('h4',`Nota confirmada: ${a.result.final_total} / ${a.result.max_total}`));for(const q of a.result.questions)section.append(node('p',`Questão ${q.order}: ${q.final_points} / ${q.max_points}`));}if(a.result.teacher_feedback)section.append(node('h4','Devolutiva do professor'),node('p',a.result.teacher_feedback));}
      else if(a.submitted)section.append(node('p','O resultado ainda não foi divulgado. Pendências e falhas técnicas não equivalem a nota zero.'));
    }
    load().catch(e=>{message.textContent=e.message;});return {dispose(){disposed=true;},reload:load};
  }
  root.ConfIADynamicStudent={create,labels};
})(window);
