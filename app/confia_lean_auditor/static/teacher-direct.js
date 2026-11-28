/* Intake only. Scores and evidence come from the existing audit workspace. */
(function(root){
  'use strict';
  const confirmation='Conferi explicitamente a transcrição com a solução original antes da auditoria.';
  const n=(tag,text)=>{const el=document.createElement(tag);if(text!=null)el.textContent=text;return el;};
  const field=(text,el)=>{const label=n('label',text);label.append(el);return label;};
  function create({host,problemId,onOpen,setBusy=()=>{},dynamic=false}){
    let busy=false, original=null, previewUrl=null;
    const form=n('form');form.className='dynamic-form tme-panel';
    const code=n('input'), solution=n('textarea'), file=n('input'),preview=n('div'),status=n('p');
    code.required=true;code.maxLength=80;code.pattern='[A-Za-z0-9._:/-]+';code.value='SOL-'+Date.now().toString(36).toUpperCase();
    code.setAttribute('aria-label','Código pseudônimo da resolução');
    solution.required=true;solution.maxLength=20000;solution.rows=10;solution.setAttribute('aria-label','Resolução digitada');
    file.type='file';file.accept='application/pdf,image/jpeg,image/png,image/webp';file.setAttribute('aria-label','Anexar original');
    status.setAttribute('role','status');
    const allow=n('input');allow.type='checkbox';allow.setAttribute('aria-label','Permitir análise com preparação pendente');
    const policy=n('select');policy.setAttribute('aria-label','Perfil de pontuação');
    for(const [value,label] of [['SCHOOL_EXAM','Correção escolar'],['FORMATIVE_LIST','Correção formativa']]){const option=n('option',label);option.value=value;policy.append(option);}
    const submit=n('button','Conferir transcrição');submit.type='submit';submit.className='tme-button';
    const clear=n('button','Remover anexo');clear.type='button';clear.className='tme-button secondary';
    function release(){if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=null;}
    function remove(){release();original=null;file.value='';preview.replaceChildren();}
    clear.addEventListener('click',remove);
    file.addEventListener('change',()=>{
      release();preview.replaceChildren();original=file.files[0]||null;
      if(!original)return;
      if(!['application/pdf','image/jpeg','image/png','image/webp'].includes(original.type)||original.size>20*1024*1024){remove();status.textContent='Use PDF, JPG, PNG ou WebP de até 20 MiB.';return;}
      previewUrl=URL.createObjectURL(original);
      const view=n(original.type==='application/pdf'?'iframe':'img');view.src=previewUrl;view.title='Solução original';view.alt='Solução original';view.style.width='100%';view.style.maxHeight='32rem';if(view.tagName==='IFRAME')view.style.height='32rem';
      preview.append(n('p',original.name),view);status.textContent='Original anexado. Digite a transcrição abaixo; o arquivo não é interpretado automaticamente.';
    });
    form.append(n('h2','Inserir resolução'),n('p','Use um código pseudônimo. Anexe o original, se disponível, e digite a resolução matemática. O anexo é preservado; nenhum OCR é executado neste percurso.'),field('Código da resolução',code),field('Original opcional · PDF, JPG, PNG ou WebP',file),clear,preview,field('Resolução digitada ou transcrição manual',solution));
    if(!dynamic && String(typeof problemId==='function'?problemId():problemId).startsWith('TME'))form.append(n('p','Identifique cada item em uma linha própria: [a], [b], [c] ou [d], conforme o problema. Preserve o desenvolvimento do aluno abaixo de cada item.'));
    if(dynamic)form.append(field('Perfil de pontuação',policy),field('Permitir análise com preparação pendente, mantendo os avisos para revisão docente',allow));
    form.append(n('p','Na próxima etapa, compare a transcrição com o original e confirme antes de corrigir.'),submit,status);host.append(form);
    form.addEventListener('submit',async event=>{
      event.preventDefault();if(busy||!form.reportValidity())return;
      if(!solution.value.trim()){status.textContent='Digite a resolução.';return;}
      busy=true;setBusy(true);const controls=[...form.querySelectorAll('input,textarea,select,button')];controls.forEach(el=>el.disabled=true);
      try{
        const body={problem_id:typeof problemId==='function'?problemId():problemId,external_candidate_ref:code.value.trim(),solution:solution.value,allow_preparation_review:allow.checked,policy_profile:policy.value||'SCHOOL_EXAM'};
        if(original){const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(Error('Não foi possível ler o original.'));reader.readAsDataURL(original);});body.original={media_type:original.type,content_base64:data};}
        status.textContent='Preservando a resolução…';
        const response=await fetch('/tme/direct-solutions',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
        const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:data.detail?.message||'Não foi possível receber a resolução.');
        release();busy=false;setBusy(false);await onOpen(data.case_id);
      }catch(error){status.textContent=error.message;}
      finally{busy=false;setBusy(false);controls.forEach(el=>el.disabled=false);}
    });
    return {cancel:release};
  }
  root.ConfIATeacherDirect={create,confirmation};
})(window);
