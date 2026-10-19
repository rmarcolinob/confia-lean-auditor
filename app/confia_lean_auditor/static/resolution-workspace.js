/* UI-02: one response context; /capture owns all ink, persistence and submission. */
(function resolutionWorkspace() {
  "use strict";
  const get = id => document.querySelector(`#${id}`);
  const frame = get("resolution-notebook");
  const entries = new Map();
  const receipts = new Map();
  const StudentFlow = Object.freeze({ TUTOR: "TUTOR", EXAM: "EXAM" });
  const captureModes = { [StudentFlow.TUTOR]: "practice", [StudentFlow.EXAM]: "submission" };
  let active = false;
  let mode = null;
  let experience = null;
  let selectedExam = null;
  let selectedExamItem = null;
  let availableExams = [];
  let examsLoaded = false;
  let examsRequest = 0;
  let submissionsPending = false;
  let serverSubmissions = null;
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
    const ink = get("workspace-ink-toolbar");
    ink.hidden = !controls || get("notebook-surface").hidden;
    for (const [action, enabled] of Object.entries({
      "pen-mode": !controls?.frozen, "mouse-mode": !controls?.frozen,
      "draw-tool": !controls?.frozen, "erase-tool": !controls?.frozen,
      undo: controls?.can_undo, redo: controls?.can_redo,
      "previous-page": controls?.can_previous_page, "next-page": controls?.can_next_page,
      "add-page": controls?.can_add_page,
    })) get(`workspace-${action}`).disabled = !enabled;
    for (const [action, selected] of Object.entries({
      "pen-mode": controls?.input_mode === "pen", "mouse-mode": controls?.input_mode === "mouse",
      "draw-tool": controls?.active_tool === "draw", "erase-tool": controls?.active_tool === "erase",
    })) get(`workspace-${action}`).setAttribute("aria-pressed", String(selected));
    setCopy("workspace-page-indicator", controls ? `Página ${controls.page_index + 1} de ${controls.page_count}` : "Página —");
    const submission = mode === "submission";
    get("workspace-submission-actions").hidden = !submission;
    get("workspace-recognition-actions").hidden = !submission;
    get("workspace-tutor-actions").hidden = mode !== "practice" || get("notebook-surface").hidden;
    get("workspace-tutor-preview").disabled = mode !== "practice" || !controls?.can_tutor_preview;
    get("workspace-tutor-feedback").disabled = mode !== "practice" || !controls?.tutor_preview_segments?.length || studentAuditPending;
    get("workspace-tutor-new-attempt").disabled = mode !== "practice" || !controls;
    setCopy("workspace-tutor-message", controls?.tutor_preview_message || "Escreva no caderno e reconheça sua solução para pedir feedback.");
    get("workspace-tutor-message").dataset.kind = controls?.tutor_preview_kind || "info";
    globalThis.ConfiaRecognitionView?.render(get("workspace-tutor-result"), controls?.tutor_preview_segments || []);
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
  function submissionTarget() {
    return selectedExam && selectedExamItem && mode === "submission"
      ? `/assessments/${selectedExam.assessment.assessment_id}/items/${selectedExamItem.assessment_item_id}/submissions`
      : "/submissions";
  }
  function configure() {
    command("configure", { problem_id: problemSelect.value, mode, submission_target: submissionTarget() });
  }
  function setNotebookProblemExpanded(expanded) {
    get("notebook-problem-body").hidden = !expanded;
    get("toggle-notebook-problem").setAttribute("aria-expanded", String(expanded));
    setCopy("toggle-notebook-problem", expanded ? "Recolher enunciado" : "Expandir enunciado");
    updateToolbarOffset();
  }
  function updateToolbarOffset() {
    const statement = get("notebook-problem-context");
    const top = statement.hidden ? 0 : Math.ceil(statement.getBoundingClientRect().height);
    get("notebook-surface").style.setProperty("--statement-sticky-height", `${top}px`);
  }
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(updateToolbarOffset).observe(get("notebook-problem-context"));
  function display() {
    get("question-picker").hidden = active;
    get("resolution-workspace").hidden = !active;
    get("response-switch").hidden = mode !== "practice";
    get("resolution-mode-switch").hidden = Boolean(experience);
    get("notebook-surface").hidden = !active || !mode || (mode === "practice" && response === "typed");
    get("practice-response").hidden = !active || mode !== "practice";
    get("typed-problem-context").hidden = !active || mode !== "practice" || response !== "typed";
    setCopy("typed-solution-heading", response === "typed" ? "Solução digitada" : experience === StudentFlow.TUTOR ? "Representação da solução" : "Representação digitada para análise");
    get("handwriting-analysis-note").hidden = response === "typed";
    setCopy("prepare-analysis-label", response === "typed" ? "Solução digitada" : experience === StudentFlow.TUTOR ? "Revisar representação digitada" : "Preparar análise");
    if (experience === StudentFlow.TUTOR) {
      setCopy("prepare-analysis-note", "Use o texto para registrar e revisar seu raciocínio.");
      setCopy("handwriting-analysis-note", "Você pode registrar ou ajustar sua representação digitada. A escrita do caderno permanece preservada.");
    }
    get("prepare-analysis-note").hidden = response === "typed";
    get("tutoria-typed-feedback-note").hidden = experience !== StudentFlow.TUTOR;
    setCopy("resolution-title", mode === "practice" ? experience ? "TutorIA · prática com feedback" : "Prática com feedback"
      : mode === "submission" ? experience ? "Exames · solução para envio" : "Solução para envio" : "Como você quer trabalhar esta questão?");
    setCopy("workspace-status", !mode ? "Escolha a finalidade da resolução." : !ready
      ? "Abrindo o caderno da questão selecionada…"
      : mode === "practice" ? "Resolva no caderno, reconheça a escrita e peça feedback." : "Confira a leitura da sua solução e envie ao professor. O ConfIA confirmará o recebimento.");
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
    const resolving = active && !get("student-area").hidden && ["resolve", "tutoria/practice", "exams"].includes(get("student-area").dataset.view);
    document.body.dataset.resolutionActive = String(resolving);
    // Practice keeps the focused chrome; both notebook modes present the question above the iframe.
    const handwriting = resolving && mode === "practice" && response === "notebook";
    document.body.dataset.handwritingFocus = String(handwriting);
    get("notebook-problem-context").hidden = !resolving || !mode || (mode === "practice" && response === "typed");
    updateToolbarOffset();
    renderNotebookControls();
    window.ConfIATutoriaAssistant?.sync();
  }
  function chooseMode(value) {
    if (!["practice", "submission"].includes(value)) return;
    if (experience && value !== captureModes[experience]) return;
    if (experience === StudentFlow.EXAM && (!selectedExamItem || selectedExamItem.problem_id !== problemSelect.value)) return;
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
      const target = submissionTarget();
      frame.src = `/capture?embedded=1&problem_id=${encodeURIComponent(problemSelect.value)}&mode=${mode}${draft ? `&draft_id=${encodeURIComponent(draft)}` : ""}${target !== "/submissions" ? `&submission_target=${encodeURIComponent(target)}` : ""}&ui=p2-assmt-02`;
      loaded = true;
    } else configure();
    display();
    window.ConfIAShell?.refreshStudent();
  }
  function open() {
    if (!selectedProblem()) return;
    if (experience === StudentFlow.EXAM && (!selectedExamItem || selectedExamItem.problem_id !== problemSelect.value)) return;
    active = true;
    if (experience) chooseMode(captureModes[experience]);
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
    const items = document.body.classList?.contains("auth-enabled") && serverSubmissions ? serverSubmissions : [...receipts.values()];
    if (!items.length) appendTextElement(list, "p", "empty-state", "Nenhuma solução enviada ao professor.");
    for (const receipt of items) {
      const article = appendTextElement(list, "article", "local-submission", "");
      appendTextElement(article, "h3", "", `Questão ${receipt.problem_id}`);
      appendTextElement(article, "p", "", `Recebida pelo ConfIA · ${formatDateTime(receipt.received_at)}`);
      appendTextElement(article, "span", "status", "Enviada").dataset.kind = "info";
      const details = appendTextElement(article, "details", "receipt-details", "");
      appendTextElement(details, "summary", "", "Comprovante do envio");
      appendTextElement(details, "p", "", `Número do envio: ${receipt.submission_id}`);
      appendTextElement(details, "p", "", receipt.assessment_id ? `Exame: ${receipt.assessment_id}` : "Envio anterior sem avaliação vinculada");
      appendTextElement(details, "p", "", `Versão enviada: ${receipt.snapshot_id}`);
    }
  }
  async function loadSubmissions() {
    if (!document.body.classList?.contains("auth-enabled") || submissionsPending) { renderReceipts(); return; }
    submissionsPending = true;
    get("student-receipt-list").replaceChildren();
    appendTextElement(get("student-receipt-list"), "p", "action-message", "Carregando submissões…").setAttribute("role", "status");
    try {
      const response = await fetch("/submissions", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível carregar as submissões.");
      const data = await response.json();
      serverSubmissions = Array.isArray(data) ? data : [];
      renderReceipts();
    } catch (_) {
      const list = get("student-receipt-list");
      list.replaceChildren();
      appendTextElement(list, "p", "empty-state", "Não foi possível carregar as submissões. Tente abrir esta área novamente.");
    } finally { submissionsPending = false; }
  }
  function filterProblems(allowedIds) {
    for (const option of problemSelect.children) {
      option.hidden = Boolean(allowedIds) && !allowedIds.includes(option.value);
      option.disabled = option.hidden;
    }
    if (allowedIds?.length && !allowedIds.includes(problemSelect.value)) problemSelect.value = allowedIds[0];
    renderExamples(); renderProblemStatement();
    get("resolve-question").disabled = !selectedProblem();
  }
  function renderExams() {
    const list = get("student-exam-list");
    list.replaceChildren();
    if (!problems.length) { setCopy("student-exams-message", "Carregando catálogo de questões…"); return; }
    const exams = availableExams.filter(exam => exam?.items?.every(item => problems.some(p => (p.problem_id || p.id) === item.problem_id)));
    setCopy("student-exams-message", exams.length ? "Escolha uma avaliação da sua turma." : "Nenhum exame disponível para sua turma no momento.");
    get("student-exams-message").className = exams.length ? "action-message" : "empty-state";
    for (const group of ["Disponíveis", "Agendados", "Enviados", "Encerrados"]) {
      const members = exams.filter(exam => group === "Enviados" ? exam.submitted_item_ids.length === exam.items.length
        : exam.submitted_item_ids.length === exam.items.length ? false
          : ({ Disponíveis: "DISPONÍVEL", Agendados: "AGENDADO", Encerrados: "ENCERRADO" })[group] === exam.availability);
      if (!members.length) continue;
      appendTextElement(list, "h3", "", group);
      for (const exam of members) {
        const card = appendTextElement(list, "article", "local-submission exam-card", "");
        appendTextElement(card, "h4", "", exam.assessment.title);
        appendTextElement(card, "p", "exam-card-meta", `${exam.classroom_name} · ${exam.teacher_name}`);
        appendTextElement(card, "p", "exam-card-meta", `Prazo: ${formatDateTime(exam.assessment.closes_at)}`);
        appendTextElement(card, "p", "exam-card-progress", `${exam.items.length} questões · ${exam.submitted_item_ids.length}/${exam.items.length} enviadas`);
        const state = appendTextElement(card, "p", "status", examProgressStatus(exam));
        state.dataset.kind = exam.submitted_item_ids.length === exam.items.length ? "success" : exam.submitted_item_ids.length ? "info" : "neutral";
        if (exam.availability !== "DISPONÍVEL") appendTextElement(card, "span", "status", exam.availability === "AGENDADO" ? "Agendada" : "Encerrada").dataset.kind = "neutral";
        const corrected = exam.items.filter(item => releasedResult(exam, item)).length;
        if (corrected) appendTextElement(card, "p", "exam-card-meta", `Correção: ${corrected} de ${exam.items.length} questões corrigidas`);
        const button = appendTextElement(card, "button", "button button-primary", "Abrir avaliação");
        button.type = "button";
        button.addEventListener("click", () => openExam(exam));
      }
    }
  }
  function examProgressStatus(exam) {
    const sent = exam.submitted_item_ids.length;
    return sent === 0 ? "Não iniciada" : sent === exam.items.length ? "Concluída" : "Em andamento";
  }
  function releasedResult(exam, item) {
    return (exam.released_results || []).find(result => result.status === "corrected"
      && result.assessment_id === exam.assessment.assessment_id && result.item_id === item.assessment_item_id
      && result.problem_id === item.problem_id);
  }
  function renderExamDetail(exam) {
    setCopy("student-exams-message", "");
    setCopy("student-exam-title", exam.assessment.title);
    setCopy("student-exam-meta", `${exam.teacher_name} · ${exam.classroom_name} · ${formatDateTime(exam.assessment.opens_at)} até ${formatDateTime(exam.assessment.closes_at)}`);
    setCopy("student-exam-progress", `Progresso: ${exam.submitted_item_ids.length}/${exam.items.length} · ${examProgressStatus(exam)}`);
    setCopy("student-exam-instructions", exam.assessment.instructions);
    const list = get("student-exam-items");
    list.replaceChildren();
    for (const item of exam.items) {
      const card = appendTextElement(list, "article", "local-submission exam-item-card", "");
      appendTextElement(card, "h4", "", `Questão ${item.order} · ${item.problem_id}`);
      appendTextElement(card, "p", "exam-item-points", `${item.points.toLocaleString("pt-BR")} pontos`);
      const submitted = exam.submitted_item_ids.includes(item.assessment_item_id);
      const result = releasedResult(exam, item);
      const state = appendTextElement(card, "p", "status", result ? "Corrigida" : submitted ? "Enviada" : "Não enviada");
      state.dataset.kind = result ? "success" : submitted ? "info" : "neutral";
      if (result) {
        const format = value => Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
        const released = appendTextElement(card, "section", "student-result", "");
        appendTextElement(released, "p", "student-result-score", `Pontuação: ${format(result.final_points)} / ${format(result.max_points)}`);
        appendTextElement(released, "h5", "", "Feedback do professor");
        appendTextElement(released, "p", "student-teacher-feedback", result.teacher_feedback || "Nenhum feedback registrado.");
      } else if (submitted) appendTextElement(card, "p", "form-help", "Aguardando resultado do professor.");
      const button = appendTextElement(card, "button", "button button-primary", "Resolver");
      button.type = "button";
      button.hidden = submitted;
      button.disabled = exam.availability !== "DISPONÍVEL" || submitted;
      button.setAttribute("aria-label", `Resolver questão ${item.order}`);
      button.addEventListener("click", () => {
        selectedExamItem = item;
        experience = StudentFlow.EXAM;
        active = false;
        mode = null;
        filterProblems([item.problem_id]);
        get("resolve-question").textContent = "Resolver questão do exame";
        get("student-exams").hidden = true;
        get("student-workspace").hidden = false;
        display();
      });
    }
  }
  function openExam(exam) {
    selectedExam = exam;
    selectedExamItem = null;
    get("student-exam-list").hidden = true;
    get("student-exam-detail").hidden = false;
    renderExamDetail(exam);
    get("student-exam-title").focus();
  }
  async function loadExams() {
    const request = ++examsRequest;
    availableExams = []; examsLoaded = false;
    setCopy("student-exams-message", "Carregando exames…");
    get("student-exams-message").className = "action-message";
    get("student-exam-list").replaceChildren();
    get("student-exam-items").replaceChildren();
    get("student-exam-detail").hidden = true;
    get("student-exams").setAttribute("aria-busy", "true");
    try {
      const response = await fetch("/assessments", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível consultar as atividades da turma.");
      const data = await response.json();
      if (request !== examsRequest) return;
      availableExams = Array.isArray(data) ? data.filter(exam => exam?.assessment && Array.isArray(exam.items)) : [];
      examsLoaded = true;
      renderExams();
      if (selectedExam) {
        const refreshed = availableExams.find(exam => exam.assessment.assessment_id === selectedExam.assessment.assessment_id);
        if (refreshed) {
          selectedExam = refreshed;
          get("student-exam-detail").hidden = false;
          renderExamDetail(refreshed);
        } else {
          selectedExam = null; selectedExamItem = null;
          get("student-exam-list").hidden = false;
        }
      }
    } catch (_) { if (request === examsRequest) setCopy("student-exams-message", "Não foi possível consultar os exames. Abra esta área novamente."); }
    finally { if (request === examsRequest) get("student-exams").setAttribute("aria-busy", "false"); }
  }
  function enter(view) {
    if (view === "tutoria/practice" || view === "resolve") {
      if (view === "resolve") { experience = null; display(); return; }
      if (experience === StudentFlow.TUTOR) { display(); return; }
      selectedExam = null;
      selectedExamItem = null;
      experience = StudentFlow.TUTOR;
      active = false;
      mode = null;
      response = "notebook";
      filterProblems(null);
      get("resolve-question").textContent = "Resolver no TutorIA";
      display();
    } else if (view === "exams") {
      selectedExam = null;
      selectedExamItem = null;
      get("student-exam-list").hidden = false;
      get("student-exam-detail").hidden = true;
      experience = StudentFlow.EXAM;
      active = false;
      mode = null;
      response = "notebook";
      filterProblems([]);
      display();
      loadExams();
    } else if (experience === StudentFlow.EXAM) {
      // Leaving the institutional view ends its UI mode without issuing a notebook command.
      experience = null; active = false; mode = null; selectedExam = null; selectedExamItem = null;
      display();
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
    get experience() { return experience; },
    get examSelected() { return Boolean(selectedExam); },
    get active() { return active; },
    get ready() { return ready; },
    get catalog() { return [...problems]; },
    get catalogLoaded() { return problemCatalogState === "ready"; },
    get catalogState() { return problemCatalogState; },
    get currentPracticeProblemId() { return active && experience === StudentFlow.TUTOR && mode === "practice" ? problemSelect.value : null; },
    studyContext() {
      const problem = selectedProblem();
      return this.currentPracticeProblemId && problem ? { kind: "question", origin: "REAL", problemId: problemSelect.value, problemTitle: problem.title } : null;
    },
    practiceProblem(id) {
      if (experience !== StudentFlow.TUTOR || !problems.some(problem => (problem.problem_id || problem.id) === id)) return false;
      problemSelect.value = id;
      renderExamples(); renderProblemStatement(); changeProblem(); open();
      return true;
    },
    display, enter, loadSubmissions, analysisContext, owns,
    canAnalyze: () => active && ready && mode === "practice",
    contextIsStale: context => !owns(context) || context.ink_version !== notebook?.ink_version || context.question_presentation_version !== notebook?.question_presentation_version,
    rememberText() { if (mode === "practice") remember(); },
    recordAnalysis(analysis) {
      const key = `${analysis.context.problem_id}:${analysis.context.draft_id}`;
      const entry = entries.get(key) || { solution: analysis.context.solution, version: analysis.context.version };
      entries.set(key, { ...entry, analysis });
      if (owns(analysis.context)) studentAnalysis = analysis;
      if (analysis.data.tutoria_feedback) window.ConfIATutoria?.recordAttempt(analysis);
      display();
    },
    onProblemSelected: changeProblem,
    catalogReady() {
      window.ConfIATutoria?.catalogChanged(problems);
      const initial = new URLSearchParams(location.search).get("problem_id");
      if (["resolve", "tutoria/practice"].includes(get("student-area").dataset.view) && initial && problems.some(p => (p.problem_id || p.id) === initial)) {
        problemSelect.value = initial;
        renderExamples(); renderProblemStatement();
        open();
        const purpose = new URLSearchParams(location.search).get("workspace_mode");
        if (purpose) chooseMode(purpose);
      }
      get("resolve-question").disabled = !selectedProblem();
      this.renderMath();
      if (examsLoaded) renderExams();
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
    if (context.mode === "submission" && context.receipt && context.receipt.snapshot_id === context.local_snapshot_id && context.receipt.problem_id === context.problem_id) {
      receipts.set(context.receipt.submission_id, context.receipt);
      renderReceipts();
      if (selectedExam && context.receipt.assessment_id === selectedExam.assessment.assessment_id) loadExams();
    }
    if (typeof context.submission_target === "string" && context.submission_target !== submissionTarget()) configure();
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
  get("student-exam-back").addEventListener("click", () => {
    selectedExam = null; selectedExamItem = null;
    get("student-exam-list").hidden = false;
    get("student-exam-detail").hidden = true;
  });
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
  get("workspace-tutor-preview").addEventListener("click", () => notebookAction("tutor-preview"));
  get("workspace-tutor-new-attempt").addEventListener("click", () => notebookAction("new-draft"));
  get("workspace-tutor-feedback").addEventListener("click", () => {
    if (mode !== "practice" || !ready || !notebook?.controls?.tutor_preview_segments?.length) return;
    const recognized = notebook.controls.tutor_preview_segments.map(segment => segment.text || segment.latex || "").filter(Boolean).join("\n").trim();
    if (!recognized) return;
    solutionInput.value = recognized;
    studentContextChanged();
    auditCurrentSolution();
  });
  for (const action of ["pen-mode", "mouse-mode", "draw-tool", "erase-tool", "undo", "redo", "previous-page", "next-page", "add-page"]) {
    get(`workspace-${action}`).addEventListener("click", () => notebookAction(action));
  }
  for (const value of ["notebook", "typed"]) get(`${value}-response`).addEventListener("click", () => {
    response = value;
    get("practice-response").open = value === "typed";
    display();
    if (value === "typed") solutionInput.focus();
  });
  function resume(typed) {
    const route = experience === StudentFlow.TUTOR ? "tutoria/practice" : "resolve";
    if (!mode) { window.ConfIAShell?.navigate("student", route); return; }
    active = true;
    if (mode !== "practice") chooseMode("practice");
    response = typed ? "typed" : "notebook";
    get("practice-response").open = typed;
    window.ConfIAShell?.navigate("student", route);
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
