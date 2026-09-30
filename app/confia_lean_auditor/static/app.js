const problemSelect = document.querySelector("#problem-select");
const exampleSelect = document.querySelector("#example-select");
const loadExampleButton = document.querySelector("#load-example");
const auditButton = document.querySelector("#audit-button");
const solutionInput = document.querySelector("#solution-input");
const resultPanel = document.querySelector("#result-panel");
const serviceStatus = document.querySelector("#service-status");
const problemTitle = document.querySelector("#problem-title");
const problemStatementText = document.querySelector("#problem-statement-text");
const tabButtons = document.querySelectorAll("[data-tab-target]");
const tabPanels = document.querySelectorAll(".tab-panel");
const studentModeButtons = document.querySelectorAll("[data-student-mode]");
const studentModeNote = document.querySelector("#student-mode-note");
const studentNameField = document.querySelector("#student-name-field");
const studentNameInput = document.querySelector("#student-name-input");
const exampleControls = document.querySelector(".example-controls");
const realSubmissionList = document.querySelector("#real-submission-list");
const demoSubmissionList = document.querySelector("#demo-submission-list");
const teacherStudentName = document.querySelector("#teacher-student-name");
const teacherProblemTitle = document.querySelector("#teacher-problem-title");
const teacherSubmissionStatus = document.querySelector("#teacher-submission-status");
const teacherSolution = document.querySelector("#teacher-solution");
const teacherAuditButton = document.querySelector("#teacher-audit-button");
const teacherCorrectionPanel = document.querySelector("#teacher-correction-panel");
const approveCorrectionButton = document.querySelector("#approve-correction");
const requestReviewButton = document.querySelector("#request-review");
const releaseFeedbackButton = document.querySelector("#release-feedback");
const teacherDecisionMessage = document.querySelector("#teacher-decision-message");

let problems = [];
let studentMode = "study";
let selectedTeacherSubmission = null;

const STUDENT_SUBMISSIONS_KEY = "confia_student_submissions";

const demoSubmissions = [
  {
    id: "demo-ana-f2q1",
    source: "demo",
    student_name: "Ana",
    problem_id: "ITA2025F2Q1",
    problem_title: "Exemplo demonstrativo F2Q1",
    solution:
      "A estudante reduziu corretamente algumas potências principais, mas deixou incompleta a comparação de coeficientes.",
    submitted_at: "2025-10-18T14:10:00.000Z",
    status: "precisa revisão",
  },
  {
    id: "demo-bruno-f2q8",
    source: "demo",
    student_name: "Bruno",
    problem_id: "ITA2025F2Q8",
    problem_title: "Exemplo demonstrativo F2Q8",
    solution:
      "O estudante apresenta a transformação de matriz e calcula parte do determinante, mas não explicita todos os sinais da soma alternada.",
    submitted_at: "2025-10-18T15:35:00.000Z",
    status: "pendente",
  },
  {
    id: "demo-carla-q4",
    source: "demo",
    student_name: "Carla",
    problem_id: "ITA2025Q4",
    problem_title: "Exemplo demonstrativo Q4",
    solution:
      "A estudante identifica candidatos para a composição, mas não justifica que as entradas em g são distintas.",
    submitted_at: "2025-10-19T09:20:00.000Z",
    status: "pendente",
  },
];

function setStatus(text, kind = "idle") {
  serviceStatus.textContent = text;
  serviceStatus.dataset.kind = kind;
}

function selectedProblem() {
  return problems.find((problem) => (problem.problem_id || problem.id) === problemSelect.value);
}

function setBusy(isBusy) {
  auditButton.disabled = isBusy;
  loadExampleButton.disabled = isBusy;
  problemSelect.disabled = isBusy;
  exampleSelect.disabled = isBusy;
  studentNameInput.disabled = isBusy;
  for (const button of studentModeButtons) {
    button.disabled = isBusy;
  }
}

