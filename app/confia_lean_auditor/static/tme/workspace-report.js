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
        const statusLabel=o.effective_status==="refuted" && o.metadata?.semantic_fallback?.decision==="not_met"
          ? "Critério não atendido" : labels[o.effective_status];
        box.append(n("p",`${glyph(o.effective_status)} ${title(o.obligation_id)} — ${statusLabel}`));
        for(const id of o.source_claim_ids||[]){
          const record=records[id];if(!record)continue;
          if(record.source.raw_text)box.append(n("blockquote",record.source.raw_text,"evidence-quote"));
          else if(record.source.kind==="diagram_structured")box.append(n("p",`Evidência encontrada: diagrama estruturado confirmado${record.source.page_index==null?"":` na página ${record.source.page_index+1}`}.`));
        }
        const checks=data.bridge.auditor.facts.filter(f=>f.student_check && (o.source_claim_ids||[]).some(id=>f.source_claim_ids.includes(id))).map(f=>f.student_check);
        if(checks.some(c=>c.status==="verified" && c.compiled && c.lean_file))box.append(n("p","Verificação formal com Lean: confirmada (etapa local).","formal-status"));
        if(checks.some(c=>c.status==="refuted" && c.refutation_verified && c.refutation_lean_file))box.append(n("p","Verificação formal: afirmação incompatível (etapa local).","formal-status"));
        if(o.verification_source==="deterministic"||o.verification_source==="canonical_equivalence")box.append(n("p","Verificação matemática da evidência encontrada."));
        if(o.metadata?.semantic_fallback){
          box.append(n("p","Avaliação semântica pela pauta · sem certificação formal."));
          box.append(n("p",o.metadata.semantic_fallback.response?.justification || "Revisão pendente."));
          for(const q of o.metadata.semantic_fallback.quotes || [])box.append(n("blockquote",q.text,"evidence-quote"));
        }
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
    const reconciliation=data.engine_mode==="DYNAMIC"?options.reconciliation:null, shownScore=reconciliation?(reconciliation.reconciled_suggested_score==null?null:Number(reconciliation.reconciled_suggested_score)):data.score;
    const math = (tag, value, cls) => { const el = n(tag, null, cls); root.ConfiaRecognitionView.renderMathText(el, String(value || "")); return el; };
    const items = p.rubricItems(data), decided = items.filter(p.isDecided), checks = data.student_claim_checks || [];
    const formalStatus = check => p.formalStatus(check) === "verified" && (!check.compiled || !check.lean_file) ? "unverified" : p.formalStatus(check);
    const report = n("div", null, "workspace-report");
    const globalState = data.engine_mode==="DYNAMIC" ? ((reconciliation?reconciliation.review_required:data.review_required)?"Revisão necessária":"Análise concluída") : options.auditRun?.status === "FAILED" ? "Falha técnica" : data.rubric_assessment?.assessment_status === "partial" ? "Parcialmente decidida" : !finite(data.score) ? "Inconclusiva" : "Análise concluída";
    const summary = n("section", null, "review-outcome"); summary.setAttribute("aria-label", "Resultado sugerido");
    summary.append(n("span", "Sugestão ConfIA", "quiet-label"), n("p", finite(shownScore) ? `${number(shownScore)} / ${number(data.max_score)}` : "Pontuação não determinada", "review-score"), n("p", globalState, "review-verdict"));
    const coverage = n("section", null, "coverage"); coverage.setAttribute("aria-label", "Cobertura da análise");
    coverage.append(n("h3", "Cobertura da análise"), n("p", `${decided.length}/${items.length} critérios decididos`, "coverage-headline"));
    const bar = n("div", null, "coverage-track"); bar.setAttribute("aria-hidden", "true");
    const fill = n("span"); fill.style.width = `${items.length ? 100 * decided.length / items.length : 0}%`; bar.appendChild(fill);
    const verified = checks.filter(check => formalStatus(check) === "verified").length;
    coverage.append(bar, n("p", `${items.length} critérios · ${decided.length} decididos · ${counted(verified, "claim formalmente verificado", "claims formalmente verificados")} · ${counted(items.length - decided.length, "indeterminado", "indeterminados")}`, "coverage-stats"));
    report.append(summary, coverage);
    if(data.engine_mode==="DYNAMIC"){
      report.append(independentReviewPanel(data,options),reconciliationPanel(data,options));
      if(reconciliation)summary.append(n("p",`Sugestão reconciliada · Primeira análise preservada: ${number(data.score)} / ${number(data.max_score)}`));
    }
    if(data.engine_mode==="DYNAMIC") {
      summary.append(n("p",(reconciliation?reconciliation.review_required:data.review_required)?"Revisão necessária · sugestão provisória":"Sugestão provisória · decisão do professor","formal-warning"));
      summary.append(n("p","Modo: Correção dinâmica","quiet-label"));
      for(const warning of data.uncertainty||[])summary.append(n("p",warning,"formal-warning"));
      const evidence=n("details");evidence.append(n("summary","Evidências e verificações da resolução"));
      const labels={VERIFIED:"Verificado no escopo",REFUTED:"Refutado",ERROR:"Falha de verificação",REVIEW_ONLY:"Revisão necessária",INCOMPLETE:"Incompleto",NOT_ATTEMPTED:"Não verificado"};
      for(const claim of data.analysis?.claims||[])evidence.append(n("p",`${claim.text} — ${labels[claim.verification_status]||claim.verification_status}. ${claim.verification_detail}`));
      report.append(evidence);
    }
    const section = n("section", null, "dense-criteria"); section.appendChild(n("h3", reconciliation?"Critérios da primeira análise":"Critérios de correção"));
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
      if(item.verification_level==="SEMANTIC_NOT_FORMAL" || item.scoring_basis==="semantic_fallback") {
        row.append(n("p","Avaliação semântica pela rubrica · sem certificação formal."));
        if(item.scoring_rationale) row.append(math("p",item.scoring_rationale));
        if(item.suggested_points!=null)row.append(n("p",`Sugestão: ${number(item.suggested_points)} / ${number(item.max_points)}`));
      }
      row.appendChild(n("p", `Verificação: ${item.verification_status === "technical_error" ? "⚠ Verificação formal não concluída" : ({ verified_in_scope: "Verificado no escopo exato", review_only: "Revisão necessária", refuted_exact: "Refutado por verificação exata", not_attempted: "Verificação formal não executada", available: "Disponível", not_available: "Não disponível", verified: "Verificado formalmente", not_verified: "Não verificado" }[item.verification_status] || item.verification_status || "Não registrada")}`, "criterion-verification"));
      for (const note of item.adjustment_notes || []) row.appendChild(math("p", note));
      section.appendChild(row);
    });
    if (!items.length) section.appendChild(n("p", "Critérios não disponíveis nesta execução.", "muted"));
    report.appendChild(section);
    const map = n("section", null, "solution-map"); map.appendChild(n("h3", "Passos identificados"));
    const entries = data.engine_mode==="DYNAMIC"?(data.analysis?.claims||[]).map(c=>({claim:{...c,id:c.claim_id,evidence:c.text},check:null})):p.claimEntries(data), list = n("div", null, "claim-list"), detail = n("section", null, "claim-detail"); detail.setAttribute("aria-live", "polite");
    const buttons = [];
    const select = index => {
      saved.selectedClaim = entries[index].claim.id;
      buttons.forEach((button, i) => button.setAttribute("aria-pressed", String(i === index)));
      const {claim, check} = entries[index]; detail.replaceChildren();
      detail.append(math("p", claim.evidence || claim.raw_text || "Evidência textual não localizada.", "evidence-quote"), n("p", data.engine_mode==="DYNAMIC"?({VERIFIED:"Verificado no escopo",REFUTED:"Refutado",ERROR:"Falha de verificação",REVIEW_ONLY:"Revisão necessária"}[claim.verification_status]||"Verificação inconclusiva"):p.formalLabels[formalStatus(check)], "formal-status"));
      if (check?.lean_statement) { const d = n("details"); d.append(n("summary", "Formalização do passo"), n("code", check.lean_statement)); detail.appendChild(d); }
      // Hook for future source mapping. The current API has no verified offsets;
      // never infer document highlights from string similarity.
      if (options.onEvidenceSelection) options.onEvidenceSelection({ claimId: claim.id, mapping: null });
      detail.appendChild(n("p", data.engine_mode==="DYNAMIC"?`Trecho preservado: caracteres ${claim.start}–${claim.end} da transcrição aceita.`:"Sem vínculo preciso com um trecho da transcrição.", "mapping-note"));
    };
    entries.forEach(({claim, check, kind}, i) => {
      const button = n("button", null, "audit-claim"); button.type = "button"; button.dataset.claimId = claim.id; button.dataset.claimKind = kind; button.dataset.formalStatus = formalStatus(check);
      button.append(n("span", String(i + 1).padStart(2, "0"), "step-number"), math("span", claim.text || claim.normalized_text || claim.raw_text || claim.id, "step-label"), statusIcon(data.engine_mode==="DYNAMIC"?({VERIFIED:"supported",REFUTED:"refuted",ERROR:"technical_error"}[claim.verification_status]||"indeterminate"):formalStatus(check)));
      button.setAttribute("aria-label", `Passo ${i + 1}: ${claim.text || claim.normalized_text || claim.raw_text || claim.id}. ${data.engine_mode==="DYNAMIC"?({VERIFIED:"Verificado no escopo",REFUTED:"Refutado",ERROR:"Falha de verificação"}[claim.verification_status]||"Revisão necessária"):p.formalLabels[formalStatus(check)]}`); button.setAttribute("aria-pressed", "false");
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
  function independentReviewPanel(data,options) {
    const panel=n("section",null,"independent-review"), view=options.independentReview, record=view?.review, comparison=record?.comparison;
    panel.setAttribute("aria-label","Revisão independente");
    const details=n("details");let title=record?.status==="FAILED"?"Revisão não concluída":!comparison?"Ainda não solicitada":comparison.conflicting_criteria.length?`${comparison.conflicting_criteria.length} divergência${comparison.conflicting_criteria.length===1?" requer":"s requerem"} atenção`:`Concordância: ${comparison.agreement_count}/${comparison.criteria.length} critérios`;
    const reconciled=options.reconciliation,adjusted=reconciled?.criteria.filter(c=>c.automation.startsWith("AUTO_ADJUST")).length||0,pending=reconciled?.criteria.filter(c=>c.automation==="REVIEW_ONLY").length||0;
    if(reconciled && (adjusted||pending))title=[adjusted?`${adjusted} divergência${adjusted===1?" resolvida":"s resolvidas"}`:"",pending?`${pending} critério${pending===1?" requer":"s requerem"} revisão`:""].filter(Boolean).join(" · ");
    details.append(n("summary",`Revisão independente · ${title}`));
    if(reconciled)details.append(n("p","Comparação inicial preservada; consulte a decisão por critério na reconciliação."));
    details.append(n("p","A revisão não altera a sugestão original nem a decisão do professor."));
    if(view?.stale)details.append(n("p","Revisão de uma versão anterior; não representa a transcrição atual.","formal-warning"));
    if(record?.status==="FAILED")details.append(n("p","Não foi possível concluir a revisão. Tente novamente; nenhum acordo ou nova nota foi presumido.","formal-warning"));
    if(view?.review_required && !reconciled)details.append(n("p","Revisão necessária. Divergências e incertezas permanecem pendentes.","formal-warning"));
    const fmt=value=>value==null?"Indeterminado":String(value).replace(".",",");
    for(const item of comparison?.criteria||[]) {
      const row=n("details"), rubric=data.decisions?.find(c=>c.criterion_id===item.criterion_id), opinion=record.phase_a?.criterion_reviews.find(c=>c.criterion_id===item.criterion_id);
      row.append(n("summary",`${rubric?.description||item.criterion_id} · Grader: ${fmt(item.grader_points)} · Reviewer: ${fmt(item.reviewer_points)}`),n("p",item.reason),n("p",opinion?.explanation||""));
      for(const evidence of opinion?.evidence||[])row.append(n("blockquote",evidence));
      for(const warning of opinion?.uncertainty||[])row.append(n("p",warning,"formal-warning"));
      details.append(row);
    }
    for(const warning of record?.phase_a?.warnings||[])details.append(n("p",warning,"formal-warning"));
    if(comparison?.exact_agreement)details.append(n("p","Concordância não é prova matemática nem certificação."));
    if(options.reviewError)panel.append(n("p",options.reviewError,"formal-warning"));
    const action=n("button",options.uiState?.reviewPending?"Revisando independentemente…":record?"Solicitar nova revisão independente":"Solicitar revisão independente","secondary");action.type="button";action.disabled=Boolean(options.reviewBusy || options.auditRun?.stale);action.addEventListener("click",()=>options.onIndependentReview?.());
    panel.append(details,action);return panel;
  }
  function reconciliationPanel(data,options){
    const panel=n("section",null,"dynamic-reconciliation"),r=options.reconciliation,details=n("details"),fmt=v=>v==null?"Indeterminado":String(v).replace(".",",");
    panel.setAttribute("aria-label","Reconciliação da sugestão");
    const pending=r?.criteria.filter(c=>c.automation==="REVIEW_ONLY").length||0,changed=r?.criteria.filter(c=>c.automation.startsWith("AUTO_ADJUST")).length||0;
    details.append(n("summary",r?`Reconciliação · ${pending?`${pending} critério${pending===1?" requer":"s requerem"} revisão`:changed?`${changed} divergência${changed===1?" resolvida":"s resolvidas"}`:"Evidência compatível"}`:"Reconciliação · Pendente"));
    details.append(n("p","A sugestão reconciliada usa evidência e rubrica. Concordância entre agentes não é prova. A nota final depende da confirmação do professor."));
    if(r){
      details.append(n("p",`Perfil: ${r.policy_profile==="FORMATIVE_LIST"?"Lista formativa":"Prova escolar"}`),n("p",`Primeira análise: ${fmt(r.grader_score_snapshot)} · Sugestão reconciliada: ${fmt(r.reconciled_suggested_score)}`));
      for(const c of r.criteria){const row=n("details"),label=data.decisions?.find(d=>d.criterion_id===c.criterion_id)?.description||c.criterion_id;row.append(n("summary",`${label} · Reconciliação: ${fmt(c.reconciled_points)} / ${fmt(c.max_points)}`),n("p",`Primeira análise: ${fmt(c.grader_points)} · Revisão: ${fmt(c.reviewer_points)} · Reconciliação: ${fmt(c.reconciled_points)}`),n("p",c.reason),n("p",c.automation==="REVIEW_ONLY"?"Pontos provisórios preservados · revisão docente necessária":"Decisão sustentada no escopo verificável"));details.append(row);}
      for(const reason of r.review_reasons||[])details.append(n("p",reason,"formal-warning"));
    }
    panel.append(details);
    if(options.reconciliationError)panel.append(n("p",options.reconciliationError,"formal-warning"));
    if(!r){
      const select=n("select");select.setAttribute("aria-label","Perfil da atividade");
      for(const [value,label] of [["SCHOOL_EXAM","Prova escolar — divergências exigem revisão"],["FORMATIVE_LIST","Lista formativa — ajustes verificáveis permitidos"]]){const option=n("option",label);option.value=value;select.append(option);}
      select.value=options.dynamicPolicy?.policy_profile||options.uiState?.policyDraft||"SCHOOL_EXAM";select.disabled=Boolean(options.dynamicPolicy||options.reviewBusy);
      select.addEventListener("change",()=>{if(options.uiState)options.uiState.policyDraft=select.value;});
      const label=n("label","Perfil da atividade");label.append(select);panel.append(label,n("p",options.dynamicPolicy?"Perfil registrado na atividade; permanece fixo nesta tentativa.":"O perfil será registrado na atividade e não poderá ser trocado nesta tentativa.","muted"));
      const action=n("button",options.uiState?.reconciliationPending?"Reconciliando…":"Reconciliar sugestão","secondary");action.type="button";
      action.disabled=Boolean(options.reviewBusy||options.auditRun?.stale||!options.independentReview?.review);
      action.addEventListener("click",()=>options.onReconcile?.(select.value));panel.append(action);
    }
    return panel;
  }
  function renderQuestion(data, host, options={}) {
    const report=n("div",null,"workspace-report"), fmt=v=>v==null?"Não determinada":String(v).replace(".",",");
    const summary=n("section",null,"review-outcome");summary.setAttribute("aria-label","Resultado sugerido");
    summary.append(n("span",data.stale?"Sugestão ConfIA anterior":"Sugestão ConfIA","quiet-label"),
      n("p",data.suggested_score==null?"Pontuação não determinada":`${fmt(data.suggested_score)} / ${fmt(data.max_score)}`,"review-score"),
      n("p",data.stale?options.historical?"Histórico · leitura anterior":"Análise anterior — reanálise necessária":data.review_required?"Revisar":"Pronta","review-verdict"),
      n("p","Sugestão de análise; a nota final depende da decisão do avaliador."));
    report.append(summary);
    if(options.decisionPanel)report.append(options.decisionPanel);
    if(data.engine_mode==="DYNAMIC"){
      const opinions=n("section");opinions.setAttribute("aria-label","Pareceres da avaliação Dynamic");
      const grader=n("details"),reviewer=n("details"),reconciliation=n("details");
      grader.append(n("summary","Parecer do Grader"));
      for(const item of data.rubric_items||[]){grader.append(n("h4",item.label),n("p",item.grader_semantic_trace?.justification||item.grader_explanation||"Parecer indisponível."));for(const quote of item.grader_semantic_trace?.quotes||[])grader.append(n("blockquote",typeof quote==="string"?quote:quote.quote||quote.text||""));}
      reviewer.append(n("summary","Parecer do Reviewer"));
      for(const item of data.independent_review?.phase_a?.criterion_reviews||[]){reviewer.append(n("h4",item.criterion_id),n("p",item.explanation||"Parecer inconclusivo."));for(const quote of item.evidence||[])reviewer.append(n("blockquote",quote));}
      if(!data.independent_review?.phase_a)reviewer.append(n("p","Revisão indisponível ou não concluída."));
      reconciliation.append(n("summary","Resultado da Reconciliation"),n("p",`Nota automática: ${fmt(data.suggested_score)}`));
      for(const item of data.reconciliation?.criteria||[])reconciliation.append(n("p",`${item.criterion_id}: ${item.status} — ${item.reason}`));
      opinions.append(grader,reviewer,reconciliation);report.append(opinions);
    }
    if(data.reconciliation)report.append(n("p",`Primeira análise: ${fmt(data.grader_suggested_score)} · Sugestão reconciliada: ${fmt(data.suggested_score)} · Perfil: ${data.policy_profile}`));
    if(!data.stale && !options.historical)for(const action of data.workflow_actions||[]){
      const button=n("button",action.label,"secondary");button.type="button";button.disabled=Boolean(options.workflowDisabled);button.addEventListener("click",()=>options.onWorkflow?.(action));report.append(button);
    }
    for(const reason of [...new Set([...(data.review_reasons||[]),...(data.warnings||[])])])report.append(n("p",reason,"formal-warning"));
    const evidence=Object.fromEntries((data.evidences||[]).map(e=>[e.evidence_id,e]));
    const checks=Object.fromEntries((data.checker_summary||[]).map(c=>[c.checker_id,c]));
    const section=n("section",null,"dense-criteria");section.append(n("h3","Critérios da pauta"));
    const show=(item,container,top=false)=>{
      const row=n("details",null,"audit-criterion");row.open=top;row.dataset.criterionId=item.rubric_item_id;row.dataset.mathematicalStatus=item.status;
      const heading=n("summary");heading.append(statusIcon(item.display_status),n("span",item.label,"criterion-label"),
        n("strong",`${fmt(item.suggested_points)} / ${fmt(item.max_points)}`,"criterion-score"));
      row.append(heading,n("p",item.status_label,"criterion-verification"));
      if(item.reason)row.append(n("p",item.reason));
      if(item.review_required)row.append(n("p",item.known_points==null?"Revisão necessária. Confira as evidências e o motivo antes de homologar.":`Revisão necessária. Pontos confirmados: ${fmt(item.known_points)}; possíveis: ${fmt(item.possible_points)}.`));
      if(item.carry_forward_applied)row.append(n("p","Crédito pela continuidade coerente do raciocínio anterior."));
      for(const id of item.evidence_ids||[]){
        const e=evidence[id];if(!e)continue;
        const box=n("div",null,"criterion-evidence");
        if(e.text){const quote=n("blockquote",null,"evidence-quote");root.ConfiaRecognitionView.renderMathText(quote,e.text);box.append(quote);}
        else box.append(n("p","Evidência estruturada registrada nesta análise."));
        for(const page of e.source_pages||[]){
          const button=n('button',`Conferir evidência · página ${page.page_number}`,'secondary');button.type='button';
          button.addEventListener('click',()=>options.onOriginal?.({...e,...page,region:null}));box.append(button);
        }
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
