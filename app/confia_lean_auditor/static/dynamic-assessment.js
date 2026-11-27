/* Dynamic preparation only. Correction and closure use the shared exam workspace. */
(function(root){
  function create({host,setBusy=()=>{},onSelect=()=>{},onOpenExam=()=>{},onUpload=()=>{},simplified=false}){
    let doc=null,busy=false,disposed=false,editor=null,notice='',step='home',generation=0,capabilities=null;
    const panel=document.createElement('section');panel.className='dynamic-workflow';host.append(panel);
    const n=(tag,text,cls)=>{const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;};
    const input=(label,value='',type='text')=>{const x=n(type==='textarea'?'textarea':'input');if(type!=='textarea')x.type=type;x.value=value;x.setAttribute('aria-label',label);return x;};
    const field=(label,x)=>{const wrap=n('label',label);wrap.append(x);return wrap;};
    const button=(title,action)=>{const b=n('button',title,'tme-button');b.type='button';b.disabled=busy;b.addEventListener('click',action);return b;};
    const select=(label,options,value)=>{const s=n('select');s.setAttribute('aria-label',label);for(const [v,t] of options){const o=n('option',t);o.value=v;s.append(o);}s.value=value;return s;};
    async function request(url,body){const response=await fetch(url,{credentials:'same-origin',...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:data.detail?.message||'Não foi possível concluir. Recarregue e tente novamente.');return data;}
    async function perform(action){
      if(busy||disposed)return;
      busy=true;setBusy(true);let failed=false;
      const controls=[...panel.querySelectorAll('button,input,textarea,select')].map(c=>[c,c.disabled]);
      controls.forEach(([c])=>c.disabled=true);
      try{await action();}catch(e){failed=true;notice=e.message;}
      finally{
        busy=false;setBusy(false);
        if(!disposed){
          if(failed&&simplified){
            controls.forEach(([c,disabled])=>c.disabled=disabled);
            const status=panel.querySelectorAll('[role=status]')[0];if(status)status.textContent=notice;
          }else await render();
        }
      }
    }
    async function refresh(){if(doc)doc=await request(`/dynamic/assessments/${doc.assessment.assessment_id}`);}
    function generalForm(){
      const form=n('form',undefined,'tme-new-form'),title=input('Título da avaliação'),instructions=input('Orientações','','textarea');title.required=true;title.maxLength=160;
      const type=select('Tipo da avaliação',[['FORMATIVE_LIST','Lista/atividade'],['SCHOOL_EXAM','Prova escolar']],'SCHOOL_EXAM');
      const feedback=select('Feedback ao aluno',[['WITHHOLD','Reter feedback'],['AFTER_CONFIRMATION','Disponibilizar após confirmação docente']],'WITHHOLD');
      form.append(n('h2','Dados da avaliação'),field('Título',title),field('Tipo',type),field('Orientações',instructions),field('Feedback ao aluno',feedback));
      const submit=n('button',simplified?'Salvar e adicionar questões':'Criar avaliação','tme-button');submit.type='submit';submit.disabled=busy;form.append(submit);
      form.addEventListener('submit',event=>{event.preventDefault();return perform(async()=>{doc=await request('/dynamic/assessments',{title:title.value,instructions:instructions.value,policy_profile:type.value,feedback_policy:feedback.value});onSelect(doc.assessment.assessment_id);notice='Avaliação criada. Adicione as questões.';});});return form;
    }
    async function editQuestion(pid){
      if(busy)return;panel.replaceChildren();
      const back=button('Voltar à avaliação',async()=>{editor?.cancel();editor=null;await refresh();await render();});panel.append(back);
      const content=n('div');panel.append(content);
      editor=root.ConfIADynamic.create({host:content,assessmentOnly:true,simplified,setBusy:value=>{busy=value;setBusy(value);back.disabled=value;},onSelect:()=>{},onOpenAttempt:()=>{}});
      await editor.load(pid);
    }
    function questionForm(){
      const form=n('form',undefined,'tme-new-form'),title=input('Título da questão'),statement=input('Enunciado da questão','','textarea'),points=input('Pontos da questão',simplified?'2':'10','number');statement.required=true;statement.maxLength=20000;statement.rows=5;points.min='0.01';points.max='1000';points.step='0.01';points.required=true;
      form.append(n('h3','Adicionar questão inédita'),field('Título da questão',title),field('Enunciado',statement),field('Pontos',points));
      const submit=n('button','Adicionar questão','tme-button');submit.type='submit';submit.disabled=busy;form.append(submit);
      form.addEventListener('submit',event=>{event.preventDefault();return perform(async()=>{const problem=await request('/dynamic/problems',{title:title.value,statement:statement.value,max_score:points.value,correction_mode:'DYNAMIC'});doc=await request(`/dynamic/assessments/${doc.assessment.assessment_id}/questions`,{problem_id:problem.problem.problem_id,expected_revision:doc.dynamic_revision});notice='Questão adicionada. Prepare e revise sua rubrica.';});});return form;
    }
    async function prepareQuestions(){
      await perform(async()=>{
        const ids=doc.readiness.questions.filter(q=>!q.ready).map(q=>q.problem_id);
        for(let i=0;i<ids.length;i++){
          notice=`Preparando questão ${i+1} de ${ids.length}…`;await render();
          doc=await request(`/dynamic/assessments/${doc.assessment.assessment_id}/preparations`,{problem_ids:[ids[i]],generate_rubrics:true});
        }
        notice='Preparações concluídas. Confira cada resultado e revise as rubricas antes de aprovar.';
      });
    }
    function receiveText(){
      const form=n('form',undefined,'tme-new-form'),code=input('Código pseudônimo do participante');code.required=true;code.pattern='[A-Za-z0-9._:/-]+';code.maxLength=80;
      form.append(n('h3','Receber soluções'),field('Código pseudônimo',code));
      const answers=doc.readiness.questions.map(q=>{const area=input(`Solução Q${q.order}`,'','textarea');area.required=true;area.maxLength=20000;area.rows=5;form.append(field(`Q${q.order} — ${q.title}`,area));return area;});
      const submit=n('button','Receber participante','tme-button');submit.type='submit';submit.disabled=busy;form.append(submit);
      form.addEventListener('submit',event=>{event.preventDefault();return perform(async()=>{
        const exam=await request('/tme/exam-submissions/text',{assessment_identifier:doc.assessment.assessment_id,external_participant_code:code.value,idempotency_key:root.crypto.randomUUID(),solutions:answers.map(a=>a.value)});
        busy=false;setBusy(false);
        notice='Soluções recebidas. Confira a transcrição e siga a correção compartilhada.';onOpenExam(exam.submission.submission_id);
      });});return form;
    }
    async function publicationForm(){
      const form=n('form',undefined,'tme-new-form');panel.append(form);form.append(n('h3','Disponibilizar aos alunos'));
      try{
        const schools=await request('/institutional/me/schools');
        const school=select('Escola',schools.map(s=>[s.school_id,s.name]),schools[0]?.school_id),classroom=select('Turma',[],'');
        async function classes(){const rows=await request(`/institutional/schools/${school.value}/classrooms`);classroom.replaceChildren();for(const c of rows){const o=n('option',`${c.name} · ${c.grade}`);o.value=c.classroom_id;classroom.append(o);}}
        school.addEventListener('change',()=>classes().catch(e=>notice=e.message));await classes();
        const start=input('Início','','datetime-local'),end=input('Prazo final','','datetime-local');
        const local=d=>new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);
        start.value=local(new Date());end.value=local(new Date(Date.now()+7*86400000));start.required=end.required=true;
        const attempts=input('Limite de tentativas','1','number');attempts.min=1;attempts.max=10;attempts.required=true;
        const grade=input('Ano escolar','9','number');grade.min=6;grade.max=12;grade.required=true;
        const feedback=select('Divulgação de explicações',doc.assessment.dynamic_policy_profile==='FORMATIVE_LIST'?[['TEACHER_RELEASE','Somente após divulgação docente'],['GUIDANCE','Orientações formativas automáticas, sem solução completa'],['WITHHOLD','Reter explicações']]:[['TEACHER_RELEASE','Somente após divulgação docente'],['WITHHOLD','Reter explicações']],'TEACHER_RELEASE');
        const inputs=['TEXT','IMAGES','PDF'].map((v,i)=>{const c=input(['Permitir texto','Permitir fotografias','Permitir PDF'][i],'','checkbox');c.checked=true;form.append(field(['Permitir texto','Permitir fotografias','Permitir PDF'][i],c));return {v,c};});
        form.append(field('Escola',school),field('Turma',classroom),field('Ano escolar',grade),field('Início',start),field('Prazo final',end),field('Limite de tentativas',attempts),field('Divulgação de explicações',feedback),n('p','A publicação cria uma atividade institucional com versões fixadas. Notas sempre exigem confirmação e divulgação docente.'));
        const consent=input('Conferi as versões e as políticas','','checkbox');consent.required=true;form.append(field('Conferi as versões e as políticas',consent));
        const submit=n('button','Publicar para a turma','tme-button');submit.type='submit';form.append(submit);const key=root.crypto.randomUUID();
        form.addEventListener('submit',e=>{e.preventDefault();perform(async()=>{const result=await request(`/dynamic/assessments/${doc.assessment.assessment_id}/institutional-publications`,{source_definition_sha256:doc.assessment.definition_sha256,school_id:school.value,classroom_id:classroom.value,opens_at:new Date(start.value).toISOString(),closes_at:new Date(end.value).toISOString(),policy:{grade_year:Number(grade.value),max_attempts:Number(attempts.value),feedback:feedback.value,allowed_inputs:inputs.filter(x=>x.c.checked).map(x=>x.v)},execution_key:key});doc=await request(`/dynamic/assessments/${result.assessment.assessment_id}`);onSelect(doc.assessment.assessment_id);notice='Atividade publicada para a turma. A definição original foi preservada.';});});
      }catch(e){form.append(n('p',e.message));}
    }
    async function releaseForm(eid){
      const form=n('form',undefined,'tme-new-form');panel.append(form);form.append(n('h3','Divulgação ao aluno'));
      try{
        const data=await request(`/tme/exam-submissions/${eid}/correction`),final=data.current_final_correction;
        if(!final){form.append(n('p','Confirme as questões e finalize a correção no workspace antes de divulgar.'));return;}
        const score=input('Divulgar nota confirmada','','checkbox'),feedback=input('Divulgar devolutiva','','checkbox'),text=input('Devolutiva pedagógica','','textarea');score.checked=true;
        feedback.disabled=doc.assessment.school_policy.feedback==='WITHHOLD';text.rows=6;
        form.append(n('p',`Nota confirmada: ${final.final_total} / ${final.max_total}`),field('Divulgar nota confirmada',score),field('Divulgar devolutiva',feedback),field('Devolutiva pedagógica',text));
        const submit=n('button','Confirmar divulgação','tme-button');submit.type='submit';form.append(submit);
        form.addEventListener('submit',e=>{e.preventDefault();perform(async()=>{await request(`/dynamic/school-attempts/${eid}/release`,{final_correction_id:final.final_correction_id,release_grade:score.checked,release_feedback:feedback.checked,teacher_feedback:text.value});notice='Divulgação registrada para esta correção confirmada.';});});
      }catch(e){form.append(n('p',e.message));}
    }
    const format=value=>Number(value||0).toLocaleString('pt-BR',{maximumFractionDigits:2});
    async function choose(value,id){
      if(busy||disposed)return;
      const ticket=++generation;
      step=value;notice='';
      try {if(id!==undefined){const next=id?await request(`/dynamic/assessments/${id}`):null;if(disposed||ticket!==generation)return;doc=next;}}
      catch(e){if(!disposed&&ticket===generation){notice=e.message;await render();}return;}
      if(disposed||ticket!==generation)return;
      onSelect(doc?.assessment.assessment_id||null,step);await render();
      panel.querySelectorAll('h2')[0]?.focus();
    }
    async function renderSimple(){
      const ticket=++generation;panel.replaceChildren();
      const nav=n('nav',undefined,'dynamic-main-actions');nav.setAttribute('aria-label','DYNAMIC docente');
      for(const [value,title,description] of [['register','Cadastrar avaliação','Enunciados, valores e rubricas aprovadas por você.'],['send','Enviar provas respondidas','Fotografias ou PDF, com conferência das respostas.'],['results','Consultar correções','Critérios, evidências e decisões docentes.']]){
        const b=button('',()=>choose(value,value==='register'?null:undefined));b.className='tme-panel dynamic-action';b.setAttribute('aria-label',title);b.setAttribute('aria-pressed',String(step===value));b.append(n('strong',title),n('span',description));nav.append(b);
      }
      const status=n('p',notice);status.setAttribute('role','status');status.setAttribute('aria-live','polite');panel.append(nav,status);
      if(!capabilities){try{capabilities=await request('/dynamic/capabilities');}catch(_){capabilities={unknown:true};}if(disposed||ticket!==generation)return;}
      const availability=n('aside',undefined,'dynamic-availability');
      if(capabilities.unknown)availability.append(n('p','Não foi possível consultar a disponibilidade da inferência. Você pode continuar o cadastro manual.'));
      else {
        if(!capabilities.rubric_suggestion_configured)availability.append(n('p','Sugestão por IA indisponível nesta instalação. Você pode informar, editar e aprovar sua rubrica.'));
        if(!capabilities.handwriting_recognition_configured)availability.append(n('p','Reconhecimento automático indisponível. Envie os originais e digite a transcrição para conferência.'));
        if(!capabilities.semantic_evaluation_configured)availability.append(n('p','Avaliação semântica indisponível. Verificações exatas continuam possíveis; os demais critérios poderão ficar pendentes de decisão docente.'));
        availability.append(n('p','A configuração de um serviço não garante sua disponibilidade. Nenhuma análise é uma nota escolar definitiva sem confirmação docente.'));
      }
      panel.append(availability);
      const body=n('section',undefined,'tme-panel dynamic-content');panel.append(body);
      if(!doc){
        if(step==='register')body.append(generalForm());
        const heading=n('h2',step==='send'?'Escolha a avaliação para enviar respostas':step==='results'?'Escolha a avaliação para consultar':'Suas avaliações');heading.tabIndex=-1;body.append(heading);
        try{
          const docs=await request('/dynamic/assessments');if(disposed||ticket!==generation)return;
          if(!docs.length)body.append(n('p','Nenhuma avaliação cadastrada. Comece em “Cadastrar avaliação”.'));
          for(const item of docs){
            const a=item.assessment,ready=a.status==='PUBLISHED'&&!a.superseded_by;
            const card=n('article',undefined,'dynamic-assessment-card');card.append(n('h3',a.title),n('p',`${a.dynamic_policy_profile==='FORMATIVE_LIST'?'Lista de exercícios':'Prova'} · ${item.readiness.total_questions} questões · ${ready?'Pronta para receber respostas':a.status==='DRAFT'?'Rascunho — confira as rubricas':'Encerrada'}`));
            const destination=a.status==='DRAFT'?'register':step==='send'?'send':'results';
            card.append(button(a.status==='DRAFT'?'Continuar cadastro':step==='send'?'Selecionar avaliação':'Ver correções',()=>choose(destination,a.assessment_id)));body.append(card);
          }
        }catch(e){status.textContent=e.message;}return;
      }
      const a=doc.assessment,r=doc.readiness,id=a.assessment_id;
      body.append(button('Todas as avaliações',()=>choose(step,null)));
      const heading=n('h2',a.title);heading.tabIndex=-1;body.append(heading,n('p',`${a.dynamic_policy_profile==='FORMATIVE_LIST'?'Lista de exercícios':'Prova'} · ${r.total_questions} questões · ${format(r.questions.reduce((sum,q)=>sum+Number(q.max_score||0),0))} pontos`));
      if(a.status==='DRAFT'){
        body.append(n('p','Adicione as questões, confira os critérios e aprove cada rubrica. Salvar a avaliação não a publica para os alunos.'));
        for(const q of r.questions){
          const card=n('article',undefined,'dynamic-assessment-card');card.append(n('h3',`Questão ${q.order} — ${q.title}`),n('p',q.statement,'dynamic-statement'),n('p',`${format(q.max_score)} pontos · ${q.rubric_status==='APPROVED'?'Rubrica aprovada':q.rubric_id?'Rubrica aguardando sua aprovação':'Informe ou solicite uma rubrica'}`),button(`Conferir rubrica da questão ${q.order}`,()=>editQuestion(q.problem_id)));body.append(card);
        }
        body.append(questionForm());
        const activate=button('Salvar avaliação aprovada',()=>perform(async()=>{doc=await request(`/dynamic/assessments/${id}/activate`,{expected_revision:doc.dynamic_revision});step='send';onSelect(id,step);notice='Avaliação salva. Você já pode enviar respostas; a publicação aos alunos continua separada.';}));activate.disabled=busy||!r.ready;body.append(activate);
        if(!r.ready)body.append(n('p','A correção ficará disponível quando todas as questões tiverem rubricas aprovadas e estiverem prontas.'));
      }else if(step==='send'){
        if(r.state==='ACTIVE'&&a.scope!=='INSTITUTIONAL'){
          body.append(n('h3','Uma prova por participante'),n('p','Envie um PDF de até 50 páginas ou até 50 fotografias de uma mesma prova. Separe as provas de participantes diferentes. O envio em lote com identificação automática ainda não está disponível.'),n('p','Recomendamos espaços identificados por questão no papel. Você poderá associar as páginas manualmente; uma página pode conter mais de uma resposta.'),button('Enviar fotografias ou PDF',()=>onUpload(id)));
          const text=n('details');text.append(n('summary','Inserir respostas digitadas'),receiveText());body.append(text);
        }else body.append(n('p',a.scope==='INSTITUTIONAL'?'Esta atividade é recebida pelo módulo do aluno, respeitando as tentativas e permissões da turma. Consulte as respostas em “Consultar correções”.':'Esta avaliação está encerrada. Consulte as correções existentes.'));
      }else{
        body.append(n('h3','Provas recebidas'),n('p','As sugestões automáticas não são notas finais. Confira as questões e registre sua decisão antes de finalizar ou divulgar.'));
        try{
          const exams=(await request('/tme/exam-submissions')).filter(e=>e.assessment_id===id);if(disposed||ticket!==generation)return;
          if(!exams.length)body.append(n('p','Nenhuma resposta recebida para esta avaliação.'));
          for(const exam of exams){const card=n('article',undefined,'dynamic-assessment-card');card.append(n('h3',exam.participant_code),n('p',`${exam.page_count||0} páginas · ${exam.status==='FINALIZED'?'Correção finalizada':exam.status==='REOPENED'?'Correção reaberta':'Conferência ou correção pendente'}`),button('Abrir prova e correção',()=>onOpenExam(exam.submission_id)));if(a.scope==='INSTITUTIONAL')card.append(button('Divulgar resultado confirmado',()=>releaseForm(exam.submission_id)));body.append(card);}
        }catch(e){status.textContent=e.message;}
      }
      const audit=n('details');audit.append(n('summary','Auditoria e evidências'),n('p','Versões, vínculos e estados registrados pelo backend. Pendências não são convertidas em nota zero.'),n('pre',JSON.stringify({readiness:r,events:doc.events},null,2)));body.append(audit);
      if(a.status==='PUBLISHED'&&a.scope!=='INSTITUTIONAL'&&r.state==='ACTIVE'){
        const publication=n('details');publication.append(n('summary','Publicação e próximas versões'),n('p','Disponibilizar aos alunos é uma decisão explícita, separada do cadastro.'),button('Disponibilizar aos alunos',publicationForm),button('Preparar nova versão da avaliação',()=>perform(async()=>{doc=await request(`/dynamic/assessments/${id}/successor`,{});step='register';onSelect(doc.assessment.assessment_id,step);notice='Novo rascunho criado; as respostas anteriores permanecem vinculadas à avaliação original.';})));body.append(publication);
      }
    }
    async function render(){
      if(disposed||editor)return;
      if(simplified)return renderSimple();
      if(disposed||editor)return;panel.replaceChildren();const status=n('p',notice);status.setAttribute('role','status');status.setAttribute('aria-live','polite');panel.append(status);
      if(!doc){panel.append(generalForm());const resume=n('section');resume.append(n('h3','Retomar avaliação'));panel.append(resume);try{const docs=await request('/dynamic/assessments');if(disposed)return;for(const item of docs)resume.append(button(`${item.assessment.title} · ${item.assessment.scope==='INSTITUTIONAL'?'Turma '+item.assessment.classroom_id:'Preparação docente'} · ${item.readiness.state}`,()=>load(item.assessment.assessment_id)));}catch(e){status.textContent=e.message;}return;}
      const a=doc.assessment,r=doc.readiness,id=a.assessment_id;panel.append(button('Nova avaliação',()=>{doc=null;onSelect(null);render();}),n('h2',a.title),n('p',`${a.dynamic_policy_profile==='FORMATIVE_LIST'?'Lista/atividade':'Prova escolar'} · ${r.state} · ${r.ready_questions}/${r.total_questions} questões prontas`));
      const table=n('table');table.className='tme-table';const header=n('tr');for(const text of ['Questão','Preparação','Rubrica','Prontidão','Revisão docente'])header.append(n('th',text));table.append(header);const selected=[];
      for(const q of r.questions){const row=n('tr');row.append(n('td',`Q${q.order} — ${q.title}`),n('td',q.preparation_status),n('td',q.rubric_status),n('td',q.ready?'Pronta':q.blockers.join(' ')));const actions=n('td');
        if(a.status==='DRAFT'){actions.append(button(`Revisar Q${q.order}`,()=>editQuestion(q.problem_id)));if(q.rubric_id&&q.rubric_status!=='APPROVED'){const check=input(`Revisei a rubrica Q${q.order}`,'','checkbox');check.disabled=busy;actions.append(field('Revisei esta rubrica',check));selected.push({q,check});}}
        else actions.append(n('span',`Enunciado V${q.statement_version} fixado${q.newer_version_available?' · nova versão disponível':''}`));row.append(actions);table.append(row);}
      panel.append(table);
      if(a.status==='DRAFT'){
        panel.append(questionForm(),button('Preparar questões pendentes',prepareQuestions),button('Atualizar prontidão',()=>perform(refresh)));
        const approve=button('Aprovar rubricas selecionadas',()=>perform(async()=>{const choices=selected.filter(x=>x.check.checked).map(({q})=>({problem_id:q.problem_id,rubric_id:q.rubric_id,expected_revision:q.problem_revision,acknowledge_warnings:true}));if(!choices.length)throw new Error('Selecione somente rubricas que você revisou.');doc=await request(`/dynamic/assessments/${id}/rubrics/approve`,{questions:choices});notice='Aprovações explícitas registradas; confira a prontidão.';}));panel.append(approve);
        const activate=button('Ativar avaliação',()=>perform(async()=>{doc=await request(`/dynamic/assessments/${id}/activate`,{expected_revision:doc.dynamic_revision});notice='Avaliação ativa. Versões publicadas preservadas para as submissões.';}));activate.disabled=busy||!r.ready;panel.append(activate);
      }else{
        panel.append(n('p','As correções usam as versões desta publicação. Novas versões exigem uma nova ativação; as submissões anteriores não serão reprocessadas automaticamente.'));
        if(r.state==='ACTIVE'&&a.scope!=='INSTITUTIONAL'){panel.append(button('Disponibilizar aos alunos',publicationForm),button('Enviar fotografias ou PDF',()=>onUpload(id)),receiveText(),button('Preparar nova versão da avaliação',()=>perform(async()=>{doc=await request(`/dynamic/assessments/${id}/successor`,{});onSelect(doc.assessment.assessment_id);notice='Nova versão em rascunho. Revise antes de ativar.';})));}
        const students=n('section');students.append(n('h3','Participantes e correções'));panel.append(students);
        try{for(const exam of (await request('/tme/exam-submissions')).filter(e=>e.assessment_id===id)){students.append(button(`${exam.participant_code} · ${exam.status}`,()=>onOpenExam(exam.submission_id)));if(a.scope==='INSTITUTIONAL')students.append(button(`Divulgar resultado · ${exam.participant_code}`,()=>releaseForm(exam.submission_id)));}}catch(e){students.append(n('p',e.message));}
      }
    }
    async function load(id,section){const ticket=++generation;const value=id?await request(`/dynamic/assessments/${id}`):null;if(disposed||ticket!==generation)return;doc=value;step=['register','send','results'].includes(section)?section:doc?(doc.assessment.status==='DRAFT'?'register':'results'):'home';onSelect(id||null,simplified?step:undefined);await render();}
    return {load,cancel(){disposed=true;++generation;editor?.cancel();}};
  }
  root.ConfIADynamicAssessment={create};
})(window);
