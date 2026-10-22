/* Home consumes the server operational projection; no per-case artifact requests. */
(function (root) {
  'use strict';
  const status = c => ({ pending: 'Pendente', in_progress: 'Em andamento', inconclusive: 'Inconclusiva', finalized: 'Finalizada' }[c.operational_status]
    || { IDENTIFIED: 'Pendente', SOURCE_READY: 'Em andamento', DECIDED: 'Finalizada' }[c.status] || 'Não informado');
  const paths = {
    document: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
    plus: '<path d="M12 5v14M5 12h14"/>', list: '<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>',
    chart: '<path d="M4 20h17M7 16V9M12 16V4M17 16v-5"/>', arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    home: '<path d="m3 10 9-7 9 7v10H3zM9 20v-7h6v7"/>', user: '<circle cx="12" cy="8" r="3"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/>',
    play: '<path d="m9 5 11 7-11 7z"/>', camera: '<path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="4"/>', tablet: '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    alert: '<path d="m12 3 10 18H2zM12 9v5M12 17h.01"/>', chevron: '<path d="m9 6 6 6-6 6"/>'
  };
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text != null) n.textContent = text; if (cls) n.className = cls; return n; };
  function icon(name) { const n = el('span', null, 'home-icon'); n.setAttribute('aria-hidden', 'true'); n.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${paths[name] || paths.document}</svg>`; return n; }
  function button(text, action, cls) { const n = el('button', text, cls); n.type = 'button'; n.addEventListener('click', action); return n; }
  function StatusPill(c) { const pill = el('span', status(c), 'home-status'); pill.dataset.status = ({pending:'IDENTIFIED',in_progress:'SOURCE_READY',inconclusive:'Inconclusiva',finalized:'DECIDED'}[c.operational_status] || c.status); return pill; }
  function PrimaryCorrectionCTA(cases, open, state) {
    const next = cases[0], n = button(null, () => next && open(next.case_id), 'home-primary');
    n.disabled = state !== 'success' || !next;
    const copy = el('span', null, 'home-primary-copy'); copy.append(el('strong', 'Corrigir próxima'), el('span', state === 'loading' ? 'Carregando sua fila…' : next ? 'Receba a próxima questão da\u00a0fila' : state === 'error' ? 'Sua fila está indisponível' : 'Nenhuma correção pendente'));
    const arrow = el('span', null, 'home-primary-arrow'); arrow.append(icon('arrow')); n.append(icon('document'), copy, arrow); return n;
  }
  function QuickActions(navigate) {
    const n = el('nav', null, 'home-quick'); n.setAttribute('aria-label', 'Atalhos da Home');
    for (const [view, label, caption, glyph] of [['new','Nova correção','Buscar por código da prova','plus'],['cases','Ver fila','Visualizar e filtrar correções','list'],['results','Resultados','Acompanhar desempenho','chart']]) {
      const b = button(null, () => navigate(view), 'home-action'); b.dataset.action = view; b.append(icon(glyph), el('strong',label), el('span',caption,'home-action-caption'), icon('chevron')); n.append(b);
    } return n;
  }
  function MetricCard(label, value, tone, glyph) { const n = el('div', null, `home-metric ${tone}`); n.append(icon(glyph), el('strong', value == null ? '—' : String(value)), el('span', label)); if (value == null) n.setAttribute('aria-label', `${label}: dado indisponível na fila`); return n; }
  function OverviewMetrics(values, period, change) {
    const n = el('section', null, 'home-overview'), heading = el('div', null, 'home-section-heading');
    const select = el('select'); select.setAttribute('aria-label', 'Período de criação dos casos');
    for (const [value,label] of [['today','Hoje'],['7d','7 dias'],['30d','30 dias'],['all','Todo o período']]) { const o = el('option',label); o.value=value; select.append(o); } select.value=period; select.addEventListener('change',()=>change(select.value));
    heading.append(el('h2','Visão geral'),select); const grid=el('div',null,'home-metrics');
    grid.append(MetricCard('Pendentes',values.pending,'blue','document'),MetricCard('Inconclusivas',values.inconclusive,'yellow','alert'),MetricCard('Finalizadas',values.finalized,'green','check'),MetricCard('Em andamento',values.in_progress,'rose','play'));
    n.append(heading,grid,el('p',period === 'today' ? 'Status atual dos casos criados hoje (Fortaleza).' : period === 'all' ? 'Status atual de todos os casos da sua fila.' : `Status atual dos casos criados nos últimos ${period === '7d' ? 7 : 30} dias (Fortaleza).`,'home-footnote'));
    return n;
  }
  function PriorityCaseRow(c, open) {
    c = {...c, external_candidate_ref: c.exam_code || c.external_candidate_ref};
    const n = button(null,()=>open(c.case_id),'home-case'); n.setAttribute('aria-label', `Abrir correção ${c.external_candidate_ref} · ${c.problem_id} · ${status(c)}`);
    const identity=el('span',null,'home-case-identity'); identity.append(el('strong',c.external_candidate_ref),el('span',c.problem_id));
    const question=el('span',null,'home-case-question'); question.append(el('small','Questão'),el('span',c.question_label || (/Q(\d+)$/.test(c.problem_id)?`Q${c.problem_id.match(/Q(\d+)$/)[1]}`:c.problem_id)));
    const source=el('span',null,'home-case-source'), sourceValue=el('span',null,'home-source-value'); sourceValue.append(icon(c.source_mode==='IMAGE_SCAN'?'camera':'tablet'),el('span',c.source_mode==='IMAGE_SCAN'?'Foto / scan':'Escrita digital')); source.append(el('small','Origem'),sourceValue);
    n.append(icon('document'),identity,question,source,StatusPill(c),icon('chevron')); return n;
  }
  function sectionLink(label, action) { const n = button(label, action, 'home-text-button'); n.append(icon('chevron')); return n; }
  function PriorityQueue(cases, navigate, open) {
    const n=el('section',null,'home-priority'), list=cases, heading=el('div',null,'home-section-heading'), title=el('h2','Fila prioritária');
    title.append(el('span',String(list.length),'home-count')); heading.append(title,sectionLink('Ver fila completa',()=>navigate('cases'))); n.append(heading);
    if (!list.length) n.append(el('p','Nenhuma correção pendente.','home-empty'),button('Nova correção',()=>navigate('new'),'home-empty-action'));
    else { const rows=el('div',null,'home-case-list'); list.slice(0,3).forEach(c=>rows.append(PriorityCaseRow(c,open))); n.append(rows); } return n;
  }
  function ExamProgressCard(exam,navigate) {
    const n=el('article',null,'home-exam'), heading=el('div',null,'home-exam-heading'), title=el('div'); title.append(el('h3',exam.exam_code),el('span','Questões conhecidas','home-footnote')); heading.append(title,el('strong',`${exam.completed_items}/${exam.known_items}`));
    const bar=el('progress'); bar.max=exam.known_items; bar.value=exam.completed_items; bar.setAttribute('aria-label',`${exam.exam_code}: ${exam.completed_items} de ${exam.known_items} questões finalizadas`); const open = button(null,()=>navigate('cases'),'home-exam-open'); open.setAttribute('aria-label',`Ver correções da prova ${exam.exam_code}`); n.append(icon('document'),heading,bar,open); return n;
  }
  function ExamProgress(groups,navigate) {
    const n=el('section',null,'home-progress'), heading=el('div',null,'home-section-heading'); heading.append(el('h2','Progresso por prova'),sectionLink('Ver todas',()=>navigate('cases'))); n.append(heading);
    const grid=el('div',null,'home-exams'); groups.slice(0,2).forEach(exam=>grid.append(ExamProgressCard(exam,navigate)));
    n.append(groups.length?grid:el('p','Suas provas aparecerão aqui ao criar uma correção.','home-empty')); return n;
  }
  function MobileBottomNav(host,navigate) {
    host.replaceChildren();
    for(const [view,label,glyph] of [['home','Início','home'],['cases','Fila','list'],['new','Nova','plus'],['results','Resultados','chart']]) {
      const b=button(null,()=>navigate(view)); b.dataset.view=view; b.append(icon(glyph),el('span',label)); host.append(b);
    }
  }
  function HomeHeader() {
    const avatar=document.querySelector('#evaluator-avatar'); if (avatar) { avatar.replaceChildren(icon('user')); }
  }
  function HeroIllustration() {
    const n = el('div', null, 'home-illustration'); n.setAttribute('aria-hidden', 'true');
    // Local decorative SVG only: no remote asset, interaction, or case data.
    n.innerHTML = `<svg viewBox="0 0 260 200" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
      <path class="hero-surface" d="M40 200 95 73q11-27 42-27h78q26 0 33 25l12 129Z"/>
      <g stroke-width="2.2" stroke-linecap="round">
        <path class="hero-green" d="m10 89 28-54Q49 14 76 14h70"/>
        <path class="hero-yellow" d="m26 165 49-106q10-23 36-23h56"/>
        <path class="hero-red" d="m166 36 6-8q10-14 29-14h59"/>
      </g>
      <rect class="hero-paper" x="112" y="65" width="100" height="112" rx="18"/>
      <g class="hero-lines" stroke-width="6" stroke-linecap="round"><path d="M135 94h49M135 112h32M135 130h15"/></g>
      <circle class="hero-check-disc" cx="197" cy="145" r="25"/>
      <path d="m187 145 7 7 14-16" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
    return n;
  }
  function TmeHome({summary={counts:{pending:0,inconclusive:0,finalized:0,in_progress:0},priority_cases:[],exam_progress:[]}, state='success', period='today', changePeriod, navigate, open, retry}) {
    const n=el('div',null,'tme-home'); n.dataset.state=state;
    const hero=el('section',null,'home-hero'); hero.append(el('p','Olá, avaliador!','home-greeting'),el('h1','Vamos continuar?'),el('p','Contribua para uma correção mais ágil, justa e segura dos exames\u00a0TME.','home-intro'));
    const banner=el('div',null,'home-banner'); banner.append(hero,PrimaryCorrectionCTA(summary.priority_cases,open,state),HeroIllustration());
    n.append(banner,QuickActions(navigate));
    if (state==='loading') {
      const skeleton=el('div',null,'home-loading'); skeleton.setAttribute('role','status'); skeleton.setAttribute('aria-label','Carregando visão geral, fila prioritária e progresso por prova');
      for(const [name,cls,gridClass,count] of [['Visão geral','home-overview','home-metrics',4],['Fila prioritária','home-priority','home-case-list',3],['Progresso por prova','home-progress','home-exams',2]]) {
        const section=el('section',null,cls), heading=el('div',null,'home-section-heading'), grid=el('div',null,gridClass);
        heading.append(el('h2',name));
        for(let i=0;i<count;i++) { const shape=el('div',null,'home-skeleton'); shape.setAttribute('aria-hidden','true'); grid.append(shape); }
        section.append(heading,grid);
        if(cls==='home-overview') section.append(el('p','Status atual dos casos criados hoje (Fortaleza).','home-footnote home-loading-note'));
        skeleton.append(section);
      } n.append(skeleton);
    } else if(state==='error') { const error=el('section',null,'home-error'); error.setAttribute('role','alert'); error.append(el('h2','Não foi possível carregar os indicadores.'),button('Tentar novamente',retry,'home-empty-action')); n.append(error); }
    else n.append(OverviewMetrics(summary.counts,period,changePeriod),PriorityQueue(summary.priority_cases,navigate,open),ExamProgress(summary.exam_progress,navigate));
    return n;
  }
  const api={status,TmeHome,HomeHeader,MobileBottomNav,PriorityCaseRow};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  root.ConfiaTmeHome=api;
})(typeof window==='undefined'?globalThis:window);
