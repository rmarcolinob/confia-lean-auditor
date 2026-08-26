const problemSelect = document.querySelector("#problem-select");
const exampleSelect = document.querySelector("#example-select");
const loadExampleButton = document.querySelector("#load-example");
const auditButton = document.querySelector("#audit-button");
const solutionInput = document.querySelector("#solution-input");
const resultPanel = document.querySelector("#result-panel");
const serviceStatus = document.querySelector("#service-status");
const problemTitle = document.querySelector("#problem-title");
const problemStatementText = document.querySelector("#problem-statement-text");

let problems = [];

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
    correto: "Correto",
    parcialmente_correto: "Parcialmente correto",
    insuficiente: "Insuficiente",
    incorreto: "Incorreto",
  };
  return labels[result] || result || "Não avaliado";
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
    appendTextElement(header, "span", "mini-pill", item.result || "avaliada");
    article.appendChild(header);

    if (item.evidence) {
      appendTextElement(article, "p", "evidence-quote", item.evidence);
    }

    appendTextElement(article, "p", "evidence-explanation", item.explanation || "");
    appendTextElement(article, "p", "reliability-line", item.reliability || "não avaliada");
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

function renderReport(data) {
  const report = data.pedagogical_report;
  clearNode(resultPanel);

  if (!report) {
    appendTextElement(
      resultPanel,
      "div",
      "empty-state",
      "A auditoria terminou, mas não retornou relatório pedagógico."
    );
    resultPanel.appendChild(renderTechnicalDetails(data));
    return;
  }

  const header = document.createElement("section");
  header.className = "result-summary";
  header.dataset.result = report.result;

  appendTextElement(header, "p", "eyebrow", "Resultado");
  appendTextElement(header, "h2", "result-title", resultLabel(report.result));
  appendTextElement(header, "p", "summary-text", report.summary || "");

  const metrics = document.createElement("div");
  metrics.className = "metrics";
  appendTextElement(metrics, "div", "metric", `${report.score} / ${report.max_score}`);
  appendTextElement(metrics, "div", "metric", report.reliability || "não avaliada");
  header.appendChild(metrics);

  resultPanel.appendChild(header);
  resultPanel.appendChild(renderEvidenceItems(report.evidence_items));
  resultPanel.appendChild(renderAttentionPoints(report.attention_points));
  resultPanel.appendChild(renderTechnicalDetails(data));
}

function renderError(message) {
  clearNode(resultPanel);
  const panel = document.createElement("section");
  panel.className = "error-panel";
  appendTextElement(panel, "h2", "result-title", "Não foi possível auditar");
  appendTextElement(panel, "p", "summary-text", message);
  resultPanel.appendChild(panel);
}

async function loadProblems() {
  setStatus("Carregando", "busy");
  const response = await fetch("/problems");
  if (!response.ok) {
    throw new Error("Não foi possível carregar as questões.");
  }
  problems = await response.json();
  renderProblems();
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

problemSelect.addEventListener("change", () => {
  renderExamples();
  renderProblemStatement();
});
loadExampleButton.addEventListener("click", loadSelectedExample);
auditButton.addEventListener("click", auditCurrentSolution);

loadProblems().catch((error) => {
  renderError(error.message);
  setStatus("Erro", "error");
});
