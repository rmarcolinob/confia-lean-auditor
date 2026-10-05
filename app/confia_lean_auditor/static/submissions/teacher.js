(function teacherManuscripts() {
  "use strict";
  const inbox = document.querySelector("#manuscript-inbox");
  const legacy = document.querySelector("#teacher-text-prototype");
  const list = document.querySelector("#manuscript-list");
  const queuePanel = document.querySelector("#manuscript-queue");
  const detail = document.querySelector("#manuscript-detail");
  const message = document.querySelector("#manuscript-message");
  const showInk = document.querySelector("#show-manuscripts");
  const showText = document.querySelector("#show-text-prototype");
  const refreshButton = document.querySelector("#refresh-manuscripts");
  const filter = document.querySelector("#transcription-filter");
  const queueTitle = document.querySelector("#manuscript-queue-title");
  const queueNote = document.querySelector("#manuscript-queue-note");
  let queue = [];
  let queueLoaded = false;
  let listSequence = 0;
  let detailSequence = 0;
  let segmentSequence = 0;
  let activeEditor = null;
  const labels = { RECEIVED: "Recebida pelo ConfIA", DRAFT: "Rascunho da transcrição", NEEDS_REVIEW: "Aguardando conferência", ACCEPTED: "Transcrição conferida" };
  const statusLabel = (status) => labels[status] || "Estado indisponível";
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
      let diagnostic = null;
      try {
        diagnostic = await response.json();
      } catch (_error) {
        // Keep the status available in the diagnostic log.
      }
      const error = new Error(`HTTP ${response.status}`);
      error.status = response.status;
      error.diagnostic = diagnostic;
      throw error;
    }
    return response.json();
  }

  function productError(error, action = "load") {
    console.error("ConfIA: manuscritos/transcrição", action, error, error.diagnostic);
    if (error.status === 404) return "Não foi possível carregar esta solução. Ela pode não estar mais disponível. Atualize a lista e tente novamente.";
    if (error.status === 409) {
      const diagnostic = JSON.stringify(error.diagnostic || {});
      if (/integridade|artefato|integrity|hash|artifact|snapshot|png/i.test(diagnostic)) return "Os arquivos originais desta solução precisam ser conferidos. Reabra a solução e consulte a integridade dos arquivos.";
      return "Existe uma revisão mais recente da transcrição. Salve uma cópia das suas alterações e reabra a solução para conferir o histórico.";
    }
    if (action === "recognize") return "Não foi possível gerar a transcrição automática. Nenhuma transcrição criada. Tente novamente.";
    if (action === "save") return "Não foi possível salvar a transcrição agora. Suas alterações continuam nesta tela. Confira os campos e tente novamente.";
    if (action === "accept") return "Não foi possível registrar a conferência desta transcrição. Reabra e tente novamente.";
    return "Não foi possível consultar as soluções agora. Atualize a lista e tente novamente.";
  }

  function canLeaveEditor() {
    if (!activeEditor) return true;
    if (activeEditor.busy) {
      message.textContent = "Aguarde a operação desta transcrição terminar antes de trocar o contexto.";
      message.focus();
      return false;
    }
    if (!activeEditor.isDirty()) return true;
    message.textContent = "Alterações não salvas. Salve uma nova revisão ou use “Descartar alterações não salvas” antes de trocar o contexto.";
    message.focus();
    return false;
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
    const hashes = node("details");
    hashes.className = "disclosure";
    hashes.appendChild(node("summary", "Integridade dos arquivos"));
    hashes.appendChild(node("p", "Hashes indicam somente integridade técnica; não comprovam autoria nem validade matemática."));
    const items = node("ul");
    for (const artifact of data.integrity) {
      items.appendChild(node("li", `${artifact.filename}: ${artifact.matches ? "confere" : "divergente/ausente"} · SHA-256 esperado: ${artifact.expected_sha256} · atual: ${artifact.actual_sha256 || "ausente"}`));
    }
    hashes.appendChild(items);
    const download = node("a", "Baixar versão preparada original (JSON)");
    download.href = `/submissions/${id}/snapshot`;
    hashes.appendChild(download);
    return hashes;
  }

  function originalsIntact(data) {
    const expected = ["snapshot.json", ...data.submission.page_images.map(page => page.filename)];
    return data.integrity.length === expected.length && expected.every(filename =>
      data.integrity.some(item => item.filename === filename && item.matches));
  }

  function renderOriginal(panel, data, id) {
    const record = data.submission;
    const pages = [...record.page_images].sort((a, b) => a.page_index - b.page_index);
    let current = 0;
    panel.setAttribute("aria-label", "Solução do aluno — manuscrito original");
    panel.appendChild(node("p", "Solução do aluno")).className = "eyebrow";
    panel.appendChild(node("h3", "Manuscrito original"));
    panel.appendChild(node("p", "Solução enviada pelo caderno. O arquivo original permanece preservado."));
    const integrity = node("p", originalsIntact(data) ? "✓ Arquivos originais conferidos e preservados." : "! Os arquivos originais desta solução precisam ser conferidos.");
    integrity.className = "alert";
    integrity.dataset.kind = originalsIntact(data) ? "success" : "warning";
    panel.appendChild(integrity);
    const navigation = node("div");
    navigation.className = "page-navigation";
    const previous = node("button", "Página anterior");
    previous.type = "button";
    previous.className = "secondary-action";
    const pageLabel = node("span");
    pageLabel.setAttribute("role", "status");
    pageLabel.setAttribute("aria-live", "polite");
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
          image.hidden = true;
          const warning = node("p", "Não foi possível carregar esta página. Atualize a consulta para conferir os arquivos originais.");
          warning.setAttribute("role", "status");
          figure.appendChild(warning);
        });
        figure.appendChild(image);
      } else {
        figure.appendChild(node("p", "Esta página está indisponível. Os arquivos originais precisam ser conferidos."));
      }
      pageHost.appendChild(figure);
    }
    previous.addEventListener("click", () => { if (current > 0) { current -= 1; draw(); } });
    next.addEventListener("click", () => { if (current + 1 < pages.length) { current += 1; draw(); } });
    draw();
    panel.appendChild(integrityDetails(data, id));
  }

  function editableSegment(segment, pageCount, onChange) {
    const row = node("fieldset");
    row.className = "transcription-segment";
    row.dataset.segmentId = segment.segment_id || `manual:${Date.now()}:${++segmentSequence}`;
    row.appendChild(node("legend", `Segmento ${segment.order + 1}`));
    const kind = node("select");
    const kinds = { text: "Texto", math: "Matemática", mixed: "Misto", diagram: "Diagrama", unknown: "Não identificado" };
    for (const value of Object.keys(kinds)) kind.appendChild(option(value, kinds[value]));
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
    if (onChange) for (const control of Object.values(row.controls)) {
      control.addEventListener("input", onChange);
      control.addEventListener("change", onChange);
    }
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
    disclosure.appendChild(node("summary", `Histórico da transcrição (${history.revisions.length} ${history.revisions.length === 1 ? "revisão" : "revisões"})`));
    const changes = { initial_transcription: "Transcrição criada", reading_correction: "Leitura corrigida", other_transcription_edit: "Transcrição editada" };
    const kinds = { text: "Texto", math: "Matemática", mixed: "Misto", diagram: "Diagrama", unknown: "Não identificado" };
    for (const revision of [...history.revisions].reverse()) {
      const article = node("article");
      article.appendChild(node("h4", `Revisão ${revision.revision_number} · ${statusLabel(revision.status)}`));
      article.appendChild(node("p", `${when(revision.created_at)} · revisor não verificado: ${revision.reviewer_reference} · ${changes[revision.change_type] || "Revisão registrada"}`));
      if (revision.change_reason) article.appendChild(node("p", `Motivo: ${revision.change_reason}`));
      const items = node("ol");
      for (const segment of revision.segments) {
        items.appendChild(node("li", `Página ${segment.page_index + 1} · ${kinds[segment.kind] || "Não identificado"} · texto: ${segment.text || "—"} · LaTeX: ${segment.latex || "—"}`));
      }
      article.appendChild(items);
      const technical = node("details");
      technical.appendChild(node("summary", "Detalhes técnicos da revisão"));
      technical.appendChild(node("pre", JSON.stringify(revision, null, 2)));
      article.appendChild(technical);
      disclosure.appendChild(article);
    }
    for (const acceptance of history.acceptances || []) {
      disclosure.appendChild(node("p", `Conferência da revisão ${acceptance.revision_number} · ${when(acceptance.accepted_at)} · revisor não verificado: ${acceptance.reviewer_reference}`));
      if (acceptance.acceptance_note) disclosure.appendChild(node("p", acceptance.acceptance_note));
    }
    panel.appendChild(disclosure);
  }

  function renderTranscription(panel, data, id, history, providers) {
    const pageCount = data.submission.page_images.length;
    const latest = history?.revisions?.[history.revisions.length - 1] || null;
    panel.setAttribute("aria-label", "Transcrição da solução");
    panel.appendChild(node("h3", "Transcrição"));
    const warning = node("p", "Transcrever é representar fielmente o manuscrito. Não corrija a matemática: se o aluno escreveu “2 + 2 = 5”, preserve “2 + 2 = 5”.");
    warning.className = "transcription-warning";
    panel.appendChild(warning);
    panel.appendChild(node("p", "Transcrição conferida significa somente fidelidade ao manuscrito; não significa solução correta nem avaliação do professor."));
    panel.appendChild(node("p", latest ? `${statusLabel(latest.status)} · revisão persistida ${latest.revision_number}` : "Transcrição: ainda não criada"));
    if (latest?.recognizer_run_id) {
      if (latest.provider === "fake_test") panel.appendChild(node("p", "Transcrição de teste artificial. Conteúdo constante; não é OCR real. Confira cada segmento com o original.")).className = "transcription-warning";
      const origin = node("details");
      origin.appendChild(node("summary", "Detalhes do reconhecimento"));
      origin.appendChild(node("p", `Origem automática · provider: ${latest.provider} · execução: ${latest.recognizer_run_id} · adapter: ${latest.recognizer} ${latest.recognizer_version}`));
      origin.appendChild(node("p", "Proveniência do reconhecimento do manuscrito"));
      origin.appendChild(node("pre", JSON.stringify(latest.provenance || history.transcription.provenance || {}, null, 2)));
      panel.appendChild(origin);
      panel.appendChild(node("p", "Revise cada segmento com o manuscrito original antes de aceitar a fidelidade."));
    }
    const recognition = node("details");
    recognition.className = "recognition-assistance disclosure";
    recognition.appendChild(node("summary", "Auxiliar de transcrição — teste artificial"));
    const generateButtons = [];
    // The only current adapter is explicitly artificial and gated by the server.
    for (const provider of providers.filter(item => item.provider === "fake_test")) {
      const generate = node("button", `Gerar transcrição automática — ${provider.label} (artificial)`);
      generate.type = "button";
      generate.className = "secondary-action";
      generate.disabled = !originalsIntact(data);
      generateButtons.push(generate);
      recognition.appendChild(node("p", "Disponível em desenvolvimento/teste. Produz conteúdo artificial constante; não é OCR real."));
      recognition.appendChild(generate);
      const recognitionMessage = node("p");
      recognitionMessage.setAttribute("role", "status");
      recognition.appendChild(recognitionMessage);
      // Keep the same key across a failed transport/retry of this user action.
      const key = `teacher:${Date.now()}:${++segmentSequence}`;
      generate.addEventListener("click", async () => {
        if (editor.busy || !canLeaveEditor()) return;
        setEditorBusy(true);
        generate.setAttribute("aria-busy", "true");
        recognitionMessage.textContent = "Gerando transcrição automática de teste…";
        try {
          const run = await write(`/submissions/${id}/recognitions`, { provider: provider.provider, idempotency_key: key });
          if (run.status === "FAILED") {
            const error = new Error("Reconhecedor indisponível");
            error.diagnostic = run;
            throw error;
          }
          recognitionMessage.textContent = "Transcrição criada. Aguardando conferência humana.";
          setEditorBusy(false);
          await open(id, run.transcription_id);
        } catch (error) {
          recognitionMessage.textContent = productError(error, "recognize");
        } finally {
          setEditorBusy(false);
          generate.setAttribute("aria-busy", "false");
        }
      });
    }
    if (generateButtons.length) panel.appendChild(recognition);
    const reviewer = node("input");
    reviewer.type = "text";
    reviewer.maxLength = 80;
    reviewer.value = latest?.reviewer_reference === "automatic:pending-human-review" ? "professor-teste-01" : latest?.reviewer_reference || "professor-teste-01";
    panel.appendChild(labeled("Referência do revisor (identidade não verificada)", reviewer));
    const reason = node("input");
    reason.type = "text";
    reason.maxLength = 500;
    reason.placeholder = "Ex.: corrige palavra lida incorretamente";
    panel.appendChild(labeled("Motivo da nova revisão (opcional)", reason));
    const segmentHost = node("div");
    segmentHost.className = "transcription-segments";
    const initialSegments = latest?.segments || [{ segment_id: "", page_index: 0, order: 0, kind: "mixed" }];
    for (const segment of initialSegments) segmentHost.appendChild(editableSegment(segment, pageCount, updateDirty));
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
    const discard = node("button", "Descartar alterações não salvas");
    discard.type = "button";
    discard.className = "secondary-action";
    discard.hidden = true;
    actions.appendChild(add);
    actions.appendChild(save);
    actions.appendChild(accept);
    actions.appendChild(discard);
    panel.appendChild(actions);
    const dirtyMessage = node("p");
    dirtyMessage.className = "transcription-dirty-message";
    dirtyMessage.setAttribute("role", "status");
    dirtyMessage.setAttribute("aria-live", "polite");
    panel.appendChild(dirtyMessage);
    const editorMessage = node("p");
    editorMessage.className = "transcription-message";
    editorMessage.setAttribute("role", "status");
    editorMessage.setAttribute("aria-live", "polite");
    editorMessage.id = `transcription-error-${++segmentSequence}`;
    reviewer.setAttribute("aria-describedby", editorMessage.id);
    panel.appendChild(editorMessage);
    const initialReviewer = reviewer.value;
    const fingerprint = () => JSON.stringify({
      reviewer: reviewer.value, reason: reason.value,
      segments: Array.from(segmentHost.children).map(row => ({
        id: row.dataset.segmentId,
        values: Object.fromEntries(Object.entries(row.controls).map(([key, control]) => [key, control.value])),
      })),
    });
    let baseline = fingerprint();
    const editor = {
      busy: false,
      isDirty: () => fingerprint() !== baseline,
      discard: () => {
        reviewer.value = initialReviewer;
        reviewer.setAttribute("aria-invalid", "false");
        reason.value = "";
        segmentHost.replaceChildren();
        for (const segment of initialSegments) segmentHost.appendChild(editableSegment(segment, pageCount, updateDirty));
        baseline = fingerprint();
        editorMessage.textContent = "Alterações descartadas. A revisão persistida permanece disponível.";
        updateDirty();
      },
    };
    activeEditor = editor;

    function updateDirty() {
      const dirty = editor.isDirty();
      dirtyMessage.textContent = dirty ? "Alterações não salvas. Salve uma nova revisão antes de conferir a transcrição." : "Sem alterações não salvas.";
      dirtyMessage.dataset.dirty = String(dirty);
      accept.disabled = editor.busy || dirty || !latest || latest.status === "ACCEPTED";
      accept.title = dirty ? "Salve ou descarte as alterações antes de conferir a revisão persistida." : "Conferir somente a revisão persistida";
      discard.hidden = !dirty;
      discard.disabled = editor.busy;
    }

    function setEditorBusy(busy) {
      editor.busy = busy;
      for (const control of [reviewer, reason, add, save, ...generateButtons,
        ...Array.from(segmentHost.children).flatMap(row => Object.values(row.controls))]) {
        control.disabled = busy;
      }
      for (const button of generateButtons) button.disabled = busy || !originalsIntact(data);
      updateDirty();
    }

    function validateReviewer() {
      const invalid = !reviewer.value.trim();
      reviewer.setAttribute("aria-invalid", String(invalid));
      if (invalid) {
        editorMessage.textContent = "Informe uma referência para o revisor antes de continuar.";
        reviewer.focus();
      }
      return !invalid;
    }

    reviewer.addEventListener("input", () => { reviewer.setAttribute("aria-invalid", "false"); updateDirty(); });
    reason.addEventListener("input", updateDirty);
    discard.addEventListener("click", () => { if (!editor.busy) editor.discard(); });
    updateDirty();
    add.addEventListener("click", () => {
      if (editor.busy) return;
      segmentHost.appendChild(editableSegment({ segment_id: "", page_index: 0, order: segmentHost.children.length, kind: "mixed" }, pageCount, updateDirty));
      updateDirty();
    });
    save.addEventListener("click", async () => {
      if (editor.busy || !validateReviewer()) return;
      setEditorBusy(true);
      save.setAttribute("aria-busy", "true");
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
        baseline = fingerprint();
        editorMessage.textContent = "Revisão salva. Atualizando histórico…";
        setEditorBusy(false);
        await open(id, history?.transcription.transcription_id);
      } catch (error) {
        editorMessage.textContent = productError(error, "save");
      } finally {
        setEditorBusy(false);
        save.setAttribute("aria-busy", "false");
      }
    });
    accept.addEventListener("click", async () => {
      updateDirty();
      if (editor.busy || editor.isDirty() || !latest || latest.status === "ACCEPTED") {
        editorMessage.textContent = "Salve ou descarte as alterações. A conferência usa somente uma revisão persistida.";
        return;
      }
      if (!validateReviewer()) return;
      setEditorBusy(true);
      accept.setAttribute("aria-busy", "true");
      editorMessage.textContent = "Registrando aceite de fidelidade — sem avaliar a matemática…";
      try {
        await write(`/transcriptions/${history.transcription.transcription_id}/accept`, {
          revision_number: latest.revision_number, reviewer_reference: reviewer.value.trim(), reviewer_identity_verified: false,
          acceptance_note: "Conferida visualmente com o manuscrito original.",
        });
        setEditorBusy(false);
        await open(id, history.transcription.transcription_id);
      } catch (error) {
        editorMessage.textContent = productError(error, "accept");
      } finally {
        setEditorBusy(false);
        accept.setAttribute("aria-busy", "false");
      }
    });
    if (history) renderHistory(panel, history);
  }

  async function open(id, transcriptionId = null) {
    if (!validId(id) || !canLeaveEditor()) return;
    const sequence = ++detailSequence;
    activeEditor = null;
    detail.hidden = true;
    detail.replaceChildren();
    message.textContent = "Carregando manuscrito, transcrição e integridade…";
    try {
      const [data, summaries, available] = await Promise.all([
        request(`/submissions/${id}`), request(`/submissions/${id}/transcriptions`),
        request("/submissions/recognition-providers"),
      ]);
      if (sequence !== detailSequence) return;
      if (!Array.isArray(summaries)) throw new Error("Lista de transcrições inválida.");
      const record = data.submission;
      if (record.submission_id !== id) throw new Error("Registro retornado não corresponde à submissão selecionada.");
      let history = null;
      if (summaries.length) {
        const selected = summaries.find(item => item.transcription.transcription_id === transcriptionId) || summaries[0];
        history = await request(`/transcriptions/${selected.transcription.transcription_id}`);
        if (sequence !== detailSequence) return;
        if (history.transcription.submission_id !== id) throw new Error("Transcrição pertence a outro envio.");
      }
      const heading = node("h2", `Solução recebida · ${record.problem_id}`);
      heading.tabIndex = -1;
      const back = node("button", "Voltar à fila de soluções");
      back.type = "button";
      back.className = "secondary-action";
      back.addEventListener("click", () => {
        if (!canLeaveEditor()) return;
        ++detailSequence;
        activeEditor = null;
        detail.hidden = true;
        queuePanel.hidden = false;
        message.textContent = "Fila de soluções aberta. Selecione uma solução para continuar.";
        filter.focus();
      });
      detail.appendChild(back);
      detail.appendChild(heading);
      detail.appendChild(node("p", `${statusLabel(record.status)} · ${when(record.received_at)}`)).className = "auxiliary-text";
      const technical = node("details");
      technical.className = "disclosure submission-technical";
      technical.appendChild(node("summary", "Detalhes técnicos"));
      technical.appendChild(node("p", `Número do envio: ${id}`));
      technical.appendChild(node("p", `snapshot_id: ${record.snapshot_id} · schema: ${record.capture_schema_version} · source: ${record.source}`));
      if (record.student_reference) technical.appendChild(node("p", `Referência não verificada (sem autenticação): ${record.student_reference}`));
      const workspace = node("div");
      workspace.className = "transcription-workspace";
      const original = node("section");
      original.className = "original-manuscript-panel";
      const flow = node("div");
      flow.className = "teacher-solution-flow";
      const transcription = node("section");
      transcription.className = "transcription-panel";
      renderOriginal(original, data, id);
      flow.appendChild(renderStages(history));
      if (summaries.length > 1) {
        const selection = node("select");
        summaries.forEach((item, index) => selection.appendChild(option(item.transcription.transcription_id, `Transcrição ${summaries.length - index} · ${when(item.transcription.created_at)} · ${statusLabel(item.latest_revision.status)}`)));
        selection.value = history.transcription.transcription_id;
        selection.addEventListener("change", async () => {
          const chosen = selection.value;
          selection.value = history.transcription.transcription_id;
          await open(id, chosen);
        });
        transcription.appendChild(labeled("Abrir transcrição", selection));
      }
      renderTranscription(transcription, data, id, history, Array.isArray(available) ? available : []);
      workspace.appendChild(original);
      flow.appendChild(transcription);
      const analysis = node("section");
      analysis.className = "manuscript-analysis-panel";
      analysis.setAttribute("aria-label", "Análise ConfIA desta solução");
      analysis.appendChild(node("h3", "Análise ConfIA"));
      analysis.appendChild(node("p", "○ Não executada")).className = "status";
      analysis.appendChild(node("p", "Esta solução ainda não foi encaminhada para análise matemática."));
      flow.appendChild(analysis);
      const evaluation = node("section");
      evaluation.className = "teacher-evaluation-panel";
      evaluation.appendChild(node("h3", "Avaliação do professor"));
      evaluation.appendChild(node("p", "Avaliação docente — integração em desenvolvimento."));
      flow.appendChild(evaluation);
      workspace.appendChild(flow);
      detail.appendChild(workspace);
      detail.appendChild(technical);
      detail.hidden = false;
      queuePanel.hidden = true;
      const item = queue.find(item => item.record.submission_id === id);
      if (item) { item.summaries = summaries; item.failed = false; renderQueue(); }
      message.textContent = history ? "Solução enviada e histórico de transcrição abertos." : "Solução enviada aberta. Crie uma transcrição manual fiel ao manuscrito.";
      heading.focus();
    } catch (error) {
      if (sequence === detailSequence) {
        activeEditor = null;
        detail.replaceChildren();
        detail.hidden = true;
        queuePanel.hidden = false;
        message.textContent = productError(error);
      }
    }
  }

  function renderStages(history) {
    const latest = history?.revisions?.[history.revisions.length - 1];
    const stages = node("section");
    stages.className = "teacher-workflow-stages";
    stages.setAttribute("aria-label", "Etapas desta solução");
    stages.appendChild(node("h3", "Etapas"));
    const steps = node("ol");
    const labels = [
      ["Recebimento", "✓ Recebida pelo ConfIA", true],
      ["Transcrição", latest ? `${latest.status === "ACCEPTED" ? "✓" : "○"} ${statusLabel(latest.status)}` : "○ Ainda não criada", latest?.status === "ACCEPTED"],
      ["Análise ConfIA", "○ Não executada", false],
      ["Avaliação do professor", "○ Integração em desenvolvimento", false],
    ];
    for (const [title, state, complete] of labels) {
      const step = node("li");
      step.dataset.complete = String(Boolean(complete));
      step.appendChild(node("strong", title));
      step.appendChild(node("span", state));
      steps.appendChild(step);
    }
    stages.appendChild(steps);
    return stages;
  }

  function renderQueue() {
    list.replaceChildren();
    if (!queueLoaded) return;
    const chosen = filter.value || "all";
    const visible = queue.filter(item => {
      const revision = item.summaries?.[0]?.latest_revision;
      if (item.failed || chosen === "all") return true;
      if (chosen === "uncreated") return !revision;
      if (chosen === "accepted") return revision?.status === "ACCEPTED";
      return !revision || revision.status !== "ACCEPTED";
    });
    for (const item of visible) {
      const { record, summaries, failed } = item;
      const revision = summaries?.[0]?.latest_revision;
      const transcription = failed ? "Não foi possível consultar" : revision ? statusLabel(revision.status) : "Ainda não criada";
      const button = node("button");
      button.type = "button";
      button.className = "manuscript-queue-row secondary-action";
      button.appendChild(node("strong", `Questão ${record.problem_id}`)).className = "queue-question";
      button.appendChild(node("span", when(record.received_at))).className = "submission-date";
      button.appendChild(node("span", statusLabel(record.status))).className = "queue-receipt";
      const state = node("span", revision?.status === "ACCEPTED" && !failed ? transcription : `Transcrição: ${transcription}`);
      state.className = "status queue-transcription";
      state.dataset.kind = failed ? "error" : revision?.status === "ACCEPTED" ? "success" : "warning";
      button.appendChild(state);
      button.appendChild(node("span", "Análise ConfIA: Não executada")).className = "queue-analysis";
      button.appendChild(node("span", "Abrir →")).className = "queue-open";
      button.setAttribute("aria-label", `Abrir solução da questão ${record.problem_id}, ${when(record.received_at)}. ${statusLabel(record.status)}. Transcrição: ${transcription}. Análise ConfIA: Não executada.`);
      button.addEventListener("click", () => open(record.submission_id));
      list.appendChild(button);
    }
    if (!visible.length) list.appendChild(node("p", queue.length ? "Nenhuma solução neste filtro. Consulte todos os estados da transcrição." : "Nenhuma solução recebida pelo servidor.")).className = "empty-state";
  }

  async function refresh() {
    if (!canLeaveEditor()) return;
    const sequence = ++listSequence;
    ++detailSequence;
    activeEditor = null;
    detail.hidden = true;
    detail.replaceChildren();
    list.replaceChildren();
    queuePanel.hidden = false;
    queue = [];
    queueLoaded = false;
    refreshButton.disabled = true;
    refreshButton.setAttribute("aria-busy", "true");
    message.textContent = "Carregando soluções recebidas…";
    try {
      const records = await request("/submissions");
      if (sequence !== listSequence) return;
      if (!Array.isArray(records)) throw new Error("Lista de submissões inválida.");
      const valid = records.filter(record => validId(record.submission_id));
      const summaries = await Promise.allSettled(valid.map(record => request(`/submissions/${record.submission_id}/transcriptions`)));
      if (sequence !== listSequence) return;
      queue = valid.map((record, index) => {
        const result = summaries[index];
        const failed = result.status === "rejected" || !Array.isArray(result.value);
        if (result.status === "rejected") console.error("ConfIA: resumo da transcrição", result.reason);
        return { record, summaries: failed ? [] : result.value, failed };
      });
      queueLoaded = true;
      renderQueue();
      message.textContent = valid.length ? `${valid.length} solução(ões) recebida(s) no servidor. Selecione para abrir.${queue.some(item => item.failed) ? " Alguns estados de transcrição não puderam ser consultados. Atualize a lista." : ""}` : "Nenhuma solução recebida pelo servidor.";
    } catch (error) {
      if (sequence === listSequence) message.textContent = productError(error);
    } finally {
      if (sequence === listSequence) {
        refreshButton.disabled = false;
        refreshButton.setAttribute("aria-busy", "false");
      }
    }
  }

  function mode(manuscripts) {
    if (!canLeaveEditor()) return false;
    inbox.hidden = !manuscripts;
    legacy.hidden = manuscripts;
    showInk.setAttribute("aria-pressed", String(manuscripts));
    showText.setAttribute("aria-pressed", String(!manuscripts));
    if (manuscripts && !queueLoaded && !refreshButton.disabled) refresh();
    return true;
  }
  function showView(view) {
    if (!mode(true)) return false;
    filter.value = view === "transcriptions" ? "pending" : "all";
    queueTitle.textContent = view === "transcriptions" ? "Transcrições para conferir" : view === "analysis" ? "Soluções e Análise ConfIA" : "Soluções recebidas";
    queueNote.textContent = view === "analysis" ? "Abra uma solução para consultar suas etapas. A análise matemática dos manuscritos ainda não está integrada." : "Confira a leitura com o manuscrito original. A conferência da transcrição preserva o que o aluno escreveu.";
    renderQueue();
    return true;
  }
  window.ConfIATeacher = { canLeave: canLeaveEditor, showView, showManuscripts: () => mode(true), showText: () => mode(false) };
  filter.addEventListener("change", renderQueue);
  showInk.addEventListener("click", () => mode(true));
  showText.addEventListener("click", () => mode(false));
  refreshButton.addEventListener("click", refresh);
  document.querySelector('[data-tab-target="teacher-area"]').addEventListener("click", () => { if (!document.querySelector("#teacher-area").hidden && !inbox.hidden && detail.hidden && !list.children.length) refresh(); });
  if (new URLSearchParams(location.search).get("area") === "teacher") document.querySelector('[data-tab-target="teacher-area"]').click();
  window.addEventListener("beforeunload", (event) => {
    if (activeEditor?.isDirty() || activeEditor?.busy) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
})();
