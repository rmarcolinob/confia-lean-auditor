/* Full-exam capture in the existing TME shell. No OCR, scoring or new visual system. */
(function (root) {
  "use strict";
  function create(h) {
    const { node: n, btn, api, post, show, openExam, openQuestion, legacy, setBusy } = h;
    const Views = root.ConfiaTmeViews, Workspace = root.ConfiaCorrectionWorkspace;
    const field = (label, input) => { const el = n("label", label); el.append(input); return el; };
    const row = (...children) => { const el = n("div", undefined, "actions"); el.append(...children); return el; };
    const message = value => { const el = n("p", value, "message"); el.setAttribute("role", "status"); return el; };
    const key = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const asBase64 = file => new Promise((resolve, reject) => {
      const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]);
      reader.onerror = () => reject(new Error("Não foi possível ler o arquivo.")); reader.readAsDataURL(file);
    });
    const assetURL = (exam, id) => `/tme/exam-submissions/${exam}/assets/${id}`;
    let generation = 0;

    async function newCorrection() {
      const ticket = ++generation;
      const box = Views.Page("Nova correção", "Selecione a avaliação e envie a prova completa.");
      const content = n("div"); content.append(Views.Loading()); box.append(content); show(box);
      let assessments;
      try { assessments = await api("/tme/assessments"); }
      catch (_) { if(ticket===generation) content.replaceChildren(Views.ErrorState("Não foi possível carregar as avaliações.", newCorrection)); return; }
      if(ticket!==generation)return;
      content.replaceChildren();
      const form = n("form", undefined, "tme-new-form"), select = n("select"); select.required = true;
      select.setAttribute("aria-label", "Avaliação"); select.dataset.examField="assessment";
      const empty = n("option", "Selecione uma avaliação"); empty.value=""; select.append(empty);
      for(const doc of assessments){const option=n("option",doc.assessment.title);option.value=doc.assessment.assessment_id;select.append(option);}
      const code=n("input");code.required=true;code.maxLength=80;code.pattern="[A-Za-z0-9._:/-]+";code.autocomplete="off";code.placeholder="Ex.: PROVA-2026-0001";code.dataset.examField="participant";
      const generate=btn("Gerar código",()=>{code.value=`PROVA-${key().slice(0,8).toUpperCase()}`;invalidate();},"secondary");
      const files=n("input");files.type="file";files.multiple=true;files.accept="application/pdf,image/jpeg,image/png,image/webp";files.dataset.examField="files";
      const selected=n("div",undefined,"tme-upload-list"), error=message("");
      let documents=[],requestKey=key(),busy=false;
      function invalidate(){requestKey=key();}
      select.addEventListener("change",invalidate);code.addEventListener("input",invalidate);
      function renderFiles(){
        selected.replaceChildren();
        documents.forEach((doc,index)=>{
          const item=n("div",undefined,"card");item.append(n("p",`${index+1}. ${doc.file.name} · ${(doc.file.size/1024/1024).toFixed(1)} MiB`));
          const move=direction=>{const to=index+direction;if(to<0||to>=documents.length)return;[documents[index],documents[to]]=[documents[to],documents[index]];invalidate();renderFiles();};
          const before=btn("Mover antes",()=>move(-1),"secondary"),after=btn("Mover depois",()=>move(1),"secondary");before.disabled=index===0;after.disabled=index===documents.length-1;
          const controls=row(before,after,btn("Remover",()=>{documents.splice(index,1);invalidate();renderFiles();},"secondary"));
          if(doc.file.type!=="application/pdf")controls.append(btn(`Girar 90° · ${doc.rotation}°`,()=>{doc.rotation=(doc.rotation+90)%360;invalidate();renderFiles();},"secondary"));
          item.append(controls);selected.append(item);
        });
      }
      files.addEventListener("change",()=>{
        const incoming=Array.from(files.files||[]);
        const combined=[...documents,...incoming.map(file=>({file,rotation:0}))];
        if(combined.length>50||combined.some(d=>!["application/pdf","image/jpeg","image/png","image/webp"].includes(d.file.type)||!d.file.size||d.file.size>20*1024*1024)){
          error.textContent="Use um PDF ou até 50 imagens JPEG, PNG ou WebP, com até 20 MiB por arquivo.";files.value="";return;
        }
        if(combined.some(d=>d.file.type==="application/pdf")&&combined.length!==1){error.textContent="Envie um PDF ou um conjunto de imagens. Remova os arquivos atuais para trocar a origem.";files.value="";return;}
        if(combined.reduce((sum,d)=>sum+d.file.size,0)>40*1024*1024){error.textContent="A prova deve ter no máximo 40 MiB de originais.";files.value="";return;}
        documents=combined;invalidate();error.textContent="Confira a ordem dos arquivos antes de enviar.";files.value="";renderFiles();
      });
      const submit=btn("Receber prova", async()=>{
        if(busy||!form.reportValidity())return;
        if(!documents.length){error.textContent="Selecione um PDF ou as imagens da prova.";return;}
        busy=true;setBusy(true);submit.disabled=true;files.disabled=true;select.disabled=true;code.disabled=true;generate.disabled=true;
        for(const control of selected.querySelectorAll("button"))control.disabled=true;
        error.textContent="Preservando originais e preparando as páginas…";
        try{
          const original_documents=await Promise.all(documents.map(async d=>({media_type:d.file.type,content_base64:await asBase64(d.file),rotation_degrees:d.rotation})));
          const detail=await post("/tme/exam-submissions",{schema_version:"exam-capture-package.v1",assessment_identifier:select.value,external_participant_code:code.value.trim(),external_namespace:"tme",idempotency_key:requestKey,original_documents});
          busy=false;setBusy(false);await openExam(detail.submission.submission_id);
        }catch(e){error.textContent=e.message||"Não foi possível receber a prova. Os arquivos selecionados foram mantidos para tentar novamente.";}
        finally{busy=false;setBusy(false);submit.disabled=false;files.disabled=false;select.disabled=false;code.disabled=false;generate.disabled=false;renderFiles();}
      });
      form.addEventListener("submit",event=>{event.preventDefault();submit.click();});
      form.append(field("Avaliação",select),field("Código pseudônimo do participante / prova",code),row(generate),n("p","Não informe nome, CPF, e-mail ou matrícula. A identificação civil fica com a organização.","muted"),field("PDF ou imagens da prova",files),n("p","Até 50 páginas. O original é preservado; o recebimento não depende do reconhecimento da escrita.","muted"),selected,error,row(submit));
      if(!assessments.length){form.prepend(Views.Empty("Nenhuma avaliação disponível. Configure uma avaliação para este avaliador."));submit.disabled=true;}
      content.append(form,row(btn("Corrigir questão avulsa / escrita digital",()=>{if(!busy)return legacy();},"secondary")));
    }

    async function list(host,isCurrent=()=>true) {
      const ticket=generation;
      const records=await api("/tme/exam-submissions");
      if(!records.length||ticket!==generation||!isCurrent())return;
      const section=n("section",undefined,"tme-panel");section.append(n("h2","Provas recebidas"));
      for(const record of records){const item=btn(`${record.participant_code} · ${record.title} · ${record.page_count} páginas · ${record.question_count} questões${record.status==='FINALIZED'?` · Finalizada · Final ${points(record.final_total)} · ${record.adjusted_question_count} ajustes · ${new Date(record.finalized_at).toLocaleDateString('pt-BR')}`:record.status==='REOPENED'?' · Reaberta':''}`,()=>record.status==='FINALIZED'?summary(record.submission_id):openExam(record.submission_id),"tme-button secondary");section.append(row(item));}
      host.prepend(section);
    }

    const points=value=>value==null?'—':Number(value).toLocaleString('pt-BR',{maximumFractionDigits:2});
    const delta=value=>value==null?'—':Number(value)===0?'—':`${Number(value)>0?'+':''}${points(value)}`;
    const requests=new Map();
    function questionTable(questions,examId,historical=false){
      const wrapper=n('div'),table=n('table');wrapper.style.overflowX='auto';
      table.append(n('caption','Sugestão ConfIA e decisão humana por questão'));
      const head=n('thead'),headers=n('tr');
      for(const label of ['Questão','ConfIA','Final','Ajuste','Status'])headers.append(n('th',label));head.append(headers);table.append(head);
      const body=n('tbody');
      for(const q of questions){const tr=n('tr'),question=n('td');
        question.append(historical?n('span',`Q${q.question_order}`):btn(`Q${q.question_order}`,()=>openExam(examId,q.question_attempt_id),'secondary'));
        tr.append(question,n('td',q.suggested_score==null?'—':`${points(q.suggested_score)} / ${points(q.max_score)}`),n('td',q.final_score==null?'—':`${points(q.final_score)} / ${points(q.max_score)}`),n('td',delta(q.adjustment)),n('td',q.status==='CONFIRMED'||historical?q.review_required?'Confirmada após revisão':'Confirmada':q.blocker||'Pendente'));
        body.append(tr);
      }table.append(body);wrapper.append(table);return wrapper;
    }
    async function summary(examId,notice=''){
      const ticket=++generation;show(Views.Loading());
      let data;
      try{data=await api(`/tme/exam-submissions/${examId}/correction`);}
      catch(_){if(ticket===generation)show(Views.ErrorState('Não foi possível carregar o resumo da correção.',()=>summary(examId)));return;}
      if(ticket!==generation)return;
      const current=data.current_final_correction;
      const box=Views.Page(current?'Correção finalizada':'Resumo da correção',`${data.participant_code} · ${data.assessment_title}`);
      const panel=n('section',undefined,'queue');
      panel.append(n('h2',current?'Finalizada':data.status==='REOPENED'?'Correção reaberta':'Confira antes de finalizar'));
      if(notice)panel.append(message(notice));
      panel.append(questionTable(data.questions,examId));
      const totals=n('div',undefined,'card');
      totals.append(n('p',`ConfIA${data.suggested_total_complete?'':' parcial — incompleto'}: ${points(data.suggested_total)} / ${points(data.max_total)}`),
        n('p',`${data.final_total_complete?'Final humano':'Confirmado parcial'}: ${points(data.final_total)} / ${points(data.max_total)}`),
        n('p',`Ajuste total: ${delta(data.total_adjustment)}`),n('p',`${data.adjusted_question_count} de ${data.question_count} questões tiveram ajuste humano`),
        n('p',`${data.confirmed_question_count} confirmadas · ${data.pending_question_count} pendentes · ${data.unconfirmed_review_question_count} em revisão · ${data.review_question_count} com alerta ConfIA`));
      panel.append(totals);
      if(current)panel.append(message(`Finalizada em ${new Date(current.finalized_at).toLocaleString('pt-BR')} por ${current.finalized_by} · versão ${current.version}. Reabra explicitamente antes de alterar a prova.`));
      if(data.blockers.length){const pending=n('section',undefined,'card');pending.append(n('h3','Não é possível finalizar.'));
        for(const q of data.blockers)pending.append(n('p',`Q${q.question_order}: ${q.reason}`),btn(`Abrir Q${q.question_order} pendente`,()=>openExam(examId,q.question_attempt_id),'secondary'));
        panel.append(pending);
      }
      let busy=false;
      const controls=row(),confirmation=n('section',undefined,'card');confirmation.hidden=true;
      async function act(reopen){
        if(busy)return;busy=true;setBusy(true);
        for(const b of panel.querySelectorAll('button'))b.disabled=true;
        const body=reopen?{final_correction_id:current.final_correction_id}:{expected_snapshot_sha256:data.snapshot_sha256};
        const signature=JSON.stringify({examId,reopen,body});if(!requests.has(signature))requests.set(signature,key());
        let feedback;
        try{await post(`/tme/exam-submissions/${examId}/correction/${reopen?'reopen':'finalize'}`,{...body,execution_key:requests.get(signature)});
          requests.delete(signature);feedback=reopen?'Correção reaberta. O fechamento anterior foi preservado.':'Correção finalizada. Snapshot e totais preservados.';
        }catch(error){feedback=error.status===409?'A prova mudou ou possui pendências. Confira o resumo atualizado antes de confirmar.':'Não foi possível registrar o fechamento. Confira o estado atual e tente novamente.';if(error.status===409)requests.delete(signature);}
        finally{busy=false;setBusy(false);}
        return summary(examId,feedback);
      }
      if(current){controls.append(btn('Reabrir correção',()=>{confirmation.hidden=false;confirmation.replaceChildren(message('Reabrir permitirá alterações. Este fechamento continuará no histórico.'),btn('Confirmar reabertura',()=>act(true)),btn('Cancelar',()=>{confirmation.hidden=true;},'secondary'));},'secondary'));}
      else{const finish=btn('Finalizar correção',()=>{confirmation.hidden=false;confirmation.replaceChildren(message(`Confirme o fechamento de ${data.question_count} questões com nota final ${points(data.final_total)} / ${points(data.max_total)}.`),btn('Confirmar finalização',()=>act(false)),btn('Cancelar',()=>{confirmation.hidden=true;},'secondary'));});finish.disabled=!data.ready_to_finalize;controls.append(finish);}
      controls.append(btn('Voltar à prova',()=>openExam(examId),'secondary'));panel.append(controls,confirmation);
      const history=n('details');history.append(n('summary',`Histórico de fechamento (${data.final_corrections.length})`));
      for(const f of data.final_corrections){const entry=n('details');entry.append(n('summary',`Versão ${f.version} · Final ${points(f.final_total)} / ${points(f.max_total)} · ${new Date(f.finalized_at).toLocaleString('pt-BR')}`),n('p',`${f.participant_code} · ${f.assessment_title} · ${f.finalized_by}`),questionTable(f.questions,examId,true),n('p',`ConfIA ${points(f.suggested_total_snapshot)} · Final ${points(f.final_total)} · Ajuste ${delta(f.total_adjustment)}`));history.append(entry);}
      panel.append(history);box.append(panel);show(box);
    }

    function pageCard(examId, page){
      const item=n("section",undefined,"card photo"),img=n("img");
      img.src=assetURL(examId,page.preview_asset_id);img.alt=`Página ${page.page_number} da prova`;img.loading="lazy";
      const original=n("a",`Abrir original · página ${page.page_number}`);original.href=assetURL(examId,page.original_asset_id)+(page.original_page_number?`#page=${page.original_page_number}`:"");original.target="_blank";original.rel="noopener";
      item.append(n("h3",`Página ${page.page_number}`),img,original);return item;
    }

    async function open(examId, attemptId){
      const ticket=++generation;
      show(Views.Loading());
      try{
        const detail=await api(`/tme/exam-submissions/${examId}`);
        const question=attemptId?await api(`/tme/question-attempts/${attemptId}`):null;
        if(ticket!==generation)return;
        if(question&&question.question_attempt.exam_submission_id!==examId)throw new Error("Questão fora desta prova.");
        const box=Views.Page(Workspace.displayExamName(detail.participant.external_code),detail.assessment.assessment.title);
        const intro=message(`${detail.submission.page_count} páginas preservadas · ${detail.question_attempts.length} questões esperadas`);
        const originals=row();
        for(const asset of detail.submission.original_documents){const link=n("a",`Original ${originals.children.length+1}`,"tme-button secondary");link.href=assetURL(examId,asset.asset_id);link.target="_blank";link.rel="noopener";originals.append(link);}
        box.append(intro,originals,row(btn("Resumo da correção",()=>summary(examId),"secondary")));
        if(question)return await openQuestion(question.question_attempt,detail,question);
        const grid=n("div",undefined,"scan-grid");detail.submission.pages.forEach(page=>grid.append(pageCard(examId,page)));box.append(grid);
        const mapping=n("section",undefined,"tme-panel"),status=message("Uma página pode ser associada a mais de uma questão.");mapping.append(n("h2","Questões e páginas"),status);
        let dirty=false,busy=false;const checks=[];const openButtons=[];
        for(const attempt of detail.question_attempts){
          const group=n("fieldset",undefined,"card");group.append(n("legend",`Q${attempt.question_order} · ${attempt.problem_id} · máximo ${attempt.max_score}`));
          const choices=row();
          for(const page of detail.submission.pages){const input=n("input");input.type="checkbox";input.checked=detail.mapping.bindings.some(b=>b.question_attempt_id===attempt.case_id&&b.exam_page_id===page.exam_page_id);input.dataset.attempt=attempt.case_id;input.dataset.page=page.exam_page_id;input.addEventListener("change",()=>{dirty=true;status.textContent="Associação alterada. Salve antes de abrir a questão.";});checks.push(input);choices.append(field(`Página ${page.page_number}`,input));}
          const go=btn(`Abrir Q${attempt.question_order}`,()=>{if(dirty){status.textContent="Salve as associações antes de abrir a questão.";return;}return openExam(examId,attempt.case_id);},"secondary");openButtons.push(go);group.append(choices,row(go));mapping.append(group);
        }
        const save=btn("Salvar associações",async()=>{
          if(busy)return;busy=true;setBusy(true);save.disabled=true;checks.forEach(c=>c.disabled=true);openButtons.forEach(c=>c.disabled=true);
          const bindings=[];
          for(const attempt of detail.question_attempts){let order=0;for(const check of checks.filter(c=>c.dataset.attempt===attempt.case_id&&c.checked))bindings.push({question_attempt_id:attempt.case_id,exam_page_id:check.dataset.page,order:++order});}
          try{detail.mapping=await api(`/tme/exam-submissions/${examId}/page-mapping`,{method:"PUT",body:JSON.stringify({expected_version:detail.mapping.version,bindings})});dirty=false;status.textContent="Associações salvas. Abra uma questão para conferir suas páginas.";}
          catch(e){status.textContent=e.message;}
          finally{busy=false;setBusy(false);save.disabled=false;checks.forEach(c=>c.disabled=false);openButtons.forEach(c=>c.disabled=false);}
        });
        if(detail.correction_status==="FINALIZED"){save.disabled=true;checks.forEach(c=>c.disabled=true);status.textContent="Prova finalizada. Reabra a correção no resumo para alterar.";}
        mapping.append(row(save));box.append(mapping);show(box);
      }catch(_){if(ticket===generation)show(Views.ErrorState("Não foi possível abrir esta prova.",()=>open(examId,attemptId)));}
    }
    return {newCorrection,list,open,summary,cancel:()=>{generation++;}};
  }
  root.ConfiaFullExam={create};
})(window);
