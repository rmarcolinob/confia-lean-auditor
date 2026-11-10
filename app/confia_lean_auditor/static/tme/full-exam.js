/* Full-exam capture in the existing TME shell. No OCR, scoring or new visual system. */
(function (root) {
  "use strict";
  function create(h) {
    const { node: n, btn, api, post, show, openExam, legacy, setBusy } = h;
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

    async function list(host) {
      const records=await api("/tme/exam-submissions");
      if(!records.length)return;
      const section=n("section",undefined,"tme-panel");section.append(n("h2","Provas recebidas"));
      for(const record of records){const item=btn(`${record.participant_code} · ${record.title} · ${record.page_count} páginas · ${record.question_count} questões`,()=>openExam(record.submission_id),"tme-button secondary");section.append(row(item));}
      host.prepend(section);
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
        box.append(intro,originals);
        if(question){
          const c=question.question_attempt;
          const context=n("header",undefined,"case-context");
          context.append(n("h2",`Questão ${c.question_order} · ${c.problem_id}`),n("p",`Pontuação máxima: ${c.max_score}`,"muted"));
          const nav=Workspace.QuestionNavigator?Workspace.QuestionNavigator(c,detail.question_attempts,()=>"Recebida",id=>openExam(examId,id),false):null;
          if(nav)context.append(nav);
          else{const choices=row();for(const item of detail.question_attempts){const button=btn(`Q${item.question_order}`,()=>openExam(examId,item.case_id),"secondary");button.setAttribute("aria-current",item.case_id===c.case_id?"page":"false");choices.append(button);}context.append(choices);}
          box.append(context);
          const catalog=await api("/tme/problems");if(ticket!==generation)return;
          const statement=Workspace.ProblemStatement(catalog.find(p=>(p.problem_id||p.id)===c.problem_id),{},[]);box.append(statement);
          box.append(row(btn("Voltar às páginas e associações",()=>openExam(examId),"secondary")),n("h2","Original"));
          const grid=n("div",undefined,"scan-grid");question.pages.forEach(page=>grid.append(pageCard(examId,page)));box.append(grid);
          if(!question.pages.length)box.append(message("Esta questão ainda não tem páginas associadas. Volte às páginas e associações para selecioná-las."));
          show(box);statement.updateStatementLayout?.();return;
        }
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
        });mapping.append(row(save));box.append(mapping);show(box);
      }catch(_){if(ticket===generation)show(Views.ErrorState("Não foi possível abrir esta prova.",()=>open(examId,attemptId)));}
    }
    return {newCorrection,list,open,cancel:()=>{generation++;}};
  }
  root.ConfiaFullExam={create};
})(window);
