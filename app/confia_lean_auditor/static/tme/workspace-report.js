/* Dense presentation of the existing AuditResponse; no scoring or inference. */
(function (root) {
  "use strict";
  const n = (tag, text, cls) => { const el = document.createElement(tag); if (text != null) el.textContent = text; if (cls) el.className = cls; return el; };
  const finite = value => typeof value === "number" && Number.isFinite(value);
  const number = value => finite(value) ? String(value).replace(".", ",") : "—";
  const counted = (count, singular, plural) => `${count} ${count === 1 ? singular : plural}`;
  const glyph = status => ({ verified: "✓", supported: "✓", refuted: "×", technical_error: "⚠" }[status] || "?");
  const statusIcon = status => {
    const el=n("span",null,"result-glyph");
    const names={verified:"check",supported:"check",refuted:"refuted",technical_error:"alert"};
    const labels={verified:"Verificado",supported:"Sustentado",refuted:"Refutado",technical_error:"Falha técnica"};
    el.setAttribute("role","img");el.setAttribute("aria-label",labels[status]||"Indeterminado");
    if(root.ConfiaTmeHome?.icon) el.append(root.ConfiaTmeHome.icon(names[status]||"unknown"));
    else el.textContent=glyph(status);
    return el;
  };
  function render(data, host, options) {
    const p = root.ConfIAReport.presentation, saved = options.uiState || {};
    const math = (tag, value, cls) => { const el = n(tag, null, cls); root.ConfiaRecognitionView.renderMathText(el, String(value || "")); return el; };
    const items = p.rubricItems(data), decided = items.filter(p.isDecided), checks = data.student_claim_checks || [];
    const formalStatus = check => p.formalStatus(check) === "verified" && (!check.compiled || !check.lean_file) ? "unverified" : p.formalStatus(check);
    const report = n("div", null, "workspace-report");
    const globalState = options.auditRun?.status === "FAILED" ? "Falha técnica" : data.rubric_assessment?.assessment_status === "partial" ? "Parcialmente decidida" : !finite(data.score) ? "Inconclusiva" : "Análise concluída";
    const summary = n("section", null, "review-outcome"); summary.setAttribute("aria-label", "Resultado sugerido");
    summary.append(n("span", "Sugestão ConfIA", "quiet-label"), n("p", finite(data.score) ? `${number(data.score)} / ${number(data.max_score)}` : "Pontuação não determinada", "review-score"), n("p", globalState, "review-verdict"));
    const coverage = n("section", null, "coverage"); coverage.setAttribute("aria-label", "Cobertura da análise");
    coverage.append(n("h3", "Cobertura da análise"), n("p", `${decided.length}/${items.length} critérios decididos`, "coverage-headline"));
    const bar = n("div", null, "coverage-track"); bar.setAttribute("aria-hidden", "true");
    const fill = n("span"); fill.style.width = `${items.length ? 100 * decided.length / items.length : 0}%`; bar.appendChild(fill);
    const verified = checks.filter(check => formalStatus(check) === "verified").length;
    coverage.append(bar, n("p", `${items.length} critérios · ${decided.length} decididos · ${counted(verified, "claim formalmente verificado", "claims formalmente verificados")} · ${counted(items.length - decided.length, "indeterminado", "indeterminados")}`, "coverage-stats"));
    report.append(summary, coverage);
    const section = n("section", null, "dense-criteria"); section.appendChild(n("h3", "Critérios de correção"));
    saved.criteriaOpen ||= {};
    items.forEach((item, i) => {
      const row = n("details", null, "audit-criterion"); row.dataset.criterionId = item.id; row.dataset.mathematicalStatus = item.mathematical_status || "indeterminate"; row.dataset.verificationStatus=item.verification_status||"not_available";
      row.open = Boolean(saved.criteriaOpen[item.id]); row.addEventListener("toggle", () => { saved.criteriaOpen[item.id] = row.open; });
      const heading = n("summary"), title = n("span", `Critério ${i + 1}`, "criterion-label");
      heading.append(statusIcon(item.mathematical_status), title, n("strong", p.isDecided(item) ? `${number(item.points)} / ${number(item.max_points)}` : "Indeterminado", "criterion-score"), math("span", item.description || item.id, "criterion-description"));
      row.append(heading);
      const evidence = item.evidence || data.extracted_claims?.claims?.find(claim => claim.id === item.claim_id)?.evidence || data.pedagogical_report?.evidence_items?.find(e => e.id === item.id)?.evidence;
      row.append(math("p", evidence ? `Evidência na solução: “${evidence}”` : "Evidência textual não localizada.", "evidence-quote"));
      if (item.assessment_note) row.appendChild(math("p", item.assessment_note, "criterion-note"));
      const claim = [...(data.extracted_claims?.claims || []), ...(data.student_claims || [])].find(claim => claim.id === item.claim_id);
      if (claim) row.appendChild(math("p", `Passo relacionado: ${claim.text || claim.normalized_text || claim.raw_text || claim.id}`, "criterion-note"));
      row.appendChild(n("p", `Verificação: ${item.verification_status === "technical_error" ? "⚠ Verificação formal não concluída" : ({ available: "Disponível", not_available: "Não disponível", verified: "Verificado formalmente", not_verified: "Não verificado" }[item.verification_status] || item.verification_status || "Não registrada")}`, "criterion-verification"));
      for (const note of item.adjustment_notes || []) row.appendChild(math("p", note));
      section.appendChild(row);
    });
    if (!items.length) section.appendChild(n("p", "Critérios não disponíveis nesta execução.", "muted"));
    report.appendChild(section);
    const map = n("section", null, "solution-map"); map.appendChild(n("h3", "Passos identificados"));
    const entries = p.claimEntries(data), list = n("div", null, "claim-list"), detail = n("section", null, "claim-detail"); detail.setAttribute("aria-live", "polite");
    const buttons = [];
    const select = index => {
      saved.selectedClaim = entries[index].claim.id;
      buttons.forEach((button, i) => button.setAttribute("aria-pressed", String(i === index)));
      const {claim, check} = entries[index]; detail.replaceChildren();
      detail.append(math("p", claim.evidence || claim.raw_text || "Evidência textual não localizada.", "evidence-quote"), n("p", p.formalLabels[formalStatus(check)], "formal-status"));
      if (check?.lean_statement) { const d = n("details"); d.append(n("summary", "Formalização do passo"), n("code", check.lean_statement)); detail.appendChild(d); }
      // Hook for future source mapping. The current API has no verified offsets;
      // never infer document highlights from string similarity.
      if (options.onEvidenceSelection) options.onEvidenceSelection({ claimId: claim.id, mapping: null });
      detail.appendChild(n("p", "Sem vínculo preciso com um trecho da transcrição.", "mapping-note"));
    };
    entries.forEach(({claim, check, kind}, i) => {
      const button = n("button", null, "audit-claim"); button.type = "button"; button.dataset.claimId = claim.id; button.dataset.claimKind = kind; button.dataset.formalStatus = formalStatus(check);
      button.append(n("span", String(i + 1).padStart(2, "0"), "step-number"), math("span", claim.text || claim.normalized_text || claim.raw_text || claim.id, "step-label"), statusIcon(formalStatus(check)));
      button.setAttribute("aria-label", `Passo ${i + 1}: ${claim.text || claim.normalized_text || claim.raw_text || claim.id}. ${p.formalLabels[formalStatus(check)]}`); button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => select(i)); buttons.push(button); list.appendChild(button);
    });
    if (!entries.length) list.appendChild(n("p", "Nenhum passo matemático estruturado foi identificado nesta análise.", "muted"));
    map.append(list, detail); report.appendChild(map);
    if (entries.length) select(Math.max(0, entries.findIndex(entry => entry.claim.id === saved.selectedClaim)));
    const formal = n("section", null, "formal-checks-section"); formal.appendChild(n("h3", "Verificação matemática"));
    const unsubmitted = entries.filter(entry => p.formalStatus(entry.check) === "not_submitted").length;
    const failures = [...checks, ...(data.formal_steps || [])].filter(item => p.formalStatus(item) === "technical_error").length;
    formal.append(n("p", `${counted(verified, "claim verificado formalmente", "claims verificados formalmente")}`), n("p", `${counted(unsubmitted, "não formalizado", "não formalizados")}`), n("p", `${counted(failures, "falha técnica", "falhas técnicas")}`, failures ? "formal-warning" : "muted"));
    if (failures) formal.appendChild(n("p", "⚠ Verificação formal não concluída", "formal-warning"));
    const formalDetails = n("details"); formalDetails.append(n("summary", "Detalhes da verificação"), p.renderFormalChecks({...data, student_claim_checks: checks.map(check => ({...check,status:formalStatus(check)})), formal_steps:(data.formal_steps||[]).map(check=>({...check,status:formalStatus(check)}))})); formal.appendChild(formalDetails); report.appendChild(formal);
    const explanation = n("details", null, "review-explanation"); explanation.append(n("summary", "Resumo e evidências da análise"), math("p", data.pedagogical_report?.summary || data.feedback || "Resumo não registrado."), p.renderEvidenceItems(data.pedagogical_report?.evidence_items));
    const warnings = p.renderWarnings(data, options.auditRun); if (warnings) explanation.appendChild(warnings); report.appendChild(explanation);
    const technical = p.renderTechnicalDetails(options.auditRun || data); technical.appendChild(p.renderEnvironment(data));
    if (saved.history || saved.feedback) { const source=n("pre",JSON.stringify({transcription:saved.history,recognition:saved.feedback},root.ConfIAReport.publicTechnicalValue,2));technical.appendChild(source); } report.appendChild(technical);
    host.replaceChildren(report);
  }
  root.ConfiaWorkspaceReport = { render };
})(window);
