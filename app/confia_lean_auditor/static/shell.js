/* Institutional navigation; student responses converge on the UI-02 workspace. */
(function institutionalShell() {
  "use strict";
  const profiles = {
    student: { area: "student-area", label: "Aluno", views: {
      home: ["Início", "Um espaço para resolver, compreender e conferir sua solução matemática."],
      resolve: ["Questões / Resolver", "Escolha uma questão e resolva no Caderno de Resolução ConfIA."],
      feedback: ["Feedback", "Consulte a análise atual da resolução nesta sessão."],
      submissions: ["Envios", "Consulte os recibos de envios confirmados nesta sessão."],
    } },
    teacher: { area: "teacher-area", label: "Professor", views: {
      home: ["Início", "Acompanhe cada solução: recebimento, transcrição, Análise ConfIA e avaliação docente."],
      submissions: ["Soluções recebidas", "Manuscritos recebidos pelo ConfIA. Abra uma solução para visualizar o original."],
      transcriptions: ["Transcrições", "Selecione uma solução recebida para comparar a transcrição com o manuscrito original."],
      analysis: ["Correção / Análise ConfIA", "Consulte as etapas das soluções recebidas. A análise dos manuscritos aguarda integração."],
      text: ["Demonstração textual local", "Análise de textos locais e exemplos. Este fluxo não corresponde aos manuscritos persistidos."],
    } },
    management: { area: "management-area", label: "Gestão", views: {
      home: ["Visão demonstrativa de gestão", "Apresentação de gestão com dados ilustrativos fixos."],
      overview: ["Painel demonstrativo", "Dados ilustrativos. Os números deste painel não são indicadores reais."],
    } },
  };
  const title = document.querySelector("#page-title");
  const menus = document.querySelectorAll("[data-profile-menu]");
  const links = document.querySelectorAll("[data-shell-link]");
  const authMode = document.body?.classList?.contains("auth-enabled") || false;
  let authenticatedProfile = null;
  let authenticatedUser = null;
  let current = { profile: "student", view: "home" };
  let navigating = false;

  function visible(id, show) { document.querySelector(`#${id}`).hidden = !show; }
  function refreshStudent() {
    const student = current.profile === "student";
    const workspace = window.ConfIAWorkspace;
    visible("student-feedback", student && (current.view === "feedback" || (current.view === "resolve" && workspace?.mode === "practice" && Boolean(studentAnalysis))));
    visible("student-session-envios", student && current.view === "submissions");
    if (student && current.view === "feedback" && !studentAnalysis) renderStudentStudyEmptyState();
    workspace?.display();
  }

  function render(profile, view, focus) {
    const config = profiles[profile];
    current = { profile, view };
    document.querySelector(`#${config.area}`).dataset.view = view;
    document.querySelector("#active-profile").textContent = authMode ? `${authenticatedUser.display_name} / ${config.label}` : `Perfil de demonstração: ${config.label}`;
    document.querySelector("#profile-navigation").setAttribute("aria-label", `Navegação ${profile === "management" ? "da" : "do"} ${config.label}`);
    document.querySelector("#page-eyebrow").textContent = `Área ${profile === "management" ? "da" : "do"} ${config.label}`;
    title.textContent = config.views[view][0];
    document.querySelector("#page-description").textContent = config.views[view][1];
    for (const menu of menus) menu.hidden = menu.dataset.profileMenu !== profile;
    for (const link of links) {
      if (link.getAttribute("href") === `#${profile}/${view}` && link.closest("#profile-navigation")) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    }
    visible("student-home", profile === "student" && view === "home");
    visible("student-workspace", profile === "student" && view === "resolve");
    refreshStudent();
    visible("teacher-home", profile === "teacher" && view === "home");
    document.querySelector(".teacher-submission-modes").hidden = profile !== "teacher" || view === "home";
    if (profile === "teacher" && view !== "home") {
      if (view === "text") window.ConfIATeacher.showText();
      else window.ConfIATeacher.showView(view);
    } else {
      visible("manuscript-inbox", false);
      visible("teacher-text-prototype", false);
    }
    visible("management-home", profile === "management" && view === "home");
    visible("management-overview", profile === "management" && view === "overview");
    document.title = `ConfIA — ${config.views[view][0]}`;
    if (focus) title.focus();
  }

  function navigate(profile, view, { focus = true, historyMode = "push" } = {}) {
    if (authMode && !authenticatedProfile) return false;
    if (authMode && profile !== authenticatedProfile) { profile = authenticatedProfile; view = "home"; }
    if (!profiles[profile]?.views[view]) { profile = "student"; view = "home"; }
    if (authMode && profile !== authenticatedProfile) { profile = authenticatedProfile; view = "home"; }
    // UI-P0 protects unsaved transcription edits across every shell destination.
    navigating = true;
    const allowed = activateArea(profiles[profile].area);
    navigating = false;
    if (!allowed) {
      history.replaceState(null, "", `#${current.profile}/${current.view}`);
      document.querySelector("#manuscript-message").focus();
      return false;
    }
    render(profile, view, focus);
    const hash = `#${profile}/${view}`;
    if (location.hash !== hash) history[historyMode === "replace" ? "replaceState" : "pushState"](null, "", hash);
    return true;
  }

  window.ConfIAShell = {
    refreshStudent, navigate,
    activateProfile(area) {
      if (navigating) return;
      const profile = Object.keys(profiles).find(key => profiles[key].area === area) || "student";
      if (authMode && profile !== authenticatedProfile) return;
      render(profile, "home", true);
      history.pushState(null, "", `#${profile}/home`);
    },
  };
  for (const link of links) link.addEventListener("click", event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const [profile, view] = link.getAttribute("href").slice(1).split("/");
    navigate(profile, view);
  });
  document.querySelector("#show-manuscripts").addEventListener("click", () => {
    if (!document.querySelector("#manuscript-inbox").hidden) navigate("teacher", "submissions");
  });
  document.querySelector("#show-text-prototype").addEventListener("click", () => {
    if (!document.querySelector("#teacher-text-prototype").hidden) navigate("teacher", "text");
  });
  window.addEventListener("hashchange", () => {
    if (location.hash === "#app-root") return; // Native skip link keeps its normal focus behavior.
    const [profile, view] = location.hash.slice(1).split("/");
    navigate(profile, view, { historyMode: "replace" });
  });
  function initialNavigation() {
    const [hashProfile, hashView] = location.hash.slice(1).split("/");
    const fromCapture = new URLSearchParams(location.search).get("area") === "teacher";
    navigate(hashProfile || (authMode ? authenticatedProfile : (fromCapture ? "teacher" : "student")),
      hashView || (!authMode && fromCapture ? "submissions" : "home"),
      { focus: false, historyMode: "replace" });
  }
  if (authMode) {
    fetch("/auth/me", { credentials: "same-origin", cache: "no-store" }).then(async response => {
      if (!response.ok) { location.replace("/"); return; }
      authenticatedUser = await response.json();
      authenticatedProfile = {
        STUDENT: "student", TEACHER: "teacher", SCHOOL_MANAGER: "management",
      }[authenticatedUser.role];
      if (!authenticatedProfile) { location.replace("/"); return; }
      window.ConfIAAuthProfile = authenticatedProfile;
      document.querySelector(".brand").setAttribute("href", `#${authenticatedProfile}/home`);
      const label = profiles[authenticatedProfile].label;
      document.querySelector("#auth-identity").textContent = `${authenticatedUser.display_name} / ${label}`;
      document.querySelector("#auth-identity").hidden = false;
      document.querySelector("#auth-logout").hidden = false;
      document.querySelector("#auth-logout").addEventListener("click", async () => {
        const result = await fetch("/auth/logout", { method: "POST", credentials: "same-origin" });
        if (result.ok) location.replace("/");
      });
      document.body.classList.remove("auth-loading");
      initialNavigation();
    }).catch(() => { location.replace("/"); });
  } else initialNavigation();
})();
