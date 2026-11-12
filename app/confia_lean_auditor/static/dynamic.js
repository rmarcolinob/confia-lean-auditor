/* Teacher preparation only. The server owns versions, approval and exact points. */
(function (root) {
  "use strict";
  const labels = {
    DRAFT_AI:"Sugestão da IA", DRAFT_TEACHER:"Rascunho do professor", TEACHER_EDITED:"Revisada pelo professor",
    APPROVED:"Aprovada", SUPERSEDED:"Versão anterior", PENDING:"Aguardando preparação", RUNNING:"Preparando",
    READY_FOR_REVIEW:"Pronta para revisão", REVIEW_REQUIRED:"Revisão necessária", FAILED:"Preparação não concluída",
    VERIFIED_WITHIN_SCOPE:"Verificada no escopo disponível", PARTIALLY_VERIFIED:"Verificação parcial",
    CONTRADICTED:"Inconsistência identificada", UNRESOLVED:"Verificação pendente", UNVERIFIED:"Não verificada",
    FORMAL_NOT_ATTEMPTED:"Verificação formal não executada", CHECKED_WITHIN_SCOPE:"Verificações limitadas concluídas",
    HUMAN_REVIEW_REQUIRED:"Revisão docente necessária", UNAVAILABLE:"Verificação indisponível",
    DETERMINISTIC:"Verificação determinística", SYMBOLIC:"Verificação simbólica", NUMERIC:"Verificação numérica",
    EXACT_ARITHMETIC:"Aritmética exata", SYMBOLIC_ALGEBRA:"Álgebra simbólica", NUMERICAL:"Verificação numérica",
    FINITE_ENUMERATION:"Enumeração finita", LEAN_CANDIDATE:"Candidata à verificação formal", SEMANTIC_RESIDUAL:"Revisão de interpretação", REVIEW_ONLY:"Revisão docente",
    TEACHER:"Professor", TECHNICAL_DEMO:"Demonstração técnica", EXPLICIT:"explícita", INFERRED:"inferida"
  };
  const readable = value => String(value || "").replace(/\b[A-Z][A-Z_]+\b/g, code => labels[code] || code);
  function create({host:panel,onSelect=()=>{},setBusy=()=>{},onOpenAttempt=()=>{}}) {
  let disposed=false, creation, selectionGeneration=0;

  let detail, list, message, busy = false, loadGeneration = 0;
  const n = (tag, text, cls) => { const el = document.createElement(tag); if (text != null) el.textContent = text; if (cls) el.className = cls; return el; };
  const append = (el, ...children) => { children.forEach(child => el.appendChild(child)); return el; };
  const label = (text, input) => append(n("label", text), input);
  const input = (name, value = "", type = "text") => { const el = n(type === "textarea" ? "textarea" : "input"); el.name = name; el.value = String(value); if (type !== "textarea") el.type = type; el.setAttribute("aria-label", name); return el; };
  const button = (text, handler, cls = "tme-button secondary") => { const el = n("button", text, cls); el.type = "button"; el.addEventListener("click", handler); return el; };
  const cents = value => /^\d+(?:\.\d{1,2})?$/.test(String(value)) ? Math.round(Number(value) * 100) : null;
  const money = value => Number(value).toLocaleString("pt-BR", {maximumFractionDigits: 2});

  async function request(url, body, method = "POST") {
    const response = await fetch(url, body === undefined ? {credentials: "same-origin"} : {
      method, credentials: "same-origin", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) {
      const reason = data.detail;
      throw new Error(typeof reason === "string" ? reason : reason?.message || "Confira os campos e os pontos da rubrica. Recarregue se outra sessão alterou o problema.");
    }
    return data;
  }
  async function perform(operation, progress = "Salvando…") {
    if (busy || disposed) return;
    busy = true; setBusy(true);
    const controls = [...panel.querySelectorAll("button,input,textarea")].map(el => [el, el.disabled]);
    controls.forEach(([el]) => { el.disabled = true; });
    message.textContent = progress;
    try { await operation(); }
    catch (error) { message.textContent = error.message; }
    finally { busy = false; if(!disposed)setBusy(false); controls.forEach(([el, disabled]) => { el.disabled = disabled; }); }
  }
  async function selectProblem(problemId) {
    const generation=++selectionGeneration;
    const doc=await request(`/dynamic/problems/${encodeURIComponent(problemId)}`);
    if(!disposed && generation===selectionGeneration)renderDocument(doc);
  }
  function warningText(value,prep,criteria=[]) {
    let result=readable(value).replace(/\bclaims?\b/gi, match=>match.toLowerCase()==="claims"?"argumentos":"argumento");
    for(const candidate of prep?.proposal?.candidate_reference_solutions || [])
      result=result.split(candidate.solution_id).join(candidate.strategy_label);
    for(const criterion of criteria)result=result.split(criterion.criterion_id).join(criterion.title);
    return result;
  }
  function statusBadge(status) {
    const badge=n("span",readable(status),"home-status");
    badge.dataset.status=status==="APPROVED"?"finalized":["REVIEW_REQUIRED","PARTIALLY_VERIFIED","CONTRADICTED","FAILED"].includes(status)?"inconclusive":"pending";
    return badge;
  }
  async function refreshList() {
    const documents = await request("/dynamic/problems");
    if(disposed)return;
    list.replaceChildren();
    for (const doc of documents) {
      const statement = doc.statements[doc.statements.length - 1];
      list.appendChild(button(`${statement.title || "Questão sem título"} · Enunciado V${statement.version_number}`, () => perform(async () => {
        await selectProblem(doc.problem.problem_id); message.textContent = "Questão carregada.";
      })));
    }
    if (!documents.length) list.appendChild(n("p", "Nenhuma questão cadastrada."));
  }
  async function saved(url, body, method, notice) {
    renderDocument(await request(url, body, method));
    message.textContent = notice;
    await refreshList();
  }
  function statementForm(doc) {
    const latest = doc?.statements[doc.statements.length - 1];
    const form = n("form", null, "dynamic-form"), title = input("Título", latest?.title || ""),
      statement = input("Enunciado", latest?.statement || "", "textarea"), total = input("Valor total", latest?.max_score || "10", "number");
    title.maxLength = 160; statement.maxLength = 20000; statement.required = true;
    statement.rows = 3; total.min = "0.01"; total.max = "1000"; total.step = "0.01"; total.required = true;
    const submit = n("button", latest ? "Salvar nova versão do enunciado" : "Criar problema", "tme-button"); submit.type = "submit";
    append(form, label("Título (opcional)", title), label("Enunciado", statement), label("Valor total", total));
    if (latest) form.appendChild(n("p", "Salvar uma nova versão exige nova rubrica e aprovação. O pacote anterior permanece no histórico."));
    form.appendChild(submit);
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!statement.value.trim() || cents(total.value) === null || Number(total.value) <= 0) { message.textContent = "Informe enunciado e valor total positivo, com até duas casas decimais."; return; }
      return perform(async () => {
        const body = {title: title.value, statement: statement.value, max_score: total.value};
        if (doc) body.expected_revision = doc.revision; else body.correction_mode = "DYNAMIC";
        await saved(doc ? `/dynamic/problems/${doc.problem.problem_id}/statements` : "/dynamic/problems", body, "POST",
          doc ? "Nova versão criada. A rubrica anterior está no histórico; crie e aprove uma nova rubrica." : "Questão criada. Prepare com ConfIA ou forneça sua rubrica.");
        if (!doc) { title.value = ""; statement.value = ""; }
      });
    });
    return form;
  }
  function renderDocument(doc) {
    if(disposed)return;
    creation.hidden=true; detail.replaceChildren(); onSelect(doc.problem.problem_id);
    const statement = doc.statements[doc.statements.length - 1], pid = doc.problem.problem_id;
    const rubric = doc.rubrics.filter(r => r.statement_version === statement.version_number).slice(-1)[0];
    const context = n("nav", null, "dynamic-context"); context.setAttribute("aria-label", "Etapas da preparação");
    const question = n("section", null, "tme-panel dynamic-question");
    append(question, n("h2", statement.title || "Questão sem título"), n("p", `Enunciado V${statement.version_number} · ${money(statement.max_score)} pontos`));
    append(detail, context, question);
    if (doc.actor_notice) question.appendChild(n("p", doc.actor_notice, "prototype-note"));
    question.appendChild(n("p", statement.statement, "dynamic-statement"));
    detail.appendChild(n("p", "Soluções candidatas precisam de revisão docente. A sugestão de pontuação exige uma rubrica aprovada e continua sujeita à decisão docente."));
    const preparationSection=renderPreparation(doc);
    const editStatement = n("details"); append(editStatement, n("summary", "Criar nova versão do enunciado"), statementForm(doc)); question.appendChild(editStatement);
    const section = n("section", null, "tme-panel dynamic-rubric"), rows = n("div"), total = n("p"), heading = n("h3", rubric?.generation ? "Rubrica sugerida pela IA · revisão docente" : "Rubrica fornecida pelo professor");
    const state = n("p", rubric ? `Rubrica V${rubric.version_number} · ` : "Sem rubrica para este enunciado.");
    if(rubric)state.appendChild(statusBadge(rubric.status));
    const prep = doc.current_preparation;
    const reason = input("Motivo da nova sugestão (opcional)"); reason.maxLength = 1000;
    const ai = button(rubric?.generation ? "Rejeitar e gerar nova sugestão" : "Gerar rubrica sugerida", () => perform(() => saved(`/dynamic/problems/${pid}/rubric-suggestion`,
      {expected_revision: doc.revision, preparation_id: prep.preparation_id, reason: reason.value || null}, "POST",
      "Sugestão da IA salva. Leia os avisos, edite se necessário e aprove explicitamente."), "Gerando e revisando a rubrica…"));
    ai.disabled = !doc.automatic_suggestion_available || !prep || !["READY_FOR_REVIEW", "REVIEW_REQUIRED"].includes(prep.status);
    const unavailable = n("p", !doc.automatic_suggestion_available ? "Preparação com IA indisponível nesta instalação. A rubrica manual continua disponível."
      : !prep ? "Prepare o enunciado atual para gerar uma sugestão." : "A sugestão não ativa a rubrica. A aprovação continua sendo sua decisão.");
    const warnings = rubric?.review_warnings || [];
    const acknowledgement = input("Li os avisos e assumo a revisão docente", "", "checkbox");
    const requiresAcknowledgement = warnings.some(w => w.requires_review);
    const warningsBox = n("div", null, "dynamic-warnings");
    const uniqueWarnings = warnings.filter((w,i) => warnings.findIndex(other => other.message === w.message && other.requires_review === w.requires_review) === i);
    uniqueWarnings.forEach(w => warningsBox.appendChild(n("p", `${w.requires_review ? "Revisão necessária" : "Limite da verificação"}: ${warningText(w.message,prep,rubric?.criteria)}`)));
    if(warnings.length) {
      const raw=n("details");append(raw,n("summary","Detalhes técnicos dos avisos"));
      warnings.forEach(w=>raw.appendChild(n("p",`${w.code || "Aviso"}: ${w.message}`)));warningsBox.appendChild(raw);
    }
    if (rubric?.generation?.semantic_review) {
      const review = n("details"); append(review, n("summary", "Revisão semântica da sugestão original"), n("p", rubric.generation.semantic_review.rationale)); warningsBox.appendChild(review);
    }
    if (requiresAcknowledgement) warningsBox.appendChild(label("Li os avisos e assumo a revisão docente", acknowledgement));
    acknowledgement.addEventListener("change", () => update());
    let dirty = !rubric, nextId = 1, replaceWithTeacher = false; const editors = [];
    const usedIds = new Set(doc.rubrics.flatMap(version => version.criteria.map(c => c.criterion_id)));
    const save = button(rubric ? "Salvar como nova versão da rubrica" : "Salvar rascunho da rubrica", () => {
      const payload = read();
      if (!valid()) { message.textContent = "A soma dos critérios deve ser igual ao valor total. Confira também os textos."; return; }
      return perform(() => saved(`/dynamic/problems/${pid}/rubrics${rubric ? `/${rubric.rubric_id}` : ""}`,
        {expected_revision: doc.revision, statement_version: statement.version_number, max_score: statement.max_score, criteria: payload, ...(replaceWithTeacher ? {replace_with_teacher: true} : {})},
        rubric ? "PATCH" : "POST", "Rubrica salva como nova versão de rascunho. Revise antes de aprovar."));
    }, "tme-button");
    const approve = button("Aprovar rubrica", () => perform(() => saved(`/dynamic/problems/${pid}/rubrics/${rubric.rubric_id}/approve`,
      {expected_revision: doc.revision, ...(requiresAcknowledgement ? {acknowledge_warnings: acknowledgement.checked} : {})}, "POST", "Rubrica aprovada. Versão exata registrada na configuração aprovada.")), "tme-button");
    function read() { return editors.map((row, i) => ({...row.original, criterion_id: row.id, title: row.title.value,
      description: row.description.value, max_points: row.points.value, order: i + 1})); }
    function valid() { return editors.every(row => row.title.value.trim() && row.description.value.trim() && cents(row.points.value) !== null)
      && (!editors.length || editors.reduce((sum, row) => sum + cents(row.points.value), 0) === cents(statement.max_score)); }
    function update() {
      const values = editors.map(row => cents(row.points.value));
      total.textContent = `Total dos critérios: ${values.some(v => v === null) ? "inválido" : money(values.reduce((a,b) => a+b,0)/100)} / ${money(statement.max_score)} pontos`;
      save.disabled = !valid();
      approve.disabled = !rubric || dirty || !rubric.criteria.length || ["APPROVED", "SUPERSEDED"].includes(rubric.status) || (requiresAcknowledgement && !acknowledgement.checked);
    }
    function addCriterion(data) {
      let id = data?.criterion_id;
      if (!id) { do { id = `criterion_${nextId++}`; } while (usedIds.has(id)); }
      usedIds.add(id);
      const box = n("fieldset", null, "dynamic-criterion"), title = input(`Critério ${id}: título`, data?.title || ""),
        description = input(`Critério ${id}: descrição`, data?.description || "", "textarea"), points = input(`Critério ${id}: pontos`, data?.max_points ?? "0", "number");
      title.maxLength = 160; description.maxLength = 20000; description.rows = 2; points.min = "0"; points.max = "1000"; points.step = "0.01";
      const row = {id, title, description, points, original: data || {}, box}; editors.push(row);
      [title, description, points].forEach(el => el.addEventListener("input", () => { dirty = true; update(); }));
      append(box, n("legend", `Critério ${editors.length}`), label("Título", title), label("Descrição / justificativa", description), label("Pontos", points), button("Remover critério", () => {
        editors.splice(editors.indexOf(row), 1);
        editors.forEach(other => { if (other.original.dependencies) other.original = {...other.original, dependencies: other.original.dependencies.filter(id => id !== row.id)}; });
        rows.removeChild(box); dirty = true; update();
      }));
      if (data?.evidence) {
        const info = n("details"); append(info, n("summary", "Vínculos da sugestão original"),
          n("p", `Objetivo: ${data.evidence.mathematical_objective}`),
          n("p", `Etapas relacionadas: ${data.evidence.related_reference_claims.join(", ") || "não definidos"}`),
          n("p", `Métodos aceitos: ${data.evidence.accepted_alternative_strategies.join(", ") || "revisar"}`));
        box.appendChild(info);
      }
      rows.appendChild(box); update();
    }
    (rubric?.criteria || []).forEach(addCriterion);
    const manual = button("Fornecer minha própria rubrica", () => {
      editors.splice(0); rows.replaceChildren(); dirty = true; replaceWithTeacher = true; update();
      message.textContent = "Insira seus critérios e salve como nova versão docente. O histórico será preservado.";
    });
    append(section, heading, state, ai, label("Motivo da nova sugestão (opcional)", reason), unavailable, warningsBox, manual, rows, button("Adicionar critério", () => { dirty = true; addCriterion(); }), total, save, approve);
    if (rubric?.status === "APPROVED") section.appendChild(n("p", "A versão aprovada é imutável. Alterações serão salvas em uma nova versão de rascunho; a versão ativa só muda após aprovação."));
    detail.appendChild(section); update();
    const history = n("section", null, "tme-panel dynamic-history"); history.setAttribute("aria-label", "Histórico de versões");
    append(history, n("h3", "Histórico de versões"), n("p", doc.current_configuration
      ? `Configuração aprovada V${doc.current_configuration.package.package_version} · Enunciado V${doc.current_configuration.package.statement_version} · Rubrica V${doc.current_configuration.package.rubric_version}`
      : "Sem configuração aprovada. Uma nova rubrica aprovada é necessária."));
    for (const item of doc.statements) {
      const block = n("details"); append(block, n("summary", `Enunciado V${item.version_number}`), n("p", item.statement)); history.appendChild(block);
    }
    for (const prep of doc.preparation_history || []) {
      const block = n("details"); append(block, n("summary", `Preparação V${prep.preparation_version} · ${readable(prep.effective_status)} · Enunciado V${prep.statement_version}`));
      appendPreparationEvidence(block, prep); history.appendChild(block);
    }
    for (const item of doc.rubrics) {
      const block = n("details"); append(block, n("summary", `Rubrica V${item.version_number} · ${readable(item.status)} · Enunciado V${item.statement_version}`));
      item.criteria.forEach(c => block.appendChild(n("p", `${c.title} — ${money(c.max_points)} pontos. ${c.description}`)));
      if (item.approved_at) block.appendChild(n("p", `Aprovação: ${readable(item.approved_by.kind)} · ${item.approved_by.actor_id} · ${item.approved_at}`));
      history.appendChild(block);
    }
    detail.appendChild(history);
    for(const [title,target] of [["Questão",question],["Preparação",preparationSection],["Rubrica",section],["Histórico",history]])
      context.appendChild(button(title,()=>{target.scrollIntoView({behavior:"smooth",block:"start"});target.tabIndex=-1;target.focus();}));
    if(doc.current_configuration) {
      const next=n("section",null,"tme-panel dynamic-next");
      append(next,n("h3","Preparação salva no ConfIA"),n("p","A configuração aprovada está registrada. Receba uma resolução textual e abra o workspace Original / Transcrição / Comparar, com o painel ConfIA e decisão humana."),
        n("p","A aprovação da rubrica não elimina avisos ou incertezas e não substitui a decisão final do professor."));
      if(doc.correction_available) {
        const form=n("form",null,"dynamic-form"),code=input("Código da resolução"),solution=input("Resolução do aluno","","textarea"),allow=input("Permitir análise provisória com preparação em revisão","","checkbox");
        const policy=n("select");policy.setAttribute("aria-label","Perfil da atividade");
        for(const [value,title] of [["SCHOOL_EXAM","Prova escolar"],["FORMATIVE_LIST","Lista formativa"]]){const option=n("option",title);option.value=value;policy.append(option);}policy.value="SCHOOL_EXAM";
        code.required=true;code.maxLength=80;code.pattern="[A-Za-z0-9._:/-]+";solution.required=true;solution.maxLength=20000;solution.rows=8;
        append(form,label("Código pseudônimo da resolução",code),label("Resolução do aluno",solution),label("Perfil da atividade",policy),label("Permitir análise provisória com preparação em revisão",allow));
        const submit=n("button","Receber resolução e abrir correção","tme-button");submit.type="submit";form.appendChild(submit);
        form.addEventListener("submit",async event=>{event.preventDefault();let attempt;
          await perform(async()=>{attempt=await request(`/dynamic/problems/${pid}/attempts`,{external_candidate_ref:code.value,solution:solution.value,allow_preparation_review:allow.checked,policy_profile:policy.value});},"Recebendo resolução…");
          if(attempt && !disposed)onOpenAttempt(attempt.case_id);
        });next.appendChild(form);
      }
      detail.appendChild(next);
    }
  }
  function appendPreparationEvidence(section, prep) {
    if (prep.failure_code) {
      section.appendChild(n("p", "Não foi possível concluir a preparação. Tente novamente ou forneça sua rubrica; nenhuma solução de referência foi criada.", "dynamic-warning"));
      const failure=n("details");append(failure,n("summary","Detalhes técnicos da falha"),n("p",prep.failure_code));section.appendChild(failure);
    }
    const proposal = prep.proposal;
    if (!proposal) return;
    append(section, n("h4", `Domínio: ${proposal.mathematical_domain}`), n("p", proposal.normalized_problem), n("p", `Objetivo: ${proposal.target}`));
    (proposal.assumptions || []).forEach(a => section.appendChild(n("p", `Hipótese ${readable(a.source)}: ${a.text}`)));
    for (const candidate of proposal.candidate_reference_solutions || []) {
      const evidence = (prep.analysis?.candidate_checks || []).find(c => c.solution_id === candidate.solution_id);
      const block = n("details"); append(block, n("summary", `Solução de referência candidata · ${candidate.strategy_label} · ${readable(evidence?.status || "UNRESOLVED")}`));
      candidate.claims.forEach(c => block.appendChild(n("p", c.text)));
      block.appendChild(n("p", `Resultado candidato: ${candidate.final_result.text}`)); section.appendChild(block);
    }
    section.appendChild(n("h4", "Métodos alternativos"));
    (proposal.alternative_strategies || []).forEach(s => section.appendChild(n("p", s.description)));
    section.appendChild(n("h4", "Avisos e incertezas"));
    (prep.analysis?.warnings || []).forEach(w => section.appendChild(n("p", `${w.requires_review ? "Revisão necessária" : "Limite"}: ${warningText(w.message,prep)}`, "dynamic-warning")));
    (proposal.uncertainties || []).forEach(u => section.appendChild(n("p", u)));
    const plan = n("details"); plan.appendChild(n("summary", "Verificações e limites"));
    (prep.analysis?.verifier_plan || []).forEach(c => plan.appendChild(n("p", `${c.claim_id} · ${readable(c.capability)} · ${readable(c.status)} · ${readable(c.formal_status)}. ${readable(c.detail)} ${c.scope}`)));
    section.appendChild(plan);
    const technical=n("details");technical.appendChild(n("summary","Detalhes técnicos e proveniência"));
    technical.appendChild(n("p",`Estado registrado: ${prep.status}. Confiança: ${prep.analysis?.trust_state}.`));
    if (prep.provenance) technical.appendChild(n("p", `Origem: ${prep.provenance.provider} · ${prep.provenance.returned_model} · ${prep.provenance.prompt_version}. Estado de confiança: ${prep.analysis?.trust_state}.`));
    (prep.analysis?.warnings || []).forEach(w=>technical.appendChild(n("p",`${w.code || "Aviso"}: ${w.message}`)));
    section.appendChild(technical);
  }
  function renderPreparation(doc) {
    const section = n("section", null, "tme-panel dynamic-preparation"), prep = doc.current_preparation;
    const reason = input("Motivo da nova preparação (opcional)"); reason.maxLength = 1000;
    const prepare = button(prep ? "Gerar nova preparação" : "Preparar com ConfIA", () => perform(() => saved(`/dynamic/problems/${doc.problem.problem_id}/preparations`,
      {expected_revision:doc.revision, reason:reason.value || null}, "POST", "Preparação registrada. Confira o estado e as evidências antes de gerar uma rubrica."), "Preparando com ConfIA… Aguarde as checagens matemáticas."));
    prepare.disabled = !doc.automatic_suggestion_available;
    append(section, n("h3", "Preparação"), prep ? append(n("p", `Preparação V${prep.preparation_version} · `),statusBadge(prep.status)) : n("p","Ainda não preparada."), prepare,
      label("Motivo da nova preparação (opcional)",reason));
    section.appendChild(button("Atualizar preparação", () => perform(async () => renderDocument(await request(`/dynamic/problems/${doc.problem.problem_id}`)))));
    if (prep && ["PENDING","RUNNING"].includes(prep.status)) {
      section.appendChild(n("p", "Preparação em andamento. Após interrupção, uma nova tentativa pode ser feita em 3 minutos."));
    }
    if (prep) appendPreparationEvidence(section, prep);
    detail.appendChild(section);return section;
  }
  function newQuestion() {
    if(busy || disposed)return;
    ++loadGeneration;++selectionGeneration;detail.replaceChildren();creation.hidden=false;message.textContent="";onSelect(null);
  }
  async function load(problemId) {
    const generation = ++loadGeneration;
    panel.replaceChildren();
    message = n("p"); message.setAttribute("role", "status"); message.setAttribute("aria-live", "polite");
    list = n("div", null, "dynamic-problem-list"); detail = n("div");
    creation=n("section",null,"tme-panel dynamic-creation");
    append(creation,n("h2","Dados da atividade"),n("p","Nesta etapa, prepare uma questão por vez, com título, enunciado e pontos. Tipos de atividade (lista, atividade ou prova) e agrupamento de questões serão integrados futuramente."),statementForm());
    const resume=n("details",null,"tme-panel dynamic-resume");append(resume,n("summary","Retomar preparação"),list);
    append(panel,button("Nova questão",newQuestion),resume,message,creation,detail);
    try {
      await refreshList();
      if(generation===loadGeneration && !disposed && problemId)await selectProblem(problemId);
    } catch(error) {if(generation===loadGeneration && !disposed)message.textContent=error.message;}
  }
  return {load,cancel(){disposed=true;++loadGeneration;}};
  }
  root.ConfIADynamic = {create};
})(window);
