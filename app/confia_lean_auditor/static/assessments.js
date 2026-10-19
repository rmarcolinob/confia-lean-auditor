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
  let progressSequence = 0;
  let selectedCard = null;
  let selectedButton = null;
  const text = (tag, content, className = "") => {
    const element = document.createElement(tag);
    element.textContent = content;
    if (className) element.className = className;
    return element;
  };
  const date = value => new Date(value).toLocaleString("pt-BR");
  const availability = view => ({ RASCUNHO: "Rascunho", AGENDADO: "Agendada", DISPONÍVEL: "Disponível", ENCERRADO: "Encerrada" })[view.availability] || "Indisponível";
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
        const card = text("article", "", "local-submission exam-card");
        const heading = text("h4", "");
        const select = button(exam.title, () => showProgress(view, card, select));
        select.className = "exam-select";
        select.setAttribute("aria-expanded", "false");
        select.setAttribute("aria-controls", "teacher-exam-progress");
        heading.appendChild(select);
        card.appendChild(heading);
        card.appendChild(text("p", `${view.classroom_name} · ${date(exam.opens_at)} até ${date(exam.closes_at)}`, "exam-preview"));
        card.appendChild(text("p", `${view.items.length} questões · ${view.items.reduce((sum, item) => sum + item.points, 0).toLocaleString("pt-BR")} pontos`, "exam-preview"));
        const state = text("span", availability(view), "status exam-preview");
        state.dataset.kind = view.availability === "DISPONÍVEL" ? "info" : "neutral";
        card.appendChild(state);
        if (status === "DRAFT") {
          const actions = text("div", "", "action-row");
          const editButton = button("Editar rascunho", () => edit(view)); editButton.className = "secondary-action";
          actions.appendChild(editButton); actions.appendChild(button("Publicar", () => publish(exam.assessment_id)));
          card.appendChild(actions);
        }
        list.appendChild(card);
      }
    }
    if (!assessments.length) list.appendChild(text("p", "Nenhum exame criado para esta turma.", "empty-state"));
  }
  async function load() {
    const current = ++sequence;
    ++progressSequence;
    selectedCard = null;
    selectedButton = null;
    assessments = [];
    const { schoolId, classroomId } = context();
    list.replaceChildren(); progress.hidden = true; progress.replaceChildren();
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
  function renderSummary(view) {
    const exam = view.assessment;
    const summary = text("dl", "", "exam-summary");
    for (const [label, value] of [
      ["Turma", view.classroom_name],
      ["Período", `${date(exam.opens_at)} até ${date(exam.closes_at)}`],
      ["Questões", view.items.length],
      ["Total de pontos", view.items.reduce((sum, item) => sum + item.points, 0).toLocaleString("pt-BR")],
      ["Status", availability(view)],
    ]) {
      const entry = text("div", "");
      entry.appendChild(text("dt", label));
      entry.appendChild(text("dd", value));
      summary.appendChild(entry);
    }
    progress.replaceChildren(text("h3", exam.title), summary, text("h4", "Entregas dos alunos"));
  }
  function deliveryLabel(status) {
    if (status === "DECISION_FINALIZED" || status === "RESULT_RELEASED") return "Corrigida";
    if (["TRANSCRIPTION_REVIEW", "ANALYSIS_AVAILABLE", "DECISION_DRAFT"].includes(status)) return "Em correção";
    return "Enviada";
  }
  // Keep row composition separate so a future paginated response can reuse the same table.
  function renderStudentRow(student, items, view) {
    const row = text("tr", "");
    const name = row.appendChild(text("th", student.display_name));
    name.setAttribute("scope", "row");
    let submitted = 0;
    for (const item of items) {
      const cell = text("td", "");
      const submissionId = student.submissions[item.assessment_item_id];
      if (submissionId) {
        submitted++;
        const status = student.correction_statuses?.[item.assessment_item_id];
        const label = deliveryLabel(status);
        const action = button(label, () => {
          if (window.ConfIAShell?.navigate("teacher", "submissions") === false) return;
          return window.ConfIATeacher?.openSubmission(submissionId, {
            submissionId, assessmentId: view.assessment.assessment_id, assessmentTitle: view.assessment.title,
            assessmentItemId: item.assessment_item_id, problemId: item.problem_id, questionOrder: item.order,
            studentId: student.user_id, studentName: student.display_name,
            classroomName: view.classroom_name, ...(context().schoolName ? { schoolName: context().schoolName } : {}),
          });
        });
        action.className = "exam-delivery-link status";
        action.dataset.kind = label === "Corrigida" ? "success" : label === "Em correção" ? "pending" : "info";
        action.setAttribute("aria-label", `${label} · ${student.display_name} · Q${item.order}`);
        action.title = window.ConfIADecisions?.labels[status] || label;
        cell.appendChild(action);
      } else cell.appendChild(text("span", "Não enviada", "status")).dataset.kind = "neutral";
      row.appendChild(cell);
    }
    row.appendChild(text("td", `${submitted}/${items.length}`, "exam-student-progress"));
    return row;
  }
  function renderDeliveries(data, view) {
    const items = [...data.items].sort((a, b) => a.order - b.order);
    const scroll = text("div", "", "exam-deliveries-scroll");
    scroll.tabIndex = 0;
    scroll.setAttribute("role", "region");
    scroll.setAttribute("aria-label", `Entregas dos alunos · ${view.assessment.title}`);
    const table = text("table", "");
    table.appendChild(text("caption", `${data.students.length} aluno(s) · Progresso: questões enviadas / total`));
    const thead = table.appendChild(text("thead", ""));
    const head = thead.appendChild(text("tr", ""));
    for (const label of ["Aluno", ...items.map(item => `Q${item.order}`), "Progresso"]) {
      head.appendChild(text("th", label)).setAttribute("scope", "col");
    }
    const tbody = table.appendChild(text("tbody", ""));
    const students = [...data.students].sort((a, b) => a.display_name.localeCompare(b.display_name, "pt-BR"));
    for (const student of students) tbody.appendChild(renderStudentRow(student, items, view));
    scroll.appendChild(table);
    progress.appendChild(scroll);
    if (!data.students.length) progress.appendChild(text("p", "Nenhum aluno matriculado nesta turma.", "empty-state"));
    else if (!data.students.some(student => items.some(item => student.submissions[item.assessment_item_id]))) {
      progress.appendChild(text("p", "Nenhuma solução enviada para esta avaliação.", "empty-state"));
    }
  }
  async function showProgress(view, card, select) {
    const current = ++progressSequence;
    const scope = context();
    const stillSelected = () => current === progressSequence
      && scope.schoolId === context().schoolId && scope.classroomId === context().classroomId;
    if (selectedCard) selectedCard.dataset.selected = "false";
    selectedButton?.setAttribute("aria-expanded", "false");
    selectedCard = card;
    selectedButton = select;
    card.dataset.selected = "true";
    select.setAttribute("aria-expanded", "true");
    card.appendChild(progress);
    progress.hidden = false;
    progress.setAttribute("aria-busy", "true");
    renderSummary(view);
    // Collapsing a preceding exam can move the selected heading above the viewport.
    // Bring that heading back into view, never the bottom of the deliveries table.
    const revealSelection = () => {
      const bounds = select.getBoundingClientRect();
      if (bounds.top < 0 || bounds.bottom > window.innerHeight / 3) card.scrollIntoView({ block: "start", behavior: "instant" });
    };
    revealSelection();
    if (view.assessment.status === "DRAFT") {
      progress.appendChild(text("p", "Publique o exame para acompanhar entregas."));
      progress.setAttribute("aria-busy", "false");
      return;
    }
    const loading = text("p", "Carregando entregas…");
    loading.setAttribute("role", "status");
    progress.appendChild(loading);
    try {
      const data = await request(`/assessments/${view.assessment.assessment_id}/progress`);
      if (!stillSelected()) return;
      if (data.assessment.assessment_id !== view.assessment.assessment_id) throw new Error("Exame divergente.");
      progress.removeChild(loading);
      renderDeliveries(data, view);
      revealSelection();
    } catch (_) {
      if (stillSelected()) {
        renderSummary(view);
        const error = text("p", "Não foi possível carregar as entregas. Selecione a avaliação para tentar novamente.", "alert");
        error.dataset.kind = "error"; error.setAttribute("role", "status"); progress.appendChild(error);
      }
    } finally { if (stillSelected()) progress.setAttribute("aria-busy", "false"); }
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
