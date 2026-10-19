/* Institutional management shows only server-supplied aggregate data. */
(function managementPanel() {
  "use strict";
  const get = id => document.querySelector(`#${id}`);
  const labels = {
    number_of_schools: "Escolas", number_of_classrooms: "Turmas",
    number_of_students: "Alunos", number_of_teachers: "Professores",
    submissions_count: "Submissões", audit_runs_count: "Auditorias",
    transcriptions_count: "Transcrições", recognition_success_count: "Reconhecimentos concluídos",
    recognition_failure_count: "Falhas de reconhecimento", completed_audits: "Análises concluídas",
    inconclusive_audits: "Análises inconclusivas",
    decisions_finalized_count: "Decisões finalizadas",
    decisions_released_count: "Resultados liberados",
    override_count: "Decisões com alteração da sugestão",
  };
  let sequence = 0;
  let currentSchool = null;
  let currentClassroom = null;
  function node(tag, content) {
    const item = document.createElement(tag);
    if (content !== undefined) item.textContent = content;
    return item;
  }
  async function read(url) {
    const response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  function renderCards(metrics) {
    const host = get("management-cards");
    host.replaceChildren();
    for (const [key, label] of Object.entries(labels)) {
      const card = node("article"); card.className = "macro-card";
      card.appendChild(node("span", label));
      card.appendChild(node("strong", metrics[key] == null ? "Indisponível" : String(metrics[key])));
      host.appendChild(card);
    }
  }
  function button(text, action) {
    const item = node("button", text); item.type = "button";
    item.className = "secondary-action"; item.addEventListener("click", action);
    return item;
  }
  function renderRows(headers, rows, makeRow) {
    const host = get("management-table"); host.replaceChildren();
    const table = node("table"); table.className = "management-table";
    const head = node("thead"), headRow = node("tr");
    for (const label of headers) headRow.appendChild(node("th", label));
    head.appendChild(headRow); table.appendChild(head);
    const body = node("tbody");
    for (const row of rows) body.appendChild(makeRow(row));
    table.appendChild(body); host.appendChild(table);
    if (!rows.length) host.appendChild(node("p", "Nenhum registro disponível neste escopo."));
  }
  function cell(row, content) { row.appendChild(node("td", content == null ? "Indisponível" : String(content))); }
  function usage(metrics) {
    if (metrics.submissions_count == null) return "Indisponível";
    return metrics.number_of_students ? `${(metrics.submissions_count / metrics.number_of_students).toFixed(1)} envio(s)/aluno` : "Sem matrículas";
  }
  function crumbs() {
    const host = get("management-breadcrumb"); host.replaceChildren();
    if (currentSchool || currentClassroom) host.appendChild(button("Visão geral", () => { currentSchool = null; currentClassroom = null; load(); }));
    if (currentClassroom) host.appendChild(button("Escola", () => { currentClassroom = null; load(); }));
  }
  async function load() {
    const user = window.ConfIAAuthUser;
    if (!user || !["SCHOOL_MANAGER", "NETWORK_MANAGER"].includes(user.role)) return;
    const token = ++sequence;
    get("management-message").textContent = "Carregando indicadores…";
    get("management-table").replaceChildren();
    try {
      let overview, rows;
      if (currentClassroom) {
        overview = await read(`/management/classrooms/${encodeURIComponent(currentClassroom)}/overview`);
        if (token !== sequence) return;
        get("management-heading").textContent = `${overview.school.name} · ${overview.classroom.name}`;
      } else if (currentSchool || user.role === "SCHOOL_MANAGER") {
        if (!currentSchool) {
          const schools = await read("/management/schools");
          if (token !== sequence) return;
          currentSchool = schools[0]?.school.school_id || null;
        }
        if (!currentSchool) throw new Error("Escola de gestão não vinculada.");
        [overview, rows] = await Promise.all([
          read(`/management/schools/${encodeURIComponent(currentSchool)}/overview`),
          read(`/management/schools/${encodeURIComponent(currentSchool)}/classrooms`),
        ]);
        if (token !== sequence) return;
        get("management-heading").textContent = overview.school.name;
        renderRows(["Turma", "Alunos", "Submissões", "Auditorias"], rows, item => {
          const row = node("tr"), first = node("td");
          first.appendChild(button(item.classroom.name, () => { currentClassroom = item.classroom.classroom_id; load(); }));
          row.appendChild(first); cell(row, item.metrics.number_of_students);
          cell(row, item.metrics.submissions_count); cell(row, item.metrics.audit_runs_count);
          return row;
        });
      } else {
        [overview, rows] = await Promise.all([read("/management/network/overview"), read("/management/schools")]);
        if (token !== sequence) return;
        get("management-heading").textContent = "Visão geral da rede";
        renderRows(["Escola", "Município", "Turmas", "Alunos", "Submissões", "Auditorias", "Uso"], rows, item => {
          const row = node("tr"), first = node("td");
          first.appendChild(button(item.school.name, () => { currentSchool = item.school.school_id; load(); }));
          row.appendChild(first); cell(row, item.school.municipality);
          cell(row, item.metrics.number_of_classrooms); cell(row, item.metrics.number_of_students);
          cell(row, item.metrics.submissions_count); cell(row, item.metrics.audit_runs_count);
          cell(row, usage(item.metrics)); return row;
        });
      }
      renderCards(overview.metrics); crumbs();
      get("management-message").textContent = `Ano letivo ${overview.academic_year} · dados agregados persistidos. O score sugerido pelo ConfIA não é nota oficial.`;
    } catch (_error) {
      if (token === sequence) get("management-message").textContent = "Não foi possível carregar os indicadores institucionais.";
    }
  }
  window.ConfIAManagement = { load };
})();
