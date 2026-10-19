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
  const assessmentFilter = document.querySelector("#assessment-filter");
  const problemFilter = document.querySelector("#assessment-problem-filter");
  const queueTitle = document.querySelector("#manuscript-queue-title");
  const queueNote = document.querySelector("#manuscript-queue-note");
  let queue = [];
  let queueLoaded = false;
  let listSequence = 0;
  let detailSequence = 0;
  let segmentSequence = 0;
  let activeEditor = null;
  let activeDecision = null;
  let activeSubmissionContext = null;
  let selectedSchool = "";
  let selectedClassroom = "";
  let institutionalMode = false;
  let contextSequence = 0;
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

  const auditErrors = {
    TRANSCRIPTION_NOT_ACCEPTED: "A transcrição precisa ser conferida antes da análise.",
    SOURCE_INTEGRITY_MISMATCH: "A fonte desta análise não passou na verificação de integridade.",
    RESULT_INTEGRITY_MISMATCH: "Não foi possível validar a integridade do resultado desta análise.",
    REPRODUCIBILITY_INTEGRITY_MISMATCH: "Não foi possível validar os metadados desta análise.",
    REVISION_CONFLICT: "Existe uma revisão mais recente ou um aceite de outra revisão. Atualize a solução.",
    AUDIT_RUN_CONFLICT: "Não foi possível recuperar esta análise. Atualize a solução ou execute uma nova análise.",
  };
  const safeErrorCode = error => Object.hasOwn(auditErrors, error?.diagnostic?.error_code)
    ? error.diagnostic.error_code : null;

  function productError(error, action = "load") {
    console.error("ConfIA: manuscritos/transcrição", action, error.status, safeErrorCode(error));
    if (safeErrorCode(error)) return auditErrors[safeErrorCode(error)];
    if (action === "audit" && error.status === 409) {
      const diagnostic = String(error.diagnostic?.detail || "");
      if (/metadados|manifesto/i.test(diagnostic)) return auditErrors.REPRODUCIBILITY_INTEGRITY_MISMATCH;
      if (/integridade|arquivos originais/i.test(diagnostic)) return auditErrors.SOURCE_INTEGRITY_MISMATCH;
      if (/transcrição.*conferida/i.test(diagnostic)) return auditErrors.TRANSCRIPTION_NOT_ACCEPTED;
      if (/result_sha256/i.test(diagnostic)) return auditErrors.RESULT_INTEGRITY_MISMATCH;
      return auditErrors.AUDIT_RUN_CONFLICT;
    }
    if (/integridade da revisão ou do aceite/i.test(JSON.stringify(error.diagnostic || {}))) {
      return action === "audit" ? "A integridade da revisão ou do aceite está divergente. A análise foi bloqueada."
        : "A integridade da revisão ou do aceite está divergente. Reabra a solução para conferir o histórico.";
    }
    if (action === "audit") {
      const diagnostic = JSON.stringify(error.diagnostic || {});
      if (/arquivos originais/i.test(diagnostic)) return "Os arquivos originais desta solução precisam ser conferidos.";
      if (/transcrição.*conferida/i.test(diagnostic)) return "A transcrição precisa ser conferida antes da análise.";
      return "Não foi possível concluir a Análise ConfIA.";
    }
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
    if (activeDecision?.busy || activeDecision?.isDirty()) {
      message.textContent = activeDecision.busy ? "Aguarde a operação da decisão terminar."
        : "Salve ou descarte as alterações da decisão antes de trocar o contexto.";
      message.focus();
      return false;
    }
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
    panel.appendChild(node("h3", "Manuscrito original"));
    panel.appendChild(node("p", "Solução enviada pelo aluno."));
    const integrity = node("p", originalsIntact(data) ? "✓ Arquivos originais conferidos e preservados." : "! Os arquivos originais desta solução precisam ser conferidos.");
    integrity.className = "alert";
    integrity.dataset.kind = originalsIntact(data) ? "success" : "warning";
    if (!originalsIntact(data)) panel.appendChild(integrity);
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
    const evidence = integrityDetails(data, id);
    if (originalsIntact(data)) evidence.appendChild(integrity);
    panel.appendChild(evidence);
  }

  const orderedSegments = segments => [...segments].sort((a, b) => a.page_index - b.page_index || a.order - b.order);

  function transcriptionSource(segment) {
    // One representation per segment, shared by the reading page and source editor.
    // Mathpix latex_styled is persisted as latex; text is its fallback, never an appendix.
    // Distinct, complementary segments retain their own position in the document.
    const hasLatex = typeof segment.latex === "string" && Boolean(segment.latex.trim());
    const source = hasLatex ? segment.latex : segment.text || "";
    const bareMath = hasLatex || segment.kind === "math"
      || /^\s*\\(?:frac|sqrt|sum|int|lim|left|begin)\b/.test(source);
    const parts = globalThis.ConfiaRecognitionView.splitMathText(source, bareMath);
    // Add source delimiters only for an undelimited formula. Stored strings stay intact.
    return parts.length === 1 && parts[0].math && parts[0].value === source.trim()
      ? `\\[${source}\\]` : source;
  }

  function renderTranscriptionContent(host, segments) {
    host.replaceChildren();
    const document = node("div");
    document.className = "transcription-document";
    document.setAttribute("role", "document");
    document.setAttribute("aria-label", "Transcrição reconhecida");
    const view = globalThis.ConfiaRecognitionView;
    let count = 0;
    for (const segment of orderedSegments(segments)) {
      const source = transcriptionSource(segment);
      if (!source) continue;
      const content = node("div");
      content.className = "transcription-document-segment";
      view.renderMathText(content, source);
      document.appendChild(content);
      count++;
    }
    if (!count) document.appendChild(node("p", "Nenhuma transcrição disponível."));
    host.appendChild(document);
  }

  function renderHistory(panel, history) {
    const disclosure = node("details");
    disclosure.className = "transcription-history";
    disclosure.appendChild(node("summary", `Histórico da transcrição (${history.revisions.length} ${history.revisions.length === 1 ? "revisão" : "revisões"})`));
    for (const revision of [...history.revisions].reverse()) {
      const article = node("article");
      article.appendChild(node("h4", `Revisão ${revision.revision_number} · ${statusLabel(revision.status)}`));
      const origin = revision.source === "automatic" && revision.change_type === "initial_transcription" ? "Automática" : "Manual";
      article.appendChild(node("p", `${when(revision.created_at)} · ${origin}`));
      const content = node("details");
      content.appendChild(node("summary", "Ver revisão"));
      if (revision.change_reason) content.appendChild(node("p", `Motivo: ${revision.change_reason}`));
      const items = node("div");
      renderTranscriptionContent(items, revision.segments);
      content.appendChild(items);
      const technical = node("details");
      technical.appendChild(node("summary", "Detalhes técnicos da revisão"));
      technical.appendChild(node("pre", JSON.stringify(revision, null, 2)));
      content.appendChild(technical);
      article.appendChild(content);
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
    panel.appendChild(node("h3", "Transcrição reconhecida"));
    const visual = node("div");
    visual.className = "transcription-visual";
    panel.appendChild(visual);
    const revisionStatus = node("p", latest ? latest.status === "ACCEPTED" ? "Transcrição conferida" : "Transcrição a conferir" : "Transcrição: ainda não criada");
    revisionStatus.className = "transcription-status status";
    revisionStatus.dataset.kind = latest?.status === "ACCEPTED" ? "success" : "pending";
    const supportingDetails = node("div");
    if (latest?.recognizer_run_id) {
      const origin = node("details");
      origin.appendChild(node("summary", `Detalhes do reconhecimento${latest.provider === "fake_test" ? " — teste artificial" : ""}`));
      if (latest.provider === "fake_test") origin.appendChild(node("p", "Transcrição de teste artificial. Conteúdo constante; não é OCR real. Confira cada segmento com o original."));
      origin.appendChild(node("p", `Origem automática · provider: ${latest.provider} · execução: ${latest.recognizer_run_id} · adapter: ${latest.recognizer} ${latest.recognizer_version}`));
      origin.appendChild(node("p", "Proveniência do reconhecimento do manuscrito"));
      origin.appendChild(node("pre", JSON.stringify(latest.provenance || history.transcription.provenance || {}, null, 2)));
      supportingDetails.appendChild(origin);
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
    if (generateButtons.length) supportingDetails.appendChild(recognition);
    const editing = node("div");
    editing.className = "transcription-editor";
    editing.hidden = true;
    editing.id = `transcription-editor-${++segmentSequence}`;
    editing.appendChild(node("h4", "Editar transcrição"));
    const edit = node("button", "Editar transcrição");
    edit.type = "button";
    edit.className = "secondary-action";
    edit.setAttribute("aria-controls", editing.id);
    edit.setAttribute("aria-expanded", "false");
    function showEditor(visible) {
      editing.hidden = !visible;
      visual.hidden = visible;
      actions.hidden = visible;
      edit.setAttribute("aria-expanded", String(visible));
      if (visible) {
        editorMessage.textContent = "";
        sourceEditor.focus();
      }
    }
    edit.addEventListener("click", () => { if (!editor.busy) showEditor(true); });
    const initialSegments = latest?.segments || [];
    const drafts = Array.from({ length: pageCount }, (_, pageIndex) => {
      const segments = orderedSegments(initialSegments.filter(segment => segment.page_index === pageIndex));
      // Textareas normalize line endings. Compare their normalized projection, but
      // send the untouched original segments when a page's source was not edited.
      const initial = segments.map(transcriptionSource).join("\n\n").replace(/\r\n?/g, "\n");
      return { pageIndex, segments, initial, source: initial };
    });
    let selectedPage = 0;
    const pageSelect = node("select");
    pageSelect.className = "transcription-source-page";
    for (const draft of drafts) pageSelect.appendChild(option(String(draft.pageIndex), `Página ${draft.pageIndex + 1}`));
    pageSelect.value = "0";
    if (pageCount > 1) editing.appendChild(labeled("Página da transcrição", pageSelect));
    const sourceEditor = node("textarea");
    sourceEditor.className = "transcription-source";
    sourceEditor.rows = 16;
    sourceEditor.spellcheck = false;
    sourceEditor.placeholder = "Texto-fonte com matemática entre delimitadores LaTeX";
    sourceEditor.value = drafts[selectedPage].source;
    editing.appendChild(labeled("Texto-fonte da transcrição", sourceEditor));
    pageSelect.addEventListener("change", () => {
      if (editor.busy) return;
      selectedPage = Number(pageSelect.value);
      sourceEditor.value = drafts[selectedPage].source;
    });
    sourceEditor.addEventListener("input", () => {
      if (editor.busy) return;
      drafts[selectedPage].source = sourceEditor.value;
      updateDirty();
    });
    function collectSegments() {
      return drafts.flatMap(draft => {
        if (draft.source === draft.initial && draft.segments.length) return draft.segments;
        if (!draft.source && drafts.some(page => page.source)) return [];
        // A manual page has one source. Do not carry an obsolete alternate latex
        // field or measured segment coordinates into the newly edited document.
        return [{ segment_id: `manual:${Date.now()}:${++segmentSequence}`, page_index: draft.pageIndex,
          order: 0, kind: "mixed", text: draft.source || null, latex: null }];
      });
    }
    const reviewer = node("input");
    reviewer.type = "text";
    reviewer.maxLength = 80;
    reviewer.value = latest?.reviewer_reference === "automatic:pending-human-review" ? "professor-teste-01" : latest?.reviewer_reference || "professor-teste-01";
    editing.appendChild(labeled("Referência do revisor (identidade não verificada)", reviewer));
    const reason = node("input");
    reason.type = "text";
    reason.maxLength = 500;
    reason.placeholder = "Ex.: corrige palavra lida incorretamente";
    editing.appendChild(labeled("Motivo da nova revisão (opcional)", reason));
    panel.appendChild(editing);
    const actions = node("div");
    actions.className = "transcription-actions";
    const save = node("button", "Salvar nova versão");
    save.type = "button";
    save.className = "primary-action";
    const accept = node("button", "Conferir transcrição");
    accept.type = "button";
    accept.className = "secondary-action";
    const fidelityHelp = "Conferir confirma somente a fidelidade ao manuscrito; não significa solução correta nem avaliação do professor.";
    accept.setAttribute("aria-description", fidelityHelp);
    accept.disabled = !latest || latest.status === "ACCEPTED";
    const discard = node("button", "Cancelar");
    discard.type = "button";
    discard.className = "secondary-action";
    const editActions = node("div");
    editActions.className = "transcription-actions";
    editActions.appendChild(discard);
    editActions.appendChild(save);
    editing.appendChild(editActions);
    actions.appendChild(edit);
    actions.appendChild(accept);
    panel.appendChild(actions);
    panel.appendChild(revisionStatus);
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
      pages: drafts.map(draft => draft.source),
    });
    let baseline = fingerprint();
    const editor = {
      busy: false,
      isDirty: () => fingerprint() !== baseline,
      discard: () => {
        reviewer.value = initialReviewer;
        reviewer.setAttribute("aria-invalid", "false");
        reason.value = "";
        for (const draft of drafts) draft.source = draft.initial;
        sourceEditor.value = drafts[selectedPage].source;
        baseline = fingerprint();
        editorMessage.textContent = "Alterações descartadas. A revisão persistida permanece disponível.";
        updateDirty();
        showEditor(false);
        edit.focus();
      },
    };
    activeEditor = editor;

    function updateDirty() {
      const dirty = editor.isDirty();
      dirtyMessage.textContent = dirty ? "Alterações não salvas. Salve uma nova revisão antes de conferir a transcrição." : "";
      dirtyMessage.hidden = !dirty;
      dirtyMessage.dataset.dirty = String(dirty);
      accept.disabled = editor.busy || dirty || !latest || latest.status === "ACCEPTED";
      accept.title = dirty ? "Salve ou descarte as alterações antes de conferir a revisão persistida." : fidelityHelp;
      discard.disabled = editor.busy;
      editor.onChange?.();
    }

    function setEditorBusy(busy) {
      editor.busy = busy;
      for (const control of [reviewer, reason, save, edit, sourceEditor, pageSelect, ...generateButtons]) {
        control.disabled = busy;
      }
      for (const button of generateButtons) button.disabled = busy || !originalsIntact(data);
      updateDirty();
    }
    editor.setBusy = setEditorBusy;

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
    renderTranscriptionContent(visual, initialSegments);
    updateDirty();
    save.addEventListener("click", async () => {
      if (editor.busy || !validateReviewer()) return;
      const tooLong = drafts.find(draft => draft.source !== draft.initial && draft.source.length > 20000);
      if (tooLong) {
        editorMessage.textContent = `A página ${tooLong.pageIndex + 1} excede o limite de 20.000 caracteres para uma edição. O texto ainda não foi salvo.`;
        return;
      }
      setEditorBusy(true);
      save.setAttribute("aria-busy", "true");
      editorMessage.textContent = latest ? "Salvando nova revisão sem alterar a anterior…" : "Criando transcrição manual…";
      try {
        const common = { reviewer_reference: reviewer.value.trim(), reviewer_identity_verified: false, segments: collectSegments(), status: "NEEDS_REVIEW" };
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
        if (!detail.hidden) message.textContent = "Transcrição salva. A nova versão aguarda conferência.";
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
        if (!detail.hidden) message.textContent = "Transcrição conferida. A revisão está disponível para análise.";
      } catch (error) {
        editorMessage.textContent = productError(error, "accept");
      } finally {
        setEditorBusy(false);
        accept.setAttribute("aria-busy", "false");
      }
    });
    if (history) renderHistory(panel, history);
    panel.appendChild(supportingDetails);
    return editor;
  }

  function runIsStale(run, latest) {
    return run.stale || run.transcription_id !== latest?.transcription_id
      || run.revision_number !== latest?.revision_number || latest?.status !== "ACCEPTED";
  }

  function analysisLabel(runs, latest, failed = false, attemptState = null) {
    if (attemptState === "CONFLICT") return "Conflito — atualize a solução";
    if (attemptState === "FAILED") return "Não foi possível concluir";
    if (failed) return "Não foi possível consultar";
    const run = runs?.[0];
    if (!run) return "Não executada";
    if (runIsStale(run, latest)) return "Transcrição anterior";
    return run.status === "COMPLETED" ? "Concluída" : "Não foi possível concluir";
  }

  function renderAnalysis(panel, data, id, history, initialRuns, editor, stages, loadError = null, onRunChange = () => {}) {
    const latest = history?.revisions?.[history.revisions.length - 1];
    const acceptance = history?.acceptances?.find(item => item.revision_number === latest?.revision_number
      && item.transcription_id === latest.transcription_id && item.submission_id === id
      && /^acc_[0-9a-f]{32}$/.test(item.acceptance_id));
    const accepted = latest?.status === "ACCEPTED" && /^[0-9a-f]{64}$/.test(acceptance?.accepted_revision_sha256 || "");
    let runs = initialRuns || [];
    let selectedId = runs[0]?.audit_run_id;
    let executionKey = null;
    let attemptState = loadError ? (loadError.status === 409 ? "CONFLICT" : "FAILED") : null;
    let attemptMessage = loadError ? productError(loadError, "audit") : "";
    let attemptErrorCode = safeErrorCode(loadError);
    const isStale = run => runIsStale(run, latest) || run.acceptance_id !== acceptance?.acceptance_id;
    const historicalLabel = run => isStale(run) ? "Análise de uma versão anterior"
      : attemptState === "CONFLICT" ? "Análise anterior indisponível"
        : attemptState === "FAILED" ? "Análise anterior desta revisão" : null;
    panel.setAttribute("aria-label", "Análise ConfIA desta solução");
    panel.appendChild(node("h3", "Análise ConfIA"));
    const state = node("p");
    state.className = "status";
    state.setAttribute("role", "status");
    state.setAttribute("aria-live", "polite");
    panel.appendChild(state);
    const action = node("button", "Executar Análise ConfIA");
    action.type = "button";
    action.className = "primary-action";
    panel.appendChild(action);
    const rerun = node("button", "Executar novamente");
    rerun.type = "button";
    rerun.className = "secondary-action";
    panel.appendChild(rerun);
    const guidance = node("p");
    panel.appendChild(guidance);
    if (history?.acceptances?.some(item => item.revision_number === latest?.revision_number
        && !item.accepted_revision_sha256)) {
      panel.appendChild(node("p", "Aceite anterior sem vínculo de integridade. Crie e confira uma nova revisão antes da análise.")).className = "transcription-warning";
    }
    const selection = node("select");
    const selectionLabel = labeled("Histórico das análises", selection);
    panel.appendChild(selectionLabel);
    const result = node("div");
    panel.appendChild(result);

    function updateControls() {
      action.disabled = editor.busy || editor.isDirty() || !accepted || !originalsIntact(data) || initialRuns === null || attemptState === "CONFLICT";
      const current = runs.find(run => run.transcription_id === latest?.transcription_id && run.revision_number === latest?.revision_number);
      rerun.hidden = !current;
      rerun.disabled = action.disabled;
      selection.disabled = editor.busy;
      guidance.textContent = attemptState === "CONFLICT" ? attemptMessage
        : !originalsIntact(data) ? "Os arquivos originais desta solução precisam ser conferidos."
        : !accepted ? "A transcrição precisa ser conferida antes da análise."
          : editor.isDirty() ? "Salve ou descarte as alterações antes de analisar a revisão conferida."
            : "A análise usa somente a revisão persistida e conferida. Nota e resultado são sugestões para o professor.";
    }
    editor.onChange = updateControls;

    function showRuns() {
      selection.replaceChildren();
      for (const run of runs) selection.appendChild(option(run.audit_run_id, `Revisão ${run.revision_number} · ${when(run.created_at)} · ${historicalLabel(run) || (run.status === "COMPLETED" ? "Concluída" : "Não foi possível concluir")}`));
      selection.value = selectedId || "";
      selectionLabel.hidden = runs.length === 0;
      result.replaceChildren();
      const run = runs.find(item => item.audit_run_id === selectedId) || runs[0];
      state.textContent = attemptState ? attemptMessage
        : initialRuns === null ? "Não foi possível consultar as análises. Reabra a solução."
          : run ? isStale(run) ? "Análise de uma versão anterior" : run.status === "COMPLETED" ? "✓ Concluída" : "Não foi possível concluir a Análise ConfIA." : "○ Não executada";
      state.dataset.kind = attemptState || initialRuns === null || run?.status === "FAILED" ? "error"
        : run && !isStale(run) ? "success" : "neutral";
      if (!run) result.appendChild(node("p", "Esta solução ainda não foi encaminhada para análise matemática.")).className = "empty-state";
      else {
        if (attemptState || isStale(run)) result.appendChild(node("p", attemptState
          ? `${historicalLabel(run)}. Disponível somente como histórico.`
          : "Esta análise corresponde a uma versão anterior. Disponível somente como histórico.")).className = "transcription-warning";
        if (run.source.provenance?.revision?.provider === "fake_test") result.appendChild(node("p", "Análise baseada em transcrição de teste artificial; não é reconhecimento real do manuscrito.")).className = "transcription-warning";
        result.appendChild(node("p", `Análise da revisão ${run.revision_number} · conferida em ${when(run.source.accepted_at)}`));
        for (const warning of run.source.warnings || []) result.appendChild(node("p", `Página ${warning.page_index + 1}: ${warning.message}`)).className = "transcription-warning";
        if (attemptState !== "CONFLICT" && run.status === "COMPLETED" && run.result) {
          const report = node("div");
          window.ConfIAReport.render(run.result, report, { context: "teacher" });
          result.appendChild(report);
        }
        const source = node("details");
        source.appendChild(node("summary", "Fonte e rastreabilidade da análise"));
        source.appendChild(node("pre", JSON.stringify(run, window.ConfIAReport.publicTechnicalValue, 2)));
        result.appendChild(source);
      }
      if (attemptErrorCode) {
        const diagnostic = node("details");
        diagnostic.appendChild(node("summary", "Detalhes técnicos da falha"));
        diagnostic.appendChild(node("code", attemptErrorCode));
        result.appendChild(diagnostic);
      }
      stages.replaceChildren(...renderStages(history, runs, attemptState).children);
      onRunChange(run, Boolean(run && !isStale(run) && attemptState !== "CONFLICT"));
      const item = queue.find(item => item.record.submission_id === id);
      if (item) { item.audits = runs; item.auditFailed = initialRuns === null; item.auditAttemptState = attemptState; renderQueue(); }
      updateControls();
    }
    selection.addEventListener("change", () => { selectedId = selection.value; showRuns(); });

    async function execute(again) {
      updateControls();
      if (action.disabled) return;
      // Keep a rerun key on transport failure, so retry still deduplicates.
      if (again && executionKey === null) executionKey = `teacher:${Date.now()}:${++segmentSequence}`;
      editor.setBusy(true);
      action.setAttribute("aria-busy", "true");
      state.textContent = "Analisando solução...";
      try {
        const run = await write(`/submissions/${id}/audits`, {
          transcription_id: latest.transcription_id, revision_number: latest.revision_number,
          acceptance_id: acceptance.acceptance_id, ...(executionKey ? { execution_key: executionKey } : {}),
        });
        if (run.submission_id !== id || run.transcription_id !== latest.transcription_id || run.revision_number !== latest.revision_number
            || run.acceptance_id !== acceptance.acceptance_id || !["COMPLETED", "FAILED"].includes(run.status)) throw new Error("Resultado sem vínculo válido");
        runs = [run, ...runs.filter(item => item.audit_run_id !== run.audit_run_id)];
        selectedId = run.audit_run_id;
        executionKey = null;
        attemptState = null;
        attemptMessage = "";
        attemptErrorCode = null;
        showRuns();
      } catch (error) {
        attemptState = error.status === 409 ? "CONFLICT" : "FAILED";
        attemptMessage = productError(error, "audit");
        attemptErrorCode = safeErrorCode(error);
        showRuns();
      } finally {
        editor.setBusy(false);
        action.setAttribute("aria-busy", "false");
      }
    }
    action.addEventListener("click", () => execute(false));
    rerun.addEventListener("click", () => execute(true));
    showRuns();
  }

  function selectedName(selector, id) {
    return Array.from(document.querySelector(selector)?.children || []).find(option => option.value === id)?.textContent || "";
  }

  async function displayContext(record) {
    if (!record.assessment_id || !record.classroom_id || !record.school_id) return null;
    const [assessment, students] = await Promise.allSettled([
      request(`/assessments/${encodeURIComponent(record.assessment_id)}`),
      request(`/institutional/classrooms/${encodeURIComponent(record.classroom_id)}/students`),
    ]);
    const view = assessment.status === "fulfilled" && assessment.value?.assessment?.assessment_id === record.assessment_id
      ? assessment.value : null;
    const item = view?.items?.find(item => item.assessment_item_id === record.assessment_item_id && item.problem_id === record.problem_id);
    const student = students.status === "fulfilled" && Array.isArray(students.value)
      ? students.value.find(student => student.user_id === record.submitted_by_user_id) : null;
    return { submissionId: record.submission_id, assessmentId: record.assessment_id, assessmentItemId: record.assessment_item_id,
      problemId: record.problem_id, studentId: record.submitted_by_user_id,
      assessmentTitle: view?.assessment.title || "Avaliação indisponível", studentName: student?.display_name || "Aluno indisponível",
      questionOrder: item?.order, schoolName: selectedName("#teacher-school-select", record.school_id) || "Escola do envio",
      classroomName: view?.classroom_name || selectedName("#teacher-classroom-select", record.classroom_id) || "Turma do envio" };
  }

  async function open(id, transcriptionId = null, examContext = activeSubmissionContext) {
    if (!validId(id) || !canLeaveEditor()) return;
    if (examContext?.submissionId !== id) examContext = null;
    const sequence = ++detailSequence;
    activeEditor = null;
    activeDecision = null;
    activeSubmissionContext = null;
    detail.hidden = true;
    detail.replaceChildren();
    message.textContent = "Carregando manuscrito, transcrição e integridade…";
    try {
      let auditLoadError = null;
      const [data, summaries, available, auditResult] = await Promise.all([
        request(`/submissions/${id}`), request(`/submissions/${id}/transcriptions`),
        request("/submissions/recognition-providers"),
        request(`/submissions/${id}/audits`).catch(error => { auditLoadError = error; return null; }),
      ]);
      if (sequence !== detailSequence) return;
      if (!Array.isArray(summaries)) throw new Error("Lista de transcrições inválida.");
      const record = data.submission;
      if (record.submission_id !== id) throw new Error("Registro retornado não corresponde à submissão selecionada.");
      if (examContext && (examContext.assessmentId !== record.assessment_id
        || examContext.assessmentItemId !== record.assessment_item_id
        || examContext.studentId !== record.submitted_by_user_id || examContext.problemId !== record.problem_id)) {
        throw new Error("A solução retornada não corresponde à avaliação, ao aluno e à questão selecionados.");
      }
      if (!examContext) examContext = await displayContext(record);
      if (sequence !== detailSequence) return;
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
        activeDecision = null;
        activeSubmissionContext = null;
        detail.hidden = true;
        queuePanel.hidden = false;
        message.textContent = "Fila de soluções aberta. Selecione uma solução para continuar.";
        filter.focus();
      });
      detail.appendChild(back);
      detail.appendChild(heading);
      if (examContext) {
        const context = node("dl");
        context.className = "submission-context";
        context.setAttribute("aria-label", "Contexto da correção");
        for (const [label, value] of [
          ["Escola", examContext.schoolName || selectedName("#teacher-school-select", record.school_id)],
          ["Turma", examContext.classroomName || selectedName("#teacher-classroom-select", record.classroom_id)],
          ["Avaliação", examContext.assessmentTitle], ["Aluno", examContext.studentName],
          ["Questão", examContext.questionOrder ? `Q${examContext.questionOrder} · ${record.problem_id}` : record.problem_id]]) {
          if (!value) continue;
          const entry = node("div");
          entry.appendChild(node("dt", label));
          entry.appendChild(node("dd", value));
          context.appendChild(entry);
        }
        detail.appendChild(context);
        activeSubmissionContext = examContext;
      }
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
      const transcription = node("section");
      transcription.className = "transcription-panel";
      renderOriginal(original, data, id);
      const audits = Array.isArray(auditResult) ? auditResult : null;
      const stages = renderStages(history, audits);
      detail.appendChild(stages);
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
      const editor = renderTranscription(transcription, data, id, history, Array.isArray(available) ? available : []);
      workspace.appendChild(original);
      workspace.appendChild(transcription);
      detail.appendChild(workspace);
      const analysis = node("section");
      analysis.className = "manuscript-analysis-panel";
      const evaluation = node("section");
      const decisionController = window.ConfIADecisions.mount(evaluation, record, decision => {
        if (sequence !== detailSequence) return;
        const item = queue.find(item => item.record.submission_id === id);
        if (item) { item.decision = decision; renderQueue(); }
        updateDecisionStage(stages, decision);
      });
      activeDecision = decisionController;
      renderAnalysis(analysis, data, id, history, audits, editor, stages, auditLoadError,
        (run, usable) => {
          decisionController.setOpenedRun(run, usable);
          updateDecisionStage(stages, decisionController.decision);
        });
      detail.appendChild(analysis);
      detail.appendChild(evaluation);
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
        activeDecision = null;
        activeSubmissionContext = null;
        detail.replaceChildren();
        detail.hidden = true;
        queuePanel.hidden = false;
        message.textContent = productError(error);
      }
    }
  }

  function updateDecisionStage(stages, decision) {
    const step = stages.children[1]?.children[3];
    if (step) {
      step.children[1].textContent = window.ConfIADecisions.decisionLabel(decision);
      step.dataset.complete = String(Boolean(decision && decision.status !== "DRAFT"));
      step.children[1].dataset.kind = decision?.status === "RELEASED" ? "success" : decision?.status === "DRAFT" ? "pending" : decision ? "info" : "neutral";
    }
  }

  function renderStages(history, runs = [], attemptState = null) {
    const latest = history?.revisions?.[history.revisions.length - 1];
    const stages = node("section");
    stages.className = "teacher-workflow-stages";
    stages.setAttribute("aria-label", "Etapas desta solução");
    stages.appendChild(node("h3", "Etapas"));
    const steps = node("ol");
    const labels = [
      ["Recebimento", "✓ Recebida pelo ConfIA", true],
      ["Transcrição", latest ? `${latest.status === "ACCEPTED" ? "✓" : "○"} ${statusLabel(latest.status)}` : "○ Ainda não criada", latest?.status === "ACCEPTED"],
      ["Análise ConfIA", analysisLabel(runs, latest, runs === null, attemptState), analysisLabel(runs, latest, runs === null, attemptState) === "Concluída"],
      ["Decisão do professor", "○ Aguardando decisão", false],
    ];
    for (const [title, state, complete] of labels) {
      const step = node("li");
      step.dataset.complete = String(Boolean(complete));
      step.appendChild(node("strong", title));
      const badge = step.appendChild(node("span", state));
      badge.className = "status";
      badge.dataset.kind = complete ? "success" : "neutral";
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
      if (assessmentFilter.value && assessmentFilter.value !== "all" && item.record.assessment_id !== assessmentFilter.value) return false;
      if (problemFilter.value && problemFilter.value !== "all" && item.record.problem_id !== problemFilter.value) return false;
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
      const analysis = analysisLabel(item.audits, revision, item.auditFailed, item.auditAttemptState);
      button.appendChild(node("span", `Análise ConfIA: ${analysis}`)).className = "queue-analysis";
      if (item.decision) button.appendChild(node("span", window.ConfIADecisions.decisionLabel(item.decision))).className = "queue-decision";
      button.appendChild(node("span", "Abrir →")).className = "queue-open";
      button.setAttribute("aria-label", `Abrir solução da questão ${record.problem_id}, ${when(record.received_at)}. ${statusLabel(record.status)}. Transcrição: ${transcription}. Análise ConfIA: ${analysis}.${item.decision ? ` ${window.ConfIADecisions.decisionLabel(item.decision)}.` : ""}`);
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
    activeDecision = null;
    activeSubmissionContext = null;
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
      const scope = institutionalMode ? `?school_id=${encodeURIComponent(selectedSchool)}&classroom_id=${encodeURIComponent(selectedClassroom)}` : "";
      const records = institutionalMode && !selectedClassroom ? [] : await request(`/submissions${scope}`);
      if (sequence !== listSequence) return;
      if (!Array.isArray(records)) throw new Error("Lista de submissões inválida.");
      const valid = records.filter(record => validId(record.submission_id));
      const [summaries, audits, decisions, assessments] = await Promise.all([
        Promise.allSettled(valid.map(record => request(`/submissions/${record.submission_id}/transcriptions`))),
        Promise.allSettled(valid.map(record => request(`/submissions/${record.submission_id}/audits`))),
        Promise.allSettled(valid.map(record => record.assessment_id
          ? request(`/submissions/${record.submission_id}/teacher-decision`) : Promise.resolve(null))),
        valid.some(record => record.assessment_id) ? request(`/assessments${scope}`).catch(() => []) : [],
      ]);
      if (sequence !== listSequence) return;
      queue = valid.map((record, index) => {
        const result = summaries[index];
        const failed = result.status === "rejected" || !Array.isArray(result.value);
        if (result.status === "rejected") console.error("ConfIA: resumo da transcrição", result.reason?.status, safeErrorCode(result.reason));
        const audit = audits[index];
        const auditFailed = audit.status === "rejected" || !Array.isArray(audit.value);
        const decision = decisions[index].status === "fulfilled" ? decisions[index].value : null;
        return { record, summaries: failed ? [] : result.value, failed, audits: auditFailed ? [] : audit.value, auditFailed, decision };
      });
      const selectedAssessment = assessmentFilter.value;
      const selectedProblem = problemFilter.value;
      const assessmentNames = new Map((Array.isArray(assessments) ? assessments : [])
        .filter(view => view.assessment && (!institutionalMode || (view.assessment.school_id === selectedSchool
          && view.assessment.classroom_id === selectedClassroom)))
        .map(view => [view.assessment.assessment_id, view.assessment.title]));
      assessmentFilter.replaceChildren(option("all", "Todos os exames"));
      for (const assessmentId of [...new Set(valid.map(record => record.assessment_id).filter(Boolean))]) {
        assessmentFilter.appendChild(option(assessmentId, assessmentNames.get(assessmentId) || `Avaliação indisponível · ${assessmentFilter.children.length}`));
      }
      if ([...assessmentFilter.children].some(item => item.value === selectedAssessment)) assessmentFilter.value = selectedAssessment;
      problemFilter.replaceChildren(option("all", "Todas as questões"));
      for (const problemId of [...new Set(valid.map(record => record.problem_id))]) problemFilter.appendChild(option(problemId, problemId));
      if ([...problemFilter.children].some(item => item.value === selectedProblem)) problemFilter.value = selectedProblem;
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
    const reopeningInbox = inbox.hidden;
    inbox.hidden = !manuscripts;
    legacy.hidden = manuscripts;
    showInk.setAttribute("aria-pressed", String(manuscripts));
    showText.setAttribute("aria-pressed", String(!manuscripts));
    if (manuscripts && (reopeningInbox || !queueLoaded) && !refreshButton.disabled) refresh();
    return true;
  }
  function showView(view) {
    if (view === "students") {
      if (!canLeaveEditor()) return false;
      ++listSequence; ++detailSequence;
      queueLoaded = false; activeEditor = null; activeDecision = null;
      detail.hidden = true; detail.replaceChildren();
      inbox.hidden = false; legacy.hidden = true;
      showInk.setAttribute("aria-pressed", "true");
      showText.setAttribute("aria-pressed", "false");
    } else if (!mode(true)) return false;
    document.querySelector("#teacher-students-panel").hidden = view !== "students";
    document.querySelector("#teacher-queue-header").hidden = view === "students";
    queuePanel.hidden = view === "students";
    if (view === "students") {
      showStudents();
      return true;
    }
    filter.value = view === "transcriptions" ? "pending" : "all";
    queueTitle.textContent = view === "transcriptions" ? "Transcrições para conferir" : view === "analysis" ? "Soluções e Análise ConfIA" : "Soluções recebidas";
    queueNote.textContent = view === "analysis" ? "Abra uma solução para consultar a Análise ConfIA e registrar a decisão do professor." : "Confira a leitura com o manuscrito original. A conferência da transcrição preserva o que o aluno escreveu.";
    renderQueue();
    return true;
  }
  async function showStudents() {
    const panel = document.querySelector("#teacher-students-panel");
    panel.replaceChildren(node("h2", "Alunos da turma"));
    if (!selectedSchool || !selectedClassroom) { panel.appendChild(node("p", "Selecione uma turma.")); return; }
    const sequence = ++contextSequence;
    try {
      const scope = `?school_id=${encodeURIComponent(selectedSchool)}&classroom_id=${encodeURIComponent(selectedClassroom)}`;
      const [students, assessments, records] = await Promise.all([
        request(`/institutional/classrooms/${encodeURIComponent(selectedClassroom)}/students`),
        request(`/assessments${scope}`), request(`/submissions${scope}`),
      ]);
      if (sequence !== contextSequence) return;
      if (![students, assessments, records].every(Array.isArray)) throw new Error("Listas da turma inválidas.");
      const exams = assessments.filter(view => view.assessment?.status !== "DRAFT"
        && view.assessment?.school_id === selectedSchool
        && view.assessment?.classroom_id === selectedClassroom);
      const enrolled = new Set(students.map(student => student.user_id));
      const visible = records.filter(record => enrolled.has(record.submitted_by_user_id)
        && record.school_id === selectedSchool && record.classroom_id === selectedClassroom
        && validId(record.submission_id));
      const [summaries, progress] = await Promise.all([
        Promise.allSettled(visible.map(record => request(`/submissions/${record.submission_id}/transcriptions`))),
        Promise.allSettled(exams.map(view => request(`/assessments/${view.assessment.assessment_id}/progress`))),
      ]);
      if (sequence !== contextSequence) return;
      const revisions = new Map(visible.map((record, index) => [record.submission_id,
        summaries[index].status === "fulfilled" && Array.isArray(summaries[index].value)
          ? summaries[index].value[0]?.latest_revision : null]));
      const correctionStatuses = new Map();
      for (const response of progress) if (response.status === "fulfilled") {
        for (const student of response.value.students || []) {
          for (const [itemId, submissionId] of Object.entries(student.submissions)) {
            correctionStatuses.set(submissionId, student.correction_statuses?.[itemId]);
          }
        }
      }
      const openStudentSubmission = submissionId => {
        window.ConfIAShell?.navigate("teacher", "submissions");
        window.ConfIATeacher?.openSubmission(submissionId);
      };
      function addDelivery(container, record) {
        container.appendChild(node("span", record ? "Enviada" : "Não enviada"));
        if (!record) return;
        const correction = correctionStatuses.get(record.submission_id);
        const status = revisions.get(record.submission_id)?.status;
        if (correction && correction !== "SUBMITTED") container.appendChild(node("span", window.ConfIADecisions.labels[correction]));
        else if (status === "NEEDS_REVIEW") container.appendChild(node("span", "Transcrição em conferência"));
        else if (status === "ACCEPTED") container.appendChild(node("span", "Transcrição aceita"));
        const button = node("button", "Abrir solução");
        button.type = "button";
        button.className = "button button-primary";
        button.addEventListener("click", () => openStudentSubmission(record.submission_id));
        container.appendChild(button);
      }
      if (!students.length) panel.appendChild(node("p", "Nenhum aluno matriculado nesta turma."));
      for (const student of students) {
        const card = node("article");
        card.className = "teacher-student-card";
        card.appendChild(node("h3", student.display_name));
        const deliveries = visible.filter(record => record.submitted_by_user_id === student.user_id);
        for (const view of exams) {
          const group = node("section");
          group.className = "teacher-student-assessment";
          group.appendChild(node("h4", view.assessment.title));
          const items = node("ul");
          for (const item of [...view.items].sort((a, b) => a.order - b.order)) {
            const row = node("li");
            row.className = "teacher-student-item";
            row.appendChild(node("strong", `Questão ${item.order} · ${item.problem_id} · ${Number(item.points).toLocaleString("pt-BR")} ${item.points === 1 ? "ponto" : "pontos"}`));
            const record = deliveries.find(entry => entry.assessment_id === view.assessment.assessment_id
              && entry.assessment_item_id === item.assessment_item_id && entry.problem_id === item.problem_id);
            addDelivery(row, record);
            items.appendChild(row);
          }
          group.appendChild(items);
          card.appendChild(group);
        }
        const legacy = deliveries.filter(record => !record.assessment_id);
        if (legacy.length) {
          const group = node("section");
          group.className = "teacher-student-assessment";
          group.appendChild(node("h4", "Envios anteriores / sem avaliação vinculada"));
          const items = node("ul");
          for (const record of legacy) {
            const row = node("li");
            row.className = "teacher-student-item";
            row.appendChild(node("strong", `Questão ${record.problem_id}`));
            addDelivery(row, record);
            items.appendChild(row);
          }
          group.appendChild(items);
          card.appendChild(group);
        }
        if (!exams.length && !legacy.length) card.appendChild(node("p", "Nenhuma avaliação ou envio nesta turma."));
        panel.appendChild(card);
      }
    } catch (error) { if (sequence === contextSequence) panel.appendChild(node("p", "Não foi possível carregar os alunos.")); }
  }
  function clearInstitutionalQueue() {
    ++listSequence; ++detailSequence; ++contextSequence;
    queue = []; queueLoaded = false; activeEditor = null; activeDecision = null;
    activeSubmissionContext = null;
    list.replaceChildren(); detail.replaceChildren(); detail.hidden = true;
    message.textContent = selectedClassroom ? "Carregando turma…" : "Selecione uma turma.";
    if (!document.querySelector("#teacher-exams").hidden) window.ConfIAAssessments?.load();
    if (!document.querySelector("#teacher-students-panel").hidden) showStudents();
    else if (!inbox.hidden && selectedClassroom) refresh();
  }
  async function initInstitutional(user) {
    if (!user || user.role !== "TEACHER") return;
    institutionalMode = true;
    const box = document.querySelector("#teacher-institutional-context");
    const schoolSelect = document.querySelector("#teacher-school-select");
    const classroomSelect = document.querySelector("#teacher-classroom-select");
    const status = document.querySelector("#teacher-context-message");
    box.hidden = false;
    document.querySelector("#teacher-context-name").textContent = /^professor(a)?\b/i.test(user.display_name)
      ? user.display_name : `Professor ${user.display_name}`;
    function fill(select, items, key, label, placeholder) {
      select.replaceChildren(option("", placeholder));
      for (const item of items) select.appendChild(option(item[key], item[label]));
    }
    async function loadClasses() {
      if (!canLeaveEditor()) { schoolSelect.value = selectedSchool; return; }
      selectedSchool = schoolSelect.value;
      selectedClassroom = "";
      fill(classroomSelect, [], "classroom_id", "name", "Selecione a turma");
      clearInstitutionalQueue();
      if (!selectedSchool) return;
      const sequence = ++contextSequence;
      try {
        const classes = await request(`/institutional/schools/${encodeURIComponent(selectedSchool)}/classrooms`);
        if (sequence !== contextSequence) return;
        fill(classroomSelect, classes, "classroom_id", "name", "Selecione a turma");
        if (classes.length === 1) classroomSelect.value = classes[0].classroom_id;
        selectedClassroom = classroomSelect.value;
        clearInstitutionalQueue();
      } catch (_error) { if (sequence === contextSequence) status.textContent = "Não foi possível carregar as turmas."; }
    }
    schoolSelect.addEventListener("change", loadClasses);
    classroomSelect.addEventListener("change", () => {
      if (!canLeaveEditor()) { classroomSelect.value = selectedClassroom; return; }
      selectedClassroom = classroomSelect.value;
      clearInstitutionalQueue();
    });
    try {
      const context = await request("/institutional/me/context");
      document.querySelector("#teacher-academic-year").textContent = `Ano ${context.academic_year}`;
      fill(schoolSelect, context.schools, "school_id", "name", "Selecione a escola");
      if (context.schools.length === 1) schoolSelect.value = context.schools[0].school_id;
      await loadClasses();
    } catch (_error) { status.textContent = "Não foi possível carregar o contexto institucional."; }
  }
  window.ConfIATeacher = { canLeave: canLeaveEditor, showView, initInstitutional,
    openSubmission: async (id, examContext = null) => {
      if (!validId(id) || !canLeaveEditor()) return;
      const refreshed = refresh();
      const listVersion = listSequence, detailVersion = detailSequence;
      await refreshed;
      if (listVersion !== listSequence || detailVersion !== detailSequence) return;
      await open(id, null, examContext);
    },
    context: () => ({ schoolId: selectedSchool, classroomId: selectedClassroom,
      schoolName: selectedName("#teacher-school-select", selectedSchool), classroomName: selectedName("#teacher-classroom-select", selectedClassroom) }),
    showManuscripts: () => mode(true), showText: () => mode(false) };
  filter.addEventListener("change", renderQueue);
  assessmentFilter.addEventListener("change", renderQueue);
  problemFilter.addEventListener("change", renderQueue);
  showInk.addEventListener("click", () => mode(true));
  showText.addEventListener("click", () => mode(false));
  refreshButton.addEventListener("click", refresh);
  document.querySelector('[data-tab-target="teacher-area"]').addEventListener("click", () => { if (!document.querySelector("#teacher-area").hidden && !inbox.hidden && detail.hidden && !list.children.length) refresh(); });
  if (new URLSearchParams(location.search).get("area") === "teacher") document.querySelector('[data-tab-target="teacher-area"]').click();
  window.addEventListener("beforeunload", (event) => {
    if (activeEditor?.isDirty() || activeEditor?.busy || activeDecision?.isDirty() || activeDecision?.busy) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
})();
