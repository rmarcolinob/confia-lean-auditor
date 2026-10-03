/* UI-01 presentation router. UI-02 will place /capture within response flows;
 * this shell deliberately keeps the notebook as a separate route and contract. */
(function institutionalShell() {
  "use strict";
  const profiles = {
    student: { area: "student-area", label: "Aluno", views: {
      home: ["Início", "Um espaço para resolver, compreender e conferir sua solução matemática."],
      resolve: ["Questões / Resolver", "Escolha uma questão e prepare sua solução para a Análise ConfIA."],
      feedback: ["Feedback", "Consulte a análise da solução enviada. Edições posteriores continuam identificadas."],
      submissions: ["Envios", "Salve e consulte soluções textuais de demonstração neste navegador."],
    } },
    teacher: { area: "teacher-area", label: "Professor", views: {
      home: ["Início", "Receba soluções, confira transcrições e explore a análise textual demonstrativa."],
      submissions: ["Soluções recebidas", "Manuscritos recebidos pelo ConfIA. Abra uma solução para visualizar o original."],
      transcriptions: ["Transcrições", "Selecione uma solução recebida para comparar a transcrição com o manuscrito original."],
      analysis: ["Correção / Análise ConfIA", "Protótipo de correção textual com registros locais e exemplos demonstrativos."],
    } },
    management: { area: "management-area", label: "Gestão", views: {
      home: ["Visão demonstrativa de gestão", "Apresentação de gestão com dados ilustrativos fixos."],
      overview: ["Painel demonstrativo", "Dados ilustrativos. Os números deste painel não são indicadores reais."],
    } },
  };
  const title = document.querySelector("#page-title");
  const menus = document.querySelectorAll("[data-profile-menu]");
  const links = document.querySelectorAll("[data-shell-link]");
  let current = { profile: "student", view: "home" };
  let navigating = false;

  function visible(id, show) { document.querySelector(`#${id}`).hidden = !show; }
  function refreshLocalSubmissions() {
    const list = document.querySelector("#student-local-list");
    list.replaceChildren();
    const records = readLocalSubmissions();
    if (!records.length) {
      appendTextElement(list, "p", "empty-state", "Nenhuma solução salva neste navegador. Use o formulário para criar um envio de demonstração.");
      return;
    }
    for (const record of records) {
      const article = appendTextElement(list, "article", "local-submission", "");
      appendTextElement(article, "h3", "", record.problem_title || record.problem_id);
      appendTextElement(article, "p", "", `Solução enviada por ${record.student_name || "Aluno"} · ${formatDateTime(record.submitted_at)}`);
      appendTextElement(article, "span", "badge", "Registro local de demonstração");
    }
  }

  function render(profile, view, focus) {
    const config = profiles[profile];
    current = { profile, view };
    document.querySelector(`#${config.area}`).dataset.view = view;
    document.querySelector("#active-profile").textContent = `Perfil de demonstração: ${config.label}`;
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
    visible("student-workspace", profile === "student" && ["resolve", "submissions"].includes(view));
    visible("result-panel", profile === "student" && view !== "home");
    visible("student-local-envios", profile === "student" && view === "submissions");
    if (profile === "student" && view !== "home") setStudentMode(view === "submissions" ? "submit" : "study");
    visible("teacher-home", profile === "teacher" && view === "home");
    document.querySelector(".teacher-submission-modes").hidden = profile !== "teacher" || view === "home";
    if (profile === "teacher" && view !== "home") {
      if (view === "analysis") window.ConfIATeacher.showText();
      else window.ConfIATeacher.showManuscripts();
    } else {
      visible("manuscript-inbox", false);
      visible("teacher-text-prototype", false);
    }
    visible("management-home", profile === "management" && view === "home");
    visible("management-overview", profile === "management" && view === "overview");
    if (view === "submissions" && profile === "student") refreshLocalSubmissions();
    document.title = `ConfIA — ${config.views[view][0]}`;
    if (focus) title.focus();
  }

  function navigate(profile, view, { focus = true, historyMode = "push" } = {}) {
    if (!profiles[profile]?.views[view]) { profile = "student"; view = "home"; }
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
    refreshLocalSubmissions,
    activateProfile(area) {
      if (navigating) return;
      const profile = Object.keys(profiles).find(key => profiles[key].area === area) || "student";
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
  for (const button of document.querySelectorAll("[data-student-mode]")) button.addEventListener("click", () => {
    navigate("student", button.dataset.studentMode === "submit" ? "submissions" : "resolve", { focus: false });
  });
  document.querySelector("#show-manuscripts").addEventListener("click", () => {
    if (!document.querySelector("#manuscript-inbox").hidden) navigate("teacher", "submissions");
  });
  document.querySelector("#show-text-prototype").addEventListener("click", () => {
    if (!document.querySelector("#teacher-text-prototype").hidden) navigate("teacher", "analysis");
  });
  window.addEventListener("hashchange", () => {
    if (location.hash === "#app-root") return; // Native skip link keeps its normal focus behavior.
    const [profile, view] = location.hash.slice(1).split("/");
    navigate(profile, view, { historyMode: "replace" });
  });
  const [hashProfile, hashView] = location.hash.slice(1).split("/");
  const fromCapture = new URLSearchParams(location.search).get("area") === "teacher";
  navigate(hashProfile || (fromCapture ? "teacher" : "student"), hashView || (fromCapture ? "submissions" : "home"), { focus: false, historyMode: "replace" });
})();
