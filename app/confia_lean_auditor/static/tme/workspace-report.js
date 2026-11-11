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
  // Presentation only: all point/status decisions come from the persisted engine.
  const p5Labels = {
    candidate:"Apresenta uma decomposição candidata",product:"Calcula o produto da decomposição",
    enumeration:"Compara as decomposições possíveis",structural_max:"Justifica a maximalidade do produto",
    normal_list:"Apresenta a lista na forma reduzida",one_domain:"Estabelece as condições para eliminar parcelas iguais a um",
    one_sum:"Preserva a soma ao eliminar uma parcela um",one_gain:"Mostra o aumento do produto ao eliminar uma parcela um",
    domain:"Estabelece o domínio da substituição",sum_preserved:"Preserva a soma na substituição",
    increase:"Demonstra o aumento do produto",four_sum:"Preserva a soma ao trocar quatro por dois e dois",
    four_product:"Preserva o produto ao trocar quatro por dois e dois",twos_sum:"Preserva a soma ao substituir três parcelas dois",
    twos_gain:"Mostra o ganho de produto ao substituir três parcelas dois",old_contribution:"Calcula a contribuição anterior ao produto",
    new_contribution:"Calcula a nova contribuição ao produto",comparison:"Compara os produtos antes e depois",
    no_ones:"Exclui parcelas iguais a um no máximo",no_ge5:"Exclui parcelas maiores ou iguais a cinco",
    threes_count:"Determina a quantidade de parcelas três",twos_count:"Determina a quantidade de parcelas dois",
    decomposition:"Verifica a decomposição da soma",max_product:"Conclui o produto máximo",general_rule:"Apresenta a regra geral",
    quotient:"Determina o quociente da divisão por três",general_complete:"Justifica todos os casos da regra geral",
    residue0_twos:"Determina os dois no caso de resto zero",residue0_threes:"Determina os três no caso de resto zero",
    residue1_twos:"Determina os dois no caso de resto um",residue1_threes:"Determina os três no caso de resto um",
    residue2_twos:"Determina os dois no caso de resto dois",residue2_threes:"Determina os três no caso de resto dois",
    list_twos:"Apresenta a lista com parcelas dois",list_four:"Apresenta a lista com uma parcela quatro",
    uniqueness:"Justifica que não há outras listas máximas",size_twos:"Conta os termos da lista com parcelas dois",
    size_four:"Conta os termos da lista com uma parcela quatro",different_sizes:"Reconhece os comprimentos distintos",
    sizes:"Conclui os comprimentos das listas",cf_adoption:"Explicita o resultado anterior adotado",
    cf_dependency:"Relaciona a etapa atual ao resultado adotado",cf_coherence:"Mantém o raciocínio coerente com o resultado adotado"
  };
  function renderTME(data, host, options) {
    const report=n("div",null,"workspace-report"), a=data.assessment;
    const fmt=v=>v==null?"Pendente":String(v).replace(".",",");
    const labels={supported:"Atendido",refuted:"Afirmação refutada",indeterminate:"Não foi possível determinar com segurança — revisão necessária",technical_error:"Erro técnico — revisão necessária"};
    const definitions=Object.fromEntries(data.pauta.obligations.map(o=>[o.id,o.description]));
    const rules={}; const index=r=>{rules[r.id]=r;(r.children||[]).forEach(index);};data.pauta.items.forEach(index);
    const records=Object.fromEntries(data.bridge.auditor.records.map(r=>[r.record_id,r]));
    const title=id=>definitions[id] && definitions[id]!==id ? definitions[id].replace("avaliada upstream", "disponível") : p5Labels[id.split(".").at(-1)] || "Etapa do raciocínio";
    const summary=n("section",null,"review-outcome");summary.setAttribute("aria-label","Resultado sugerido");
    summary.append(n("span","Sugestão ConfIA","quiet-label"),n("p",data.score==null?"Pontuação não determinada":`${fmt(data.score)} / ${fmt(data.max_score)}`,"review-score"),n("p",a.needs_review?"Sugestão provisória — revisão necessária":"Análise concluída","review-verdict"));
    summary.append(n("p","A nota final é uma decisão do avaliador."));report.append(summary);
    for(const warning of data.input_warnings||[]) report.append(n("p",warning,"formal-warning"));
    const showDecision=(decision,container,top=false)=>{
      const row=n("details",null,"audit-criterion");row.open=top;row.dataset.criterionId=decision.item_id;
      row.dataset.mathematicalStatus=decision.status;
      const label=top?`Item (${decision.item_id})`:rules[decision.item_id]?.description || "Etapa da correção";
      row.append(n("summary",`${label} — ${fmt(decision.points_awarded)} / ${fmt(decision.max_points)}`));
      if(decision.needs_review)row.append(n("p",`Revisão necessária. Pontos confirmados: ${fmt(decision.known_points)}; possíveis: ${fmt(decision.possible_points)}.`));
      if(decision.carry_forward_applied)row.append(n("p","Crédito pela continuidade coerente do raciocínio anterior."));
      const seen=new Set();
      for(const o of decision.obligations||[]){
        if(seen.has(o.obligation_id))continue;seen.add(o.obligation_id);
        const box=n("div",null,"criterion-evidence");box.dataset.mathematicalStatus=o.effective_status;
        box.append(n("p",`${glyph(o.effective_status)} ${title(o.obligation_id)} — ${labels[o.effective_status]}`));
        for(const id of o.source_claim_ids||[]){
          const record=records[id];if(!record)continue;
          if(record.source.raw_text)box.append(n("blockquote",record.source.raw_text,"evidence-quote"));
          else if(record.source.kind==="diagram_structured")box.append(n("p",`Evidência encontrada: diagrama estruturado confirmado${record.source.page_index==null?"":` na página ${record.source.page_index+1}`}.`));
        }
        const checks=data.bridge.auditor.facts.filter(f=>f.student_check && (o.source_claim_ids||[]).some(id=>f.source_claim_ids.includes(id))).map(f=>f.student_check);
        if(checks.some(c=>c.status==="verified" && c.compiled && c.lean_file))box.append(n("p","Verificação formal com Lean: confirmada (etapa local).","formal-status"));
        if(checks.some(c=>c.status==="refuted" && c.refutation_verified && c.refutation_lean_file))box.append(n("p","Verificação formal: afirmação incompatível (etapa local).","formal-status"));
        if(o.verification_source==="deterministic"||o.verification_source==="canonical_equivalence")box.append(n("p","Verificação matemática da evidência encontrada."));
        row.append(box);
      }
      const selected=decision.selected_method_path || decision.selected_band;
      const children=selected?(decision.children||[]).filter(c=>c.item_id===selected):(decision.children||[]);
      children.forEach(child=>showDecision(child,row));container.append(row);
    };
    const criteria=n("section",null,"dense-criteria");criteria.append(n("h3","Critérios da pauta"));
    a.items.forEach(item=>showDecision(item,criteria,true));report.append(criteria);
    if(root.ConfIAReport?.presentation)report.append(root.ConfIAReport.presentation.renderTechnicalDetails(options.auditRun||data));
    host.replaceChildren(report);
  }

  function render(data, host, options) {
    if (data.schema_version === "tme-audit-result.v1") return renderTME(data, host, options);
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
  function renderQuestion(data, host, options={}) {
    const report=n("div",null,"workspace-report"), fmt=v=>v==null?"Não determinada":String(v).replace(".",",");
    const summary=n("section",null,"review-outcome");summary.setAttribute("aria-label","Resultado sugerido");
    summary.append(n("span",data.stale?"Sugestão ConfIA anterior":"Sugestão ConfIA","quiet-label"),
      n("p",data.suggested_score==null?"Pontuação não determinada":`${fmt(data.suggested_score)} / ${fmt(data.max_score)}`,"review-score"),
      n("p",data.stale?options.historical?"Histórico · leitura anterior":"Análise anterior — reanálise necessária":data.review_required?"Revisar":"Pronta","review-verdict"),
      n("p","Sugestão de análise; a nota final depende da decisão do avaliador."));
    report.append(summary);
    for(const reason of [...new Set([...(data.review_reasons||[]),...(data.warnings||[])])])report.append(n("p",reason,"formal-warning"));
    const evidence=Object.fromEntries((data.evidences||[]).map(e=>[e.evidence_id,e]));
    const checks=Object.fromEntries((data.checker_summary||[]).map(c=>[c.checker_id,c]));
    const section=n("section",null,"dense-criteria");section.append(n("h3","Critérios da pauta"));
    const show=(item,container,top=false)=>{
      const row=n("details",null,"audit-criterion");row.open=top;row.dataset.criterionId=item.rubric_item_id;row.dataset.mathematicalStatus=item.status;
      const heading=n("summary");heading.append(statusIcon(item.display_status),n("span",item.label,"criterion-label"),
        n("strong",`${fmt(item.suggested_points)} / ${fmt(item.max_points)}`,"criterion-score"));
      row.append(heading,n("p",item.status_label,"criterion-verification"));
      if(item.review_required)row.append(n("p",`Revisão necessária. Pontos confirmados: ${fmt(item.known_points)}; possíveis: ${fmt(item.possible_points)}.`));
      if(item.carry_forward_applied)row.append(n("p","Crédito pela continuidade coerente do raciocínio anterior."));
      for(const id of item.evidence_ids||[]){
        const e=evidence[id];if(!e)continue;
        const box=n("div",null,"criterion-evidence");
        if(e.text){const quote=n("blockquote",null,"evidence-quote");root.ConfiaRecognitionView.renderMathText(quote,e.text);box.append(quote);}
        else box.append(n("p","Evidência estruturada registrada nesta análise."));
        if(e.exam_page_id && options.onOriginal){
          const button=n("button",`Ver no original · página ${e.page_number}`,"secondary");button.type="button";
          button.addEventListener("click",()=>options.onOriginal(e));box.append(button);
          if(e.page_reference_scope==="item_page")box.append(n("p","Página do item; sem destaque de trecho específico.","muted"));
        }
        row.append(box);
      }
      for(const label of new Set((item.checker_ids||[]).map(id=>checks[id]?.status_label).filter(Boolean)))row.append(n("p",label,"formal-status"));
      if(!(item.evidence_ids||[]).length && !(item.children||[]).length)row.append(n("p","Evidência textual não localizada; consulte os motivos e referências da análise.","muted"));
      (item.children||[]).forEach(child=>show(child,row));container.append(row);
    };
    (data.rubric_items||[]).forEach(item=>show(item,section,true));
    if(!(data.rubric_items||[]).length)section.append(n("p","Critérios indisponíveis nesta execução. A análise requer revisão."));
    report.append(section);
    const details=n("details",null,"technical-details");details.append(n("summary","Detalhes da análise"),
      n("p",`Análise: ${data.audit_run_id}`),n("p",`Transcrição: versão ${data.revision_number} · ${data.transcription_version_id}`),
      n("p",`Motor: ${data.engine_mode} · ${data.engine_version}`),
      n("p",`Início: ${data.started_at?new Date(data.started_at).toLocaleString("pt-BR"):"não registrado"} · conclusão: ${data.completed_at?new Date(data.completed_at).toLocaleString("pt-BR"):"não registrada"}`),
      n("p",data.engine_config?.use_lean===false?"Execução configurada com verificações determinísticas, sem Lean.":"Execução com verificações determinísticas e Lean quando aplicável."),
      n("pre",JSON.stringify(data,root.ConfIAReport.publicTechnicalValue,2)));
    report.append(details);host.replaceChildren(report);
  }
  root.ConfiaWorkspaceReport = { render, renderQuestion };
})(window);
