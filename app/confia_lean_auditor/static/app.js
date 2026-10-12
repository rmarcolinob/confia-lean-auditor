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
const teacherDecisionMessage = document.querySelector("#teacher-decision-message");
const teacherAnalysisStatus = document.querySelector("#teacher-analysis-status");
const studentValidationMessage = document.querySelector("#student-validation-message");

let problems = [];
let studentMode = "study";
let selectedTeacherSubmission = null;
let studentVersion = 0;
let studentAnalysis = null;
let studentAuditPending = false;
let studentAuditContext = null;
let studentAuditSequence = 0;
let exampleSequence = 0;
let examplePending = false;
const teacherAnalyses = new Map();
const ANALYSIS_ERROR = "Não foi possível analisar esta solução agora. Confira a questão e tente novamente.";

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
  studentAuditPending = isBusy;
  updateStudentAction();
}

function studentResultIsStale() {
  return Boolean(studentAnalysis && (
    studentAnalysis.context.version !== studentVersion ||
    studentAnalysis.context.problem_id !== problemSelect.value ||
    studentAnalysis.context.solution !== solutionInput.value.trim() ||
    (typeof window !== "undefined" && window.ConfIAWorkspace?.contextIsStale(studentAnalysis.context))
  ));
}

function updateStudentAction() {
  const analyzing = studentMode === "study" && studentAuditPending;
  auditButton.disabled = analyzing || !selectedProblem();
  auditButton.setAttribute("aria-busy", String(analyzing));
  auditButton.textContent = studentMode === "submit"
    ? "Salvar como envio de demonstração neste navegador"
    : analyzing ? "Analisando…" : studentResultIsStale() ? "Analisar novamente" : "Analisar minha solução";
  if (typeof window !== "undefined") window.ConfIAWorkspace?.display();
  loadExampleButton.disabled = examplePending || !selectedProblem() || !exampleSelect.value;
}

function clearStudentValidation() {
  studentValidationMessage.textContent = "";
  for (const field of [problemSelect, solutionInput, studentNameInput]) {
    field.setAttribute("aria-invalid", "false");
  }
}

function studentValidation(field, message) {
  clearStudentValidation();
  field.setAttribute("aria-invalid", "true");
  studentValidationMessage.textContent = message;
  field.focus();
}

function studentContextChanged() {
  studentVersion += 1;
  if (typeof window !== "undefined") window.ConfIAWorkspace?.rememberText();
  clearStudentValidation();
  renderStudentAnalysis();
  updateStudentAction();
}

function renderAnalysisContext(panel, context, stale, analyzeAgain) {
  const block = appendTextElement(panel, "section", "analysis-context", "");
  block.dataset.stale = String(stale);
  appendTextElement(block, "strong", "", stale ? "Análise de versão anterior" : "Análise atual");
  appendTextElement(block, "p", "", `Questão analisada: ${context.problem_id}`);
  if (stale) {
    appendTextElement(block, "p", "", "Esta análise corresponde a uma versão anterior da solução. Você alterou a solução ou trocou a questão depois de iniciar esta análise.");
    const again = appendTextElement(block, "button", "secondary-action", "Analisar novamente");
    again.type = "button";
    again.disabled = panel === resultPanel ? studentAuditPending : Boolean(teacherAnalyses.get(context.submission_id)?.pending);
    again.addEventListener("click", analyzeAgain);
  }
  const original = appendTextElement(block, "details", "", "");
  appendTextElement(original, "summary", "", "Solução enviada para esta análise");
  appendTextElement(original, "pre", "", context.solution);
}

function renderStudentAnalysis() {
  if (studentMode !== "study" || (typeof window !== "undefined" && window.ConfIAWorkspace && window.ConfIAWorkspace.mode !== "practice")) return;
  if (studentAnalysis) {
    const stale = studentResultIsStale();
    const renderKey = `${studentAnalysis.context.sequence}:${stale}:${studentAuditPending}`;
    // Repeated typing must not rebuild the report or collapse its disclosures.
    if (resultPanel.dataset.analysisRenderKey === renderKey) return;
    renderReport(studentAnalysis.data, resultPanel, {
      analysis: studentAnalysis, stale, analyzeAgain: auditCurrentSolution,
    });
    resultPanel.dataset.analysisRenderKey = renderKey;
  } else if (studentAuditPending && (typeof window === "undefined" || !window.ConfIAWorkspace || window.ConfIAWorkspace.owns(studentAuditContext))) {
    clearNode(resultPanel);
    appendTextElement(resultPanel, "p", "empty-state", "Analisando a solução enviada. Este processo pode levar alguns instantes.");
  } else {
    renderStudentStudyEmptyState();
  }
}

