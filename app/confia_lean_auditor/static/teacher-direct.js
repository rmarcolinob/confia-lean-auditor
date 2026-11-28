/* Direct UI orchestration; existing stores, acceptance, engines and reports own all results. */
(function(root){
  'use strict';
  const confirmation='Conferi explicitamente a transcrição com a solução original antes da auditoria.';
  const n=(tag,text)=>{const el=document.createElement(tag);if(text!=null)el.textContent=text;return el;};
  const field=(text,el)=>{const label=n('label',text);label.append(el);return label;};
  async function request(url,body){
    const response=await fetch(url,body===undefined?{credentials:'same-origin'}:{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:data.detail?.message||'Não foi possível concluir. Seus dados foram mantidos.');return data;
  }
  function create({host,problemId,onOpen=()=>{},setBusy=()=>{},dynamic=false,ready=()=>true}){
    let busy=false,disposed=false,original=null,previewUrl=null,mode='image',attempt=null,attemptText=null,recognized=null,auditKey=null,generation=0;
    const form=n('form');form.className='dynamic-form tme-panel';
    const status=n('p'),result=n('section'),preview=n('div'),digital=n('div'),solution=n('textarea'),check=n('input');
    status.setAttribute('role','status');result.setAttribute('aria-label','Resultado da correção');result.setAttribute('aria-live','polite');
    solution.rows=8;solution.maxLength=20000;solution.setAttribute('aria-label','Solução já digital');check.type='checkbox';check.setAttribute('aria-label','Confirmo o texto da solução');
    const file=n('input');file.type='file';file.accept='application/pdf,image/jpeg,image/png,image/webp';file.setAttribute('aria-label','Fazer upload da solução');
    const camera=n('input');camera.type='file';camera.accept='image/*';camera.setAttribute('capture','environment');camera.setAttribute('aria-label','Tirar foto da solução');
    const photoButton=n('button','Foto ou upload'),textButton=n('button','Solução já digital');
    for(const button of [photoButton,textButton]){button.type='button';button.className='tme-button secondary';}
    const uploads=n('div');uploads.append(field('Tirar foto',camera),field('Fazer upload · PDF, JPG, PNG ou WebP',file),preview);
    const submit=n('button','Corrigir solução');submit.type='submit';submit.className='tme-button';
    digital.append(n('p','Para soluções que já existem em texto digital, cole o conteúdo abaixo. Não é necessário transcrever manuscritos: imagens aguardam a integração de leitura automática.'),field('Solução já digital',solution),field('Confirmo que este texto corresponde à solução a corrigir',check));
    form.append(n('h2','Solução do aluno'),photoButton,textButton,uploads,digital,status,submit);host.append(form,result);
    const pid=()=>typeof problemId==='function'?problemId():problemId;
    function release(){if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=null;}
    function update(){
      digital.hidden=mode==='image'&&!recognized;uploads.hidden=mode==='digital';
      photoButton.setAttribute('aria-pressed',String(mode==='image'));textButton.setAttribute('aria-pressed',String(mode==='digital'));
      submit.disabled=busy||!ready()||!check.checked||(!recognized&&mode!=='digital')||!solution.value.trim();
    }
    function choose(value){
      if(busy)return;mode=value;recognized=null;attempt=null;attemptText=null;auditKey=null;check.checked=false;solution.readOnly=false;result.replaceChildren();
      status.textContent=value==='image'?'Leitura automática de fotos e arquivos ainda indisponível neste percurso. O arquivo não será interpretado nem corrigido.':'Somente o texto digital será corrigido; nenhum arquivo será interpretado.';update();
    }
    photoButton.addEventListener('click',()=>choose('image'));textButton.addEventListener('click',()=>choose('digital'));
    check.addEventListener('change',update);solution.addEventListener('input',()=>{check.checked=false;attempt=null;attemptText=null;auditKey=null;result.replaceChildren();update();});
    async function selectFile(input){
      if(busy)return;choose('image');release();preview.replaceChildren();original=input.files?.[0]||null;
      if(!original)return;
      if(!['application/pdf','image/jpeg','image/png','image/webp'].includes(original.type)||original.size>20*1024*1024){input.value='';original=null;status.textContent='Use PDF, JPG, PNG ou WebP de até 20 MiB.';return;}
      previewUrl=URL.createObjectURL(original);const view=n(original.type==='application/pdf'?'iframe':'img');view.src=previewUrl;view.title='Solução original';view.alt='Solução original';view.style.width='100%';view.style.maxHeight='32rem';if(original.type==='application/pdf')view.style.height='32rem';
      preview.append(n('p',original.name),view);status.textContent='Original selecionado apenas para visualização local. Aguardando integração de leitura automática; nenhum texto ou nota foi gerado.';
    }
    file.addEventListener('change',()=>selectFile(file));camera.addEventListener('change',()=>selectFile(camera));
    async function history(c){const base=`/tme/cases/${c.case_id}`;const rows=await request(base+'/transcriptions');if(!rows.length)throw Error('Leitura automática ainda não disponível.');return request(base+'/transcriptions/'+rows[0].transcription.transcription_id);}
    function savedLink(c){const link=n('a','Consultar histórico e decisão docente');link.href=`/tme?case_id=${encodeURIComponent(c.case_id)}`;link.className='tme-button secondary';return link;}
    async function showRun(c,run){
      result.replaceChildren(n('h2','Resultado da correção'),savedLink(c));
      if(run.status!=='COMPLETED'||!run.result){result.append(n('p','Falha técnica da auditoria. Isso não indica erro matemático e não produz nota.'));return;}
      let rec=null,review=null,reviewError='';
      if(dynamic)try{
        const completed=await root.ConfIADynamicCorrection.complete({caseId:c.case_id,run,api:request,post:request});rec=completed?.reconciliation;
        const rows=await request(`/dynamic/attempts/${c.case_id}/audits/${run.audit_run_id}/independent-reviews`);review=rows.find(r=>!r.stale);
      }catch(error){reviewError='Grader preservado. Reviewer ou Reconciliation pendente; nenhuma nota final foi confirmada.';}
      if(disposed)return;
      const report=n('div');result.append(report);if(reviewError)result.append(n('p',reviewError));
      root.ConfIAReport.render(run.result,report,{context:'evaluator',auditRun:run,independentReview:review,reconciliation:rec,reviewError});
      result.append(n('p','Resultado automático sujeito à revisão docente. Nenhuma divulgação foi realizada.'));
    }
    form.addEventListener('submit',async event=>{
      event.preventDefault();update();if(submit.disabled||disposed)return;
      busy=true;setBusy(true);const controls=[...form.querySelectorAll('input,textarea,button')];controls.forEach(el=>el.disabled=true);
      try{
        if(!recognized && (!attempt||attemptText!==solution.value)){
          status.textContent='Preservando solução digital…';
          attempt=await request('/tme/direct-solutions',{problem_id:pid(),external_candidate_ref:'SOL-'+root.crypto.randomUUID(),solution:solution.value,allow_preparation_review:true,policy_profile:'SCHOOL_EXAM'});attemptText=solution.value;
        }
        const c=recognized?.case||attempt;
        const h=await history(c),latest=h.revisions.at(-1);
        if(recognized && (h.transcription.transcription_id!==recognized.transcriptionId||latest.revision_number!==recognized.revision)){recognized=null;check.checked=false;throw Error('A leitura automática mudou. Carregue e confira a versão atual antes de corrigir.');}
        if(!recognized && latest.segments.map(s=>[s.text,s.latex].filter(Boolean).join('\n')).join('\n')!==attemptText)throw Error('A solução salva foi alterada em outra revisão. Consulte o histórico antes de corrigir.');
        let acceptance=h.acceptances.find(a=>a.revision_number===latest.revision_number);
        if(!acceptance)acceptance=(await request(`/tme/cases/${c.case_id}/transcriptions/${h.transcription.transcription_id}/accept`,{revision_number:latest.revision_number,reviewer_identity_verified:false,acceptance_note:confirmation})).acceptance;
        status.textContent='Corrigindo com o motor existente…';
        auditKey ||= root.crypto.randomUUID();
        const run=await request(`/tme/cases/${c.case_id}/audits`,{execution_key:auditKey,transcription_id:h.transcription.transcription_id,revision_number:latest.revision_number,acceptance_id:acceptance.acceptance_id});
        if(run.status==='FAILED')auditKey=null;
        if(disposed)return;await showRun(c,run);status.textContent=run.status==='COMPLETED'?'Correção disponível abaixo. Confira evidências e pendências.':'Auditoria não concluída; solução preservada.';
      }catch(error){if(!disposed){status.textContent=error.message;if(attempt)result.replaceChildren(savedLink(attempt));}}
      finally{busy=false;if(!disposed){setBusy(false);controls.forEach(el=>el.disabled=false);update();}}
    });
    // Integration point for Luis: consume ONLY a server-persisted transcription,
    // preserving its source, revision and acceptance. Never re-label OCR as manual text.
    async function loadAutomaticCase(caseId){
      if(busy||disposed)return;const ticket=++generation;const c=await request(`/tme/cases/${encodeURIComponent(caseId)}`);
      if(c.problem_id!==pid()||Boolean(c.dynamic_context)!==dynamic||c.exam_submission_id)throw Error('Leitura fora do contexto desta correção direta.');
      const h=await history(c),revision=h.revisions.at(-1);
      if(!['automatic','mathpix_strokes','mathpix_image','vision_model','capture'].includes(h.transcription.source)||!revision||revision.input_issues?.some(i=>i.requires_review)||revision.segments.some(s=>s.kind==='unknown'||s.kind==='diagram'))throw Error('Leitura automática ausente ou com trechos não resolvidos.');
      const text=revision.segments.map(s=>[s.text,s.latex].filter(Boolean).join('\n')).join('\n');if(!text.trim())throw Error('Leitura automática vazia.');
      const detail=await request(`/tme/cases/${c.case_id}/submission`);
      if(ticket!==generation||disposed)return;
      recognized={case:c,transcriptionId:h.transcription.transcription_id,revision:revision.revision_number};mode='image';check.checked=false;solution.value=text;solution.readOnly=true;
      preview.replaceChildren(savedLink(c));
      for(const page of detail.submission.page_images||[]){const view=n('img');view.src=`/tme/cases/${c.case_id}/${c.source_mode==='IMAGE_SCAN'?'originals':'pages'}/${page.page_index}`;view.alt=`Original da solução · página ${page.page_index+1}`;view.style.width='100%';preview.append(view);}
      status.textContent='Leitura automática recebida do servidor. Confira o texto antes de corrigir; a origem e a versão serão preservadas.';update();
    }
    function resetContext(){attempt=null;attemptText=null;recognized=null;auditKey=null;check.checked=false;solution.readOnly=false;if(result.children.length)result.replaceChildren(n('p','A configuração mudou. O resultado anterior permanece no histórico; corrija novamente com a rubrica aprovada atual.'));update();}
    choose('image');return {refresh:update,resetContext,loadAutomaticCase,cancel(){disposed=true;++generation;release();}};
  }
  root.ConfIATeacherDirect={create,confirmation};
})(window);
