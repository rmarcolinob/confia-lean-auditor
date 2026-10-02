(function teacherManuscripts() {
  "use strict";
  const inbox = document.querySelector("#manuscript-inbox");
  const legacy = document.querySelector("#teacher-text-prototype");
  const list = document.querySelector("#manuscript-list");
  const detail = document.querySelector("#manuscript-detail");
  const message = document.querySelector("#manuscript-message");
  const showInk = document.querySelector("#show-manuscripts");
  const showText = document.querySelector("#show-text-prototype");
  let listSequence = 0;
  let detailSequence = 0;
  let segmentSequence = 0;
  const validId = (id) => typeof id === "string" && /^sub_[0-9a-f]{32}$/.test(id);
  const when = (value) => new Date(value).toLocaleString("pt-BR");

  function node(tag, content) {
    const value = document.createElement(tag);
    if (content !== undefined) value.textContent = content;
    return value;
  }

  function labeled(text, control) {
    const label = node("label");
    label.appendChild(node("span", text));
    label.appendChild(control);
    return label;
  }

  function option(value, text) {
    const item = node("option", text);
    item.value = value;
    return item;
  }

  async function request(url, options = {}) {
    const response = await fetch(url, { cache: "no-store", ...options });
    if (!response.ok) {
      let explanation = "";
      try {
        const body = await response.json();
        explanation = body.detail ? ` ${body.detail}` : "";
      } catch (_error) {
        // HTTP status remains a safe, useful fallback.
      }
      throw new Error(`Consulta indisponível (HTTP ${response.status}).${explanation} Tente atualizar novamente.`);
    }
    return response.json();
  }

  function write(url, body) {
    return request(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  function integrityDetails(data, id) {
    const record = data.submission;
    const block = node("div");
    const intact = data.integrity.length === record.page_images.length + 1 && data.integrity.every((item) => item.matches);
    block.appendChild(node("p", intact ? "Integridade técnica: hashes SHA-256 conferem." : "Alerta: há artefato ausente ou com hash divergente."));
    block.appendChild(node("p", "Hashes indicam somente integridade técnica; não comprovam autoria nem validade matemática."));
    const hashes = node("details");
    hashes.appendChild(node("summary", "Detalhes de integridade e recibo"));
    hashes.appendChild(node("p", `snapshot_id: ${record.snapshot_id} · schema: ${record.capture_schema_version} · source: ${record.source}`));
    const items = node("ul");
    for (const artifact of data.integrity) {
      items.appendChild(node("li", `${artifact.filename}: ${artifact.matches ? "confere" : "divergente/ausente"} · SHA-256 esperado: ${artifact.expected_sha256} · atual: ${artifact.actual_sha256 || "ausente"}`));
    }
    hashes.appendChild(items);
    const download = node("a", "Baixar snapshot original (JSON)");
    download.href = `/submissions/${id}/snapshot`;
    hashes.appendChild(download);
    block.appendChild(hashes);
    return block;
  }

  function renderOriginal(panel, data, id) {
    const record = data.submission;
    const pages = [...record.page_images].sort((a, b) => a.page_index - b.page_index);
    let current = 0;
    panel.appendChild(node("h3", "Manuscrito original"));
    panel.appendChild(node("p", "PNG recebido do tablet. Esta visualização e a transcrição não alteram o arquivo original."));
    const navigation = node("div");
    navigation.className = "page-navigation";
    const previous = node("button", "Página anterior");
    previous.type = "button";
    previous.className = "secondary-action";
    const pageLabel = node("span");
    const next = node("button", "Próxima página");
    next.type = "button";
    next.className = "secondary-action";
    navigation.appendChild(previous);
    navigation.appendChild(pageLabel);
    navigation.appendChild(next);
    panel.appendChild(navigation);
    const pageHost = node("div");
    panel.appendChild(pageHost);

    function draw() {
      pageHost.replaceChildren();
      const page = pages[current];
      if (!page || !Number.isInteger(page.page_index) || page.page_index < 0 || page.page_index > 2) {
        pageHost.appendChild(node("p", "Índice de página inválido."));
        return;
      }
      pageLabel.textContent = `Página ${current + 1} de ${pages.length}`;
      previous.disabled = current === 0;
      next.disabled = current === pages.length - 1;
      const figure = node("figure");
      figure.appendChild(node("figcaption", `Página ${page.page_index + 1} · PNG original recebido`));
      const integrity = data.integrity.find((item) => item.filename === page.filename);
      if (integrity?.matches) {
        const image = node("img");
        image.alt = `Manuscrito original da questão ${record.problem_id}, página ${page.page_index + 1}`;
        image.src = `/submissions/${id}/pages/${page.page_index}`;
        image.addEventListener("error", () => {
          figure.appendChild(node("p", "Não foi possível carregar este PNG. Atualize a consulta para conferir a integridade."));
        });
        figure.appendChild(image);
      } else {
        figure.appendChild(node("p", "PNG indisponível por divergência de integridade."));
      }
      pageHost.appendChild(figure);
    }
    previous.addEventListener("click", () => { if (current > 0) { current -= 1; draw(); } });
    next.addEventListener("click", () => { if (current + 1 < pages.length) { current += 1; draw(); } });
    draw();
  }

  function editableSegment(segment, pageCount) {
    const row = node("fieldset");
    row.className = "transcription-segment";
    row.dataset.segmentId = segment.segment_id || `manual:${Date.now()}:${++segmentSequence}`;
    row.appendChild(node("legend", `Segmento ${segment.order + 1}`));
    const kind = node("select");
    for (const value of ["text", "math", "mixed", "diagram", "unknown"]) kind.appendChild(option(value, value));
    kind.value = segment.kind || "mixed";
    const page = node("select");
    for (let index = 0; index < pageCount; index += 1) page.appendChild(option(String(index), `Página ${index + 1}`));
    page.value = String(segment.page_index || 0);
    const text = node("textarea");
    text.rows = 3;
    text.value = segment.text || "";
    text.placeholder = "Texto exatamente como aparece no manuscrito";
    const latex = node("textarea");
    latex.rows = 3;
    latex.value = segment.latex || "";
    latex.placeholder = "LaTeX fiel ao manuscrito, mesmo quando a matemática estiver errada";
    row.appendChild(labeled("Tipo", kind));
    row.appendChild(labeled("Página", page));
    row.appendChild(labeled("Texto (opcional)", text));
    row.appendChild(labeled("Matemática / LaTeX (opcional)", latex));
    row.controls = { kind, page, text, latex };
    return row;
  }

  function collectSegments(host) {
    return Array.from(host.children).map((row, order) => {
      const item = { segment_id: row.dataset.segmentId, page_index: Number(row.controls.page.value), order, kind: row.controls.kind.value };
      const text = row.controls.text.value.trim();
      const latex = row.controls.latex.value.trim();
      if (text) item.text = text;
      if (latex) item.latex = latex;
      return item;
    });
  }

  function renderHistory(panel, history) {
    const disclosure = node("details");
    disclosure.className = "transcription-history";
    disclosure.appendChild(node("summary", `Histórico de revisões (${history.revisions.length})`));
    for (const revision of [...history.revisions].reverse()) {
      const article = node("article");
      article.appendChild(node("h4", `Revisão ${revision.revision_number} · ${revision.status}`));
      article.appendChild(node("p", `${when(revision.created_at)} · revisor não verificado: ${revision.reviewer_reference} · alteração: ${revision.change_type}`));
      if (revision.change_reason) article.appendChild(node("p", `Motivo: ${revision.change_reason}`));
      const items = node("ol");
      for (const segment of revision.segments) {
        items.appendChild(node("li", `Página ${segment.page_index + 1} · ${segment.kind} · texto: ${segment.text || "—"} · LaTeX: ${segment.latex || "—"}`));
      }
      article.appendChild(items);
      disclosure.appendChild(article);
    }
    panel.appendChild(disclosure);
  }

  function renderTranscription(panel, data, id, history) {
    const pageCount = data.submission.page_images.length;
    const latest = history?.revisions?.[history.revisions.length - 1] || null;
    panel.appendChild(node("h3", "Transcrição"));
    const warning = node("p", "Transcrever é representar fielmente o manuscrito. Não corrija a matemática: se o aluno escreveu “2 + 2 = 5”, preserve “2 + 2 = 5”.");
    warning.className = "transcription-warning";
    panel.appendChild(warning);
    panel.appendChild(node("p", "ACCEPTED significa somente que a transcrição foi aceita como representação do manuscrito; não significa solução correta."));
    const reviewer = node("input");
    reviewer.type = "text";
    reviewer.maxLength = 80;
    reviewer.value = latest?.reviewer_reference || "professor-teste-01";
    panel.appendChild(labeled("Referência do revisor (identidade não verificada)", reviewer));
    const reason = node("input");
    reason.type = "text";
    reason.maxLength = 500;
    reason.placeholder = "Ex.: corrige palavra lida incorretamente";
    panel.appendChild(labeled("Motivo da nova revisão (opcional)", reason));
    const segmentHost = node("div");
    segmentHost.className = "transcription-segments";
    const initialSegments = latest?.segments || [{ segment_id: "", page_index: 0, order: 0, kind: "mixed" }];
    for (const segment of initialSegments) segmentHost.appendChild(editableSegment(segment, pageCount));
    panel.appendChild(segmentHost);
    const actions = node("div");
    actions.className = "transcription-actions";
    const add = node("button", "Adicionar segmento");
    add.type = "button";
    add.className = "secondary-action";
    const save = node("button", latest ? "Salvar como nova revisão" : "Criar transcrição manual");
    save.type = "button";
    save.className = "primary-action";
    const accept = node("button", "Aceitar como fiel ao manuscrito");
    accept.type = "button";
    accept.className = "secondary-action";
    accept.disabled = !latest || latest.status === "ACCEPTED";
    actions.appendChild(add);
    actions.appendChild(save);
    actions.appendChild(accept);
    panel.appendChild(actions);
    const editorMessage = node("p");
    editorMessage.className = "transcription-message";
    editorMessage.setAttribute("role", "status");
    editorMessage.setAttribute("aria-live", "polite");
    panel.appendChild(editorMessage);
    add.addEventListener("click", () => {
      segmentHost.appendChild(editableSegment({ segment_id: "", page_index: 0, order: segmentHost.children.length, kind: "mixed" }, pageCount));
    });
    save.addEventListener("click", async () => {
      save.disabled = true;
      editorMessage.textContent = latest ? "Salvando nova revisão sem alterar a anterior…" : "Criando transcrição manual…";
      try {
        const common = { reviewer_reference: reviewer.value.trim(), reviewer_identity_verified: false, segments: collectSegments(segmentHost), status: "NEEDS_REVIEW" };
        if (latest) {
          await write(`/transcriptions/${history.transcription.transcription_id}/revisions`, {
            ...common, based_on_revision_number: latest.revision_number, change_type: "reading_correction",
            ...(reason.value.trim() ? { change_reason: reason.value.trim() } : {}),
          });
        } else {
          await write(`/submissions/${id}/transcriptions`, { ...common, source: "manual", recognizer: null, recognizer_version: null });
        }
        editorMessage.textContent = "Revisão salva. Atualizando histórico…";
        await open(id);
      } catch (error) {
        save.disabled = false;
        editorMessage.textContent = error.message;
      }
    });
    accept.addEventListener("click", async () => {
      accept.disabled = true;
      editorMessage.textContent = "Registrando aceite de fidelidade — sem avaliar a matemática…";
      try {
        await write(`/transcriptions/${history.transcription.transcription_id}/accept`, {
          revision_number: latest.revision_number, reviewer_reference: reviewer.value.trim(), reviewer_identity_verified: false,
          acceptance_note: "Conferida visualmente com o manuscrito original.",
        });
        await open(id);
      } catch (error) {
        accept.disabled = false;
        editorMessage.textContent = error.message;
      }
    });
    if (history) renderHistory(panel, history);
  }

  async function open(id) {
    if (!validId(id)) return;
    const sequence = ++detailSequence;
    detail.hidden = true;
    detail.replaceChildren();
    message.textContent = "Carregando manuscrito, transcrição e integridade…";
    try {
      const [data, summaries] = await Promise.all([request(`/submissions/${id}`), request(`/submissions/${id}/transcriptions`)]);
      if (sequence !== detailSequence) return;
      if (!Array.isArray(summaries)) throw new Error("Lista de transcrições inválida.");
      const record = data.submission;
      if (record.submission_id !== id) throw new Error("Registro retornado não corresponde à submissão selecionada.");
      let history = null;
      if (summaries.length) {
        history = await request(`/transcriptions/${summaries[0].transcription.transcription_id}`);
        if (sequence !== detailSequence) return;
      }
      detail.appendChild(node("h2", "Revisão do manuscrito recebido"));
      detail.appendChild(node("p", `submission_id: ${id}`));
      detail.appendChild(node("p", `Questão: ${record.problem_id} · Recebida em: ${when(record.received_at)} · Status: ${record.status}`));
      if (record.student_reference) detail.appendChild(node("p", `Referência não verificada (sem autenticação): ${record.student_reference}`));
      detail.appendChild(integrityDetails(data, id));
      const workspace = node("div");
      workspace.className = "transcription-workspace";
      const original = node("section");
      original.className = "original-manuscript-panel";
      const transcription = node("section");
      transcription.className = "transcription-panel";
      renderOriginal(original, data, id);
      renderTranscription(transcription, data, id, history);
      workspace.appendChild(original);
      workspace.appendChild(transcription);
      detail.appendChild(workspace);
      detail.hidden = false;
      message.textContent = history ? "Submissão e histórico de transcrição abertos." : "Submissão aberta. Crie uma transcrição manual fiel ao manuscrito.";
    } catch (error) {
      if (sequence === detailSequence) {
        detail.replaceChildren();
        detail.hidden = true;
        message.textContent = error.message;
      }
    }
  }

  async function refresh() {
    const sequence = ++listSequence;
    ++detailSequence;
    detail.hidden = true;
    detail.replaceChildren();
    list.replaceChildren();
    message.textContent = "Consultando submissões recebidas…";
    try {
      const records = await request("/submissions");
      if (sequence !== listSequence) return;
      if (!Array.isArray(records)) throw new Error("Lista de submissões inválida.");
      for (const record of records) {
        if (!validId(record.submission_id)) continue;
        const button = node("button", `${record.problem_id} · ${record.status} · ${when(record.received_at)} · ${record.submission_id}`);
        button.type = "button";
        button.className = "secondary-action";
        button.addEventListener("click", () => open(record.submission_id));
        list.appendChild(button);
      }
      message.textContent = records.length ? `${records.length} submissão(ões) no servidor. Selecione para abrir.` : "Nenhuma submissão recebida pelo servidor.";
    } catch (error) {
      if (sequence === listSequence) message.textContent = error.message;
    }
  }

  function mode(manuscripts) {
    inbox.hidden = !manuscripts;
    legacy.hidden = manuscripts;
    showInk.setAttribute("aria-pressed", String(manuscripts));
    showText.setAttribute("aria-pressed", String(!manuscripts));
    if (manuscripts) refresh();
  }
  showInk.addEventListener("click", () => mode(true));
  showText.addEventListener("click", () => mode(false));
  document.querySelector("#refresh-manuscripts").addEventListener("click", refresh);
  document.querySelector('[data-tab-target="teacher-area"]').addEventListener("click", () => { if (!inbox.hidden) refresh(); });
  if (new URLSearchParams(location.search).get("area") === "teacher") document.querySelector('[data-tab-target="teacher-area"]').click();
})();
