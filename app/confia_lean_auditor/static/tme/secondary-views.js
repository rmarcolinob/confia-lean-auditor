/* Operational screens share Home components and tokens. No artifact reads here. */
(function(root){
  'use strict';
  const H=root.ConfiaTmeHome;
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  const button=(text,action,cls='tme-button')=>{const n=el('button',text,cls);n.type='button';n.addEventListener('click',action);return n;};
  const examName=value=>root.ConfiaCorrectionWorkspace.displayExamName(value);
  const question=c=>c.problem_id.match(/Q\d+$/)?.[0]||c.problem_id;
  const date=value=>value?new Date(value).toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short',timeZone:'America/Fortaleza'}):'—';
  function Page(title,subtitle){const n=el('section',null,'tme-page'),heading=el('header',null,'tme-page-heading'),copy=el('div');copy.append(el('h1',title),el('p',subtitle));heading.append(copy);n.append(heading);n.heading=heading;return n;}
  function Empty(text){const n=el('div',text,'tme-empty');n.setAttribute('role','status');return n;}
  function Loading(){const n=el('div',null,'tme-loading');n.setAttribute('role','status');n.setAttribute('aria-label','Carregando dados');for(let i=0;i<4;i++)n.append(el('div',null,'home-skeleton'));return n;}
  function ErrorState(message,retry){const n=el('div',null,'tme-empty');n.setAttribute('role','alert');n.append(el('p',message),button('Tentar novamente',retry));return n;}
  function Pagination(data,change){const n=el('nav',null,'tme-pagination');n.setAttribute('aria-label','Paginação');const previous=button('Anterior',()=>change(data.page-1)),next=button('Próxima',()=>change(data.page+1));previous.disabled=data.page<=1;next.disabled=data.page*data.size>=data.total;n.append(el('span',`${data.total} ${data.total===1?'registro':'registros'} · Página ${data.page} de ${Math.max(1,Math.ceil(data.total/data.size))}`),previous,next);return n;}
  function Filters(values,questions,change,refresh,exams=false){const n=el('form',null,'tme-filters');n.addEventListener('submit',e=>{e.preventDefault();change('search',search.value);});
    const search=el('input');search.type='search';search.placeholder='Buscar prova…';search.value=values.search||'';search.maxLength=80;search.dataset.filter='search';const label=el('label','Buscar prova');label.append(search);n.append(label);
    search.addEventListener('change',()=>change('search',search.value));
    if(!exams)for(const [key,title,options] of [['origin','Dados',[['synthetic_demo','Sintéticos'],['real','Reais']]],['sample','Inspeção',[['selected','Amostra']]],['question','Questão',questions.map(q=>[q,q])],['status','Status',[['pending','Pendente'],['in_progress','Em andamento'],['inconclusive','Inconclusiva'],['finalized','Finalizada']]],['source','Origem',[['IMAGE_SCAN','Foto / scan'],['DIGITAL_INK','Escrita digital']]]]){
      const label=el('label',title),select=el('select');select.dataset.filter=key;for(const [value,text]of [['','Todos'],...options]){const o=el('option',text);o.value=value;select.append(o);}select.value=values[key]||'';select.addEventListener('change',()=>change(key,select.value));label.append(select);n.append(label);
    }
    const apply=button('Buscar',()=>change('search',search.value),'tme-button secondary'),actions=el('div',null,'tme-filter-actions');actions.append(apply);
    const reload=button(null,refresh,'tme-button tme-refresh');reload.setAttribute('aria-label','Atualizar dados');reload.title='Atualizar dados';reload.append(H.icon('rotate'));actions.append(reload);n.append(actions);return n;
  }
  function QueueRows(items,open){const list=el('div',null,'tme-queue-list');const headings=el('div',null,'tme-queue-head');headings.setAttribute('aria-hidden','true');for(const title of ['Prova','Questão','Origem','Status','Sugestão ConfIA','Atualização',''])headings.append(el('span',title));list.append(headings);
    for(const c of items){const n=button(null,()=>open(c.case_id),'tme-queue-row');n.setAttribute('aria-label',`Abrir correção ${c.exam_code} · ${c.problem_id} · ${H.status(c)}`);
      const identity=el('span',null,'tme-row-identity');identity.append(el('strong',examName(c.exam_code)));if(c.data_origin==='synthetic_demo')identity.append(el('small','CASO SINTÉTICO'));if(c.demo_sample_groups?.length)identity.append(el('small','AMOSTRA VISUAL'));
      const q=el('span',null,'tme-row-question');q.append(el('strong',question(c)),el('small',c.problem_id));
      const source=el('span',null,'tme-row-source');source.append(H.icon(c.source_mode==='IMAGE_SCAN'?'camera':'tablet'),el('span',c.source_mode==='IMAGE_SCAN'?'Foto / scan':'Escrita digital'));
      const suggestion=el('span',null,'tme-row-suggestion');suggestion.append(el('small','Sugestão ConfIA'),el('span',c.suggested_score!=null?`${c.suggested_score} / ${c.max_score??'—'}`:c.suggestion_available||c.operational_status==='inconclusive'?'Não determinada':'Não disponível'));
      const updated=el('span',null,'tme-row-updated');updated.append(el('small','Atualizado'),el('span',date(c.updated_at)));
      n.append(identity,q,source,H.StatusPill(c),suggestion,updated,H.icon('chevron'));list.append(n);
    }return list;
  }
  function Exams(items,navigate){const grid=el('div',null,'tme-exam-grid');for(const exam of items){const card=button(null,()=>navigate('cases',{exam:exam.exam_code}),'tme-exam-card');card.setAttribute('aria-label',`Ver questões da prova ${exam.exam_code}`);const heading=el('span',null,'home-exam-heading');heading.append(el('strong',examName(exam.exam_code)),el('strong',`${exam.completed_items}/${exam.known_items}`));
      const questions=el('span',null,'tme-question-chips');for(const c of exam.questions){const chip=el('span',`${question(c)} ${c.operational_status==='finalized'?'✓':c.operational_status==='pending'?'○':'●'}`);chip.dataset.status=c.operational_status;chip.setAttribute('aria-label',`${c.problem_id}: ${H.status(c)}`);chip.title=`${c.problem_id}: ${H.status(c)}`;questions.append(chip);}
      const bar=el('progress');bar.max=exam.known_items;bar.value=exam.completed_items;bar.setAttribute('aria-label',`${exam.completed_items} de ${exam.known_items} questões finalizadas`);card.append(heading,el('span','Questões conhecidas','home-footnote'),questions,bar,el('span',`Atualizado ${date(exam.latest_update)}`,'home-footnote'),H.icon('chevron'));grid.append(card);}return grid;
  }
  function Results(data,navigate){const fragment=el('div',null,'tme-results');const counts=data.summary.counts;fragment.append(H.OverviewMetrics(counts,'all',null));
    const columns=el('div',null,'tme-results-columns'),byQuestion=el('section',null,'tme-panel'),distribution=el('section',null,'tme-panel');byQuestion.append(el('h2','Correções por questão'));distribution.append(el('h2','Distribuição atual'));
    const max=Math.max(1,...data.questions.map(q=>q.finalized));for(const q of data.questions){const row=button(null,()=>navigate('cases',{question:q.problem_id}),'tme-bar-row');row.append(el('strong',q.problem_id),el('span',`${q.finalized} finalizadas`));const bar=el('progress');bar.max=max;bar.value=q.finalized;bar.setAttribute('aria-label',`${q.problem_id}: ${q.finalized} finalizadas`);row.append(bar);byQuestion.append(row);}
    const total=Object.values(counts).reduce((a,b)=>a+b,0);for(const [key,label]of [['finalized','Finalizadas'],['pending','Pendentes'],['inconclusive','Inconclusivas'],['in_progress','Em andamento']]){const row=button(null,()=>navigate('cases',{status:key}),'tme-bar-row');row.append(el('strong',label),el('span',String(counts[key])));const bar=el('progress');bar.max=Math.max(1,total);bar.value=counts[key];bar.setAttribute('aria-label',`${label}: ${counts[key]}`);row.append(bar);distribution.append(row);}
    if(!total)fragment.append(Empty('Ainda não há dados suficientes.'));else{columns.append(byQuestion,distribution);fragment.append(columns);}return fragment;
  }
  root.ConfiaTmeViews={Page,Empty,Loading,ErrorState,Pagination,Filters,QueueRows,Exams,Results};
})(window);
