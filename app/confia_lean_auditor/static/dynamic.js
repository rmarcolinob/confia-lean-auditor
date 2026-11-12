/* Teacher preparation only. The server owns versions, approval and exact points. */
(function (root) {
  "use strict";
  const panel = document.querySelector("#teacher-dynamic");
  if (!panel) return;
  let detail, list, message, current = null, busy = false, loadGeneration = 0;
  const n = (tag, text, cls) => { const el = document.createElement(tag); if (text != null) el.textContent = text; if (cls) el.className = cls; return el; };
  const append = (el, ...children) => { children.forEach(child => el.appendChild(child)); return el; };
  const label = (text, input) => append(n("label", text), input);
  const input = (name, value = "", type = "text") => { const el = n(type === "textarea" ? "textarea" : "input"); el.name = name; el.value = String(value); if (type !== "textarea") el.type = type; el.setAttribute("aria-label", name); return el; };
  const button = (text, handler, cls = "button button-secondary") => { const el = n("button", text, cls); el.type = "button"; el.addEventListener("click", handler); return el; };
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
  async function perform(operation) {
    if (busy) return;
    busy = true;
    const controls = [...panel.querySelectorAll("button,input,textarea")].map(el => [el, el.disabled]);
    controls.forEach(([el]) => { el.disabled = true; });
    message.textContent = "Salvando…";
    try { await operation(); }
    catch (error) { message.textContent = error.message; }
    finally { busy = false; controls.forEach(([el, disabled]) => { el.disabled = disabled; }); }
  }
  async function refreshList() {
    const documents = await request("/dynamic/problems");
    list.replaceChildren();
    for (const doc of documents) {
      const statement = doc.statements[doc.statements.length - 1];
      list.appendChild(button(`${statement.title || "Questão sem título"} · Enunciado V${statement.version_number}`, () => perform(async () => {
        renderDocument(await request(`/dynamic/problems/${doc.problem.problem_id}`)); message.textContent = "Problema carregado.";
      })));
    }
    if (!documents.length) list.appendChild(n("p", "Nenhum problema Dynamic cadastrado."));
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
    const submit = n("button", latest ? "Salvar nova versão do enunciado" : "Criar problema", "button button-primary"); submit.type = "submit";
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
          doc ? "Nova versão criada. A rubrica anterior está no histórico; crie e aprove uma nova rubrica." : "Problema criado. Forneça a rubrica do professor.");
        if (!doc) { title.value = ""; statement.value = ""; }
      });
    });
    return form;
  }
  function renderDocument(doc) {
    current = doc; detail.replaceChildren();
    const statement = doc.statements[doc.statements.length - 1], pid = doc.problem.problem_id;
    const rubric = doc.rubrics.filter(r => r.statement_version === statement.version_number).slice(-1)[0];
    append(detail, n("h2", statement.title || "Problema Dynamic"), n("p", `Enunciado V${statement.version_number} · ${money(statement.max_score)} pontos`));
    if (doc.actor_notice) detail.appendChild(n("p", doc.actor_notice, "prototype-note"));
    detail.appendChild(n("p", "Preparação matemática automática ainda não realizada. Correção de soluções disponível em etapa futura."));
    const editStatement = n("details"); append(editStatement, n("summary", "Criar nova versão do enunciado"), statementForm(doc)); detail.appendChild(editStatement);
    const section = n("section", null, "dynamic-rubric"), rows = n("div"), total = n("p"), heading = n("h3", "Rubrica fornecida pelo professor");
    const state = n("p", rubric ? `Rubrica V${rubric.version_number} · ${rubric.status}` : "Sem rubrica para este enunciado.");
    const ai = button("Sugerir rubrica por IA", () => {}); ai.disabled = true;
    const unavailable = n("p", "Disponível no próximo estágio de preparação automática.");
    let dirty = !rubric, nextId = 1; const editors = [];
    const usedIds = new Set(doc.rubrics.flatMap(version => version.criteria.map(c => c.criterion_id)));
    const save = button(rubric ? "Salvar como nova versão da rubrica" : "Salvar rubrica draft", () => {
      const payload = read();
      if (!valid()) { message.textContent = "A soma dos critérios deve ser igual ao valor total. Confira também os textos."; return; }
      return perform(() => saved(`/dynamic/problems/${pid}/rubrics${rubric ? `/${rubric.rubric_id}` : ""}`,
        {expected_revision: doc.revision, statement_version: statement.version_number, max_score: statement.max_score, criteria: payload},
        rubric ? "PATCH" : "POST", "Rubrica salva como nova versão draft. Revise antes de aprovar."));
    }, "button button-primary");
    const approve = button("Aprovar rubrica", () => perform(() => saved(`/dynamic/problems/${pid}/rubrics/${rubric.rubric_id}/approve`,
      {expected_revision: doc.revision}, "POST", "Rubrica aprovada. Versão exata registrada no pacote ativo.")), "button button-primary");
    function read() { return editors.map((row, i) => ({...row.original, criterion_id: row.id, title: row.title.value,
      description: row.description.value, max_points: row.points.value, order: i + 1})); }
    function valid() { return editors.every(row => row.title.value.trim() && row.description.value.trim() && cents(row.points.value) !== null)
      && (!editors.length || editors.reduce((sum, row) => sum + cents(row.points.value), 0) === cents(statement.max_score)); }
    function update() {
      const values = editors.map(row => cents(row.points.value));
      total.textContent = `Total dos critérios: ${values.some(v => v === null) ? "inválido" : money(values.reduce((a,b) => a+b,0)/100)} / ${money(statement.max_score)} pontos`;
      save.disabled = !valid();
      approve.disabled = !rubric || dirty || !rubric.criteria.length || ["APPROVED", "SUPERSEDED"].includes(rubric.status);
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
      append(box, n("legend", `Critério · ${id}`), label("Título", title), label("Descrição / justificativa", description), label("Pontos", points), button("Remover critério", () => {
        editors.splice(editors.indexOf(row), 1); rows.removeChild(box); dirty = true; update();
      })); rows.appendChild(box); update();
    }
    (rubric?.criteria || []).forEach(addCriterion);
    append(section, heading, state, ai, unavailable, rows, button("Adicionar critério", () => { dirty = true; addCriterion(); }), total, save, approve);
    if (rubric?.status === "APPROVED") section.appendChild(n("p", "A versão aprovada é imutável. Alterações serão salvas em uma nova versão draft; a versão ativa só muda após aprovação."));
    detail.appendChild(section); update();
    const history = n("section", null, "dynamic-history"); history.setAttribute("aria-label", "Histórico de versões");
    append(history, n("h3", "Histórico de versões"), n("p", doc.current_configuration
      ? `Pacote ativo V${doc.current_configuration.package.package_version} · Enunciado V${doc.current_configuration.package.statement_version} · Rubrica V${doc.current_configuration.package.rubric_version}`
      : "Sem pacote ativo. Uma nova rubrica aprovada é necessária."));
    for (const item of doc.statements) {
      const block = n("details"); append(block, n("summary", `Enunciado V${item.version_number}`), n("p", item.statement)); history.appendChild(block);
    }
    for (const item of doc.rubrics) {
      const block = n("details"); append(block, n("summary", `Rubrica V${item.version_number} · ${item.status} · Enunciado V${item.statement_version}`));
      item.criteria.forEach(c => block.appendChild(n("p", `${c.title} — ${money(c.max_points)} pontos. ${c.description}`)));
      if (item.approved_at) block.appendChild(n("p", `Aprovação: ${item.approved_by.kind} · ${item.approved_by.actor_id} · ${item.approved_at}`));
      history.appendChild(block);
    }
    detail.appendChild(history);
  }
  async function load() {
    const generation = ++loadGeneration;
    panel.replaceChildren();
    message = n("p"); message.setAttribute("role", "status"); message.setAttribute("aria-live", "polite");
    list = n("div", null, "dynamic-problem-list"); detail = n("section");
    append(panel, n("h2", "ConfIA Dynamic · Problemas e rubricas"), n("p", "Cadastre um problema e aprove a rubrica que será usada nas próximas etapas."), message,
      n("h3", "Criar problema"), statementForm(), n("h3", "Meus problemas"), list, detail);
    try { await refreshList(); if (generation === loadGeneration && current) renderDocument(await request(`/dynamic/problems/${current.problem.problem_id}`)); }
    catch (error) { if (generation === loadGeneration) message.textContent = error.message; }
  }
  root.ConfIADynamic = {load};
})(window);
