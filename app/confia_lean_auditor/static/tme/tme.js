(function () {
  "use strict";
  const root = document.querySelector("#app");
  const state = { cases: [], current: null, history: null, audit: null, photos: [], message: "",
    feedback: null, busy: false, adjusting: false, cache: new Map(), view: "home", homePeriod: "today", generation: 0, filters: { cases: {}, results: {} } };
  const Home = window.ConfiaTmeHome;
  function navigate(view) {
    if (state.busy) return;
    window.scrollTo(0, 0); document.querySelector("#main")?.scrollTo?.(0, 0);
    return Promise.resolve(view === "home" ? home() : view === "new" ? newCase() : view === "results" ? results() : cases()).catch(showError);
  }
  async function home() {
    state.view = "home";
    const generation = ++state.generation;
    let summary;
    const render = status => {
      if (generation !== state.generation) return;
      show(Home.TmeHome({ summary, state: status, period: state.homePeriod,
        changePeriod: async value => { state.homePeriod = value; await home(); document.querySelector(".home-overview select")?.focus(); }, navigate,
        open: id => openCase(id).catch(showError), retry: home }));
    };
    render("loading");
    try { summary = await api(`/tme/home-summary?period=${encodeURIComponent(state.homePeriod)}`); render("success"); } catch (_) { summary = undefined; render("error"); }
  }
  const Scan = window.ConfiaTMEScan;
  const maxPages = Scan.maxPages;
  const node = (tag, value, className) => {
    const item = document.createElement(tag);
    if (value !== undefined) item.textContent = value;
    if (className) item.className = className;
    return item;
  };
  const btn = (label, action, cls = "") => {
    const item = node("button", label, cls); item.type = "button"; item.addEventListener("click", action); return item;
  };
  const card = (title) => { const item = node("section", undefined, "card"); if (title) item.appendChild(node("h2", title)); return item; };
  const actions = (...children) => { const item = node("div", undefined, "actions"); item.append(...children); return item; };
  const field = (title, control) => { const label = node("label", title); label.appendChild(control); return label; };
  const show = (...children) => { root.dataset.view = state.view; if (document.body) document.body.dataset.view = state.view; root.replaceChildren(...children); renderRecentCases(); };
  const note = (message, error = false) => { const p = node("p", message, `message${error ? " error" : ""}`); p.setAttribute("role", "status"); p.setAttribute("aria-live", "polite"); return p; };
  async function api(path, options = {}) {
    const response = await fetch(path, { cache: "no-store", credentials: "same-origin", ...options,
      headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) } });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(response.status === 401 ? "A sessão não está disponível. Acesse novamente para continuar." : "Não foi possível concluir esta etapa. Tente novamente.");
      error.code = data?.error_code; throw error;
    }
    return data;
  }
  const post = (path, value) => api(path, { method: "POST", body: JSON.stringify(value) });
  const problemLabel = p => `${p.problem_id || p.id} · ${p.title || p.name || "Questão"}`;
  async function refreshCases() {
    if (!state.caseRequest) state.caseRequest = api("/tme/cases").finally(() => { state.caseRequest = null; });
    state.cases = await state.caseRequest;
  }
  const local = c => {
    if (!state.cache.has(c.case_id)) state.cache.set(c.case_id, { page: 0, zoom: 1, rotation: 0, tab: "original", draft: {}, editors: {}, audits: null, history: null, decision: undefined, detail: null, feedback: null });
    return state.cache.get(c.case_id);
  };
  const questionNumber = c => c.problem_id.match(/Q(\d+)$/)?.[1];
  function renderRecentCases() {
    const recent = document.querySelector("#recent-cases"); if (!recent) return;
    recent.replaceChildren();
    const entries = state.current ? [state.current, ...state.cases.filter(c => c.case_id !== state.current.case_id)] : state.cases;
    for (const c of entries.slice(0, 8)) {
      const item = btn("", () => { if (!state.busy) openCase(c.case_id).catch(showError); }, "recent-case");
      item.title = `${c.external_candidate_ref} · ${c.problem_id} · ${caseStatus(c)}`;
      item.setAttribute("aria-label", `Abrir ${item.title}`);
      item.setAttribute("aria-current", state.view === "workspace" && state.current?.case_id === c.case_id ? "page" : "false");
      const indicator = node("span", "", "case-dot"); indicator.dataset.status = caseStatus(c); indicator.setAttribute("aria-hidden", "true");
      item.append(indicator, node("span", c.external_candidate_ref, "recent-code"), node("span", questionNumber(c) ? `Q${questionNumber(c)}` : c.problem_id, "recent-question")); recent.appendChild(item);
    }
    for (const link of document.querySelectorAll("nav [data-view]")) link.setAttribute("aria-current", link.dataset.view === state.view ? "page" : "false");
  }
  const origin = c => c.source_mode === "IMAGE_SCAN" ? "Foto / scan" : "Escrita digital";
  const runFor = c => {
    const saved = local(c);
    if (saved.decision?.audit_run_id) return saved.audits?.find(r => r.audit_run_id === saved.decision.audit_run_id);
    return saved.audits?.find(r => !r.stale && r.status === "COMPLETED") || saved.audits?.[0];
  };
  function caseStatus(c) {
    const saved = local(c), run = runFor(c);
    if (saved.decision || c.status === "DECIDED") return "Finalizada";
    if (saved.processing === "audit") return "Analisando";
    if (saved.processing === "recognition") return "Reconhecendo";
    if (run?.status === "FAILED" || saved.feedback?.state === "FAILED") return "Falha técnica";
    if (run?.stale) return "Aguardando análise";
    if (run?.result) return run.result.score == null ? "Inconclusiva" : "Aguardando decisão";
    return saved.history ? "Aguardando análise" : "Aguardando reconhecimento";
  }
  async function loadCaseData(c, force = false) {
    const saved = local(c), base = `/tme/cases/${c.case_id}`;
    if (!c.submission_id) return saved;
    if (force || !saved.loaded) {
      const [summaries, audits, decision, detail, feedback] = await Promise.all([
        api(`${base}/transcriptions`), api(`${base}/audits`), api(`${base}/decision`),
        saved.detail ? Promise.resolve(saved.detail) : api(`${base}/submission`), api(`${base}/recognition-status`),
      ]);
      saved.history = summaries.length ? await api(`${base}/transcriptions/${summaries[0].transcription.transcription_id}`) : null;
      Object.assign(saved, { audits, decision, detail, feedback, loaded: true, loadError: false });
    }
    return saved;
  }
  async function cases(resultsOnly = false) {
    state.view = resultsOnly ? "results" : "cases";
    const generation = ++state.generation;
    show(loading("Carregando correções…"));
    await refreshCases();
    // Bounded reads; the queue reuses case data already loaded in this session.
    for (let i = 0; i < state.cases.length; i += 4) await Promise.all(state.cases.slice(i, i + 4).map(c => loadCaseData(c).catch(() => { local(c).loadError = true; })));
    if (generation !== state.generation) return;
    const box = card(resultsOnly ? "Resultados" : "Correções"); box.classList.add("queue");
    const search = node("input"); search.type = "search"; search.placeholder = "Buscar código da prova";
    const select = (label, values) => { const el = node("select"); for (const value of ["", ...values]) { const option = node("option", value || "Todos"); option.value = value; el.appendChild(option); } return [field(label, el), el]; };
    const [questionField, question] = select("Questão", [...new Set(state.cases.map(c => c.problem_id))]);
    const [statusField, status] = select("Status", [...new Set(state.cases.map(caseStatus))]);
    const [originField, source] = select("Origem", ["Foto / scan", "Escrita digital"]);
    const remembered = state.filters[state.view];
    search.value = remembered.search || "";
    for (const [key, control] of [["question", question], ["status", status], ["source", source]]) {
      if (remembered[key] && !Array.from(control.children).some(option => option.value === remembered[key])) { const option = node("option", remembered[key]); option.value = remembered[key]; control.appendChild(option); }
      control.value = remembered[key] || "";
    }
    const filters = node("div", undefined, "queue-filters"); filters.append(field("Código da prova", search), questionField, statusField, originField);
    const mobileQueue = node("div", undefined, "mobile-queue");
    const tableWrap = node("div", undefined, "queue-scroll"), table = node("table"), head = node("thead"), heading = node("tr"), body = node("tbody");
    table.appendChild(node("caption", "Fila de correções do avaliador"));
    for (const title of ["Código", "Questão", "Origem", "Status", "Sugestão", "Atualização"]) { const th = node("th", title); th.setAttribute("scope", "col"); heading.appendChild(th); }
    head.appendChild(heading); table.append(head, body); tableWrap.appendChild(table);
    const count = note("");
    const update = () => {
      Object.assign(remembered, { search: search.value, question: question.value, status: status.value, source: source.value });
      body.replaceChildren(); mobileQueue.replaceChildren();
      const selected = state.cases.filter(c => (!resultsOnly || caseStatus(c) === "Finalizada") && (!question.value || c.problem_id === question.value) && (!status.value || caseStatus(c) === status.value) && (!source.value || origin(c) === source.value) && c.external_candidate_ref.toLowerCase().includes(search.value.toLowerCase()));
      count.textContent = `${selected.length} ${selected.length === 1 ? "correção" : "correções"}`;
      for (const c of selected) {
        const saved = local(c), run = runFor(c), row = node("tr"), first = node("td");
        const open = btn(c.external_candidate_ref, () => openCase(c.case_id).catch(showError), "secondary"); open.setAttribute("aria-label", `Abrir correção ${c.external_candidate_ref}`); first.appendChild(open); row.appendChild(first);
        const date = saved.decision?.decided_at || run?.created_at || saved.history?.revisions.at(-1)?.created_at || c.created_at;
        for (const value of [c.problem_id, origin(c), saved.loadError ? "Dados indisponíveis" : caseStatus(c), run?.result?.score == null ? "Não determinada" : `${run.result.score} / ${run.result.max_score}`, date ? new Date(date).toLocaleString("pt-BR") : "—"]) row.appendChild(node("td", value));
        body.appendChild(row);
        const mobileRow = Home.PriorityCaseRow(c, id => openCase(id).catch(showError));
        const statusPill = Array.from(mobileRow.children).find(n => n.className === "home-status");
        statusPill.textContent = caseStatus(c); statusPill.dataset.status = caseStatus(c);
        mobileRow.setAttribute("aria-label", `Abrir correção ${c.external_candidate_ref} · ${c.problem_id} · ${caseStatus(c)}`);
        mobileQueue.appendChild(mobileRow);
      }
    };
    for (const control of [search, question, status, source]) control.addEventListener(control === search ? "input" : "change", update);
    box.append(actions(btn("Atualizar fila", () => { for (const cached of state.cache.values()) cached.loaded = false; cases(resultsOnly).catch(showError); }, "secondary")), filters, count, tableWrap, mobileQueue); update(); show(box);
  }
  const results = () => cases(true);
  const showError = () => show(note("Não foi possível carregar esta etapa. Tente novamente.", true), actions(btn("Correções", () => cases().catch(showError))));
  async function newCase() {
    state.view = "new"; ++state.generation;
    const box = card("Nova correção"); const form = node("form");
    const select = node("select"); select.required = true;
    const placeholder = node("option", "Selecione uma questão"); placeholder.value = ""; select.appendChild(placeholder);
    try { for (const p of await api("/tme/problems")) { const option = node("option", problemLabel(p)); option.value = p.problem_id || p.id; select.appendChild(option); } }
    catch (error) { box.appendChild(note(error.message, true)); }
    const code = node("input"); code.required = true; code.maxLength = 80; code.pattern = "[A-Za-z0-9._:/-]+"; code.autocomplete = "off"; code.placeholder = "Ex.: PROVA-2026-0001";
    form.append(field("Questão", select), field("Código da prova / participante", code), node("p", "Use um código pseudônimo; não informe o nome do participante.", "muted"));
    form.appendChild(node("h2", "Como deseja inserir a solução?"));
    const choices = node("div", undefined, "choice-row"); let mode = null;
    for (const [name, value] of [["Fotografar solução", "IMAGE_SCAN"], ["Escrever no tablet", "DIGITAL_INK"]]) {
      const choice = btn(name, () => { mode = value; for (const item of choices.children) item.classList.toggle("selected", item === choice); }, "choice"); choices.appendChild(choice);
    }
    form.append(choices, actions(btn("Continuar", async () => {
      if (!form.reportValidity()) return;
      if (!mode) { error.textContent = "Escolha uma forma de entrada."; return; }
      try { const c = await post("/tme/cases", { problem_id: select.value, external_candidate_ref: code.value.trim(), source_mode: mode }); await openCase(c.case_id); }
      catch (e) { error.textContent = e.message; }
    }))); const error = node("p", "", "field-error"); form.appendChild(error); box.appendChild(form); show(box);
  }
  function steps(active) {
    const list = node("ol", undefined, "steps"); list.setAttribute("aria-label", "Progresso da correção");
    ["Entrada", "Transcrição", "Análise", "Decisão"].forEach((label, i) => {
      const item = node("li", label, i === active ? "active" : ""); if (i === active) item.setAttribute("aria-current", "step"); list.appendChild(item);
    }); return list;
  }
  function context(c, active) {
    const header = node("header", undefined, "case-context");
    const status = node("span", caseStatus(c), "status");
    status.dataset.kind = caseStatus(c) === "Finalizada" ? "success" : ["Inconclusiva", "Falha técnica"].includes(caseStatus(c)) ? "pending" : "info";
    header.append(node("h1", `Prova ${c.external_candidate_ref} · ${questionNumber(c) ? `Questão ${questionNumber(c)}` : c.problem_id} · ${origin(c)}`), status, steps(active)); return header;
  }
  async function openCase(caseId) {
    state.view = "workspace"; const generation = ++state.generation;
    const c = await api(`/tme/cases/${caseId}`);
    if (generation !== state.generation) return;
    if (state.current?.case_id !== caseId) { for (const photo of state.photos) URL.revokeObjectURL(photo.url); state.photos = []; }
    state.current = c; state.message = ""; state.adjusting = false; state.feedback = local(c).feedback;
    if (!c.submission_id) return c.source_mode === "IMAGE_SCAN" ? renderScan() : renderInk();
    await loadCaseData(c); if (generation === state.generation) await renderCorrection();
  }
  function renderInk() {
    const c = state.current, box = card("Escrever no tablet");
    box.append(node("p", `${c.external_candidate_ref} · ${c.problem_id}`, "muted"));
    const frame = node("iframe", undefined, "frame"); frame.title = "Caderno de escrita digital ConfIA";
    frame.src = `/tme/cases/${c.case_id}/capture?embedded=1&tme_case_id=${encodeURIComponent(c.case_id)}&problem_id=${encodeURIComponent(c.problem_id)}&submission_target=${encodeURIComponent(`/tme/cases/${c.case_id}/digital-submission`)}`;
    frame.addEventListener("load", () => { state.captureWindow = frame.contentWindow; });
    box.append(frame, actions(btn("Atualizar correção", () => openCase(c.case_id), "secondary"))); show(context(c, 0), box);
  }
  function imageInput(capture, onFile) {
    const input = node("input"); input.type = "file"; input.accept = "image/*"; if (capture) input.setAttribute("capture", "environment");
    input.className = "sr-only"; input.addEventListener("change", () => { if (input.files?.[0]) onFile(input.files[0]); input.value = ""; });
    return input;
  }
  function acceptFile(file, index = null) {
    let photo;
    try { Scan.validate(file); photo = Scan.photo(file, URL.createObjectURL(file), new Date().toISOString());
      if (index === null) Scan.add(state.photos, photo);
      else URL.revokeObjectURL(Scan.replace(state.photos, index, photo).url);
    } catch (e) {
      if (photo) URL.revokeObjectURL(photo.url);
      state.message = e.message; return renderScan();
    }
    state.message = "Confira a página e selecione Usar esta página."; renderScan();
  }
  function renderScan() {
    const c = state.current, box = card("Fotografar solução"); box.append(node("p", `${c.external_candidate_ref} · ${c.problem_id}`),
      node("p", "Fotografe a folha inteira, evite sombras, mantenha a câmera paralela ao papel e confira se a escrita está legível.", "muted"));
    box.appendChild(scanStatus("WAITING"));
    if (state.adjusting) box.appendChild(note("Ao continuar, será criada uma nova correção com as páginas ajustadas. Esta versão e seus originais ficam preservados."));
    const camera = imageInput(true, f => acceptFile(f)); const existing = imageInput(false, f => acceptFile(f));
    const cameraButton = btn("Fotografar página", () => camera.click());
    const existingButton = btn("Selecionar imagem", () => existing.click(), "secondary");
    cameraButton.disabled = existingButton.disabled = state.photos.length >= maxPages;
    box.append(camera, existing, actions(cameraButton, existingButton));
    if (state.photos.length) {
      const grid = node("div", undefined, "scan-grid");
      state.photos.forEach((photo, i) => {
        const item = node("div", undefined, "photo"); item.append(node("h2", `Página ${i + 1}`));
        const img = node("img"); img.src = photo.url; img.alt = `Prévia da página ${i + 1}`; img.style.transform = `rotate(${photo.rotation}deg)`; item.appendChild(img);
        const replace = imageInput(true, f => acceptFile(f, i)); item.appendChild(replace);
        item.append(actions(btn("Repetir foto", () => replace.click(), "secondary"),
          btn("Girar 90°", () => { Scan.rotate(photo); renderScan(); }, "secondary"),
          btn("Usar esta página", () => { Scan.confirm(photo); renderScan(); }),
          btn("Remover", () => { URL.revokeObjectURL(Scan.remove(state.photos, i).url); renderScan(); }, "danger"),
          btn("Mover para cima", () => movePhoto(i, -1), "secondary"), btn("Mover para baixo", () => movePhoto(i, 1), "secondary")));
        item.appendChild(node("p", photo.confirmed ? "Página confirmada" : "Aguardando conferência", "muted")); grid.appendChild(item);
      }); box.appendChild(grid);
    }
    if (state.photos.length < maxPages) box.appendChild(actions(btn("Adicionar página", () => camera.click(), "secondary")));
    const continueButton = btn("Continuar", uploadScan); continueButton.disabled = !Scan.ready(state.photos);
    box.append(actions(continueButton));
    if (state.adjusting) box.appendChild(actions(btn("Voltar à versão preservada", () => openCase(c.case_id), "secondary")));
    if (state.message) box.appendChild(note(state.message, /erro|não|inválid|indisponível/i.test(state.message)));
    if (state.busy) for (const control of box.querySelectorAll("button,input")) control.disabled = true;
    show(context(c, 0), box);
  }
  function movePhoto(index, direction) { Scan.move(state.photos, index, direction); renderScan(); }
  async function fileBase64(file) {
    return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.onerror = () => reject(new Error("Não foi possível ler a foto.")); reader.readAsDataURL(file); });
  }
  const derive = photo => Scan.derive(photo, (...args) => createImageBitmap(...args), () => document.createElement("canvas"));
  async function uploadScan() {
    let c = state.current;
    if (state.busy || !Scan.ready(state.photos)) return;
    state.busy = true;
    state.message = "Preservando originais e preparando reconhecimento…"; renderScan();
    try {
      const pages = await Promise.all(state.photos.map(async p => ({ original_base64: await fileBase64(p.file),
        original_mime: p.file.type, captured_at: p.capturedAt, rotation_degrees: p.rotation, ...await derive(p) })));
      if (state.adjusting) {
        c = await post("/tme/cases", { problem_id: c.problem_id,
          external_candidate_ref: c.external_candidate_ref, source_mode: "IMAGE_SCAN" });
        state.current = c; state.adjusting = false;
      }
      await post(`/tme/cases/${c.case_id}/scan`, { pages });
      state.current = await api(`/tme/cases/${c.case_id}`);
      state.message = "Páginas preservadas."; state.busy = false;
      await recognize();
    } catch (e) {
      state.busy = false; state.message = e.message;
      // A lost upload response may still have bound the immutable source.
      state.current = await api(`/tme/cases/${c.case_id}`).catch(() => c);
      if (state.current.submission_id && !state.adjusting) await renderCorrection(); else renderScan();
    }
  }
  function scanStatus(value) {
    const labels = { WAITING: "Aguardando reconhecimento", RECOGNIZING: "Reconhecendo", RECOGNIZED: "Reconhecida", FAILED: "Falha de reconhecimento" };
    const status = node("p", labels[value] || labels.WAITING, "status status-pill");
    status.dataset.kind = value === "FAILED" ? "error" : value === "RECOGNIZED" ? "success" : "pending";
    status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite"); return status;
  }
  async function adjustPages() {
    if (state.busy) return;
    const c = state.current, restored = [];
    try {
      const manifest = await api(`/tme/cases/${c.case_id}/scan-manifest`);
      for (const page of [...manifest.pages].sort((a, b) => a.index - b.index)) {
        const response = await fetch(`/tme/cases/${c.case_id}/originals/${page.index}`, { cache: "no-store", credentials: "same-origin" });
        if (!response.ok) throw new Error("Não foi possível recuperar as páginas preservadas. Tente novamente.");
        const file = new File([await response.blob()], `pagina-${page.index + 1}`, { type: page.original_mime });
        const photo = Scan.photo(file, URL.createObjectURL(file), page.captured_at);
        photo.rotation = page.rotation_degrees; restored.push(photo);
      }
      for (const photo of state.photos) URL.revokeObjectURL(photo.url);
      state.photos = restored; state.adjusting = true;
      state.message = "Ajuste as páginas e confirme cada uma antes de continuar."; renderScan();
    } catch (e) {
      for (const photo of restored) URL.revokeObjectURL(photo.url);
      state.message = e.message; await renderCorrection();
    }
  }
  async function recognize() {
    if (state.busy) return;
    const c = state.current;
    state.busy = true; local(c).processing = "recognition"; state.message = "";
    state.feedback = { state: "RECOGNIZING", message: "Reconhecendo as páginas preservadas…" };
    try {
      await renderCorrection();
      const run = await post(`/tme/cases/${c.case_id}/recognize`, {});
      if (state.current?.case_id !== c.case_id) return;
      state.feedback = await api(`/tme/cases/${c.case_id}/recognition-status`);
      state.message = run.status === "FAILED" ? "" : "Transcrição automática disponível.";
    } catch (error) {
      if (state.current?.case_id !== c.case_id) return;
      state.feedback = { state: "FAILED", error_code: error.code,
        message: error.code ? error.message : "Não foi possível reconhecer esta solução agora. As páginas foram preservadas." };
    } finally { state.busy = false; local(c).processing = null; local(c).loaded = false; }
    if (state.current?.case_id === c.case_id && state.view === "workspace") await renderCorrection();
  }
  function manuscriptPage(c, index) {
    const page = node("div", undefined, "page-review"); page.appendChild(node("h3", `Página ${index + 1}`));
    const originalUrl = c.source_mode === "IMAGE_SCAN" ? `/tme/cases/${c.case_id}/originals/${index}` : `/tme/cases/${c.case_id}/pages/${index}`;
    const img = node("img"); img.src = originalUrl; img.alt = `Manuscrito original da página ${index + 1}`;
    img.onerror = () => {
      img.onerror = null;
      if (c.source_mode === "IMAGE_SCAN") {
        img.src = `/tme/cases/${c.case_id}/pages/${index}`; img.alt = `Prévia normalizada da página ${index + 1}`;
        page.appendChild(node("p", "Este navegador exibe a prévia normalizada. O original continua preservado.", "muted"));
      }
    };
    page.appendChild(img);
    if (c.source_mode === "IMAGE_SCAN") {
      const link = node("a", "Abrir original preservado"); link.href = originalUrl; link.target = "_blank"; link.rel = "noopener";
      page.appendChild(link);
    }
    return page;
  }
  function loading(message) {
    const box = node("div", undefined, "processing-state"); box.appendChild(note(message));
    const skeleton = node("div", undefined, "skeleton-lines"); skeleton.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 3; i++) skeleton.appendChild(node("span")); box.appendChild(skeleton); return box;
  }
  async function renderCorrection() {
    const c = state.current, saved = await loadCaseData(c);
    if (state.current !== c || state.view !== "workspace") return;
    state.history = saved.history;
    const latest = saved.history?.revisions.at(-1), run = runFor(c);
    const layout = node("div", undefined, "correction-workspace"), solution = card(), right = node("aside", undefined, "analysis-column");
    solution.classList.add("solution-panel"); solution.id = "solution-pane"; right.id = "analysis-pane"; right.setAttribute("aria-label", "Análise ConfIA");
    const solutionHeading = node("header", undefined, "pane-header"); solutionHeading.appendChild(node("h2", "SOLUÇÃO DO PARTICIPANTE"));
    const tabs = node("div", undefined, "solution-tabs"), views = node("div", undefined, "solution-views"); views.id = "solution-views"; views.setAttribute("role", "tabpanel"); views.tabIndex = 0;
    tabs.setAttribute("aria-label", "Visualização da solução"); tabs.setAttribute("role", "tablist");
    const original = node("section", undefined, "original-document"), transcript = node("section", undefined, "transcript-document");
    original.setAttribute("aria-label", "Original"); transcript.setAttribute("aria-label", "Transcrição");
    const pages = [...new Set([...(saved.detail?.submission?.page_images || []).map(p => p.page_index), ...(latest?.segments || []).map(s => s.page_index)])].sort((a,b) => a-b);
    const pageNodes = pages.map(index => manuscriptPage(c, index)); original.append(...pageNodes);
    saved.page = Math.min(saved.page, Math.max(0, pages.length - 1));
    const pagination = node("span", "", "page-position");
    const updatePages = () => {
      pageNodes.forEach((page, i) => { page.hidden = i !== saved.page; const img = page.querySelectorAll("img")[0]; img.style.transform = `scale(${saved.zoom}) rotate(${saved.rotation}deg)`; });
      pagination.textContent = `${Math.round(saved.zoom * 100)}% · Página ${pages.length ? saved.page + 1 : 0}/${pages.length}`;
    };
    const toolbar = actions(btn("Zoom −", () => { saved.zoom = Math.max(.5, saved.zoom - .25); updatePages(); }, "secondary"), pagination,
      btn("Zoom +", () => { saved.zoom = Math.min(3, saved.zoom + .25); updatePages(); }, "secondary"),
      btn("Anterior", () => { saved.page = Math.max(0, saved.page - 1); updatePages(); }, "secondary"),
      btn("Próxima", () => { saved.page = Math.min(Math.max(0, pages.length - 1), saved.page + 1); updatePages(); }, "secondary"),
      btn("Rotacionar", () => { saved.rotation = (saved.rotation + 90) % 360; updatePages(); }, "secondary"));
    toolbar.classList.add("viewer-commands"); toolbar.setAttribute("aria-label", "Comandos do original"); updatePages();
    const editor = node("div", undefined, "transcription-editor"); editor.hidden = !saved.editing;
    const documentView = node("div"); documentView.hidden = Boolean(saved.editing);
    if (latest) {
      for (const index of pages) {
        const text = latest.segments.filter(s => s.page_index === index).sort((a,b) => a.order-b.order).map(s => s.text || s.latex || "").join("\n\n");
        const doc = node("div", undefined, "document"); doc.setAttribute("role", "document"); doc.setAttribute("aria-label", `Transcrição da página ${index + 1}`);
        window.ConfiaRecognitionView.renderMathText(doc, text); documentView.appendChild(doc);
        const area = node("textarea"); area.value = saved.editors[index] ?? text; area.addEventListener("input", () => { saved.editors[index] = area.value; });
        editor.appendChild(field(`Editar página ${index + 1}`, area));
      }
      editor.append(note("Cada salvamento cria uma revisão. Preserve a matemática escrita pelo participante."), actions(btn("Salvar nova revisão", () => saveRevision(c, editor)), btn("Cancelar edição", () => { saved.editing = false; editor.hidden = true; documentView.hidden = false; }, "secondary")));
    } else documentView.appendChild(note("A transcrição aparecerá após o reconhecimento automático."));
    transcript.append(documentView, editor);
    const setTab = value => {
      saved.tab = value; original.hidden = value === "transcript"; transcript.hidden = value === "original"; toolbar.hidden = value === "transcript";
      views.classList.toggle("compare", value === "compare"); views.setAttribute("aria-labelledby", `tab-${value}`);
      for (const button of tabs.children) { button.setAttribute("aria-selected", String(button.dataset.tab === value)); button.tabIndex = button.dataset.tab === value ? 0 : -1; }
    };
    for (const [value, label] of [["original", "Original"], ["transcript", "Transcrição"], ["compare", "Comparar"]]) {
      const button = btn(label, () => setTab(value), "secondary"); button.id = `tab-${value}`; button.dataset.tab = value; button.setAttribute("role", "tab"); button.setAttribute("aria-controls", "solution-views");
      button.addEventListener("keydown", event => {
        const list = Array.from(tabs.children), i = list.indexOf(button);
        const next = { ArrowRight: (i + 1) % 3, ArrowLeft: (i + 2) % 3, Home: 0, End: 2 }[event.key];
        if (next !== undefined) { event.preventDefault(); setTab(list[next].dataset.tab); list[next].focus(); }
      }); tabs.appendChild(button);
    }
    views.append(original, transcript); setTab(saved.tab);
    const secondary = actions(); secondary.classList.add("transcript-commands");
    if (latest) secondary.append(btn("Editar", () => { saved.editing = true; editor.hidden = false; documentView.hidden = true; setTab("transcript"); }, "secondary"), btn("Reprocessar", recognize, "secondary"));
    for (const button of secondary.children) button.disabled = state.busy;
    solutionHeading.appendChild(secondary);
    const provenance = node("details", undefined, "transcription-metadata"); provenance.appendChild(node("summary", latest ? "Transcrição automática · metadados" : "Originais e histórico"));
    const meta = saved.history?.transcription;
    if (meta) provenance.appendChild(node("p", `${meta.provider || meta.recognizer || "Provider não registrado"} · ${meta.recognizer_version || "Versão não registrada"} · ${meta.created_at ? new Date(meta.created_at).toLocaleString("pt-BR") : "Horário não registrado"}`));
    if (c.source_mode === "IMAGE_SCAN") { const adjust = btn("Voltar e ajustar páginas", adjustPages, "secondary"); adjust.disabled = state.busy; provenance.appendChild(adjust); }
    const technical = node("details", undefined, "technical-details"); technical.append(node("summary", "Detalhes técnicos da transcrição"), node("pre", JSON.stringify({ transcription: saved.history, recognition: saved.feedback }, window.ConfIAReport.publicTechnicalValue, 2))); provenance.appendChild(technical);
    solution.append(solutionHeading, tabs, toolbar, views, provenance);
    const analysis = node("section", undefined, "analysis-panel"), analysisHeading = node("header", undefined, "pane-header"); analysisHeading.appendChild(node("h2", "ANÁLISE CONFIA"));
    const analysisBody = node("div"); analysisBody.id = "analysis-content"; analysisBody.hidden = Boolean(saved.analysisCollapsed);
    const collapse = btn(saved.analysisCollapsed ? "Expandir análise" : "Recolher análise", () => {
      saved.analysisCollapsed = !saved.analysisCollapsed; analysisBody.hidden = saved.analysisCollapsed;
      collapse.textContent = saved.analysisCollapsed ? "Expandir análise" : "Recolher análise"; collapse.setAttribute("aria-expanded", String(!saved.analysisCollapsed));
    }, "secondary"); collapse.setAttribute("aria-controls", "analysis-content"); collapse.setAttribute("aria-expanded", String(!saved.analysisCollapsed));
    analysisHeading.appendChild(collapse); analysis.append(analysisHeading, analysisBody);
    if (saved.processing === "audit") analysisBody.appendChild(loading("Analisando matemática · executando verificações…"));
    if (run) {
      if (run.stale) analysisBody.appendChild(note("Análise de uma revisão anterior. Analise a revisão atual antes de vincular a decisão."));
      if (run.result) { const report = node("div"); window.ConfIAReport.render(run.result, report, { context: "evaluator", auditRun: run, workspace: true, uiState: saved }); analysisBody.appendChild(report); }
      else analysisBody.appendChild(note("Não foi possível concluir a análise. A decisão humana permanece disponível."));
    } else if (!saved.processing) analysisBody.appendChild(note("Reconheça a solução e analise para consultar critérios, evidências e verificações."));
    const openDrawer = btn("Abrir análise", () => drawer(true), "secondary drawer-trigger"); openDrawer.setAttribute("aria-controls", "analysis-pane");
    const closeDrawer = btn("Fechar análise", () => { drawer(false); openDrawer.focus(); }, "secondary drawer-close");
    const drawer = open => { saved.drawerOpen = open; right.dataset.open = String(open); openDrawer.setAttribute("aria-expanded", String(open)); if (open) closeDrawer.focus(); };
    right.dataset.open = String(Boolean(saved.drawerOpen)); openDrawer.setAttribute("aria-expanded", String(Boolean(saved.drawerOpen)));
    right.addEventListener("keydown", event => { if (event.key === "Escape") { drawer(false); openDrawer.focus(); } });
    right.append(closeDrawer, analysis);
    const divider = node("div", undefined, "pane-splitter"); layout.append(solution, divider, right); window.ConfiaWorkspaceControls.attachSplitter(layout, divider);
    const decisionBox = decisionPanel(c, saved, run?.status === "COMPLETED" && (!run.stale || saved.decision) ? run : null);
    const actionbar = node("div", undefined, "workspace-actions");
    const progress = saved.processing === "audit" ? "Analisando matemática · executando verificações…" : saved.processing === "recognition" ? "Reconhecendo solução…" : state.message || (run ? "Análise concluída." : latest ? "Transcrição automática disponível." : saved.feedback?.state === "FAILED" ? saved.feedback.message : "Aguardando reconhecimento");
    actionbar.appendChild(note(progress));
    let primary;
    if (!latest) primary = btn(saved.feedback?.state === "FAILED" ? "Tentar novamente" : "Reconhecer", recognize);
    else if (!run || run.stale || run.status === "FAILED") primary = btn("Analisar com ConfIA", audit);
    if (primary) { primary.disabled = state.busy; actionbar.appendChild(primary); }
    if (saved.processing === "recognition") actionbar.appendChild(loading("Reconhecendo…"));
    const heading = context(c, saved.decision ? 3 : run ? 2 : latest ? 1 : 0); heading.appendChild(openDrawer);
    show(heading, layout, actionbar, decisionBox);
  }
  async function saveRevision(c, editor) {
    if (state.busy) return;
    const saved = local(c), history = saved.history, latest = history.revisions.at(-1);
    const areas = Array.from(editor.querySelectorAll("textarea")), pages = [...new Set(latest.segments.map(s => s.page_index))].sort((a,b) => a-b);
    if (areas.some(area => !area.value.trim())) { state.message = "Todas as páginas precisam de transcrição."; return renderCorrection(); }
    state.busy = true;
    try {
      await post(`/tme/cases/${c.case_id}/transcriptions/${history.transcription.transcription_id}/revisions`, {
        based_on_revision_number: latest.revision_number, reviewer_identity_verified: false, change_type: "reading_correction", status: "NEEDS_REVIEW",
        segments: pages.map((index, i) => ({ segment_id: `tme-page:${index}`, page_index: index, order: 0, kind: "text", text: areas[i].value.trim() })) });
      saved.loaded = false; saved.editing = false; saved.editors = {}; state.message = "Nova revisão salva. A leitura anterior foi preservada.";
    } catch (_) { state.message = "Não foi possível salvar a revisão. Seu texto foi preservado; tente novamente."; }
    finally { state.busy = false; }
    if (state.current === c) await renderCorrection();
  }
  async function audit() {
    if (state.busy) return;
    const c = state.current, saved = local(c), history = saved.history, latest = history?.revisions.at(-1);
    if (!latest) return;
    state.busy = true; saved.processing = "audit"; await renderCorrection();
    try {
      let accepted = history.acceptances.find(a => a.revision_number === latest.revision_number);
      // Existing integrity receipt binds the exact revision. No human-review claim.
      if (!accepted) {
        const receipt = await post(`/tme/cases/${c.case_id}/transcriptions/${history.transcription.transcription_id}/accept`, { revision_number: latest.revision_number, reviewer_identity_verified: false, acceptance_note: "Vinculação automática da revisão para análise a pedido do avaliador; sem conferência humana obrigatória." });
        accepted = receipt.acceptance; history.acceptances.push(accepted);
      }
      const run = await post(`/tme/cases/${c.case_id}/audits`, { transcription_id: history.transcription.transcription_id, revision_number: latest.revision_number, acceptance_id: accepted.acceptance_id });
      saved.audits = [run, ...(saved.audits || []).filter(r => r.audit_run_id !== run.audit_run_id)]; state.message = run.status === "COMPLETED" ? "Análise concluída." : "Não foi possível concluir a análise matemática.";
    } catch (_) { state.message = "Não foi possível concluir a análise matemática. A solução permanece preservada; tente novamente."; }
    finally { state.busy = false; saved.processing = null; }
    if (state.current === c && state.view === "workspace") await renderCorrection();
  }
  function decisionPanel(c, saved, run) {
    const box = node("section", undefined, "decision-bar"); box.setAttribute("aria-label", "Decisão do avaliador");
    const suggestion = node("div", undefined, "decision-suggestion"); suggestion.append(node("span", "Sugestão ConfIA", "quiet-label"), node("strong", run?.result?.score == null ? "Não determinada" : `${String(run.result.score).replace(".", ",")} / ${run.result.max_score}`)); box.appendChild(suggestion);
    if (saved.decision) { box.append(node("strong", `Pontuação final do avaliador: ${saved.decision.final_points} / ${saved.decision.max_points}`), node("span", "Finalizada", "status")); const detail = node("details"); detail.append(node("summary", "Observação registrada"), node("p", saved.decision.feedback || "Sem comentário.")); box.appendChild(detail); return box; }
    const form = node("form"), controls = {}, extras = node("details", undefined, "decision-observation"); extras.open = Boolean(saved.observationOpen);
    const observationFields = node("div", undefined, "observation-fields");
    extras.append(node("summary", "Adicionar observação"), observationFields); extras.addEventListener("toggle", () => { saved.observationOpen = extras.open; });
    for (const [name, label] of [["max", "Pontuação máxima"], ["final", "Pontuação final"], ["feedback", "Justificativa / devolutiva"], ["reason", "Motivo para divergir da sugestão"]]) {
      const input = node(["max", "final"].includes(name) ? "input" : "textarea"); controls[name] = input; input.name = name;
      if (["max", "final"].includes(name)) { input.type = "number"; input.min = name === "max" ? "0.01" : "0"; input.max = "1000"; input.step = "0.01"; input.required = true; }
      input.value = saved.draft[name] ?? (name === "max" ? String(run?.result?.max_score || 10) : "");
      input.addEventListener("input", () => { saved.draft[name] = input.value; });
      (name === "final" ? form : observationFields).appendChild(field(label, input));
    }
    const use = btn("Usar sugestão", () => { if (run?.result?.score != null) { controls.final.value = String(run.result.score); saved.draft.final = controls.final.value; controls.final.focus(); } }, "secondary"); use.disabled = state.busy || run?.result?.score == null;
    const error = note(""); error.classList.add("decision-error");
    const submit = btn("Finalizar correção", async () => {
      if (state.busy) return;
      if (!controls.max.checkValidity()) { extras.open = true; controls.max.reportValidity(); return; }
      if (!controls.final.reportValidity()) return;
      if (Number(controls.final.value) > Number(controls.max.value)) { error.textContent = "A pontuação final não pode superar a máxima."; return; }
      state.busy = true; submit.disabled = true; use.disabled = true;
      try {
        saved.decision = await post(`/tme/cases/${c.case_id}/decision`, { audit_run_id: run?.audit_run_id || null, max_points: Number(controls.max.value), final_points: Number(controls.final.value), feedback: controls.feedback.value, override_reason: controls.reason.value.trim() || null });
        saved.draft = {}; state.message = "Decisão registrada.";
      } catch (_) { extras.open = true; error.textContent = "Não foi possível registrar a decisão. Confira a justificativa e tente novamente."; }
      finally { state.busy = false; submit.disabled = false; use.disabled = run?.result?.score == null; }
      if (saved.decision && state.current === c && state.view === "workspace") await renderCorrection();
    }, run ? "" : "secondary"); submit.disabled = state.busy;
    form.addEventListener("submit", event => { event.preventDefault(); submit.click(); }); form.append(use, extras, submit, error); box.appendChild(form); return box;
  }
  Home.HomeHeader();
  const bottomNav = document.querySelector("#home-bottom-nav");
  if (bottomNav) Home.MobileBottomNav(bottomNav, navigate);
  for (const item of document.querySelectorAll("#workspace-nav [data-view]")) item.addEventListener("click", () => navigate(item.dataset.view));
  window.addEventListener("message", event => {
    if (event.origin !== window.location.origin || event.data?.type !== "confia-notebook-context") return;
    if (event.data.context?.tmeRecognitionFinished && event.source === state.captureWindow && state.current?.source_mode === "DIGITAL_INK") {
      local(state.current).loaded = false;
      openCase(state.current.case_id).catch(showError);
    }
  });
  const toggle = document.querySelector("#sidebar-toggle"), sidebar = document.querySelector("#sidebar");
  const setSidebar = collapsed => {
    toggle.setAttribute("aria-expanded", String(!collapsed)); toggle.setAttribute("aria-label", collapsed ? "Expandir menu" : "Recolher menu"); toggle.textContent = collapsed ? "›" : "‹";
    sidebar.classList.toggle("collapsed", collapsed);
    try { window.localStorage.setItem("confia.correction.sidebar-collapsed", String(collapsed)); } catch (_) { /* Optional preference. */ }
  };
  toggle?.addEventListener("click", () => setSidebar(toggle.getAttribute("aria-expanded") === "true"));
  try { if (window.localStorage.getItem("confia.correction.sidebar-collapsed") === "true") setSidebar(true); } catch (_) { /* Default expanded. */ }
  (async () => {
    const label = document.querySelector("#session-label"), detail = document.querySelector("#session-detail"), logout = document.querySelector("#logout");
    try {
      const user = await api("/auth/me"); label.textContent = user.display_name || user.login; const homeSession = document.querySelector("#home-session"); if (homeSession) homeSession.textContent = user.display_name || user.login || "Avaliador ConfIA"; detail.textContent = "Sessão autenticada · Avaliador"; logout.hidden = false;
      logout.addEventListener("click", async () => { const response = await fetch("/auth/logout", { method: "POST", credentials: "same-origin" }); if (response.ok) window.location.assign("/auth"); else detail.textContent = "Não foi possível encerrar a sessão."; });
    } catch (_) { if (detail) detail.textContent = "Sessão do piloto · acesso conforme configuração do servidor"; }
  })();
  home();
})();
