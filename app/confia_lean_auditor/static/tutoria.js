/* TutorIA presentation and session-only practice. No institutional persistence or audit transport. */
(function tutoriaExperience() {
  "use strict";
  const demo = window.ConfIATutoriaDemo;
  const host = document.querySelector("#tutoria-content");
  if (!host || !demo) return;
  const attempts = []; // Real user input in this page session; feedback has its own DEMO provenance.
  let activeView = "", topicId = null, lessonId = null, chosenAttempt = null;
  let catalog = [], catalogState = "loading", search = "";
  const filters = {};
  const node = (tag, text, className = "") => {
    const element = document.createElement(tag); element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const append = (parent, tag, text, className) => parent.appendChild(node(tag, text, className));
  function badge(parent, label = "Visão demonstrativa", origin = "DEMO") {
    const state = append(parent, "span", label, "status"); state.dataset.kind = origin === "REAL" ? "info" : "neutral";
    parent.dataset.origin = origin; return state;
  }
  function link(parent, label, view, action, primary = false) {
    const a = append(parent, "a", label, primary ? "button button-primary" : "button button-secondary");
    a.href = `#student/tutoria${view ? `/${view}` : ""}`;
    a.addEventListener("click", event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (window.ConfIAShell?.navigate("student", view ? `tutoria/${view}` : "tutoria") !== false) action?.();
    });
    return a;
  }
  function button(parent, label, action, primary = false) {
    const b = append(parent, "button", label, primary ? "primary-action" : "secondary-action");
    b.type = "button"; b.addEventListener("click", action); return b;
  }
  function math(parent, source) {
    const document = append(parent, "div", undefined, "tutoria-document");
    if (globalThis.ConfiaRecognitionView) globalThis.ConfiaRecognitionView.renderMathText(document, source);
    else document.textContent = source;
    return document;
  }
  function heading(title, description, illustrative = false) {
    const header = append(host, "header", undefined, "tutoria-section-heading");
    if (illustrative) badge(header);
    const h = append(header, "h2", title); h.tabIndex = -1;
    if (description) append(header, "p", description, "form-help");
    return h;
  }
  function list(parent, items) {
    const ul = append(parent, "ul", undefined, "tutoria-list");
    items.forEach(text => append(ul, "li", text)); return ul;
  }
  function openLesson(id) { lessonId = id; topicId = null; render(); host.querySelectorAll("h2")[0]?.focus(); }
  function openTopic(id) { topicId = id; lessonId = null; render(); host.querySelectorAll("h2")[0]?.focus(); }
  function startPractice(id) {
    if (window.ConfIAShell?.navigate("student", "tutoria/practice") === false) return;
    if (id) window.ConfIAWorkspace?.practiceProblem(id);
  }
  function featured(parent) {
    const lesson = demo.topics.flatMap(topic => topic.lessons).find(item => item.id === demo.featured.lessonId);
    const card = append(parent, "article", undefined, "card tutoria-featured"); badge(card, "Conteúdo demonstrativo");
    append(card, "p", "CONTEÚDO EM DESTAQUE", "eyebrow");
    append(card, "h2", lesson.title); append(card, "p", lesson.description);
    append(card, "p", `${demo.featured.topic} · ${demo.featured.level} · ${demo.featured.minutes} min estimados (ilustrativo)`, "form-help");
    list(card, demo.featured.objectives);
    const actions = append(card, "div", undefined, "action-row");
    link(actions, "Ver conteúdo", "content", () => openLesson(lesson.id), true);
    link(actions, "Praticar questões", "questions");
    math(card, String.raw`\(f(x)=2x+1\)`);
    return card;
  }
  function recommendations(parent) {
    const section = append(parent, "section", undefined, "card");
    badge(section, "Sugestões ilustrativas"); append(section, "h2", "Recomendado para você");
    for (const item of demo.recommendations) {
      const card = append(section, "article", undefined, "tutoria-list-item");
      append(card, "h3", item.title); append(card, "p", item.description, "form-help");
      link(card, "Explorar", item.destination, item.lessonId ? () => openLesson(item.lessonId) : null);
    }
  }
  function activities(parent, full = false) {
    const section = append(parent, "section", undefined, "card");
    append(section, "h2", full ? "Minhas tentativas" : "Atividades recentes");
    if (attempts.length) {
      badge(section, "Nesta sessão", "REAL");
      append(section, "p", "Registros desta sessão de prática. O histórico permanente está em desenvolvimento.", "form-help");
      for (const attempt of [...attempts].reverse().slice(0, full ? 20 : 3)) {
        const item = append(section, "article", undefined, "tutoria-list-item");
        append(item, "h3", attempt.title);
        append(item, "p", `${attempt.problemId} · ${new Date(attempt.createdAt).toLocaleString("pt-BR")} · Feedback demonstrativo`, "form-help");
        link(item, "Rever tentativa", "feedback", () => { chosenAttempt = attempt; render(); });
      }
    } else {
      badge(section, "Atividades ilustrativas");
      append(section, "p", "Conheça como suas atividades poderão aparecer aqui.", "form-help");
      for (const activity of demo.activities_demo) {
        const item = append(section, "article", undefined, "tutoria-list-item");
        append(item, "h3", activity.title); append(item, "p", activity.detail, "form-help");
        link(item, "Ver exemplo", activity.destination, activity.lessonId ? () => openLesson(activity.lessonId) : null);
      }
    }
    if (!full) link(section, "Ver minhas atividades", "attempts");
    else link(section, "Iniciar uma prática", "questions", null, true);
  }
  function home() {
    const intro = append(host, "section", undefined, "tutoria-intro");
    append(intro, "p", "SEU ESPAÇO DE APRENDIZAGEM", "eyebrow");
    append(intro, "h2", "Um próximo passo para cada descoberta.");
    append(intro, "p", "Explore uma ideia, pratique no caderno e volte ao seu raciocínio para avançar.");
    const modules = append(host, "div", undefined, "tutoria-module-grid");
    for (const item of demo.modules) {
      const card = append(modules, "article", undefined, "card tutoria-module"); card.dataset.module = item.id; card.dataset.state = item.state;
      const icon = append(card, "span", item.icon, "tutoria-icon"); icon.setAttribute("aria-hidden", "true");
      append(card, "h3", item.title); append(card, "p", item.description);
      if (item.state === "DEMO") badge(card, "Demonstração");
      link(card, item.id === "practice" ? "Começar a praticar" : `Abrir ${item.title.toLocaleLowerCase("pt-BR")}`, item.id, null, false);
    }
    const features = append(host, "div", undefined, "tutoria-feature-grid"); featured(features); recommendations(features);
    activities(host);
  }
  function content() {
    const topics = demo.topics;
    const lesson = topics.flatMap(topic => topic.lessons).find(item => item.id === lessonId);
    if (lesson) {
      heading(lesson.title, "Uma amostra da biblioteca de aprendizagem do TutorIA.", true);
      button(host, "← Voltar aos temas", () => { topicId = lessonId = null; render(); });
      const article = append(host, "article", undefined, "card tutoria-lesson");
      append(article, "h3", "Para compreender"); append(article, "p", lesson.description);
      append(article, "h3", "Observe este exemplo"); math(article, lesson.example);
      append(article, "h3", "Agora é com você");
      append(article, "p", "Explique a ideia com suas próprias palavras. Crie um exemplo e descreva cada etapa da resolução.");
      link(article, "Praticar questões do catálogo", "questions", null, true);

      append(article, "p", "O catálogo atual reúne problemas de diferentes assuntos; a seleção por conteúdo está em desenvolvimento.", "form-help");
      return;
    }
    const topic = topics.find(item => item.id === topicId);
    heading(topic?.title || "Conteúdos", topic?.description || "Uma biblioteca por temas para retomar conceitos e explorar novas ideias.", true);
    if (topic) button(host, "← Todos os temas", () => { topicId = null; render(); });
    const grid = append(host, "div", undefined, "tutoria-card-grid");
    for (const item of topic ? topic.lessons : topics) {
      const card = append(grid, "article", undefined, "card"); append(card, "h3", item.title); append(card, "p", item.description);
      if (item.lessons) append(card, "p", `${item.lessons.length} materiais demonstrativos`, "form-help");
      button(card, topic ? "Ver conteúdo" : "Explorar", () => topic ? openLesson(item.id) : openTopic(item.id));
    }
  }
  const metadataKeys = { theme: ["topic", "theme"], difficulty: ["difficulty"], grade: ["grade"], origin: ["origin", "source"] };
  function metadata(problem, key) { return metadataKeys[key].map(name => problem[name]).find(value => typeof value === "string" && value.trim()) || ""; }
  function questions() {
    heading("Banco de questões", "Questões reais do catálogo ConfIA. Escolha uma para praticar no caderno.");
    const form = append(host, "div", undefined, "card tutoria-filters");
    const label = append(form, "label", "Buscar questão", "form-field tutoria-search");
    const input = append(label, "input"); input.type = "search"; input.value = search; input.placeholder = "Código, título ou enunciado";
    input.setAttribute("aria-controls", "tutoria-question-results");
    const resultStatus = node("p", undefined, "action-message"); resultStatus.setAttribute("role", "status"); resultStatus.setAttribute("aria-live", "polite");
    const results = node("div", undefined, "tutoria-card-grid"); results.id = "tutoria-question-results";
    let missingMetadata = false;
    for (const [key, title] of [["theme", "Tema"], ["difficulty", "Dificuldade"], ["grade", "Série"], ["origin", "Origem"]]) {
      const wrapper = append(form, "label", title, "form-field");
      const select = append(wrapper, "select"); select.name = key;
      const values = [...new Set(catalog.map(problem => metadata(problem, key)).filter(Boolean))].sort();
      const all = append(select, "option", values.length ? "Todos" : "Em desenvolvimento"); all.value = "";
      values.forEach(value => { append(select, "option", value).value = value; });
      select.disabled = !values.length; missingMetadata ||= !values.length;
      select.value = values.includes(filters[key]) ? filters[key] : ""; filters[key] = select.value;
      select.setAttribute("aria-describedby", "tutoria-filter-help");
      select.addEventListener("change", () => { filters[key] = select.value; updateResults(); window.ConfIATutoriaAssistant?.sync(); });
    }
    const help = append(form, "p", missingMetadata ? "Alguns filtros estão em desenvolvimento: o catálogo ainda não informa esses dados. A busca por código, título e enunciado está disponível." : "Filtros usam somente informações disponíveis no catálogo.", "form-help tutoria-filter-help"); help.id = "tutoria-filter-help";
    host.appendChild(resultStatus); host.appendChild(results);
    function updateResults() {
      results.replaceChildren();
      if (catalogState !== "ready") {
        resultStatus.textContent = catalogState === "error" ? "Não foi possível carregar o catálogo. Atualize a página para tentar novamente." : "Carregando questões…";
        return;
      }
      const normalize = text => text.toLocaleLowerCase("pt-BR").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const query = normalize(search.trim());
      const visible = catalog.filter(problem => normalize(`${problem.problem_id || problem.id} ${problem.title || ""} ${problem.statement || ""}`).includes(query)
        && Object.keys(metadataKeys).every(key => !filters[key] || metadata(problem, key) === filters[key]));
      resultStatus.textContent = `${visible.length} questão(ões) encontrada(s).`;
      if (!visible.length) append(results, "p", catalog.length ? "Nenhuma questão corresponde à busca. Experimente outro termo." : "Nenhuma questão disponível no catálogo neste momento.", "empty-state");
      for (const problem of visible) {
        const id = problem.problem_id || problem.id;
        const card = append(results, "article", undefined, "card tutoria-question"); card.dataset.origin = "REAL";
        append(card, "p", id, "eyebrow"); append(card, "h3", problem.title || id);
        if (metadata(problem, "origin")) append(card, "p", metadata(problem, "origin"), "form-help");
        if (metadata(problem, "difficulty")) badge(card, metadata(problem, "difficulty"), "REAL");
        const excerpt = append(card, "details"); append(excerpt, "summary", "Ver enunciado"); math(excerpt, problem.statement || "Enunciado indisponível.");
        const resolve = button(card, "Resolver", () => startPractice(id), true); resolve.setAttribute("aria-label", `Resolver ${id}`);
      }
    }
    input.addEventListener("input", () => { search = input.value; updateResults(); }); updateResults();
  }
  function feedbackDocument(parent, attempt) {
    const realInput = Boolean(attempt);
    badge(parent, realInput ? "Tentativa desta sessão" : "Exemplo ilustrativo", realInput ? "REAL" : "DEMO");
    append(parent, "h3", realInput ? attempt.title : demo.feedback_demo.title);
    if (realInput) append(parent, "p", `${attempt.problemId} · ${new Date(attempt.createdAt).toLocaleString("pt-BR")}`, "form-help");
    math(parent, realInput ? attempt.solution : demo.feedback_demo.solution);
    const feedback = append(parent, "section", undefined, "tutoria-guidance"); badge(feedback, "Feedback demonstrativo");
    append(feedback, "p", realInput ? "Orientações ilustrativas de revisão, sem análise automática desta tentativa." : "Exemplo de como as orientações de aprendizagem poderão ser apresentadas.", "form-help");
    const guidance = realInput ? demo.practice_guidance_demo : demo.feedback_demo;
    for (const [title, key] of [[realInput ? "O que você já fez" : "O que você acertou", "positive"], ["Pontos para revisar", "review"], ["Próximo passo", "next"]]) {
      const section = append(feedback, "section"); append(section, "h4", title); append(section, "p", guidance[key]);
    }
  }
  function feedback() {
    heading("Feedback pedagógico", "Retome seu raciocínio, observe as etapas e planeje uma nova tentativa.");
    const attempt = chosenAttempt || attempts.at(-1);
    const card = append(host, "article", undefined, "card"); feedbackDocument(card, attempt);
    const actions = append(card, "div", undefined, "action-row");
    if (attempt) button(actions, "Experimente novamente", () => startPractice(attempt.problemId), true);
    else link(actions, "Começar uma prática", "questions", null, true);

    link(actions, "Minhas tentativas", "attempts");
  }
  function progressBar(parent, label, value) {
    append(parent, "p", `${label} · ${value}%`, "tutoria-progress-label");
    const progress = append(parent, "progress"); progress.max = 100; progress.value = value; progress.setAttribute("aria-label", `${label} — progresso ilustrativo`);
  }
  function trails() {
    heading("Trilhas de aprendizagem", "Percursos ilustrativos: os percentuais e as etapas concluídas não representam seu desempenho.", true);
    const grid = append(host, "div", undefined, "tutoria-card-grid");
    for (const trail of demo.trails) {
      const card = append(grid, "article", undefined, "card"); card.dataset.origin = "DEMO";
      append(card, "h3", trail.title); badge(card, trail.completed ? "Em andamento · exemplo" : "Para começar · exemplo");
      progressBar(card, `${trail.completed}/${trail.steps.length} etapas`, Math.round(trail.completed / trail.steps.length * 100));
      const steps = append(card, "ol", undefined, "tutoria-list");
      trail.steps.forEach((step, index) => append(steps, "li", `${index < trail.completed ? "✓ " : ""}${step}`));
      const actions = append(card, "div", undefined, "action-row");
      link(actions, "Explorar conteúdos", "content", () => openTopic(trail.topic)); link(actions, "Ver questões", "questions");
    }
  }
  function progress() {
    heading("Meu progresso", "Dados ilustrativos para apresentar a visão de acompanhamento. Não representam seu desempenho real.", true);
    const metrics = append(host, "div", undefined, "tutoria-metrics");
    for (const [title, value] of [["Temas estudados", demo.progress_demo.studiedTopics], ["Atividades recentes", demo.progress_demo.activities], ["Questões resolvidas", demo.progress_demo.questions]]) {
      const metric = append(metrics, "article", undefined, "card"); metric.dataset.origin = "DEMO";
      append(metric, "strong", String(value), "tutoria-metric-value"); append(metric, "h3", title); append(metric, "p", "Dado ilustrativo", "form-help");
    }
    const grid = append(host, "div", undefined, "tutoria-feature-grid");
    const themes = append(grid, "section", undefined, "card"); badge(themes, "Evolução ilustrativa por tema");
    append(themes, "h2", "Construindo conhecimentos"); demo.progress_demo.themes.forEach(theme => progressBar(themes, theme.title, theme.percent));
    recommendations(grid); activities(host);
  }
  function render() {
    host.replaceChildren();
    const renderers = { tutoria: home, "tutoria/content": content, "tutoria/questions": questions,
      "tutoria/feedback": feedback,
      "tutoria/trails": trails, "tutoria/progress": progress, "tutoria/attempts": () => activities(host, true) };
    renderers[activeView]?.();
    window.ConfIATutoriaAssistant?.sync();
  }
  function navigation() {
    const nav = document.querySelector("#tutoria-navigation"); nav.replaceChildren();
    for (const [title, view] of [["Visão geral", ""], ["Conteúdos", "content"], ["Banco de questões", "questions"], ["Minhas atividades", "attempts"], ["Meu progresso", "progress"]]) {
      const a = link(nav, title, view);
      const route = view ? `tutoria/${view}` : "tutoria";
      if (activeView === route || (view === "attempts" && activeView === "tutoria/feedback") || (view === "content" && activeView === "tutoria/trails") || (view === "questions" && activeView === "tutoria/practice")) a.setAttribute("aria-current", "page");
    }
  }
  window.ConfIATutoria = {
    studyContext() {
      if (activeView === "tutoria/questions") return { kind: "bank", origin: "REAL", theme: filters.theme || undefined };
      if (activeView === "tutoria/content") {
        const topic = demo.topics.find(topic => topic.lessons.some(lesson => lesson.id === lessonId)) || demo.topics.find(topic => topic.id === topicId);
        const lesson = topic?.lessons.find(lesson => lesson.id === lessonId);
        if (topic) return { kind: "content", origin: "DEMO", theme: topic.title, contentId: lesson?.id, contentTitle: lesson?.title };
      }
      if (activeView === "tutoria/feedback") {
        const attempt = chosenAttempt || attempts.at(-1);
        return attempt ? { kind: "attempt", origin: "REAL", problemId: attempt.problemId,
          problemTitle: catalog.find(problem => (problem.problem_id || problem.id) === attempt.problemId)?.title || attempt.problemId, attemptText: attempt.solution }
          : { kind: "attempt", origin: "DEMO", contentTitle: demo.feedback_demo.title, attemptText: demo.feedback_demo.solution };
      }
      return { kind: "home", origin: "REAL" };
    },
    show(view) { activeView = view; navigation(); this.updateContext(); render(); },
    updateContext() {
      document.querySelector("#tutoria-student-context").textContent = `${window.ConfIAAuthUser?.display_name || "Sua área de estudo"} · ${document.querySelector("#student-institutional-context").textContent || "Contexto escolar nesta sessão"}`;
    },
    catalogChanged(items, failed = false) {
      catalog = Array.isArray(items) ? items.filter(item => item && (item.problem_id || item.id)) : [];
      catalogState = failed ? "error" : "ready";
      if (activeView === "tutoria/questions") render();
    },
    requestFeedback(context) {
      // Until a dedicated pedagogical service exists, this adapter is explicitly demonstrative.
      // It MUST NOT fall back to the exam auditor or write institutional submissions.
      return Promise.resolve({ problem_id: context.problem_id, tutoria_feedback: { origin: "DEMO", ...demo.practice_guidance_demo } });
    },
    recordAttempt(analysis) {
      if (analysis.context.mode !== "practice" || analysis.data.tutoria_feedback?.origin !== "DEMO") return;
      const attempt = { origin: "REAL", feedbackOrigin: "DEMO", problemId: analysis.context.problem_id,
        title: `Tentativa ${attempts.filter(item => item.problemId === analysis.context.problem_id).length + 1}`,
        solution: analysis.context.solution, createdAt: new Date().toISOString(), sequence: analysis.context.sequence };
      attempts.push(attempt); chosenAttempt = attempt;
      if (["tutoria", "tutoria/attempts", "tutoria/feedback"].includes(activeView)) render();
    },
    renderPracticeFeedback(target, analysis, stale, pending) {
      target.replaceChildren();
      if (!analysis) { append(target, "p", pending ? "Preparando orientações…" : "Registre sua solução e peça feedback para conhecer a experiência de revisão.", "empty-state"); return; }
      const attempt = attempts.find(item => item.sequence === analysis.context.sequence && item.problemId === analysis.context.problem_id);
      if (!attempt) { append(target, "p", "Peça feedback para esta tentativa.", "empty-state"); return; }
      if (stale) append(target, "p", "Registro de uma versão anterior. Sua solução foi alterada depois deste feedback.", "alert");
      feedbackDocument(target, attempt);
      link(target, "Abrir feedback pedagógico", "feedback", () => { chosenAttempt = attempt; render(); });
    },
  };
  if (window.ConfIAWorkspace?.catalogState !== "loading") window.ConfIATutoria.catalogChanged(window.ConfIAWorkspace?.catalog, window.ConfIAWorkspace?.catalogState === "error");
})();
