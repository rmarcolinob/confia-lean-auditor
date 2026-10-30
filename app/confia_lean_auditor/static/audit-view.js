(function (root) {
  "use strict";
  function clearNode(node) { node.replaceChildren(); }
  function appendTextElement(parent, tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
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
  appendTextElement(technical, "pre", "", JSON.stringify(metadata.record, publicTechnicalValue, 2));
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

function mathText(parent, tag, className, text) {
  const element = appendTextElement(parent, tag, className, "");
  const renderer = root.ConfiaRecognitionView || globalThis.ConfiaRecognitionView;
  if (renderer) renderer.renderMathText(element, String(text));
  else element.textContent = text;
  return element;
}
const number = value => typeof value === "number" && Number.isFinite(value);
const format = value => number(value) ? String(value) : "—";
const counted = (count, singular, plural) => `${count} ${count === 1 ? singular : plural}`;
const mathematicalLabels = { supported: "Verificado", refuted: "Refutado", indeterminate: "Indeterminado" };
function formalStatus(item) {
  if (!item) return "not_submitted";
  if (item.status === "refuted") return item.refutation_verified && item.refutation_lean_file ? "refuted" : "unverified";
  if (["technical_error", "error", "lean_timeout", "lean_error", "lean_error_unknown_identifier"].includes(item.status)) return "technical_error";
  if (item.status === "verified") return "verified";
  if (item.status === "unsupported" || item.status === "not_generated") return "not_submitted";
  return "unverified";
}
const formalLabels = {
  verified: "Verificado formalmente", refuted: "Refutado formalmente",
  unverified: "Não verificado — a tentativa formal não estabeleceu a afirmação",
  technical_error: "Verificação formal não concluída",
  not_submitted: "Não submetido à verificação formal",
};
function rubricItems(data) { return data.rubric_assessment?.items || []; }
function isDecided(item) { return number(item.points) && item.mathematical_status !== "indeterminate"; }
function evidenceFor(data, item) {
  return item.evidence || data.extracted_claims?.claims?.find(claim => claim.id === item.claim_id)?.evidence
    || data.pedagogical_report?.evidence_items?.find(evidence => evidence.id === item.id)?.evidence;
}
function renderRubricSection(data) {
  const section = document.createElement("section"); section.className = "rubric-section";
  appendTextElement(section, "h3", "section-title", "Critérios de avaliação");
  const items = rubricItems(data);
  if (!items.length) appendTextElement(section, "p", "muted", "Critérios de avaliação não disponíveis neste retorno.");
  for (const [index, item] of items.entries()) {
    const card = appendTextElement(section, "article", "audit-criterion", "");
    card.dataset.criterionId = item.id;
    card.dataset.mathematicalStatus = item.mathematical_status || "unrecorded";
    card.dataset.verificationStatus = item.verification_status || "unrecorded";
    mathText(card, "h4", "", `Critério ${index + 1} — ${item.description || item.id}`);
    appendTextElement(card, "p", "audit-points", isDecided(item)
      ? `Pontos decididos: ${format(item.points)} / ${format(item.max_points)}`
      : `Pontos decididos: Indeterminado · Máximo: ${format(item.max_points)}`);
    appendTextElement(card, "p", "audit-status", `Status matemático: ${mathematicalLabels[item.mathematical_status] || "Não registrado"}`);
    const evidence = evidenceFor(data, item);
    mathText(card, "p", "evidence-quote", evidence ? `Evidência: ${evidence}` : "Evidência: não identificada no resultado desta análise.");
    if (item.assessment_note) mathText(card, "p", "", `${isDecided(item) ? "Justificativa" : "Motivo"}: ${item.assessment_note}`);
    else if (!isDecided(item)) appendTextElement(card, "p", "", item.verification_status === "technical_error"
      ? "Motivo: verificação não concluída por falha técnica. Isso não refuta o critério."
      : "Motivo: o auditor não registrou evidência suficiente para decidir este critério.");
    for (const note of item.adjustment_notes || []) mathText(card, "p", "muted", note);
    if (item.verification_status === "technical_error") appendTextElement(card, "p", "muted", "Verificação formal não concluída.");
  }
  return section;
}
function claimEntries(data) {
  const entries = [];
  const checks = data.student_claim_checks || [];
  for (const claim of data.extracted_claims?.claims || []) entries.push({ claim, check: null, kind: "extracted" });
  for (const claim of data.student_claims || []) entries.push({ claim, check: checks.find(check => check.id === claim.id), kind: "student" });
  for (const check of checks) if (!entries.some(entry => entry.kind === "student" && entry.claim.id === check.id))
    entries.push({ claim: check, check, kind: "student" });
  return entries;
}
function renderClaims(data) {
  const section = document.createElement("section"); section.className = "audit-claims";
  appendTextElement(section, "h3", "section-title", "Passos / claims identificados");
  const entries = claimEntries(data);
  if (!entries.length) appendTextElement(section, "p", "muted", "Nenhum claim intermediário foi identificado nesta execução.");
  entries.forEach(({ claim, check, kind }, index) => {
    const row = appendTextElement(section, "article", "audit-claim", "");
    row.dataset.claimId = claim.id; row.dataset.claimKind = kind;
    row.dataset.formalStatus = formalStatus(check);
    const related = rubricItems(data).filter(item => item.claim_id === claim.id);
    mathText(row, "h4", "", `Passo ${index + 1} — ${claim.text || claim.normalized_text || claim.raw_text || claim.id}`);
    appendTextElement(row, "p", "audit-status", `Status: ${formalLabels[formalStatus(check)]}`);
    if (check?.lean_statement) {
      const formalization = document.createElement("details");
      formalization.appendChild(document.createElement("summary")).textContent = "Formalização do passo";
      appendTextElement(formalization, "code", "", check.lean_statement); row.appendChild(formalization);
    }
    for (const item of related) appendTextElement(row, "p", "muted", `Critério relacionado: ${item.description || item.id} · ${mathematicalLabels[item.mathematical_status] || "Não registrado"}`);
    mathText(row, "p", "evidence-quote", `Evidência: ${claim.evidence || claim.raw_text || claim.context || "não registrada neste resultado."}`);
  });
  return section;
}
function renderFormalChecks(data) {
  const section = document.createElement("section"); section.className = "formal-checks-section";
  appendTextElement(section, "h3", "section-title", "Verificação matemática");
  appendTextElement(section, "p", "muted", "Lean verifica somente os claims e passos formalizados pelo auditor. Isso não verifica toda a solução nem substitui a decisão humana.");
  const checks = data.student_claim_checks || [], steps = data.formal_steps || [];
  const entries = [...steps, ...checks];
  const unchecked = claimEntries(data).filter(entry => !entry.check);
  const counts = { verified: 0, refuted: 0, unverified: 0, technical_error: 0, not_submitted: unchecked.length };
  for (const item of entries) counts[formalStatus(item)]++;
  appendTextElement(section, "p", "", [
    counted(checks.filter(item => formalStatus(item) === "verified").length, "claim verificado", "claims verificados"),
    counted(steps.filter(item => formalStatus(item) === "verified").length, "passo formal verificado", "passos formais verificados"),
    counted(counts.not_submitted, "claim/passo não formalizado", "claims/passos não formalizados"),
    counted(counts.technical_error, "erro técnico", "erros técnicos"),
  ].join(" · "));
  if (counts.technical_error) appendTextElement(section, "p", "", `Verificação formal não concluída: ${counted(counts.technical_error, "claim/passo", "claims/passos")}.`);
  if (counts.unverified) appendTextElement(section, "p", "", `${counted(counts.unverified, "claim/passo não verificado", "claims/passos não verificados")}; isso não demonstra falsidade.`);
  if (counts.refuted) appendTextElement(section, "p", "", `${counted(counts.refuted, "claim refutado", "claims refutados")} com artefato formal de refutação.`);
  if (!entries.length) appendTextElement(section, "p", "", "Nenhum claim ou passo foi submetido às verificações formais individuais nesta execução.");
  const details = document.createElement("details");
  details.appendChild(document.createElement("summary")).textContent = "Consultar claims, passos e resultados formais";
  for (const item of entries) {
    const row = appendTextElement(details, "p", "", ""); row.dataset.formalStatus = formalStatus(item);
    mathText(row, "span", "", `${item.description || item.raw_text || item.claim_id || item.id || "Verificação"}: ${formalLabels[formalStatus(item)]}`);
  }
  // Microclaims are the auditor's selective checks, not a claim that the entire solution was proved.
  let verifiedMicroclaims = 0;
  for (const item of data.microclaims || []) {
    const verified = ["verified_by_lean", "verified_by_formal_steps"].includes(item.lean_status)
      && item.dependencies_verified !== false && item.formal_steps_verified !== false;
    if (verified) verifiedMicroclaims++;
    mathText(details, "p", "", `${item.description || item.id}: ${verified ? "Verificado formalmente (microclaim)"
      : item.verification_status === "technical_error" ? formalLabels.technical_error : "Microclaim não verificado nesta execução"}`);
  }
  if (data.microclaims?.length) appendTextElement(section, "p", "", `Verificações seletivas da rubrica: ${counted(verifiedMicroclaims, "microclaim verificado formalmente", "microclaims verificados formalmente")} de ${data.microclaims.length}.`);

  section.appendChild(details); return section;
}
function renderWarnings(data, run) {
  const section = document.createElement("section"); section.className = "audit-warnings";
  const warnings = (run?.source?.warnings || []).map(item => `Página ${item.page_index + 1}: ${item.message}`);
  if (rubricItems(data).some(item => !isDecided(item))) warnings.push("Há critérios indeterminados; consulte suas evidências e justificativas.");
  if ([...(data.formal_steps || []), ...(data.student_claim_checks || [])].some(item => formalStatus(item) === "technical_error"))
    warnings.push("A verificação formal de parte dos passos não foi concluída. Falha técnica não equivale a erro matemático.");
  if (claimEntries(data).some(item => !item.check)) warnings.push("Há claims identificados que não foram submetidos à verificação formal individual.");
  if (!warnings.length) return null;
  appendTextElement(section, "h3", "section-title", "Observações da análise");
  const list = appendTextElement(section, "ul", "", "");
  for (const warning of new Set(warnings)) mathText(list, "li", "", warning);
  return section;
}
function renderReport(data, targetPanel, options = {}) {
  if (options.workspace && root.ConfiaWorkspaceReport) return root.ConfiaWorkspaceReport.render(data, targetPanel, options);
  clearNode(targetPanel);
  const content = appendTextElement(targetPanel, "div", "confia-audit-view", "");
  const report = data.pedagogical_report || {};
  // Presence, not truthiness: a null score in the AuditResponse is authoritative.
  const score = Object.hasOwn(data, "score") ? data.score : report.score;
  const maximum = Object.hasOwn(data, "max_score") ? data.max_score : report.max_score;
  const verdict = data.verdict || report.verdict || report.result;
  const items = rubricItems(data), decided = items.filter(isDecided);
  const isEvaluator = ["teacher", "evaluator"].includes(options.context);
  const header = appendTextElement(content, "section", "result-summary", "");
  header.dataset.result = verdict || "inconclusivo";
  appendTextElement(header, "p", "eyebrow", "ANÁLISE CONFIA");
  appendTextElement(header, "h2", "result-title", isEvaluator ? "Resultado sugerido" : "Resultado da análise");
  const scoreText = number(score) ? `${format(score)} / ${format(maximum)}` : "Não determinada";
  appendTextElement(header, "p", "audit-score", `${isEvaluator ? "Pontuação sugerida" : "Pontuação"}: ${scoreText}`);
  appendTextElement(header, "p", "audit-verdict", `Resultado: ${!number(score) || verdict === "inconclusivo" ? "Análise inconclusiva" : resultLabel(verdict)}`);
  if (options.workspace) {
    const errors = [...(data.formal_steps || []), ...(data.student_claim_checks || [])].some(item => formalStatus(item) === "technical_error");
    appendTextElement(header, "p", "workspace-analysis-status", `Status: ${errors ? "Verificação formal não concluída" : decided.length && decided.length < items.length ? "Parcialmente decidida" : number(score) ? "Conclusiva" : "Inconclusiva"} · ${decided.length} de ${items.length} critérios decididos`);
  }
  if (report.reliability) appendTextElement(header, "p", "muted", `Confiabilidade: ${report.reliability}`);
  if (!number(score)) {
    const reason = appendTextElement(header, options.workspace ? "details" : "section", "audit-inconclusive", "");
    appendTextElement(reason, options.workspace ? "summary" : "h3", "", "Motivo da inconclusividade");
    const pending = items.length - decided.length;
    appendTextElement(reason, "p", "", pending
      ? `Não foi possível determinar uma pontuação global porque ${pending} de ${items.length} critérios ${pending === 1 ? "permaneceu indeterminado" : "permaneceram indeterminados"}.`
      : "O auditor não determinou uma pontuação global nesta execução. Consulte o resumo e as observações da análise.");
    appendTextElement(reason, "p", "", `Critérios decididos: ${decided.length}/${items.length}`);
    if (decided.length) appendTextElement(reason, "p", "", `Pontos decididos: ${format(decided.reduce((sum, item) => sum + item.points, 0))}/${format(maximum)}`);
    else appendTextElement(reason, "p", "", "Pontos decididos: nenhum critério decidido.");
    appendTextElement(reason, "p", "", "Pontuação global: não determinada. Pontos decididos descrevem apenas os critérios resolvidos; não são nota oficial nem pontuação global.");
  }
  const summary = appendTextElement(content, "section", "audit-summary", "");
  appendTextElement(summary, "h3", "section-title", "Resumo da análise");
  mathText(summary, "p", "summary-text", report.summary || data.feedback || "Resumo explicativo não registrado nesta execução.");
  if (options.workspace) {
    content.appendChild(renderRubricSection(data));
    const claims = document.createElement("details");
    claims.appendChild(document.createElement("summary")).textContent = "Passos identificados";
    claims.appendChild(renderClaims(data)); content.appendChild(claims);
    const evidence = document.createElement("details");
    evidence.appendChild(document.createElement("summary")).textContent = "Evidências e pontos de atenção";
    evidence.appendChild(renderEvidenceItems(report.evidence_items)); evidence.appendChild(renderAttentionPoints(report.attention_points)); content.appendChild(evidence);
  } else {
    content.appendChild(renderEvidenceItems(report.evidence_items)); content.appendChild(renderAttentionPoints(report.attention_points)); content.appendChild(renderRubricSection(data)); content.appendChild(renderClaims(data));
  }
  content.appendChild(renderFormalChecks(data));
  const warnings = renderWarnings(data, options.auditRun);
  if (warnings) content.appendChild(warnings);
  const technical = renderTechnicalDetails(options.auditRun || data);
  technical.children[0].textContent = "Detalhes técnicos da análise";
  technical.appendChild(renderEnvironment(data));
  content.appendChild(technical);
}

root.ConfIAReport = { render: renderReport, publicTechnicalValue, makeBadge,
  presentation: { formalStatus, formalLabels, rubricItems, isDecided, claimEntries, resultLabel,
    renderFormalChecks, renderWarnings, renderTechnicalDetails, renderEnvironment, renderEvidenceItems } };
})(typeof window !== "undefined" ? window : globalThis);
