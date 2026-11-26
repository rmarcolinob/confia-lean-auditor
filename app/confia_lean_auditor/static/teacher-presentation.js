/* Teacher presentation composed from the actual TME home. Read-only operational
   data; all correction, institutional and session actions retain their owners. */
(function (root) {
  'use strict';
  const Home = root.ConfiaTmeHome;
  const host = document.querySelector('#teacher-home');
  const header = document.querySelector('#teacher-modern-header');
  const nav = document.querySelector('#teacher-bottom-nav');
  const styles = document.querySelector('#teacher-home-styles');
  if (!Home || !host || !header || !nav || !styles) return;
  const actions = [
    ['specialized', 'SPECIALIZED', 'Questões preparadas · ITA, TME² e catálogo', 'document'],
    ['dynamic', 'DYNAMIC', 'Questões inéditas · rubricas e correção', 'plus'],
    ['activities', 'Atividades, listas e provas', 'Preparar e acompanhar as atividades', 'list'],
    ['cases', 'Correções e revisões', 'Acompanhar a fila de soluções', 'check'],
    ['results', 'Resultados e devolutivas', 'Consultar as correções realizadas', 'chart'],
    ['received', 'Soluções da turma', 'Envios, transcrições e decisão docente', 'user'],
  ];
  let active = false, generation = 0, period = 'today';
  function leave(url) {
    if (root.ConfIATeacher?.canLeave() === false) return;
    root.location.assign(url);
  }
  function navigate(view, params = {}) {
    if (view === 'home') return root.ConfIAShell.navigate('teacher', 'home');
    if (view === 'activities') return root.ConfIAShell.navigate('teacher', 'exams');
    if (view === 'received') return root.ConfIAShell.navigate('teacher', 'submissions');
    const query = new URLSearchParams();
    query.set('view', view === 'cases' ? 'queue' : ['specialized', 'dynamic'].includes(view) ? 'new' : view);
    if (['specialized', 'dynamic'].includes(view)) query.set('mode', view);
    for (const key of ['exam']) if (params[key]) query.set(key, params[key]);
    leave('/tme?' + query);
  }
  function render(state, summary) {
    const content = Home.TmeHome({state, summary, period, actions, navigate,
      changePeriod(value) { period = value; refresh(); }, retry: refresh,
      open(id) { leave('/tme?case_id=' + encodeURIComponent(id)); }});
    content.classList.add('teacher-operational-home');
    content.querySelector('h1').tabIndex = -1;
    // The aggregate belongs to the correction queue, not all institutional data.
    const overview = content.querySelector('.home-overview h2');
    if (overview) overview.textContent = 'Visão geral das correções';
    host.replaceChildren(content);
  }
  async function refresh() {
    if (!active) return;
    const token = ++generation;
    render('loading');
    try {
      const response = await fetch('/tme/home-summary?period=' + encodeURIComponent(period), {credentials:'same-origin', cache:'no-store'});
      if (!response.ok) throw new Error('summary_unavailable');
      const data = await response.json();
      if (!data.counts || !Array.isArray(data.priority_cases) || !Array.isArray(data.exam_progress)) throw new Error('invalid_summary');
      if (active && token === generation) render('success', data);
    } catch (_) { if (active && token === generation) render('error'); }
  }
  Home.MobileBottomNav(nav, navigate);
  document.querySelector('#teacher-avatar').append(Home.icon('user'));
  document.querySelector('#teacher-modern-logout').addEventListener('click', () => document.querySelector('#auth-logout').click());
  function show(profile, view) {
    const teacher = profile === 'teacher';
    document.body.dataset.teacherShell = String(teacher);
    document.body.dataset.teacherView = teacher ? view : '';
    styles.media = teacher ? 'all' : 'not all';
    header.hidden = nav.hidden = !teacher;
    active = teacher && view === 'home';
    ++generation;
    if (!teacher) return;
    const user = root.ConfIAAuthUser;
    document.querySelector('#teacher-modern-session').textContent = user ? user.display_name + ' · Professor' : 'Demonstração local · Professor';
    document.querySelector('#teacher-demo-profiles').hidden = Boolean(user);
    document.querySelector('#teacher-modern-logout').hidden = !user;
    header.querySelector('details').open = false;
    for (const button of nav.querySelectorAll('button')) button.setAttribute('aria-current', view === 'home' && button.dataset.view === 'home' ? 'page' : 'false');
    if (active) refresh();
  }
  root.ConfIATeacherPresentation = {show, refresh};
})(window);