function clearNode(node) {
  if (node === resultPanel) delete node.dataset.analysisRenderKey;
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
  if (typeof window !== "undefined" && window.ConfIATeacher && !window.ConfIATeacher.canLeave()) return false;
  for (const button of tabButtons) {
    const isActive = button.dataset.tabTarget === targetId;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  }

  for (const panel of tabPanels) {
    const isActive = panel.id === targetId;
    panel.classList.toggle("is-active", isActive);
    panel.hidden = !isActive;
  }

  if (targetId === "teacher-area") {
    renderTeacherArea();
  }
  if (typeof window !== "undefined") window.ConfIAShell?.activateProfile(targetId);
  return true;
}

function renderStudentStudyEmptyState() {
  clearNode(resultPanel);
  const empty = document.createElement("div");
  empty.className = "empty-state";
  appendTextElement(empty, "p", "eyebrow", "Análise ConfIA");
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
  appendTextElement(empty, "p", "eyebrow", "Envio de demonstração local");
  appendTextElement(
    empty,
    "p",
    "",
    message || "Salve uma solução de demonstração somente neste navegador."
  );
  appendTextElement(
    empty,
    "p",
    "",
    "Este modo de demonstração ainda não envia a solução ao servidor. O registro pode ser consultado na Área do Professor neste mesmo navegador."
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
  updateStudentAction();
  clearStudentValidation();
  studentModeNote.textContent = isSubmitMode
    ? "Envio de demonstração salvo somente neste navegador, sem envio ao servidor."
    : "Use o ConfIA para estudar com feedback pedagógico imediato.";

  if (isSubmitMode) {
    renderStudentSubmitInfo();
  } else {
    renderStudentAnalysis();
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
  if (typeof window !== "undefined") window.ConfIAWorkspace?.renderMath();
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
  updateStudentAction();
}

function resultLabel(result) {
  const labels = {
    correto: "correto",
    parcialmente_correto: "parcialmente correto",
    insuficiente: "insuficiente",
    incorreto: "incorreto",
    inconclusivo: "inconclusivo",
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

function publicTechnicalValue(key, value) {
  if (["artifact_dir", "stdout", "stderr",
    "refutation_stdout", "refutation_stderr"].includes(key)) return undefined;
  if (typeof value === "string" && /file:\/\/|[A-Za-z]:[\\/]|(?:^|[\s"'(=:])\/(?:[^\s/]+\/|Users\b|home\b|tmp\b|private\b)/i.test(value)) return null;
  return value;
}

function renderEnvironment(data) {
  const details = document.createElement("details");
  details.className = "technical-details analysis-environment";
  details.appendChild(document.createElement("summary")).textContent = "Ambiente da análise";
  const metadata = data.reproducibility;
  if (!metadata || metadata.status === "legacy_unversioned") {
    appendTextElement(details, "p", "", "Metadados de reprodutibilidade não registrados nesta execução.");
    return details;
  }
  if (metadata.status !== "recorded" || !metadata.record) {
    appendTextElement(details, "p", "", "Metadados da execução indisponíveis. O resultado matemático foi preservado.");
    return details;
  }
  const manifest = metadata.record.manifest;
  const code = manifest.code_identity;
  const application = manifest.application_identity;
  const formal = manifest.formal_environment;
  const value = entry => entry?.value || "indisponível";
  appendTextElement(details, "p", "", "Metadados da execução registrados.");
  appendTextElement(details, "p", "", `Código: ${value(code.git_commit)} · Build: ${value(code.build_id)}`);
  appendTextElement(details, "p", "", `Worktree: ${code.worktree_dirty === true ? "dirty (com alterações)" : code.worktree_dirty === false ? "clean (sem alterações)" : "estado desconhecido"}`);
  appendTextElement(details, "p", "", `Projeto: ${value(application.project_version)} · API: ${application.api_version} · Conversão: ${application.conversion_version} · Bridge: ${value(application.audit_bridge_version)}`);
  const python = manifest.python_environment;
  appendTextElement(details, "p", "", `Python: ${python.major}.${python.minor}.${python.micro} (${python.implementation})`);
  appendTextElement(details, "p", "", `Lean: ${value(formal.lean_version)} · Lake: ${value(formal.lake_version)} · Mathlib: ${value(formal.mathlib_revision)}`);
  const assets = [...manifest.problem_assets, ...manifest.configuration_assets];
  appendTextElement(details, "p", "", `Assets registrados: ${assets.filter(item => item.status === "available").length} de ${assets.length}.`);
  appendTextElement(details, "p", "muted", "O registro apoia a auditoria e a tentativa de reprodução; não garante reprodução bit a bit.");
  const technical = document.createElement("details");
  technical.appendChild(document.createElement("summary")).textContent = "Detalhes técnicos";
  appendTextElement(technical, "p", "", "SHA-256 verifica integridade técnica interna; não é assinatura digital nem prova de autoria.");
  appendTextElement(technical, "p", "", "O hash e o tamanho referem-se ao registro interno. O JSON público pode conter textos ocultados e ter bytes diferentes.");
  appendTextElement(technical, "pre", "", JSON.stringify(metadata.record, null, 2));
  details.appendChild(technical);
  return details;
}

function renderTechnicalDetails(data) {
  const details = document.createElement("details");
  details.className = "technical-details";

  const summary = document.createElement("summary");
  summary.textContent = "Detalhes técnicos";
  details.appendChild(summary);
  appendTextElement(details, "p", "", "Verificação formal com Lean: consulte abaixo os dados técnicos desta análise.");

  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(data, publicTechnicalValue, 2);
  details.appendChild(pre);

  return details;
}

function renderFormalChecks(data) {
  const section = document.createElement("section");
  section.className = "formal-checks-section";
  appendTextElement(section, "h3", "section-title", "Verificações formais");
  appendTextElement(section, "p", "muted", "Lean verifica somente os claims e passos formalizados pelo auditor. Isso não verifica toda a solução nem substitui a avaliação do professor.");
  const details = document.createElement("details");
  details.appendChild(document.createElement("summary")).textContent = "Consultar claims, passos e resultados formais";
  const entries = [...(data.formal_steps || []), ...(data.student_claim_checks || [])];
  if (!entries.length) appendTextElement(details, "p", "", "Nenhum passo ou claim do aluno foi selecionado para essas verificações.");
  for (const item of entries) {
    const statuses = { verified: "Afirmação verificada", refuted: "Erro matemático identificado",
      unverified: "Não foi possível verificar formalmente", technical_error: "Verificação formal indisponível",
      failed: "Não foi possível verificar formalmente", error: "Verificação formal indisponível",
      lean_timeout: "Verificação formal indisponível", lean_error: "Verificação formal indisponível",
      lean_error_unknown_identifier: "Verificação formal indisponível",
      lean_error_unsolved_goals: "Não foi possível verificar formalmente",
      lean_error_synthesis_failed: "Não foi possível verificar formalmente",
      invalid_formal_step: "Não foi possível verificar formalmente",
      unsupported: "Afirmação fora da cobertura formal" };
    const label = item.status === "refuted" && (!item.refutation_verified || !item.refutation_lean_file)
      ? statuses.unverified : statuses[item.status] || item.result || "Resultado nos detalhes técnicos";
    appendTextElement(details, "p", "", `${item.description || item.claim_id || item.id || "Verificação"}: ${label}`);
  }
  appendTextElement(details, "pre", "", JSON.stringify({ lean_certificate: data.lean_certificate,
    formal_steps: data.formal_steps, student_claim_checks: data.student_claim_checks, microclaims: data.microclaims }, publicTechnicalValue, 2));
  section.appendChild(details);
  return section;
}

function renderRubricSection(rubric) {
  const section = document.createElement("section");
  section.className = "rubric-section";
  appendTextElement(section, "h3", "section-title", "Critérios de avaliação");

  const items = rubric && Array.isArray(rubric.items) ? rubric.items : [];
  if (items.length === 0) {
    appendTextElement(section, "p", "muted", "Critérios de avaliação não disponíveis neste retorno.");
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
  appendTextElement(gapCard, "h3", "", "Lacunas e critérios pendentes");
  const gapList = document.createElement("ul");

  for (const item of items) {
    const label = item.points == null
      ? `${item.description || item.id}: Indeterminado — ${item.assessment_note || "verificação não concluída nesta execução"}`
      : `${item.description || item.id}: ${item.points} / ${item.max_points}`;
    if (item.points != null && Number(item.points) >= Number(item.max_points)) {
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
  if (options.analysis) {
    renderAnalysisContext(targetPanel, options.analysis.context, options.stale, options.analyzeAgain);
  }

  if (!report) {
    appendTextElement(
      targetPanel,
      "div",
      "empty-state",
      "A análise terminou, mas não retornou relatório pedagógico."
    );
    targetPanel.appendChild(renderFormalChecks(data));
    targetPanel.appendChild(renderEnvironment(data));
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
  appendTextElement(titleCopy, "p", "eyebrow", "Análise ConfIA");
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
  appendTextElement(scoreMetric, "strong", "metric-value", report.score == null
    ? "Avaliação incompleta" : `${report.score} / ${report.max_score}`);
  if (report.score == null && report.evaluated_max_score > 0) {
    appendTextElement(scoreMetric, "p", "muted", `Critérios decididos: ${report.evaluated_score} / ${report.evaluated_max_score}; sem nota global.`);
  }

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
  targetPanel.appendChild(renderFormalChecks(data));
  targetPanel.appendChild(renderEnvironment(data));
  targetPanel.appendChild(renderTechnicalDetails(data));
}

if (typeof window !== "undefined") window.ConfIAReport = { render: renderReport, publicTechnicalValue };

function renderError(message, targetPanel = resultPanel) {
  clearNode(targetPanel);
  const panel = document.createElement("section");
  panel.className = "error-panel";
  appendTextElement(panel, "h2", "result-title", "Não foi possível concluir");
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
  button.appendChild(makeBadge("Demonstração textual local", "neutral"));

  button.addEventListener("click", () => {
    selectedTeacherSubmission = submission;
    teacherDecisionMessage.textContent = "";
    renderTeacherCorrectionEmpty();
    renderTeacherArea();
  });

  return button;
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

function renderTeacherCorrectionEmpty(text = "Selecione um envio e analise com o ConfIA.") {
  clearNode(teacherCorrectionPanel);
  const empty = document.createElement("div");
  empty.className = "empty-state";
  appendTextElement(empty, "p", "eyebrow", "Painel de correção");
  appendTextElement(empty, "p", "", text);
  teacherCorrectionPanel.appendChild(empty);
}

function renderTeacherAnalysis(submission) {
  const analysis = teacherAnalyses.get(submission.id);
  teacherAuditButton.disabled = Boolean(analysis?.pending);
  teacherAuditButton.setAttribute("aria-busy", String(Boolean(analysis?.pending)));
  teacherAuditButton.textContent = analysis?.pending ? "Analisando…" : "Analisar com ConfIA";
  const state = analysis?.pending ? "processing" : analysis?.error ? "failed" : analysis?.data ? "completed" : "not-run";
  teacherAnalysisStatus.dataset.analysisState = state;
  teacherAnalysisStatus.textContent = analysis?.pending ? "Análise ConfIA: Processando"
    : analysis?.error ? "Análise ConfIA: Não foi possível concluir" : analysis?.data ? "Análise ConfIA: Concluída" : "Análise ConfIA: Não executada";
  if (analysis?.data) {
    const stale = analysis.context.problem_id !== submission.problem_id || analysis.context.solution !== submission.solution;
    renderReport(analysis.data, teacherCorrectionPanel, {
      context: "teacher", analysis, stale, analyzeAgain: auditTeacherSubmission,
    });
    if (stale) teacherAnalysisStatus.textContent += " · resultado exibido de versão anterior";
    if (analysis.error) appendTextElement(teacherCorrectionPanel, "p", "validation-message", ANALYSIS_ERROR);
  } else if (analysis?.pending) {
    renderTeacherCorrectionEmpty(`Analisando o envio de ${submission.student_name || "Aluno"} com o ConfIA.`);
  } else if (analysis?.error) {
    renderError(ANALYSIS_ERROR, teacherCorrectionPanel);
  } else {
    renderTeacherCorrectionEmpty("Análise ConfIA ainda não realizada para este envio.");
  }
}

function renderSelectedSubmission() {
  const submission = selectedTeacherSubmission;
  if (!submission) {
    teacherStudentName.textContent = "Selecione um envio";
    teacherProblemTitle.textContent = "-";
    teacherSubmissionStatus.textContent = "sem seleção";
    teacherSubmissionStatus.dataset.kind = "neutral";
    teacherSolution.textContent = "A solução enviada aparecerá aqui.";
    teacherAuditButton.disabled = true;
    teacherAuditButton.setAttribute("aria-busy", "false");
    teacherAnalysisStatus.textContent = "Análise ConfIA: falta selecionar um envio";
    teacherAnalysisStatus.dataset.analysisState = "not-run";
    teacherDecisionMessage.textContent = "";
    renderTeacherCorrectionEmpty();
    return;
  }

  teacherStudentName.textContent = submission.student_name || "Aluno";
  teacherProblemTitle.textContent = submission.problem_title || currentProblemTitle(submission.problem_id);
  teacherSubmissionStatus.textContent = "Demonstração textual local";
  teacherSubmissionStatus.dataset.kind = "neutral";
  teacherSolution.textContent = submission.solution || "Solução não informada.";
  renderTeacherAnalysis(submission);
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
    "Nenhum envio de demonstração foi salvo neste navegador."
  );
  renderSubmissionList(
    demoSubmissionList,
    visibleDemoSubmissions,
    realSubmissions.length > 0
      ? "Exemplos demonstrativos ficam ocultos quando há registros locais neste navegador."
      : "Use estes exemplos enquanto não houver registros locais."
  );
  renderSelectedSubmission();
}

function submitSolutionToTeacher() {
  const problem = selectedProblem();
  const solution = solutionInput.value.trim();
  const studentName = studentNameInput.value.trim();
  clearStudentValidation();

  if (!problem) {
    studentValidation(problemSelect, "Selecione uma questão antes de salvar o registro de demonstração.");
    return;
  }
  if (!studentName) {
    studentValidation(studentNameInput, "Informe o nome do aluno antes de salvar o registro de demonstração.");
    return;
  }
  if (!solution) {
    studentValidation(solutionInput, "Digite ou cole uma solução antes de salvar o registro de demonstração.");
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
  setStatus("Registro salvo neste navegador", "success");
  if (typeof window !== "undefined") window.ConfIAShell?.refreshLocalSubmissions?.();
  renderStudentSubmitInfo(
    "Registro salvo neste navegador. Este modo de demonstração ainda não envia a solução ao servidor."
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
  if (typeof window !== "undefined") window.ConfIAWorkspace?.catalogReady();
  setStatus("Pronto", "idle");
}

async function loadSelectedExample() {
  const problemId = problemSelect.value;
  const exampleKey = exampleSelect.value;
  const version = studentVersion;
  const sequence = ++exampleSequence;
  examplePending = true;
  loadExampleButton.disabled = true;
  loadExampleButton.setAttribute("aria-busy", "true");
  setStatus("Carregando exemplo", "busy");
  try {
    const response = await fetch(`/problems/${problemId}/examples/${exampleKey}`);
    if (!response.ok) throw new Error(`Exemplo: HTTP ${response.status}`);
    const payload = await response.json();
    if (sequence !== exampleSequence || version !== studentVersion || problemSelect.value !== problemId || exampleSelect.value !== exampleKey) {
      setStatus("Exemplo não aplicado: a seleção ou a solução foi alterada", "idle");
      return;
    }
    solutionInput.value = payload.solution || "";
    studentContextChanged();
    setStatus("Exemplo carregado", "idle");
  } catch (error) {
    console.error("ConfIA: carregamento de exemplo", error);
    studentValidationMessage.textContent = "Não foi possível carregar o exemplo selecionado. Tente novamente.";
    setStatus("Exemplo indisponível", "error");
  } finally {
    if (sequence === exampleSequence) {
      examplePending = false;
      updateStudentAction();
      loadExampleButton.setAttribute("aria-busy", "false");
    }
  }
}

async function requestAnalysis(context) {
  const response = await fetch("/audit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problem_id: context.problem_id, solution: context.solution }),
  });
  if (!response.ok) throw new Error(`Análise: HTTP ${response.status}: ${await response.text()}`);
  const data = await response.json();
  if (data.problem_id !== context.problem_id) throw new Error("A questão retornada não corresponde à questão analisada.");
  return data;
}

async function auditCurrentSolution() {
  if (studentAuditPending) return;
  if (typeof window !== "undefined" && window.ConfIAWorkspace && !window.ConfIAWorkspace.canAnalyze()) return;
  clearStudentValidation();
  const context = Object.freeze({
    problem_id: problemSelect.value,
    solution: solutionInput.value.trim(),
    version: studentVersion,
    sequence: ++studentAuditSequence,
    ...(typeof window !== "undefined" ? window.ConfIAWorkspace?.analysisContext() : {}),
  });
  if (!selectedProblem()) {
    studentValidation(problemSelect, "Selecione uma questão antes de analisar.");
    return;
  }
  if (!context.solution) {
    studentValidation(solutionInput, "Digite ou carregue uma solução antes de analisar.");
    return;
  }
  studentAuditContext = context;
  setBusy(true);
  setStatus(`Analisando a questão ${context.problem_id}`, "busy");
  renderStudentAnalysis();
  try {
    const data = await requestAnalysis(context);
    if (context.sequence !== studentAuditSequence) return;
    if (typeof window !== "undefined" && window.ConfIAWorkspace) window.ConfIAWorkspace.recordAnalysis({ context, data });
    else studentAnalysis = { context, data };
    renderStudentAnalysis();
    if (typeof window === "undefined" || !window.ConfIAWorkspace || window.ConfIAWorkspace.owns(context)) setStatus(`Análise concluída para a questão ${context.problem_id}`, "success");
  } catch (error) {
    console.error("ConfIA: análise do aluno", context, error);
    const currentContext = typeof window === "undefined" || !window.ConfIAWorkspace || window.ConfIAWorkspace.owns(context);
    if (currentContext) {
      studentValidationMessage.textContent = ANALYSIS_ERROR;
      // Keep a previous report available if a retry fails.
      if (!studentAnalysis && studentMode === "study") renderError(ANALYSIS_ERROR);
    }
    if (currentContext) setStatus(`Análise indisponível para a questão ${context.problem_id}`, "error");
  } finally {
    setBusy(false);
    if (studentAnalysis) renderStudentAnalysis();
    if (typeof window !== "undefined") window.ConfIAShell?.refreshStudent();
  }
}

async function auditTeacherSubmission() {
  const submission = selectedTeacherSubmission;
  if (!submission) {
    renderTeacherCorrectionEmpty("Selecione um envio antes de analisar.");
    return;
  }
  if (teacherAnalyses.get(submission.id)?.pending) return;
  const context = Object.freeze({
    submission_id: submission.id,
    problem_id: submission.problem_id,
    solution: submission.solution,
  });
  const previous = teacherAnalyses.get(submission.id);
  const analysis = { context: previous?.data ? previous.context : context, pending: true, data: previous?.data || null, error: null };
  teacherAnalyses.set(submission.id, analysis);
  renderSelectedSubmission();
  setStatus(`Analisando o envio de ${submission.student_name || "Aluno"}`, "busy");
  try {
    const data = await requestAnalysis(context);
    analysis.context = context;
    analysis.data = data;
    // The operation owns the original reference, never the current selection.
    submission.analysis = { context, data };
    setStatus(`Análise concluída para o envio de ${submission.student_name || "Aluno"}`, "success");
  } catch (error) {
    console.error("ConfIA: análise do professor", context, error);
    analysis.error = error;
    setStatus(`Análise indisponível para o envio de ${submission.student_name || "Aluno"}`, "error");
  } finally {
    analysis.pending = false;
    if (selectedTeacherSubmission?.id === context.submission_id) renderSelectedSubmission();
  }
}

function handleStudentPrimaryAction() {
  if (typeof window !== "undefined" && window.ConfIAWorkspace) { auditCurrentSolution(); return; }
  if (studentMode === "submit") {
    try {
      submitSolutionToTeacher();
    } catch (error) {
      console.error("ConfIA: registro local", error);
      studentValidationMessage.textContent = "Não foi possível salvar o registro neste navegador. Tente novamente.";
      setStatus("Registro local indisponível", "error");
    }
    return;
  }
  auditCurrentSolution();
}

problemSelect.addEventListener("change", () => {
  renderExamples();
  renderProblemStatement();
  if (typeof window !== "undefined") window.ConfIAWorkspace?.onProblemSelected();
  studentContextChanged();
});
solutionInput.addEventListener("input", studentContextChanged);
studentNameInput.addEventListener("input", clearStudentValidation);
for (const button of tabButtons) {
  button.addEventListener("click", () => activateArea(button.dataset.tabTarget));
}
for (const button of studentModeButtons) {
  button.addEventListener("click", () => setStudentMode(button.dataset.studentMode));
}
loadExampleButton.addEventListener("click", loadSelectedExample);
auditButton.addEventListener("click", handleStudentPrimaryAction);
teacherAuditButton.addEventListener("click", auditTeacherSubmission);

updateStudentAction();
loadProblems().catch((error) => {
  console.error("ConfIA: carregamento de questões", error);
  renderError("Não foi possível carregar as questões. Atualize a página e tente novamente.");
  setStatus("Questões indisponíveis", "error");
});
