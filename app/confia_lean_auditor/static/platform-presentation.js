/* Presentation only: shared TME components, existing shell routes and session.
   No role assignment, persistence, scoring or synthetic operational data. */
(function (root) {
  'use strict';
  const Home = root.ConfiaTmeHome;
  const get = id => document.querySelector('#' + id);
  const login = Boolean(get('login-form'));
  const entry = get('platform-home');
  if (!Home || !entry) return;
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text != null) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const go = route => {
    if (login) { get('login').focus(); return; }
    const [profile, ...view] = route.split('/');
    root.ConfIAShell.navigate(profile, view.join('/'));
  };
  function primary(title, caption, route, glyph) {
    const button = el('button', null, 'home-primary'); button.type = 'button';
    button.addEventListener('click', () => go(route));
    const copy = el('span', null, 'home-primary-copy'); copy.append(el('strong', title), el('span', caption));
    const arrow = el('span', null, 'home-primary-arrow'); arrow.append(Home.icon('arrow'));
    button.append(Home.icon(glyph), copy, arrow);
    return button;
  }
  function banner(greeting, title, intro, action) {
    const hero = el('section', null, 'home-hero');
    const heading = el('h1', title); heading.tabIndex = -1;
    hero.append(el('p', greeting, 'home-greeting'), heading, el('p', intro, 'home-intro'));
    const result = el('div', null, 'home-banner');
    result.append(hero); if (action) result.append(action);
    result.append(Home.HeroIllustration()); return result;
  }
  function panel(title, copy, glyph) {
    const result = el('section', null, 'platform-panel');
    result.append(Home.icon(glyph), el('h2', title), el('p', copy)); return result;
  }
  function entryPage() {
    const page = el('div', null, 'tme-home platform-dashboard platform-entry');
    page.append(banner('Confiabilidade e Explicabilidade em Matemática', 'Matemática com confiança.',
      'Um ambiente para aprender, acompanhar soluções e apoiar decisões pedagógicas. Escolha seu espaço no ConfIA.'));
    const authenticated = Boolean(root.ConfIAAuthUser) &&
      !document.body.classList.contains("confia-local-multi-role");
    const mode = el('section', null, 'platform-session-note');
    mode.append(Home.icon(authenticated || login ? 'user' : 'unknown'), el('div', null));
    mode.lastChild.append(el('strong', login ? 'Acesso institucional' : authenticated ? 'Sessão institucional' : 'Ambiente de demonstração local'),
      el('p', login ? 'Entre com sua conta. O perfil e as permissões são definidos pela instituição.' : authenticated
        ? 'Sua conta acessa somente o módulo autorizado pela instituição.'
        : 'Explore os módulos. Dados de escolas, turmas e atividades institucionais exigem uma sessão autenticada.'));
    page.append(mode);
    const cards = Home.QuickActions(go, [
      ['student/home','Aluno','Caderno matemático, TutorIA e suas atividades','user'],
      ['teacher/home','Professor','Questões preparadas, inéditas e correções','document'],
      ['management/home','Gestão','Indicadores e acompanhamento institucional','chart'],
    ]);
    cards.setAttribute('aria-label', 'Módulos do ConfIA');
    for (const button of cards.querySelectorAll('button')) {
      const role = button.dataset.action.split('/')[0];
      if (authenticated && role !== root.ConfIAAuthProfile) {
        button.disabled = true;
        button.querySelector('.home-action-caption').textContent = 'Indisponível para o perfil desta sessão';
      }
    }
    page.append(cards);
    const details = el('div', null, 'platform-panel-grid');
    details.append(panel('Aprender e compreender', 'Resolva no caderno, registre seu raciocínio e retome as orientações e atividades disponíveis no TutorIA.', 'tablet'),
      panel('Acompanhar com clareza', 'Da solução recebida à devolutiva, o ConfIA mantém evidências e a decisão pedagógica com o professor.', 'check'));
    page.append(details); entry.replaceChildren(page);
  }
  if (login) { entryPage(); return; }
  const header = get('platform-header'), nav = get('platform-navigation'), styles = get('platform-home-styles');
  const studentName = get('student-home-name'), studentContext = get('student-institutional-context');
  get('platform-avatar').append(Home.icon('user'));
  get('platform-logout').addEventListener('click', () => get('auth-logout').click());
  function studentHome() {
    const host = get('student-home'); host.className = 'platform-dashboard tme-home';
    const hero = banner('Sua área de estudo', 'Vamos aprender?', 'Explore uma ideia, desenvolva sua solução e acompanhe seu percurso.',
      primary('Abrir meu caderno', 'Resolver uma questão no TutorIA', 'student/tutoria/practice', 'tablet'));
    const greeting = hero.querySelector('.home-greeting'); greeting.textContent = 'Olá, '; greeting.append(studentName);
    hero.querySelector('.home-hero').append(studentContext);
    host.replaceChildren(hero, Home.QuickActions(go, [
      ['student/tutoria','TutorIA','Conteúdos, questões e resolução assistida','plus'],
      ['student/study','Estudo autônomo','Novos problemas, pistas e revisão — sem nota','check'],
      ['student/exams','Atividades e provas','Avaliações disponibilizadas pela turma','document'],
      ['student/submissions','Minhas submissões','Soluções enviadas e devolutivas','list'],
      ['student/tutoria/feedback','Feedback','Revisitar o raciocínio e as orientações','check'],
      ['student/tutoria/attempts','Minhas atividades','Retomar tentativas e histórico de prática','clock'],
      ['student/tutoria/progress','Meu progresso','Acompanhar o percurso no TutorIA','chart'],
    ]));
    const panels = el('div', null, 'platform-panel-grid');
    panels.append(panel('Seu raciocínio tem espaço', 'Escreva à mão ou digite sua solução. O enunciado e as ferramentas acompanham você no caderno.', 'tablet'),
      panel('Aprender com a revisão', 'Confira a leitura da solução e consulte o feedback disponível para planejar sua próxima tentativa.', 'check'));
    host.append(panels);
  }
  function managementHome() {
    const host = get('management-home'); host.className = 'platform-dashboard tme-home';
    host.replaceChildren(banner('Acompanhamento institucional', 'Uma visão clara da sua rede.',
      'Consulte os indicadores existentes e acompanhe escolas, turmas e atividades dentro do seu escopo de acesso.',
      primary('Abrir indicadores', 'Consultar escolas e turmas', 'management/overview', 'chart')));
  }
  const navigation = {
    student: [['home','Início','home'],['tutoria','TutorIA','plus'],['study','Estudo','check'],['exams','Atividades','document'],['submissions','Envios','list']],
    management: [['home','Início','home'],['overview','Indicadores','chart']],
  };
  function show(profile, view) {
    const enabled = ['platform','student','management'].includes(profile);
    document.body.dataset.platformProfile = enabled ? profile : '';
    document.body.dataset.platformView = view;
    styles.media = enabled ? 'all' : 'not all';
    header.hidden = !enabled; entry.hidden = profile !== 'platform';
    if (!enabled) return;
    header.querySelector('details').open = false;
    const user = root.ConfIAAuthUser;
    get('platform-session').textContent = user ? user.display_name + ' · Sessão institucional' : 'Demonstração local · sem sessão institucional';
    get('platform-logout').hidden = !user || document.body.classList.contains("confia-local-multi-role");
    get('platform-brand-context').textContent = ({platform:'Matemática com confiança',student:'Área do aluno · Aprendizagem',management:'Área da gestão · Acompanhamento'})[profile];
    nav.replaceChildren();
    for (const [target, label, glyph] of navigation[profile] || []) {
      const button = el('button'); button.type = 'button'; button.append(Home.icon(glyph),el('span',label));
      button.setAttribute('aria-current', view === target || target === 'tutoria' && view.startsWith('tutoria/') ? 'page' : 'false');
      button.addEventListener('click', () => go(profile + '/' + target)); nav.append(button);
    }
    nav.hidden = profile === 'platform';
    if (profile === 'platform') entryPage();
    if (profile === 'student' && view === 'home') studentHome();
    if (profile === 'management' && view === 'home') managementHome();
    get('platform-header').setAttribute('aria-label', ({platform:'ConfIA',student:'Área do Aluno',management:'Área da Gestão'})[profile]);
  }
  root.ConfIAPlatformPresentation = {show};
})(window);
