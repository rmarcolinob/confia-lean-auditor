/* Single-page editor; versioning, preparation, approval and scoring remain server-owned. */
(function(root){
  'use strict';
  const n=(tag,text,cls)=>{const el=document.createElement(tag);if(text!=null)el.textContent=text;if(cls)el.className=cls;return el;};
  const field=(text,el)=>{const label=n('label',text);label.append(el);return label;};
  const cents=value=>/^\d+(?:\.\d{1,2})?$/.test(String(value))?Math.round(Number(value)*100):null;
  const money=value=>(value/100).toLocaleString('pt-BR',{maximumFractionDigits:2});
  function create({host,setBusy=()=>{},onSelect=()=>{},onOpenAttempt=()=>{}}){
    let doc=null,rows=[],busy=false,disposed=false,approved=false,showConfig=true,caps={},nextId=1,intake;
    const usedIds=new Set();
    const page=n('section',null,'dynamic-form'),message=n('p'),rubric=n('section',null,'tme-panel dynamic-rubric'),rowHost=n('div'),sum=n('p'),warnings=n('div'),reading=n('input');
    const title=n('input'),statement=n('textarea'),total=n('input');
    title.maxLength=160;statement.maxLength=20000;statement.rows=4;total.type='number';total.min='0.01';total.max='1000';total.step='0.01';total.value='10';
    title.setAttribute('aria-label','Título (opcional)');statement.setAttribute('aria-label','Enunciado do problema');total.setAttribute('aria-label','Pontuação total');
    reading.type='checkbox';reading.setAttribute('aria-label','Li os avisos da rubrica');message.setAttribute('role','status');sum.setAttribute('aria-live','polite');
    const add=button('Adicionar critério',()=>{addRow();invalidate();});
    const approve=button('Aprovar rubrica',()=>perform(async()=>{
      await persist();const r=currentRubric();showWarnings();
      if(r.review_warnings?.some(w=>w.requires_review)&&!reading.checked){message.textContent='Rubrica salva. Leia os avisos abaixo e confirme sua aprovação.';return;}
      if(r.status!=='APPROVED')doc=await request(`/dynamic/problems/${doc.problem.problem_id}/rubrics/${r.rubric_id}/approve`,{expected_revision:doc.revision,acknowledge_warnings:reading.checked});
      approved=true;showConfig=false;showWarnings();message.textContent=doc.correction_available===false?'Rubrica aprovada; a preparação ainda não permite corrigir. Confira as pendências.':'Rubrica aprovada. Insira a solução abaixo e clique em Corrigir solução.';
    }));
    const suggest=button('Sugerir rubrica com IA',()=>perform(async()=>{
      approved=false;intake.resetContext();await saveStatement();
      doc=await request(`/dynamic/problems/${doc.problem.problem_id}/preparations`,{expected_revision:doc.revision});
      const prep=doc.current_preparation;
      if(!prep||!['READY_FOR_REVIEW','REVIEW_REQUIRED'].includes(prep.status))throw Error('Preparação automática indisponível. A rubrica manual permanece disponível.');
      doc=await request(`/dynamic/problems/${doc.problem.problem_id}/rubric-suggestion`,{expected_revision:doc.revision,preparation_id:prep.preparation_id});
      replaceRows(currentRubric()?.criteria||[]);reading.checked=false;showWarnings();message.textContent='Sugestão recebida. Confira os critérios e aprove explicitamente.';
    }));
    const capability=n('p'),approvalState=n('p');approvalState.setAttribute('role','status');
    rubric.append(n('h2','Rubrica'),rowHost,add,sum,suggest,capability,warnings,field('Li os avisos e assumo a revisão docente',reading),approve,approvalState);
    const source=n('div');
      const configFields=[
        field('Título (opcional)',title),
        field('Enunciado do problema',statement),
        field('Pontuação total',total),
        rubric
      ];
      const summary=n('p',null,'tme-panel');
      const edit=button('Ver ou editar problema e rubrica',()=>{
        showConfig=true;update();
      });
      const back=button('Voltar à correção',()=>{
        showConfig=false;update();
      });
      page.append(...configFields,back,summary,edit,source,message);
      host.append(page);
    intake=root.ConfIATeacherDirect.create({host:source,problemId:()=>doc?.problem.problem_id,dynamic:true,setBusy:value=>{busy=value;setBusy(value);update(false);},ready:()=>approved&&!busy&&doc?.correction_available!==false,onOpen:onOpenAttempt});
    for(const input of [title,statement,total])input.addEventListener('input',invalidate);
    reading.addEventListener('change',update);
    function button(text,fn){const b=n('button',text,'tme-button secondary');b.type='button';b.addEventListener('click',fn);return b;}
    async function request(url,body,method='POST'){
      const response=await fetch(url,body===undefined?{credentials:'same-origin'}:{method,credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:data.detail?.message||'Não foi possível salvar. Confira os critérios e recarregue se outra sessão alterou o problema.');return data;
    }
    function invalidate(){approved=false;reading.checked=false;intake?.resetContext();message.textContent='Alterações exigem nova aprovação da rubrica.';update();}
    function criteria(){return rows.map((r,i)=>({...r.original,criterion_id:r.id,title:r.title.value,description:r.description.value,max_points:r.points.value,order:i+1}));}
    function valid(){
      const max=cents(total.value);return statement.value.trim()&&max>0&&max<=100000&&rows.length>0&&rows.every(r=>r.title.value.trim()&&r.description.value.trim()&&cents(r.points.value)!==null&&(r.original.credit_levels||[]).every(level=>cents(level.points)<cents(r.points.value)))&&rows.reduce((s,r)=>s+cents(r.points.value),0)===max;
    }
    function validationBlockers(){
      const issues=[];
      if(!statement.value.trim())issues.push('preencha o enunciado');
      const max=cents(total.value);
      if(!(max>0&&max<=100000))issues.push('informe uma pontuação total válida');
      if(!rows.length)issues.push('adicione um critério');
      rows.forEach((r,i)=>{
        const k=i+1,points=cents(r.points.value);
        if(!r.title.value.trim())issues.push(`preencha o título do critério ${k}`);
        if(!r.description.value.trim())issues.push(`preencha a descrição do critério ${k}`);
        if(points===null)issues.push(`corrija os pontos do critério ${k}`);
        if((r.original.credit_levels||[]).some(level=>!(cents(level.points)<points)))
          issues.push(`revise os níveis de crédito parcial do critério ${k}`);
      });
      const values=rows.map(r=>cents(r.points.value));
      if(max!==null&&values.every(v=>v!==null)&&
         values.reduce((a,b)=>a+b,0)!==max)
        issues.push('a soma dos critérios deve corresponder ao total');
      return issues;
    }
    function update(refresh=true){
      const values=rows.map(r=>cents(r.points.value));sum.textContent=`Soma dos critérios: ${values.some(v=>v===null)?'inválida':money(values.reduce((a,b)=>a+b,0))} / ${cents(total.value)===null?'inválido':money(cents(total.value))} pontos`;
      approve.disabled=busy||approved||!valid();suggest.disabled=busy||!caps.rubric_suggestion_configured||!statement.value.trim()||!(cents(total.value)>0);add.disabled=busy;
      for(const input of [title,statement,total,reading,...rowHost.querySelectorAll('input,textarea,button')])input.disabled=busy;
      approvalState.textContent=approved?'Rubrica aprovada':valid()?
        'Rubrica pronta para aprovação.':
        'Para aprovar: '+validationBlockers().join('; ')+'.';const correcting=approved&&!showConfig;
        for(const el of configFields)
          el.style.display=correcting?'none':'';
        summary.style.display=correcting?'':'none';
        edit.style.display=correcting?'':'none';
        back.style.display=approved&&showConfig?'':'none';
        edit.disabled=busy;
        back.disabled=busy;
        summary.textContent=approved
          ? `${title.value.trim()||'Questão sem título'} · ${total.value} pontos · Rubrica aprovada`
          : '';
        if(refresh)intake?.refresh();
    }
    function addRow(data={}){
      let id=data.criterion_id;if(!id){do{id='criterion_'+nextId++;}while(usedIds.has(id));}usedIds.add(id);
      const box=n('fieldset',null,'dynamic-criterion'),t=n('input'),d=n('textarea'),p=n('input');t.value=data.title||'';d.value=data.description||'';p.value=data.max_points??'0';p.type='number';p.min='0';p.max='1000';p.step='0.01';t.maxLength=160;d.maxLength=20000;d.rows=2;
      t.setAttribute('aria-label',`Critério ${id}: título`);d.setAttribute('aria-label',`Critério ${id}: descrição`);p.setAttribute('aria-label',`Critério ${id}: pontos`);
      const row={id,title:t,description:d,points:p,original:data,box};rows.push(row);
      box.append(field('Título',t),field('Descrição',d),field('Pontos',p),button('Remover critério',()=>{
        if(rows.some(other=>other!==row&&(other.original.dependencies||[]).includes(id))){message.textContent='Este critério é pré-requisito de outro. As dependências aprovadas não podem ser removidas implicitamente.';return;}
        rows.splice(rows.indexOf(row),1);rowHost.removeChild(box);invalidate();
      }));
      if(data.credit_levels?.length||data.dependencies?.length||data.notes||data.teacher_guidance||data.evidence){
        const details=n('details');details.append(n('summary','Regras científicas preservadas'));
        for(const level of data.credit_levels||[])details.append(n('p',`Crédito parcial: ${level.points} — ${level.description}`));
        for(const dependency of data.dependency_rules||[])details.append(n('p',`Dependência ${dependency.criterion_id}: ${dependency.condition}`));
        if(data.notes)details.append(n('p',data.notes));if(data.teacher_guidance)details.append(n('p',data.teacher_guidance));
        details.append(n('p','Esta edição mantém os vínculos, níveis e dependências existentes. Reduzir pontos abaixo de um nível parcial não é permitido.'));box.append(details);
      }
      for(const input of [t,d,p])input.addEventListener('input',invalidate);rowHost.append(box);update();
    }
    function replaceRows(values){rows=[];rowHost.replaceChildren();values.forEach(addRow);}
    function currentRubric(){const version=doc?.statements.at(-1)?.version_number;return doc?.rubrics.filter(r=>r.statement_version===version).at(-1);}
    function showWarnings(){warnings.replaceChildren();for(const w of currentRubric()?.review_warnings||[])warnings.append(n('p',w.message));}
    async function saveStatement(){
      const body={title:title.value,statement:statement.value,max_score:total.value};const last=doc?.statements.at(-1);
      if(!doc){doc=await request('/dynamic/problems',{...body,correction_mode:'DYNAMIC'});onSelect(doc.problem.problem_id);}
      else if((last.title||'')!==title.value||last.statement!==statement.value||cents(last.max_score)!==cents(total.value))doc=await request(`/dynamic/problems/${doc.problem.problem_id}/statements`,{...body,expected_revision:doc.revision});
    }
    async function persist(){
      if(!valid())throw Error('Preencha enunciado e critérios. A soma precisa corresponder à pontuação total.');
      await saveStatement();const existing=currentRubric(),values=criteria();
      const same=existing&&JSON.stringify(values)===JSON.stringify(existing.criteria.map((r,i)=>({...r,max_points:String(r.max_points),order:i+1})));
      if(!same){
        doc=await request(`/dynamic/problems/${doc.problem.problem_id}/rubrics${existing?'/'+existing.rubric_id:''}`,{expected_revision:doc.revision,statement_version:doc.statements.at(-1).version_number,max_score:total.value,criteria:values},existing?'PATCH':'POST');
        // New server warnings must be read, even if an earlier version was acknowledged.
        reading.checked=false;
        for(const row of rows){const saved=currentRubric().criteria.find(c=>c.criterion_id===row.id);row.original=saved;row.title.value=saved.title;row.description.value=saved.description;row.points.value=String(saved.max_points);}
      }
    }
    async function perform(fn){
      if(busy||disposed)return;busy=true;setBusy(true);update();message.textContent='Salvando…';
      try{await fn();}catch(error){approved=false;if(!disposed)message.textContent=error.message;}
      finally{busy=false;if(!disposed){setBusy(false);update();}}
    }
    async function load(id){
      try{
        caps=await request('/dynamic/capabilities').catch(()=>({}));if(disposed)return;
        capability.textContent=caps.rubric_suggestion_configured?'A sugestão por IA não aprova a rubrica. Leia e aprove antes da correção.':'Sugestão por IA indisponível neste ambiente. Escreva sua rubrica.';
        if(id){doc=await request(`/dynamic/problems/${encodeURIComponent(id)}`);if(disposed)return;const last=doc.statements.at(-1);title.value=last.title||'';statement.value=last.statement;total.value=last.max_score;doc.rubrics.forEach(r=>r.criteria.forEach(c=>usedIds.add(c.criterion_id)));replaceRows(currentRubric()?.criteria||[]);approved=currentRubric()?.status==='APPROVED'&&Boolean(doc.current_configuration);showConfig=!approved;showWarnings();if(doc.correction_available===false)message.textContent='A correção ainda não está disponível para esta configuração. Confira as pendências.';}
        else if(!rows.length)addRow();update();
      }catch(error){if(!disposed){message.textContent=error.message;update();}}
    }
    addRow();update();return {load,cancel(){disposed=true;intake.cancel();},loadAutomaticCase:id=>intake.loadAutomaticCase(id)};
  }
  root.ConfIADynamicDirect={create};
})(window);
