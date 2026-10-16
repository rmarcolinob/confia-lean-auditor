/* Teacher Assessment UI; authority stays with the institutional API. */
(function teacherAssessments() {
  "use strict";
  const get = id => document.getElementById(id);
  const list = get("teacher-exam-list");
  const progress = get("teacher-exam-progress");
  const message = get("teacher-exams-message");
  const form = get("teacher-exam-form");
  let catalog = [];
  let assessments = [];
  let editing = null;
  let sequence = 0;
  const text = (tag, content, className = "") => {
    const element = document.createElement(tag);
    element.textContent = content;
    if (className) element.className = className;
    return element;
  };
  const date = value => new Date(value).toLocaleString("pt-BR");
  async function request(url, options = {}) {
    const response = await fetch(url, { credentials: "same-origin", cache: "no-store", ...options });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  function button(label, action) {
    const element = text("button", label, "button button-primary");
    element.type = "button";
    element.addEventListener("click", action);
    return element;
  }
  function context() { return window.ConfIATeacher?.context() || { schoolId: "", classroomId: "" }; }
  function render() {
    list.replaceChildren();
    for (const [status, heading] of [["DRAFT", "Rascunhos"], ["PUBLISHED", "Publicados"], ["CLOSED", "Encerrados"]]) {
      const entries = assessments.filter(view => status === "CLOSED"
        ? view.availability === "ENCERRADO"
        : view.assessment.status === status && view.availability !== "ENCERRADO");
      if (!entries.length) continue;
      list.appendChild(text("h3", heading));
      for (const view of entries) {
        const exam = view.assessment;
        const card = text("article", "", "local-submission");
        card.appendChild(text("h4", exam.title));
        card.appendChild(text("p", `${view.classroom_name} · ${date(exam.opens_at)} até ${date(exam.closes_at)}`));
        card.appendChild(text("p", `${view.items.length} questões · ${view.items.reduce((sum, item) => sum + item.points, 0)} pontos · ${view.availability}`));
        card.appendChild(button("Abrir exame", () => showProgress(view)));
        if (status === "DRAFT") {
          card.appendChild(button("Editar rascunho", () => edit(view)));
          card.appendChild(button("Publicar", () => publish(exam.assessment_id)));
        }
        list.appendChild(card);
      }
    }
    if (!assessments.length) list.appendChild(text("p", "Nenhum exame criado para esta turma.", "empty-state"));
  }
  async function load() {
    const current = ++sequence;
    const { schoolId, classroomId } = context();
    list.replaceChildren(); progress.hidden = true;
    get("teacher-create-exam").disabled = !schoolId || !classroomId;
    if (!schoolId || !classroomId) { message.textContent = "Selecione uma escola e uma turma."; return; }
    message.textContent = "Carregando exames…";
    try {
      const data = await request(`/assessments?school_id=${encodeURIComponent(schoolId)}&classroom_id=${encodeURIComponent(classroomId)}`);
      if (current !== sequence) return;
      assessments = data;
      message.textContent = `${data.length} exame(s) da turma.`;
      render();
    } catch (_) { if (current === sequence) message.textContent = "Não foi possível carregar os exames da turma."; }
  }
  async function showProgress(view) {
    progress.hidden = false;
    progress.replaceChildren(text("h3", view.assessment.title));
    if (view.assessment.status === "DRAFT") {
      progress.appendChild(text("p", "Publique o exame para acompanhar entregas."));
      return;
    }
    try {
      const data = await request(`/assessments/${view.assessment.assessment_id}/progress`);
      const table = document.createElement("table");
      const head = document.createElement("tr");
      head.appendChild(text("th", "Aluno"));
      for (const item of data.items) head.appendChild(text("th", `${item.order}. ${item.problem_id}`));
      table.appendChild(head);
      for (const student of data.students) {
        const row = document.createElement("tr");
        row.appendChild(text("th", student.display_name));
        for (const item of data.items) {
          const cell = document.createElement("td");
          const submissionId = student.submissions[item.assessment_item_id];
          if (submissionId) cell.appendChild(button("Enviado", () => {
            window.ConfIAShell?.navigate("teacher", "submissions");
            window.ConfIATeacher?.openSubmission(submissionId);
          }));
          else cell.textContent = "Pendente";
          row.appendChild(cell);
        }
        table.appendChild(row);
      }
      progress.appendChild(table);
    } catch (_) { progress.appendChild(text("p", "Não foi possível carregar o progresso.")); }
  }
  async function publish(id) {
    try {
      await request(`/assessments/${id}/publish`, { method: "POST" });
      await load();
    } catch (_) { message.textContent = "Não foi possível publicar. Confira questões, vínculo docente e período."; }
  }
  async function loadCatalog() {
    if (catalog.length) return;
    catalog = await request("/problems");
    const holder = get("teacher-exam-catalog");
    holder.replaceChildren();
    for (const problem of catalog) {
      const id = problem.problem_id || problem.id;
      const label = document.createElement("label");
      const checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.value = id;
      const points = document.createElement("input"); points.type = "number"; points.min = "0.01"; points.max = "1000"; points.step = "0.01"; points.value = "5";
      points.setAttribute("aria-label", `Pontos de ${id}`);
      label.append(checkbox, text("span", `${id} · ${problem.title || "Questão"}`), points);
      holder.appendChild(label);
    }
  }
  async function edit(view) {
    try { await loadCatalog(); } catch (_) { message.textContent = "Não foi possível carregar o catálogo de questões."; return; }
    editing = view;
    form.hidden = false;
    get("teacher-exam-title").value = view.assessment.title;
    get("teacher-exam-instructions").value = view.assessment.instructions;
    const local = value => { const date = new Date(value); return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16); };
    get("teacher-exam-opens").value = local(view.assessment.opens_at);
    get("teacher-exam-closes").value = local(view.assessment.closes_at);
    for (const label of get("teacher-exam-catalog").querySelectorAll("label")) {
      const checkbox = label.querySelector('input[type="checkbox"]');
      const item = view.items.find(item => item.problem_id === checkbox.value);
      checkbox.checked = Boolean(item);
      label.querySelector('input[type="number"]').value = item ? String(item.points) : "5";
    }
  }
  get("teacher-create-exam").addEventListener("click", async () => {
    editing = null;
    form.reset();
    form.hidden = false;
    try { await loadCatalog(); } catch (_) { message.textContent = "Não foi possível carregar o catálogo de questões."; }
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const { schoolId, classroomId } = context();
    const chosen = [...get("teacher-exam-catalog").querySelectorAll("label")].filter(label => label.querySelector('input[type="checkbox"]').checked);
    if (!chosen.length) { message.textContent = "Selecione ao menos uma questão."; return; }
    const body = { title: get("teacher-exam-title").value.trim(), instructions: get("teacher-exam-instructions").value,
      school_id: schoolId, classroom_id: classroomId,
      opens_at: new Date(get("teacher-exam-opens").value).toISOString(),
      closes_at: new Date(get("teacher-exam-closes").value).toISOString() };
    try {
      const id = editing?.assessment.assessment_id;
      const base = id ? `/assessments/${id}` : "/assessments";
      const created = await request(base, { method: id ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(id
          ? { title: body.title, instructions: body.instructions, opens_at: body.opens_at, closes_at: body.closes_at }
          : body) });
      const examId = created.assessment.assessment_id;
      const selected = new Map(chosen.map(label => [label.querySelector('input[type="checkbox"]').value,
        Number(label.querySelector('input[type="number"]').value)]));
      if (editing) for (const item of editing.items) {
        const target = `/assessments/${examId}/items/${item.assessment_item_id}`;
        if (!selected.has(item.problem_id)) await request(target, { method: "DELETE" });
        else if (selected.get(item.problem_id) !== item.points) await request(target, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ points: selected.get(item.problem_id) }),
        });
      }
      for (const [problemId, points] of selected) {
        if (editing?.items.some(item => item.problem_id === problemId)) continue;
        await request(`/assessments/${examId}/items`, { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ problem_id: problemId, points }) });
      }
      form.hidden = true; form.reset();
      editing = null;
      await load();
      message.textContent = "Rascunho salvo. Confira e publique o exame.";
    } catch (_) { message.textContent = "Não foi possível criar o exame. Confira dados e vínculo docente."; }
  });
  get("teacher-school-select").addEventListener("change", () => setTimeout(load, 0));
  get("teacher-classroom-select").addEventListener("change", () => setTimeout(load, 0));
  window.ConfIAAssessments = { load };
})();
