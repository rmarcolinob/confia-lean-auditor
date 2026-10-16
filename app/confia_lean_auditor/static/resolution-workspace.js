/* UI-02: one response context; /capture owns all ink, persistence and submission. */
(function resolutionWorkspace() {
  "use strict";
  const get = id => document.querySelector(`#${id}`);
  const frame = get("resolution-notebook");
  const entries = new Map();
  const receipts = new Map();
  let active = false;
  let mode = null;
  let response = "notebook";
  let notebook = null;
  let currentKey = null;
  let loaded = false;
  let ready = false;
  let presentationRegistry = [];

  function setCopy(id, value) {
    const node = get(id);
    if (node.textContent !== value) node.textContent = value;
  }
  function remember() {
    if (!currentKey || mode !== "practice") return;
    entries.set(currentKey, { solution: solutionInput.value, analysis: studentAnalysis, version: studentVersion });
  }
  function restore(context) {
    const key = `${context.problem_id}:${context.draft_id}`;
    if (key !== currentKey) {
      remember();
      currentKey = key;
      const entry = entries.get(key);
      solutionInput.value = entry?.solution || "";
      studentAnalysis = mode === "practice" ? entry?.analysis || null : null;
      studentVersion = entry?.version || 0;
      get("practice-response").open = response === "typed";
      delete resultPanel.dataset.analysisRenderKey;
    }
    notebook = context;
  }
  function command(action, values = {}) {
    if (loaded) frame.contentWindow.postMessage({ type: "confia-workspace-command", action, ...values }, location.origin);
  }
  function notebookAction(action, values = {}) {
    if (!ready || !notebook?.controls?.document_id) return;
    command(action, { problem_id: problemSelect.value, mode, document_id: notebook.controls.document_id, ...values });
  }
  function renderNotebookControls() {
    const controls = ready ? notebook?.controls : null;
    const submission = mode === "submission";
    get("workspace-submission-actions").hidden = !submission;
    get("workspace-recognition-actions").hidden = !submission;
    setCopy("workspace-draft-persistence", controls?.persistence || "Abrindo o caderno…");
    get("workspace-draft-persistence").dataset.state = controls?.persistence_kind || "idle";
    setCopy("workspace-capture-status", controls?.status || "");
    get("workspace-capture-status").dataset.kind = controls?.status_kind || "info";
    const versions = get("workspace-saved-document");
    const selected = versions.value;
    versions.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Selecione uma versão salva";
    versions.appendChild(placeholder);
    for (const saved of controls?.saved_documents || []) {
      const option = document.createElement("option");
      option.value = saved.id;
      option.textContent = saved.label;
      versions.appendChild(option);
    }
    versions.value = (controls?.saved_documents || []).some(saved => saved.id === selected) ? selected : "";
    get("workspace-open-document").disabled = !controls || !versions.value;
    get("workspace-new-draft").disabled = !controls;
    get("workspace-continue-draft").hidden = !controls?.frozen;
    get("workspace-continue-draft").disabled = !controls?.frozen;
    get("workspace-prepare-snapshot").disabled = !submission || !controls?.can_prepare;
    get("workspace-preview-writing").disabled = !submission || !controls?.can_preview;
    setCopy("workspace-preview-message", controls?.preview_message || "");
    get("workspace-preview-message").dataset.kind = controls?.preview_kind || "info";
    globalThis.ConfiaRecognitionView?.render(get("workspace-preview-result"), controls?.preview_segments || []);
    get("workspace-send-solution").disabled = !submission || !controls?.can_send;
    setCopy("workspace-send-solution", controls?.send_label || "Enviar solução");
    get("workspace-recognize-writing").disabled = !submission || !controls?.can_recognize;
    setCopy("workspace-recognize-writing", controls?.recognize_label || "Reconhecer escrita");
    setCopy("workspace-snapshot-message", controls?.snapshot_message || "");
    setCopy("workspace-submission-message", controls?.submission_message || "");
    get("workspace-submission-message").dataset.kind = controls?.submission_kind || "info";
    setCopy("workspace-submission-receipt", controls?.submission_receipt || "");
    get("workspace-submission-receipt").hidden = !controls?.submission_receipt;
    setCopy("workspace-recognition-message", controls?.recognition_message || "");
    globalThis.ConfiaRecognitionView?.render(get("workspace-recognition-preview"), controls?.recognition_segments || []);
    setCopy("workspace-document-state", controls?.document_state || "");
    setCopy("workspace-document-id", controls ? `Identificador: ${controls.document_id}` : "");
    setCopy("workspace-storage-state", controls?.storage_state || "");
    get("workspace-export-json").disabled = !controls;
    get("workspace-export-png").disabled = !controls;
  }
  function configure() {
    command("configure", { problem_id: problemSelect.value, mode });
  }
  function setNotebookProblemExpanded(expanded) {
    get("notebook-problem-body").hidden = !expanded;
    get("toggle-notebook-problem").setAttribute("aria-expanded", String(expanded));
    setCopy("toggle-notebook-problem", expanded ? "Recolher enunciado" : "Expandir enunciado");
  }
  function display() {
    get("question-picker").hidden = active;
    get("resolution-workspace").hidden = !active;
    get("response-switch").hidden = mode !== "practice";
    get("notebook-surface").hidden = !active || !mode || (mode === "practice" && response === "typed");
    get("practice-response").hidden = !active || mode !== "practice";
    get("typed-problem-context").hidden = !active || mode !== "practice" || response !== "typed";
    setCopy("typed-solution-heading", response === "typed" ? "Solução digitada" : "Representação digitada para análise");
    get("handwriting-analysis-note").hidden = response === "typed";
    setCopy("prepare-analysis-label", response === "typed" ? "Solução digitada" : "Preparar análise");
    get("prepare-analysis-note").hidden = response === "typed";
    setCopy("resolution-title", mode === "practice" ? "Prática com feedback" : mode === "submission" ? "Solução para envio" : "Como você quer trabalhar esta questão?");
    setCopy("workspace-status", !mode ? "Escolha a finalidade da resolução." : !ready
      ? "Abrindo o caderno da questão selecionada…"
      : mode === "practice" ? "Resolva no caderno e use sua versão digitada para a Análise ConfIA." : "Prepare uma versão congelada e envie para receber o recibo do ConfIA.");
    for (const value of ["practice", "submission"]) {
      const button = get(`${value}-mode`);
      button.setAttribute("aria-pressed", String(mode === value));
      button.classList.toggle("is-active", mode === value);
    }
    for (const value of ["notebook", "typed"]) {
      const button = get(`${value}-response`);
      button.setAttribute("aria-pressed", String(response === value));
      button.classList.toggle("is-active", response === value);
    }
    get("feedback-actions").hidden = !studentAnalysis || mode !== "practice";
    auditButton.disabled = !ready || mode !== "practice" || studentAuditPending || !selectedProblem();
    get("reanalyze-solution").disabled = auditButton.disabled;
    // Compact navigation reserves the full width for the validated notebook.
    const resolving = active && !get("student-area").hidden && get("student-area").dataset.view === "resolve";
    document.body.dataset.resolutionActive = String(resolving);
    // Practice keeps the focused chrome; both notebook modes present the question above the iframe.
    const handwriting = resolving && mode === "practice" && response === "notebook";
    document.body.dataset.handwritingFocus = String(handwriting);
    get("notebook-problem-context").hidden = !resolving || !mode || (mode === "practice" && response === "typed");
    renderNotebookControls();
  }
  function chooseMode(value) {
    if (!["practice", "submission"].includes(value)) return;
    if (mode === "practice") remember();
    mode = value;
    get("practice-response").open = value === "practice" && response === "typed";
    setStatus(value === "practice" ? "Prática com feedback" : "Solução para envio", "idle");
    if (mode === "submission") {
      studentAnalysis = null;
      clearNode(resultPanel);
    } else {
      studentAnalysis = entries.get(currentKey)?.analysis || null;
      renderStudentAnalysis();
    }
    ready = false;
    notebook = null;
    if (!loaded) {
      // The iframe is created once. Question/mode changes reuse this exact notebook.
      const initial = new URLSearchParams(location.search);
      const draft = initial.get("problem_id") === problemSelect.value ? initial.get("draft_id") : null;
      frame.src = `/capture?embedded=1&problem_id=${encodeURIComponent(problemSelect.value)}&mode=${mode}${draft ? `&draft_id=${encodeURIComponent(draft)}` : ""}&ui=ui-05-fit-notebook`;
      loaded = true;
    } else configure();
    display();
    window.ConfIAShell?.refreshStudent();
  }
  function open() {
    if (!selectedProblem()) return;
    active = true;
    display();
    get("resolution-title").focus();
  }
  function changeProblem() {
    remember();
    active = false;
    ready = false;
    notebook = null;
    currentKey = null;
    mode = null;
    response = "notebook";
    get("practice-response").open = false;
    setNotebookProblemExpanded(true);
    solutionInput.value = "";
    studentAnalysis = null;
    clearNode(resultPanel);
    display();
    renderStudentAnalysis();
    window.ConfIAShell?.refreshStudent();
  }
  function renderReceipts() {
    const list = get("student-receipt-list");
    list.replaceChildren();
    if (!receipts.size) appendTextElement(list, "p", "empty-state", "Nenhum recibo nesta sessão. O salvamento do rascunho não confirma envio.");
    for (const receipt of receipts.values()) {
      const article = appendTextElement(list, "article", "local-submission", "");
      appendTextElement(article, "h3", "", `Questão ${receipt.problem_id}`);
      appendTextElement(article, "p", "", `Recebida pelo ConfIA · ${formatDateTime(receipt.received_at)}`);
      appendTextElement(article, "p", "", `Número do envio: ${receipt.submission_id}`);
      appendTextElement(article, "p", "", `Versão enviada: ${receipt.snapshot_id}`);
    }
  }
  function analysisContext() {
    return { mode, draft_id: notebook?.draft_id, local_snapshot_id: notebook?.local_snapshot_id || null,
      question_presentation_version: notebook?.question_presentation_version ?? null, ink_version: notebook?.ink_version };
  }
  function owns(context) {
    return mode === "practice" && context.mode === "practice" && context.problem_id === problemSelect.value && context.draft_id === notebook?.draft_id;
  }
  window.ConfIAWorkspace = {
    get mode() { return mode; },
    get active() { return active; },
    get ready() { return ready; },
    display, analysisContext, owns,
    canAnalyze: () => active && ready && mode === "practice",
    contextIsStale: context => !owns(context) || context.ink_version !== notebook?.ink_version || context.question_presentation_version !== notebook?.question_presentation_version,
    rememberText() { if (mode === "practice") remember(); },
    recordAnalysis(analysis) {
      const key = `${analysis.context.problem_id}:${analysis.context.draft_id}`;
      const entry = entries.get(key) || { solution: analysis.context.solution, version: analysis.context.version };
      entries.set(key, { ...entry, analysis });
      if (owns(analysis.context)) studentAnalysis = analysis;
      display();
    },
    onProblemSelected: changeProblem,
    catalogReady() {
      const initial = new URLSearchParams(location.search).get("problem_id");
      if (initial && problems.some(p => (p.problem_id || p.id) === initial)) {
        problemSelect.value = initial;
        renderExamples(); renderProblemStatement();
        open();
        const purpose = new URLSearchParams(location.search).get("workspace_mode");
        if (purpose) chooseMode(purpose);
      }
      get("resolve-question").disabled = !selectedProblem();
      this.renderMath();
    },
    renderMath() {
      const problem = selectedProblem();
      const options = { problemId: problemSelect.value, registry: presentationRegistry };
      globalThis.ConfiaProblemMath?.render(problemStatementText, get("catalog-math-message"), options);
      get("typed-problem-title").textContent = problem ? `${problemSelect.value} · ${problem.title}` : "Selecione uma questão";
      get("typed-problem-statement").textContent = problem?.statement || "";
      globalThis.ConfiaProblemMath?.render(get("typed-problem-statement"), get("typed-math-message"), options);
      get("notebook-problem-code").textContent = problemSelect.value;
      get("notebook-problem-statement").textContent = problem?.statement || "";
      globalThis.ConfiaProblemMath?.render(get("notebook-problem-statement"), get("notebook-math-message"), options);
    },
  };
  window.addEventListener("message", event => {
    if (event.origin !== location.origin || event.source !== frame.contentWindow) return;
    if (event.data?.type === "confia-workspace-navigation" && event.data.destination === "teacher-submissions") {
      window.ConfIAShell?.navigate("teacher", "submissions");
      return;
    }
    if (event.data?.type !== "confia-notebook-context") return;
    const context = event.data.context;
    if (!context || !context.draft_id) return;
    // Receipts are emitted only by the existing, validated P2-CAP-02 sender.
    if (context.receipt && context.receipt.snapshot_id === context.local_snapshot_id && context.receipt.problem_id === context.problem_id) {
      receipts.set(context.receipt.submission_id, context.receipt);
      renderReceipts();
    }
    if (!active || !mode || context.problem_id !== problemSelect.value || context.mode !== mode) { configure(); return; }
    if (Number.isFinite(context.content_height) && context.content_height >= 640 && context.content_height <= 4000) {
      frame.style.height = `${context.content_height}px`;
    }
    restore(context);
    if (mode === "submission" && context.receipt) setStatus("Solução recebida pelo ConfIA", "success");
    ready = true;
    renderStudentAnalysis(); updateStudentAction(); display();
  });
  frame.addEventListener("load", configure);
  get("resolve-question").addEventListener("click", open);
  get("change-question").addEventListener("click", () => { active = false; display(); problemSelect.focus(); });
  get("practice-mode").addEventListener("click", () => chooseMode("practice"));
  get("submission-mode").addEventListener("click", () => chooseMode("submission"));
  get("toggle-notebook-problem").addEventListener("click", () => {
    setNotebookProblemExpanded(get("toggle-notebook-problem").getAttribute("aria-expanded") !== "true");
  });
  get("workspace-saved-document").addEventListener("change", () => {
    get("workspace-open-document").disabled = !ready || !notebook?.controls || !get("workspace-saved-document").value;
  });
  get("workspace-open-document").addEventListener("click", () => notebookAction("open-document", { saved_document_id: get("workspace-saved-document").value }));
  for (const action of ["new-draft", "continue-draft", "prepare-snapshot", "preview-writing", "send-solution", "recognize-writing", "export-json", "export-png"]) {
    get(`workspace-${action}`).addEventListener("click", () => notebookAction(action));
  }
  for (const value of ["notebook", "typed"]) get(`${value}-response`).addEventListener("click", () => {
    response = value;
    get("practice-response").open = value === "typed";
    display();
    if (value === "typed") solutionInput.focus();
  });
  function resume(typed) {
    if (!mode) { window.ConfIAShell?.navigate("student", "resolve"); return; }
    active = true;
    if (mode !== "practice") chooseMode("practice");
    response = typed ? "typed" : "notebook";
    get("practice-response").open = typed;
    window.ConfIAShell?.navigate("student", "resolve");
    display();
    if (typed) solutionInput.focus(); else frame.focus();
  }
  get("continue-solving").addEventListener("click", () => resume(false));
  get("edit-solution").addEventListener("click", () => resume(true));
  get("reanalyze-solution").addEventListener("click", auditCurrentSolution);
  fetch("/static/problem-presentations/registry.json", { headers: { Accept: "application/json" } })
    .then(r => r.ok ? r.json() : []).then(registry => {
      presentationRegistry = Array.isArray(registry) ? registry : [];
      renderProblemStatement();
    }).catch(() => {});
  // app.js starts the catalog request before this controller is registered.
  if (problems.length) window.ConfIAWorkspace.catalogReady();
  display();
})();