function clearNode(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function appendTextElement(parent, tag, className, text) {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  parent.appendChild(element);
  return element;
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "data não informada";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function readLocalSubmissions() {
  try {
    const raw = localStorage.getItem(STUDENT_SUBMISSIONS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.map((submission) => ({ ...submission, source: "real" }));
  } catch (_error) {
    return [];
  }
}

function writeLocalSubmissions(submissions) {
  const cleanSubmissions = submissions.map(({ source, ...submission }) => submission);
  localStorage.setItem(STUDENT_SUBMISSIONS_KEY, JSON.stringify(cleanSubmissions));
}

function activateArea(targetId) {
  for (const button of tabButtons) {
    const isActive = button.dataset.tabTarget === targetId;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  }

  for (const panel of tabPanels) {
    const isActive = panel.id === targetId;
    panel.classList.toggle("is-active", isActive);
    panel.hidden = !isActive;
  }

  if (targetId === "teacher-area") {
    renderTeacherArea();
  }
}

function renderStudentStudyEmptyState() {
  clearNode(resultPanel);
  const empty = document.createElement("div");
  empty.className = "empty-state";
  appendTextElement(empty, "p", "eyebrow", "Auditoria CONFIA");
  appendTextElement(
    empty,
    "p",
    "",
    "Selecione uma questão, carregue um exemplo ou cole uma solução para começar."
  );
  resultPanel.appendChild(empty);
}

function renderStudentSubmitInfo(message) {
  clearNode(resultPanel);
  const empty = document.createElement("div");
  empty.className = "empty-state submit-state";
  appendTextElement(empty, "p", "eyebrow", "Envio ao professor");
  appendTextElement(
    empty,
    "p",
    "",
    message || "Neste modo, o aluno não recebe a correção automaticamente."
  );
  appendTextElement(
    empty,
    "p",
    "",
    "A solução ficará disponível na Área do Professor para auditoria e decisão docente."
  );
  resultPanel.appendChild(empty);
}

function setStudentMode(mode) {
  studentMode = mode;

  for (const button of studentModeButtons) {
    const isActive = button.dataset.studentMode === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  }

  const isSubmitMode = mode === "submit";
  studentNameField.hidden = !isSubmitMode;
  exampleControls.hidden = isSubmitMode;
  auditButton.textContent = isSubmitMode ? "Enviar solução ao professor" : "Auditar solução";
  studentModeNote.textContent = isSubmitMode
    ? "Neste modo, o aluno não recebe a correção automaticamente."
    : "Use o ConfIA para estudar com feedback pedagógico imediato.";

  if (isSubmitMode) {
    renderStudentSubmitInfo();
  } else {
    renderStudentStudyEmptyState();
  }
}

function renderExamples() {
  clearNode(exampleSelect);
  const problem = selectedProblem();
  if (!problem) {
    return;
  }

  for (const example of problem.examples) {
    const option = document.createElement("option");
    option.value = example.key;
    option.textContent = example.label;
    exampleSelect.appendChild(option);
  }
}

function renderProblemStatement() {
  const problem = selectedProblem();
  if (!problem) {
    problemTitle.textContent = "Selecione uma questão";
    problemStatementText.textContent = "O enunciado da questão selecionada aparecerá aqui.";
    return;
  }

  problemTitle.textContent = problem.title || problem.problem_id || problem.id;
  problemStatementText.textContent = problem.statement || "Enunciado não disponível.";
}

function renderProblems() {
  clearNode(problemSelect);

  for (const problem of problems) {
    const option = document.createElement("option");
    const problemId = problem.problem_id || problem.id;
    option.value = problemId;
    option.textContent = `${problemId} - ${problem.title}`;
    problemSelect.appendChild(option);
  }

  renderExamples();
  renderProblemStatement();
}

function resultLabel(result) {
  const labels = {
    correto: "correto",
    parcialmente_correto: "parcialmente correto",
    insuficiente: "insuficiente",
    incorreto: "incorreto",
  };
  return labels[result] || result || "Não avaliado";
}

function reliabilityKind(text) {
  const normalized = (text || "").toLowerCase();
  if (normalized.includes("alta")) {
    return "high";
  }
  if (normalized.includes("média") || normalized.includes("media")) {
    return "medium";
  }
  if (normalized.includes("baixa")) {
    return "low";
  }
  return "unknown";
}

function makeBadge(text, kind) {
  const badge = document.createElement("span");
  badge.className = "badge";
  badge.dataset.kind = kind || "neutral";
  badge.textContent = text;
  return badge;
}

function renderEvidenceItems(items) {
  const section = document.createElement("section");
  section.className = "evidence-section";
  appendTextElement(section, "h3", "section-title", "Evidências");

  if (!items || items.length === 0) {
    appendTextElement(
      section,
      "p",
      "muted",
      "Nenhuma evidência específica foi destacada para esta solução."
    );
    return section;
  }

  const list = document.createElement("div");
  list.className = "evidence-list";

  for (const item of items) {
    const article = document.createElement("article");
    article.className = "evidence-item";

    const header = document.createElement("div");
    header.className = "evidence-header";
    appendTextElement(header, "strong", "evidence-title", item.title || "Evidência");
    header.appendChild(makeBadge(item.result || "avaliada", item.result || "neutral"));
    article.appendChild(header);

    if (item.evidence) {
      appendTextElement(article, "p", "evidence-quote", item.evidence);
    }

    appendTextElement(article, "p", "evidence-explanation", item.explanation || "");
    const reliability = appendTextElement(article, "p", "reliability-line", "");
    reliability.appendChild(
      makeBadge(item.reliability || "não avaliada", reliabilityKind(item.reliability))
    );
    list.appendChild(article);
  }

  section.appendChild(list);
  return section;
}

function renderAttentionPoints(points) {
  const section = document.createElement("section");
  section.className = "attention-section";
  appendTextElement(section, "h3", "section-title", "Pontos de atenção");

  if (!points || points.length === 0) {
    appendTextElement(
      section,
      "p",
      "muted",
      "Nenhum ponto de atenção adicional foi identificado."
    );
    return section;
  }

  const list = document.createElement("ul");
  for (const point of points) {
    appendTextElement(list, "li", "", point);
  }
  section.appendChild(list);
  return section;
}

function renderTechnicalDetails(data) {
  const details = document.createElement("details");
  details.className = "technical-details";

  const summary = document.createElement("summary");
  summary.textContent = "Detalhes técnicos";
  details.appendChild(summary);

  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(data, null, 2);
  details.appendChild(pre);

  return details;
}

function renderRubricSection(rubric) {
  const section = document.createElement("section");
  section.className = "rubric-section";
  appendTextElement(section, "h3", "section-title", "Critérios/lacunas");

  const items = rubric && Array.isArray(rubric.items) ? rubric.items : [];
  if (items.length === 0) {
    appendTextElement(section, "p", "muted", "Critérios da rubrica não disponíveis neste retorno.");
    return section;
  }

  const grid = document.createElement("div");
  grid.className = "teacher-grid";

  const metCard = document.createElement("article");
  metCard.className = "review-card";
  appendTextElement(metCard, "h3", "", "Critérios atendidos");
  const metList = document.createElement("ul");

  const gapCard = document.createElement("article");
  gapCard.className = "review-card";
  appendTextElement(gapCard, "h3", "", "Lacunas");
  const gapList = document.createElement("ul");

  for (const item of items) {
    const label = `${item.description || item.id}: ${item.points} / ${item.max_points}`;
    if (Number(item.points) >= Number(item.max_points)) {
      appendTextElement(metList, "li", "", label);
    } else {
      appendTextElement(gapList, "li", "", label);
    }
  }

  if (metList.childNodes.length === 0) {
    appendTextElement(metList, "li", "", "Nenhum critério integralmente atendido foi destacado.");
  }
  if (gapList.childNodes.length === 0) {
    appendTextElement(gapList, "li", "", "Nenhuma lacuna foi destacada.");
  }

  metCard.appendChild(metList);
  gapCard.appendChild(gapList);
  grid.appendChild(metCard);
  grid.appendChild(gapCard);
  section.appendChild(grid);
  return section;
}

function renderReport(data, targetPanel = resultPanel, options = {}) {
  const report = data.pedagogical_report;
  clearNode(targetPanel);

  if (!report) {
    appendTextElement(
      targetPanel,
      "div",
      "empty-state",
      "A auditoria terminou, mas não retornou relatório pedagógico."
    );
    targetPanel.appendChild(renderTechnicalDetails(data));
    return;
  }

  const isTeacher = options.context === "teacher";
  const header = document.createElement("section");
  header.className = "result-summary";
  header.dataset.result = report.result;

  const titleRow = document.createElement("div");
  titleRow.className = "result-heading";
  const titleCopy = document.createElement("div");
  appendTextElement(titleCopy, "p", "eyebrow", isTeacher ? "Correção assistida" : "Auditoria CONFIA");
  appendTextElement(
    titleCopy,
    "h2",
    "result-title",
    isTeacher ? "Painel de correção" : "Relatório pedagógico"
  );
  titleRow.appendChild(titleCopy);
  titleRow.appendChild(makeBadge(resultLabel(report.result), report.result || "neutral"));
  header.appendChild(titleRow);

  appendTextElement(header, "p", "summary-text", report.summary || "");

  const metrics = document.createElement("div");
  metrics.className = "metrics";
  const scoreMetric = appendTextElement(metrics, "div", "metric", "");
  appendTextElement(scoreMetric, "span", "metric-label", isTeacher ? "Nota sugerida" : "Pontuação");
  appendTextElement(scoreMetric, "strong", "metric-value", `${report.score} / ${report.max_score}`);

  const reliabilityMetric = appendTextElement(metrics, "div", "metric", "");
  appendTextElement(reliabilityMetric, "span", "metric-label", "Confiabilidade");
  reliabilityMetric.appendChild(
    makeBadge(report.reliability || "não avaliada", reliabilityKind(report.reliability))
  );

  const resultMetric = appendTextElement(metrics, "div", "metric", "");
  appendTextElement(resultMetric, "span", "metric-label", isTeacher ? "Resultado sugerido" : "Resultado");
  resultMetric.appendChild(makeBadge(resultLabel(report.result), report.result || "neutral"));
  header.appendChild(metrics);

  targetPanel.appendChild(header);
  targetPanel.appendChild(renderEvidenceItems(report.evidence_items));
  targetPanel.appendChild(renderAttentionPoints(report.attention_points));
  if (isTeacher) {
    targetPanel.appendChild(renderRubricSection(data.rubric_assessment));
  }
  targetPanel.appendChild(renderTechnicalDetails(data));
}

function renderError(message, targetPanel = resultPanel) {
  clearNode(targetPanel);
  const panel = document.createElement("section");
  panel.className = "error-panel";
  appendTextElement(panel, "h2", "result-title", "Não foi possível auditar");
  appendTextElement(panel, "p", "summary-text", message);
  targetPanel.appendChild(panel);
}

function currentProblemTitle(problemId) {
  const problem = problems.find((item) => (item.problem_id || item.id) === problemId);
  if (!problem) {
    return problemId;
  }
  return problem.title || problem.problem_id || problem.id;
}

function createSubmissionButton(submission) {
  const button = document.createElement("button");
  button.className = "submission-row";
  button.type = "button";
  button.classList.toggle(
    "is-selected",
    selectedTeacherSubmission && selectedTeacherSubmission.id === submission.id
  );

  const name = appendTextElement(button, "strong", "", submission.student_name || "Aluno");
  name.title = submission.student_name || "Aluno";
  appendTextElement(button, "span", "", submission.problem_title || submission.problem_id || "Questão");
  appendTextElement(button, "span", "submission-date", formatDateTime(submission.submitted_at));
  button.appendChild(makeBadge(submission.status || "pendente", statusKind(submission.status)));

  button.addEventListener("click", () => {
    selectedTeacherSubmission = submission;
    teacherDecisionMessage.textContent = "";
    renderTeacherCorrectionEmpty();
    renderTeacherArea();
  });

  return button;
}

function statusKind(status) {
  const normalized = (status || "").toLowerCase();
  if (normalized.includes("aprov")) {
    return "high";
  }
  if (normalized.includes("revis") || normalized.includes("pendente")) {
    return "medium";
  }
  if (normalized.includes("devolutiva") || normalized.includes("audit")) {
    return "high";
  }
  return "neutral";
}

function renderSubmissionList(target, submissions, emptyText) {
  clearNode(target);
  if (!submissions.length) {
    appendTextElement(target, "p", "muted list-empty", emptyText);
    return;
  }

  for (const submission of submissions) {
    target.appendChild(createSubmissionButton(submission));
  }
}

function renderTeacherCorrectionEmpty(text = "Selecione uma submissão e audite com o ConfIA.") {
  clearNode(teacherCorrectionPanel);
  const empty = document.createElement("div");
  empty.className = "empty-state";
  appendTextElement(empty, "p", "eyebrow", "Painel de correção");
  appendTextElement(empty, "p", "", text);
  teacherCorrectionPanel.appendChild(empty);
}

function renderSelectedSubmission() {
  const submission = selectedTeacherSubmission;
  if (!submission) {
    teacherStudentName.textContent = "Selecione uma submissão";
    teacherProblemTitle.textContent = "-";
    teacherSubmissionStatus.textContent = "sem seleção";
    teacherSubmissionStatus.dataset.kind = "neutral";
    teacherSolution.textContent = "A solução enviada aparecerá aqui.";
    teacherAuditButton.disabled = true;
    teacherDecisionMessage.textContent = "";
    renderTeacherCorrectionEmpty();
    return;
  }

  teacherStudentName.textContent = submission.student_name || "Aluno";
  teacherProblemTitle.textContent = submission.problem_title || currentProblemTitle(submission.problem_id);
  teacherSubmissionStatus.textContent = submission.status || "pendente";
  teacherSubmissionStatus.dataset.kind = statusKind(submission.status);
  teacherSolution.textContent = submission.solution || "Solução não informada.";
  teacherAuditButton.disabled = false;
}

function renderTeacherArea() {
  const realSubmissions = readLocalSubmissions();
  const visibleDemoSubmissions = realSubmissions.length === 0 ? demoSubmissions : [];
  const allVisibleSubmissions = [...realSubmissions, ...visibleDemoSubmissions];

  if (
    selectedTeacherSubmission &&
    !allVisibleSubmissions.some((submission) => submission.id === selectedTeacherSubmission.id)
  ) {
    selectedTeacherSubmission = null;
  }

  if (!selectedTeacherSubmission && allVisibleSubmissions.length > 0) {
    selectedTeacherSubmission = allVisibleSubmissions[0];
  }

  renderSubmissionList(
    realSubmissionList,
    realSubmissions,
    "Nenhuma submissão real foi enviada neste navegador."
  );
  renderSubmissionList(
    demoSubmissionList,
    visibleDemoSubmissions,
    realSubmissions.length > 0
      ? "Exemplos demonstrativos ficam ocultos quando há submissões recebidas neste navegador."
      : "Use estes exemplos enquanto não houver submissões recebidas."
  );
  renderSelectedSubmission();
}

function updateSelectedSubmissionStatus(status, message) {
  if (!selectedTeacherSubmission) {
    return;
  }

  selectedTeacherSubmission.status = status;
  if (selectedTeacherSubmission.source === "real") {
    const submissions = readLocalSubmissions().map((submission) => {
      if (submission.id === selectedTeacherSubmission.id) {
        return { ...submission, status };
      }
      return submission;
    });
    writeLocalSubmissions(submissions);
  }

  teacherDecisionMessage.textContent = message;
  renderTeacherArea();
}

function submitSolutionToTeacher() {
  const problem = selectedProblem();
  const solution = solutionInput.value.trim();
  const studentName = studentNameInput.value.trim();

  if (!problem) {
    renderStudentSubmitInfo("Selecione uma questão antes de enviar ao professor.");
    return;
  }
  if (!studentName) {
    renderStudentSubmitInfo("Informe o Nome do aluno antes de enviar ao professor.");
    studentNameInput.focus();
    return;
  }
  if (!solution) {
    renderStudentSubmitInfo("Digite ou cole uma solução antes de enviar ao professor.");
    return;
  }

  const problemId = problem.problem_id || problem.id;
  const submission = {
    id: `sub_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    student_name: studentName,
    problem_id: problemId,
    problem_title: problem.title || problemId,
    solution,
    submitted_at: new Date().toISOString(),
    status: "pendente",
  };
  const submissions = readLocalSubmissions();
  submissions.unshift(submission);
  writeLocalSubmissions(submissions);
  selectedTeacherSubmission = { ...submission, source: "real" };
  renderTeacherArea();
  setStatus("Solução enviada", "idle");
  renderStudentSubmitInfo(
    "Solução enviada ao professor. A correção será realizada na Área do Professor."
  );
}

async function loadProblems() {
  setStatus("Carregando", "busy");
  const response = await fetch("/problems");
  if (!response.ok) {
    throw new Error("Não foi possível carregar as questões.");
  }
  problems = await response.json();
  renderProblems();
  renderTeacherArea();
  setStatus("Pronto", "idle");
}

async function loadSelectedExample() {
  const problemId = problemSelect.value;
  const exampleKey = exampleSelect.value;

  setBusy(true);
  setStatus("Carregando exemplo", "busy");
  try {
    const response = await fetch(`/problems/${problemId}/examples/${exampleKey}`);
    if (!response.ok) {
      throw new Error("Não foi possível carregar o exemplo selecionado.");
    }
    const payload = await response.json();
    solutionInput.value = payload.solution || "";
    setStatus("Exemplo carregado", "idle");
  } catch (error) {
    renderError(error.message);
    setStatus("Erro", "error");
  } finally {
    setBusy(false);
  }
}

async function auditCurrentSolution() {
  const problemId = problemSelect.value;
  const solution = solutionInput.value.trim();

  if (!solution) {
    renderError("Digite ou carregue uma solução antes de auditar.");
    return;
  }

  setBusy(true);
  setStatus("Auditando", "busy");
  clearNode(resultPanel);
  appendTextElement(
    resultPanel,
    "div",
    "empty-state",
    "Auditando a solução. Este processo pode levar alguns instantes."
  );

  try {
    const response = await fetch("/audit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        problem_id: problemId,
        solution,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "A auditoria não foi concluída.");
    }

    const data = await response.json();
    renderReport(data);
    setStatus("Auditoria concluída", "idle");
  } catch (error) {
    renderError(error.message);
    setStatus("Erro", "error");
  } finally {
    setBusy(false);
  }
}

async function auditTeacherSubmission() {
  if (!selectedTeacherSubmission) {
    renderTeacherCorrectionEmpty("Selecione uma submissão antes de auditar.");
    return;
  }

  teacherAuditButton.disabled = true;
  setStatus("Auditando para o professor", "busy");
  renderTeacherCorrectionEmpty("Auditando a submissão com o ConfIA.");

  try {
    const response = await fetch("/audit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        problem_id: selectedTeacherSubmission.problem_id,
        solution: selectedTeacherSubmission.solution,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "A auditoria não foi concluída.");
    }

    const data = await response.json();
    renderReport(data, teacherCorrectionPanel, { context: "teacher" });
    updateSelectedSubmissionStatus(
      "auditada",
      "Auditoria sugerida pelo ConfIA registrada localmente para decisão do professor."
    );
    setStatus("Auditoria concluída", "idle");
  } catch (error) {
    renderError(error.message, teacherCorrectionPanel);
    setStatus("Erro", "error");
  } finally {
    teacherAuditButton.disabled = false;
  }
}

function handleStudentPrimaryAction() {
  if (studentMode === "submit") {
    submitSolutionToTeacher();
    return;
  }
  auditCurrentSolution();
}

problemSelect.addEventListener("change", () => {
  renderExamples();
  renderProblemStatement();
});
for (const button of tabButtons) {
  button.addEventListener("click", () => activateArea(button.dataset.tabTarget));
}
for (const button of studentModeButtons) {
  button.addEventListener("click", () => setStudentMode(button.dataset.studentMode));
}
loadExampleButton.addEventListener("click", loadSelectedExample);
auditButton.addEventListener("click", handleStudentPrimaryAction);
teacherAuditButton.addEventListener("click", auditTeacherSubmission);
approveCorrectionButton.addEventListener("click", () =>
  updateSelectedSubmissionStatus("correção aprovada", "Correção aprovada localmente pelo professor.")
);
requestReviewButton.addEventListener("click", () =>
  updateSelectedSubmissionStatus("revisão solicitada", "Revisão solicitada localmente pelo professor.")
);
releaseFeedbackButton.addEventListener("click", () =>
  updateSelectedSubmissionStatus("devolutiva liberada", "Devolutiva liberada localmente pelo professor.")
);

loadProblems().catch((error) => {
  renderError(error.message);
  setStatus("Erro", "error");
});
