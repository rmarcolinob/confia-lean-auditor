(function startCapturePage() {
  "use strict";

  const params = globalThis.location ? new URLSearchParams(globalThis.location.search) : null;
  const embedded = params?.get("embedded") === "1" && globalThis.parent !== globalThis;
  let resolutionMode = embedded && params?.get("mode") === "practice" ? "practice" : "submission";
  let transitionQueue = Promise.resolve();
  let initialized = false;
  let preparing = false;
  let preparationFinished = Promise.resolve();
  let finishPreparation = () => {};
  if (embedded) {
    document.body.dataset.embedded = "true";
    document.body.dataset.workspaceMode = resolutionMode;
  }

  const Model = globalThis.ConfiaInkModel;
  const Canvas = globalThis.ConfiaInkCanvas;
  const Store = globalThis.ConfiaDraftStore;
  const Sender = globalThis.ConfiaSubmissionClient?.create(Canvas, (...args) => fetch(...args));

  const elements = {
    problemSelect: document.querySelector("#problem-select"),
    problemDock: document.querySelector("#problem-dock"),
    problemCode: document.querySelector("#problem-code"),
    problemTitle: document.querySelector("#problem-title"),
    problemStatement: document.querySelector("#problem-statement"),
    problemMathMessage: document.querySelector("#problem-math-message"),
    problemStatementWrap: document.querySelector("#problem-statement-wrap"),
    toggleProblem: document.querySelector("#toggle-problem"),
    savedSelect: document.querySelector("#saved-document-select"),
    openDocument: document.querySelector("#open-document"),
    newDraft: document.querySelector("#new-draft"),
    penMode: document.querySelector("#pen-mode"),
    mouseMode: document.querySelector("#mouse-mode"),
    drawTool: document.querySelector("#draw-tool"),
    eraseTool: document.querySelector("#erase-tool"),
    undo: document.querySelector("#undo"),
    redo: document.querySelector("#redo"),
    previousPage: document.querySelector("#previous-page"),
    nextPage: document.querySelector("#next-page"),
    addPage: document.querySelector("#add-page"),
    pageIndicator: document.querySelector("#page-indicator"),
    canvas: document.querySelector("#ink-canvas"),
    preview: document.querySelector("#export-preview"),
    inputHint: document.querySelector("#input-hint"),
    documentState: document.querySelector("#document-state"),
    documentProblem: document.querySelector("#document-problem"),
    documentId: document.querySelector("#document-id"),
    storageState: document.querySelector("#storage-state"),
    draftPersistence: document.querySelector("#draft-persistence"),
    statusMessage: document.querySelector("#status-message"),
    continueDraft: document.querySelector("#continue-draft"),
    prepareSnapshot: document.querySelector("#prepare-snapshot"),
    exportJson: document.querySelector("#export-json"),
    exportPng: document.querySelector("#export-png"),
    snapshotMessage: document.querySelector("#snapshot-message"),
    technicalDetails: document.querySelector("#technical-details"),
    sendSolution: document.querySelector("#send-solution"),
    previewWriting: document.querySelector("#preview-writing"),
    previewMessage: document.querySelector("#preview-message"),
    previewResult: document.querySelector("#preview-result"),
    submissionMessage: document.querySelector("#submission-message"),
    submissionReceipt: document.querySelector("#submission-receipt"),
    recognizeWriting: document.querySelector("#recognize-writing"),
    recognitionMessage: document.querySelector("#recognition-message"),
    recognitionPreview: document.querySelector("#recognition-preview"),
    exportTitle: document.querySelector("#export-title"),
    exportNote: document.querySelector("#export-note"),
    modeTitle: document.querySelector("#capture-mode-title"),
    openTeacher: document.querySelector("#open-teacher"),
    directPractice: document.querySelector("#direct-practice"),
  };

  let problems = [];
  let problemPresentations = [];
  let captureDocument = null;
  let pageIndex = 0;
  let inputMode = "pen";
  let activeTool = "draw";
  let currentStroke = null;
  let activePointerId = null;
  let strokeStartTime = 0;
  let saveQueue = Promise.resolve();
  // UI-only sequence: an older save must not announce that newer changes are saved.
  let persistenceRequest = 0;
  let savedDocumentsRequest = 0;
  let submissionBusy = false;
  const recognitionBusy = new Set();
  let previewPending = null;
  let previewGeneration = 0;
  let transientPreview = null;
  const submissionStates = new Map();
  const recognitionStates = new Map();

  function notifyContext(value = captureDocument, receipt = null, mode = resolutionMode) {
    if (!embedded || !value) return;
    const shell = document.querySelector(".capture-shell");
    const measuredHeight = shell && Number.isFinite(shell.offsetHeight) ? Math.ceil(shell.offsetTop + shell.offsetHeight + 8) : null;
    const presentation = problemPresentations.find(item => item.problem_id === value.problem_id && item.source_statement === problems.find(p => (p.problem_id || p.id) === value.problem_id)?.statement);
    const state = submissionStates.get(value.local_snapshot_id);
    // The parent renders controls; this page remains the sole owner of state and actions.
    const controls = value === captureDocument ? {
      document_id: documentStorageId(value),
      frozen: value.document_kind === "local_snapshot",
      document_state: elements.documentState.textContent,
      storage_state: elements.storageState.textContent,
      persistence: elements.draftPersistence.textContent,
      persistence_kind: elements.draftPersistence.dataset.state,
      status: elements.statusMessage.textContent,
      status_kind: elements.statusMessage.dataset.kind,
      saved_documents: elements.savedSelect.children ? Array.from(elements.savedSelect.children).map(option => ({ id: option.value, label: option.textContent })).filter(option => option.id) : [],
      can_prepare: !elements.prepareSnapshot.disabled,
      can_send: !elements.sendSolution.disabled,
      can_preview: !elements.previewWriting.disabled,
      preview_message: elements.previewMessage.textContent,
      preview_kind: elements.previewMessage.dataset.kind,
      preview_segments: transientPreview?.snapshot === value ? transientPreview.segments : [],
      send_label: elements.sendSolution.textContent,
      can_recognize: !elements.recognizeWriting.disabled,
      recognize_label: elements.recognizeWriting.textContent,
      snapshot_message: elements.snapshotMessage.textContent,
      submission_message: elements.submissionMessage.textContent,
      submission_kind: elements.submissionMessage.dataset.kind,
      submission_receipt: elements.submissionReceipt.textContent,
      recognition_message: elements.recognitionMessage.textContent,
      recognition_segments: recognitionStates.get(value.local_snapshot_id)?.segments || [],
    } : null;
    globalThis.parent.postMessage({ type: "confia-notebook-context", context: {
      problem_id: value.problem_id, mode, draft_id: value.draft_id,
      local_snapshot_id: value.local_snapshot_id || null,
      question_presentation_version: presentation?.display_version ?? null,
      ink_version: `${value.operations.length}:${value.pages.length}:${value.active_stroke_ids.length}`,
      receipt: receipt || state?.receipt || null,
      controls,
      content_height: measuredHeight && measuredHeight > 0 ? Math.min(4000, measuredHeight) : null,
    } }, globalThis.location.origin);
  }

  function renderSubmission() {
    const frozen = captureDocument?.document_kind === "local_snapshot";
    const state = submissionStates.get(captureDocument?.local_snapshot_id);
    const previewBusy = previewPending?.snapshot === captureDocument;
    const preview = transientPreview?.snapshot === captureDocument ? transientPreview : null;
    const previewReady = !captureDocument?.active_stroke_ids?.length || Boolean(preview?.segments?.length && !preview?.loading);
    elements.sendSolution.disabled = resolutionMode !== "submission" || !Sender || !frozen || submissionBusy || previewBusy
      || !previewReady || Boolean(state?.receipt);
    elements.sendSolution.textContent = state?.receipt ? "Solução recebida" : "Enviar solução";
    elements.previewWriting.disabled = resolutionMode !== "submission" || !frozen || previewBusy
      || !captureDocument?.active_stroke_ids?.length || Boolean(state?.receipt);
    elements.previewMessage.textContent = previewBusy && preview?.loading ? "Reconhecendo..."
      : preview?.message || (frozen ? captureDocument?.active_stroke_ids?.length
        ? "Reconheça a versão preparada para conferir a leitura antes do envio."
        : "Esta versão não contém escrita ativa para reconhecer."
        : "Prepare uma versão para gerar a prévia.");
    elements.previewMessage.dataset.kind = preview?.kind || "info";
    globalThis.ConfiaRecognitionView?.render(elements.previewResult, preview?.segments || []);
    elements.submissionMessage.dataset.kind = state?.kind || "info";
    elements.submissionMessage.textContent = state?.message || (frozen
      ? previewReady ? "Versão preparada neste dispositivo. Envie para receber confirmação do servidor."
        : "Reconheça e confira a versão preparada antes de enviar."
      : "Prepare uma versão antes de enviar. Salvar o rascunho neste dispositivo não envia a solução.");
    elements.submissionReceipt.hidden = !state?.receipt;
    elements.submissionReceipt.textContent = state?.receipt
      ? `submission_id: ${state.receipt.submission_id} · Questão: ${state.receipt.problem_id} · Recebida em: ${new Date(state.receipt.received_at).toLocaleString("pt-BR")}`
      : "";
    if (state?.receipt) elements.snapshotMessage.textContent = "Versão congelada preservada neste dispositivo.";
    else if (state) elements.snapshotMessage.textContent = "Versão local preservada; recebimento pelo servidor ainda não confirmado.";
    const recognition = recognitionStates.get(captureDocument?.local_snapshot_id);
    elements.recognizeWriting.disabled = resolutionMode !== "submission" || !state?.receipt
      || recognitionBusy.has(state.receipt.submission_id) || Boolean(recognition?.segments?.length && !recognition.failed);
    elements.recognizeWriting.textContent = recognition?.segments?.length && !recognition.failed
      ? "Transcrição gerada" : recognition?.failed ? "Tentar reconhecimento novamente" : "Reconhecer escrita";
    elements.recognitionMessage.textContent = recognition?.message || (state?.receipt
      ? captureDocument?.active_stroke_ids?.length
        ? "A transcrição automática oficial será gerada a partir da versão enviada."
        : "Esta versão não contém escrita ativa para reconhecer."
      : "Envie a versão preparada para reconhecer a escrita.");
    globalThis.ConfiaRecognitionView?.render(elements.recognitionPreview, recognition?.segments || []);
    notifyContext();
  }

  function selectedProblem() {
    return problems.find((problem) => (problem.problem_id || problem.id) === elements.problemSelect.value);
  }

  function currentPage() {
    return captureDocument && captureDocument.pages[pageIndex];
  }

  function documentStorageId(value) {
    return Store.storageId(value);
  }

  function setStatus(message, kind) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.dataset.kind = kind || "info";
    notifyContext();
  }

  function setPersistenceState(state) {
    const frozen = captureDocument && captureDocument.document_kind === "local_snapshot";
    const messages = {
      idle: "Comece a escrever — salvamento automático",
      saving: "Salvando...",
      saved: frozen ? "Cópia local salva neste dispositivo" : "Rascunho salvo neste dispositivo",
      error: "Não foi possível salvar o rascunho",
      unavailable: "Armazenamento local indisponível",
    };
    elements.draftPersistence.dataset.state = state;
    elements.draftPersistence.textContent = messages[state];
    notifyContext();
  }

  function setToggle(first, second, firstActive) {
    first.classList.toggle("is-active", firstActive);
    first.setAttribute("aria-pressed", String(firstActive));
    second.classList.toggle("is-active", !firstActive);
    second.setAttribute("aria-pressed", String(!firstActive));
  }

  function renderProblem() {
    const problem = selectedProblem();
    elements.problemCode.textContent = problem ? (problem.problem_id || problem.id) : "—";
    elements.problemTitle.textContent = problem ? problem.title : "Questão não disponível";
    elements.problemStatement.textContent = problem ? problem.statement : "";
    if (globalThis.ConfiaProblemMath) {
      globalThis.ConfiaProblemMath.render(elements.problemStatement, elements.problemMathMessage, {
        problemId: problem && (problem.problem_id || problem.id),
        registry: problemPresentations,
      });
    }
  }

  function setProblemExpanded(expanded) {
    elements.problemDock.classList.toggle("is-collapsed", !expanded);
    elements.problemStatementWrap.hidden = !expanded;
    elements.toggleProblem.setAttribute("aria-expanded", String(expanded));
    elements.toggleProblem.textContent = expanded ? "Recolher enunciado" : "Expandir enunciado";
  }

  function renderCanvas() {
    if (!captureDocument || !currentPage()) return;
    Canvas.render(elements.canvas, captureDocument, currentPage().page_id, {
      grid: true,
      transientStroke: currentStroke,
    });
    Canvas.render(elements.preview, captureDocument, currentPage().page_id, { grid: false });
  }

  function renderState() {
    if (!captureDocument) return;
    if (embedded) document.body.dataset.workspaceMode = resolutionMode;
    pageIndex = Math.max(0, Math.min(pageIndex, captureDocument.pages.length - 1));
    const frozen = captureDocument.document_kind === "local_snapshot";
    const stacks = Model.historyStacks(captureDocument);
    elements.documentState.textContent = frozen ? "Cópia local congelada" : "Rascunho editável";
    elements.documentProblem.textContent = captureDocument.problem_id;
    elements.documentId.textContent = documentStorageId(captureDocument);
    elements.pageIndicator.textContent = `Página ${pageIndex + 1} de ${captureDocument.pages.length}`;
    elements.previousPage.disabled = pageIndex === 0;
    elements.nextPage.disabled = pageIndex >= captureDocument.pages.length - 1;
    elements.addPage.disabled = frozen || captureDocument.pages.length >= Model.CONFIG.maxPages;
    elements.undo.disabled = frozen || stacks.undo.length === 0;
    elements.redo.disabled = frozen || stacks.redo.length === 0;
    elements.penMode.disabled = frozen;
    elements.mouseMode.disabled = frozen;
    elements.drawTool.disabled = frozen;
    elements.eraseTool.disabled = frozen;
    elements.prepareSnapshot.disabled = frozen || preparing || resolutionMode !== "submission";
    elements.continueDraft.hidden = !frozen;
    elements.inputHint.textContent = frozen
      ? "Esta cópia está congelada. Para editar, crie uma nova versão de rascunho."
      : inputMode === "pen"
        ? "Modo caneta: toque e mouse não desenham. A rejeição de palma depende do dispositivo e ainda precisa de teste físico."
        : "Modo mouse ativado explicitamente para teste em computador. Toque não desenha.";
    for (const control of document.querySelectorAll("[data-submission-only]")) control.hidden = resolutionMode !== "submission";
    elements.exportTitle.textContent = resolutionMode === "practice" ? "Exportar cópia local" : "Preparar e exportar";
    elements.exportNote.textContent = resolutionMode === "practice"
      ? "Guarde uma cópia dos traços ou da imagem da página. A análise utiliza somente a versão digitada no workspace."
      : "A preparação congela uma cópia independente no IndexedDB. Não autentica autoria e não gera recibo de servidor.";
    elements.modeTitle.textContent = resolutionMode === "practice" ? "Prática com feedback" : "Solução para envio";
    renderCanvas();
    renderSubmission();
  }

  async function refreshSavedDocuments() {
    const problemId = elements.problemSelect.value;
    const request = ++savedDocumentsRequest;
    elements.savedSelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Selecione uma versão salva";
    elements.savedSelect.appendChild(placeholder);
    try {
      const records = await Store.list(problemId);
      if (request !== savedDocumentsRequest || problemId !== elements.problemSelect.value) return;
      for (const record of records) {
        const option = document.createElement("option");
        option.value = record.storage_id;
        const kind = record.document_kind === "local_snapshot" ? "cópia congelada" : "rascunho";
        option.textContent = `${kind} · ${new Date(record.client_updated_at).toLocaleString("pt-BR")} · ${record.storage_id.slice(-8)}`;
        elements.savedSelect.appendChild(option);
      }
      notifyContext();
    } catch (error) {
      setStatus(`${error.message} Continue usando exportação manual para preservar os dados.`, "error");
      elements.storageState.textContent = "Armazenamento indisponível";
      if (elements.draftPersistence.dataset.state === "idle") setPersistenceState("unavailable");
    }
  }

  function persist(documentToSave, options) {
    const settings = { announce: true, refresh: true, ...options };
    const immutableCopy = Model.exportClone(documentToSave);
    const savedId = documentStorageId(immutableCopy);
    const request = ++persistenceRequest;
    if (captureDocument && documentStorageId(captureDocument) === savedId) {
      elements.storageState.textContent = "Salvando…";
      setPersistenceState("saving");
    }
    saveQueue = saveQueue
      .catch(() => undefined)
      .then(() => Store.save(immutableCopy))
      .then(async () => {
        if (captureDocument && documentStorageId(captureDocument) === savedId && request === persistenceRequest) {
          elements.storageState.textContent = "Salvo neste dispositivo";
          setPersistenceState("saved");
          if (settings.announce) setStatus("Salvo neste dispositivo.", "saved");
        }
        if (settings.refresh) await refreshSavedDocuments();
        return true;
      })
      .catch((error) => {
        if (captureDocument && documentStorageId(captureDocument) === savedId && request === persistenceRequest) {
          elements.storageState.textContent = "Falha ao salvar";
          setPersistenceState("error");
          setStatus(`Não foi possível salvar localmente: ${error.message} Exporte os traços para não perder esta versão.`, "error");
        }
        return false;
      });
    return saveQueue;
  }

  function setDocument(nextDocument, nextPageIndex) {
    previewGeneration += 1;
    previewPending = null;
    transientPreview = null;
    captureDocument = nextDocument;
    pageIndex = nextPageIndex || 0;
    currentStroke = null;
    activePointerId = null;
    elements.storageState.textContent = "Ainda não salvo";
    persistenceRequest += 1;
    setPersistenceState("idle");
    elements.snapshotMessage.textContent = "";
    renderState();
  }

  async function changeProblem(problemId) {
    if (!problems.some(p => (p.problem_id || p.id) === problemId)) return;
    stopStroke(true);
    if (captureDocument && captureDocument.document_kind === "draft") await persist(captureDocument, { announce: false });
    elements.problemSelect.value = problemId;
    renderProblem();
    setDocument(Model.createDraft(problemId), 0);
    await refreshSavedDocuments();
    setStatus("Novo rascunho local. Ele será salvo após a primeira operação concluída.");
  }

  function mutate(nextDocument, statusText) {
    if (nextDocument === captureDocument) return;
    previewGeneration += 1;
    previewPending = null;
    transientPreview = null;
    captureDocument = nextDocument;
    elements.storageState.textContent = "Salvando…";
    renderState();
    persist(captureDocument, { announce: !statusText });
    if (statusText) setStatus(statusText);
  }

  function allowedPointer(event) {
    if (preparing) return false;
    return !captureDocument || captureDocument.document_kind === "draft"
      ? event.pointerType === inputMode
      : false;
  }

  function stopStroke(interrupted, finalEvent) {
    if (!currentStroke) return;
    const pointerId = activePointerId;
    if (finalEvent && finalEvent.pointerId === pointerId) {
      Canvas.appendEventPoints(currentStroke.points, finalEvent, elements.canvas, currentPage(), strokeStartTime);
    }
    currentStroke.interrupted = Boolean(interrupted);
    const completed = currentStroke;
    currentStroke = null;
    activePointerId = null;
    if (elements.canvas.hasPointerCapture && elements.canvas.hasPointerCapture(pointerId)) {
      elements.canvas.releasePointerCapture(pointerId);
    }
    try {
      mutate(Model.addStroke(captureDocument, completed));
    } catch (error) {
      setStatus(error.message, "error");
      renderCanvas();
    }
  }

  function pointerDown(event) {
    if (!allowedPointer(event) || !currentPage()) return;
    event.preventDefault();
    if (activeTool === "erase") {
      const point = Canvas.eventPoint(event, elements.canvas, currentPage(), event.timeStamp);
      const strokeId = Canvas.hitTest(captureDocument, currentPage().page_id, point, 24);
      if (strokeId) mutate(Model.eraseStroke(captureDocument, strokeId));
      return;
    }
    if (activePointerId !== null) return;
    activePointerId = event.pointerId;
    strokeStartTime = event.timeStamp;
    currentStroke = {
      stroke_id: Model.newId("stroke"),
      page_id: currentPage().page_id,
      pointer_type: event.pointerType,
      color: Model.CONFIG.strokeColor,
      width: Model.CONFIG.penWidth,
      interrupted: false,
      points: [],
    };
    Canvas.appendEventPoints(currentStroke.points, event, elements.canvas, currentPage(), strokeStartTime);
    if (elements.canvas.setPointerCapture) elements.canvas.setPointerCapture(event.pointerId);
    renderCanvas();
  }

  function pointerMove(event) {
    if (!currentStroke || event.pointerId !== activePointerId) return;
    event.preventDefault();
    Canvas.appendEventPoints(currentStroke.points, event, elements.canvas, currentPage(), strokeStartTime);
    if (currentStroke.points.length >= Model.CONFIG.maxPointsPerStroke) {
      stopStroke(true);
      setStatus("Traço encerrado no limite de pontos do protótipo.", "error");
      return;
    }
    renderCanvas();
  }

  function download(blob, filename) {
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function safeFilename(value) {
    return value.replace(/[^A-Za-z0-9._-]+/g, "-");
  }

  async function loadProblemPresentations() {
    try {
      const response = await fetch("/static/problem-presentations/registry.json", { headers: { Accept: "application/json" } });
      if (!response.ok) return [];
      const registry = await response.json();
      return Array.isArray(registry) ? registry : [];
    } catch (error) {
      // Presentation availability must not disable writing or local persistence.
      return [];
    }
  }

  async function initialize() {
    try {
      const [response, registry] = await Promise.all([
        fetch("/problems", { headers: { Accept: "application/json" } }),
        loadProblemPresentations(),
      ]);
      if (!response.ok) throw new Error(`Catálogo indisponível (${response.status}).`);
      problems = await response.json();
      problemPresentations = registry;
      for (const problem of problems) {
        const option = document.createElement("option");
        option.value = problem.problem_id || problem.id;
        option.textContent = `${option.value} — ${problem.title}`;
        elements.problemSelect.appendChild(option);
      }
      if (!problems.length) throw new Error("O catálogo não contém questões.");
      const requested = params?.get("problem_id");
      if (requested && !problems.some(p => (p.problem_id || p.id) === requested)) throw new Error("A questão solicitada não está no catálogo. Volte às questões para selecionar uma questão disponível.");
      if (requested) elements.problemSelect.value = requested;
      renderProblem();
      // The catalog already presents the statement. Keep it available in the
      // sticky dock while giving handwriting the initial viewport priority.
      if (embedded) setProblemExpanded(false);
      const requestedDraft = params?.get("draft_id");
      let restored = null;
      if (requestedDraft) {
        restored = await Store.get(requestedDraft);
        if (!restored || restored.problem_id !== elements.problemSelect.value) throw new Error("O rascunho solicitado não pertence a esta questão ou não está disponível neste dispositivo.");
      }
      setDocument(restored || Model.createDraft(elements.problemSelect.value), 0);
      initialized = true;
      await refreshSavedDocuments();
      setStatus("Escolha uma versão salva ou comece um novo rascunho.");
      notifyContext();
    } catch (error) {
      setStatus(error.message, "error");
      for (const button of document.querySelectorAll("button")) button.disabled = true;
    }
  }

  function queueTransition(action) {
    transitionQueue = transitionQueue.catch(() => undefined).then(action);
    return transitionQueue;
  }
  elements.problemSelect.addEventListener("change", () => {
    const id = elements.problemSelect.value;
    return queueTransition(() => changeProblem(id));
  });
  globalThis.addEventListener("message", event => {
    if (!embedded || !initialized || event.origin !== globalThis.location.origin || event.source !== globalThis.parent || event.data?.type !== "confia-workspace-command") return;
    const { action, problem_id: problemId, mode } = event.data;
    if (!["practice", "submission"].includes(mode)) return;
    if (action === "configure") {
      queueTransition(async () => {
        await preparationFinished;
        if (captureDocument.problem_id !== problemId) await changeProblem(problemId);
        resolutionMode = mode;
        renderState();
      });
      return;
    }
    if (problemId !== captureDocument.problem_id || mode !== resolutionMode || event.data.document_id !== documentStorageId(captureDocument) || preparing) return;
    const buttons = {
      "new-draft": elements.newDraft,
      "continue-draft": elements.continueDraft,
      "prepare-snapshot": elements.prepareSnapshot,
      "send-solution": elements.sendSolution,
      "preview-writing": elements.previewWriting,
      "recognize-writing": elements.recognizeWriting,
      "export-json": elements.exportJson,
      "export-png": elements.exportPng,
    };
    if (action === "open-document") {
      const id = event.data.saved_document_id;
      if (typeof id !== "string" || !Array.from(elements.savedSelect.children).some(option => option.value === id)) return;
      elements.savedSelect.value = id;
      elements.openDocument.click();
      return;
    }
    const button = buttons[action];
    if (!button || button.disabled || button.hidden || (action === "continue-draft" && captureDocument.document_kind !== "local_snapshot")) return;
    button.click();
  });
  elements.openTeacher.addEventListener("click", event => {
    if (!embedded) return;
    event.preventDefault();
    globalThis.parent.postMessage({ type: "confia-workspace-navigation", destination: "teacher-submissions" }, globalThis.location.origin);
  });
  elements.directPractice.addEventListener("click", async () => {
    if (!captureDocument || preparing) return;
    stopStroke(true);
    if (!await persist(captureDocument, { announce: false })) return;
    globalThis.location.href = `/?problem_id=${encodeURIComponent(captureDocument.problem_id)}&draft_id=${encodeURIComponent(documentStorageId(captureDocument))}&workspace_mode=practice#student/resolve`;
  });
  elements.toggleProblem.addEventListener("click", () => {
    setProblemExpanded(elements.toggleProblem.getAttribute("aria-expanded") !== "true");
  });
  elements.technicalDetails.addEventListener("toggle", () => {
    if (elements.technicalDetails.open) requestAnimationFrame(renderCanvas);
  });
  elements.newDraft.addEventListener("click", async () => {
    if (preparing) return;
    stopStroke(true);
    if (captureDocument && captureDocument.document_kind === "draft") await persist(captureDocument, { announce: false });
    setDocument(Model.createDraft(elements.problemSelect.value), 0);
    setStatus("Novo rascunho criado sem substituir as versões anteriores.");
  });
  elements.openDocument.addEventListener("click", async () => {
    if (preparing) return;
    stopStroke(true);
    const id = elements.savedSelect.value;
    if (!id) {
      setStatus("Selecione uma versão salva para abrir.", "error");
      return;
    }
    if (captureDocument && captureDocument.document_kind === "draft") await persist(captureDocument, { announce: false });
    try {
      const stored = await Store.get(id);
      if (!stored) throw new Error("A versão selecionada não foi encontrada.");
      if (stored.problem_id !== elements.problemSelect.value) throw new Error("Este rascunho pertence a outra questão.");
      setDocument(stored, 0);
      elements.storageState.textContent = "Recuperado deste dispositivo";
      setPersistenceState("saved");
      setStatus("Versão recuperada explicitamente deste dispositivo.", "saved");
    } catch (error) {
      setStatus(`Não foi possível recuperar: ${error.message}`, "error");
    }
  });

  elements.penMode.addEventListener("click", () => {
    inputMode = "pen";
    setToggle(elements.penMode, elements.mouseMode, true);
    renderState();
  });
  elements.mouseMode.addEventListener("click", () => {
    inputMode = "mouse";
    setToggle(elements.penMode, elements.mouseMode, false);
    renderState();
  });
  elements.drawTool.addEventListener("click", () => {
    activeTool = "draw";
    setToggle(elements.drawTool, elements.eraseTool, true);
  });
  elements.eraseTool.addEventListener("click", () => {
    activeTool = "erase";
    setToggle(elements.drawTool, elements.eraseTool, false);
  });
  elements.undo.addEventListener("click", () => mutate(Model.undo(captureDocument)));
  elements.redo.addEventListener("click", () => mutate(Model.redo(captureDocument)));
  elements.previousPage.addEventListener("click", () => {
    pageIndex = Math.max(0, pageIndex - 1);
    renderState();
  });
  elements.nextPage.addEventListener("click", () => {
    pageIndex = Math.min(captureDocument.pages.length - 1, pageIndex + 1);
    renderState();
  });
  elements.addPage.addEventListener("click", () => {
    try {
      previewGeneration += 1;
      previewPending = null;
      transientPreview = null;
      captureDocument = Model.addPage(captureDocument);
      pageIndex = captureDocument.pages.length - 1;
      renderState();
      persist(captureDocument);
    } catch (error) {
      setStatus(error.message, "error");
    }
  });

  elements.canvas.addEventListener("pointerdown", pointerDown);
  elements.canvas.addEventListener("pointermove", pointerMove);
  elements.canvas.addEventListener("pointerup", (event) => {
    if (event.pointerId === activePointerId) stopStroke(false, event);
  });
  elements.canvas.addEventListener("pointercancel", (event) => {
    if (event.pointerId === activePointerId) stopStroke(true, event);
  });
  elements.canvas.addEventListener("lostpointercapture", (event) => {
    if (event.pointerId === activePointerId) stopStroke(true);
  });

  elements.prepareSnapshot.addEventListener("click", async () => {
    if (resolutionMode !== "submission" || preparing || captureDocument?.document_kind !== "draft") return;
    stopStroke(true);
    preparing = true;
    preparationFinished = new Promise(resolve => { finishPreparation = resolve; });
    const source = captureDocument;
    renderState();
    try {
      await persist(source, { announce: false });
      const snapshot = Model.freeze(source);
      await Store.save(snapshot);
      if (captureDocument !== source) return;
      setDocument(snapshot, pageIndex);
      elements.storageState.textContent = "Cópia congelada neste dispositivo";
      setPersistenceState("saved");
      elements.snapshotMessage.textContent = "Versão preparada localmente. Envie para confirmar o recebimento.";
      setStatus("A cópia congelada foi salva localmente. Use Enviar solução para solicitar recebimento pelo servidor.", "saved");
      await refreshSavedDocuments();
      elements.savedSelect.value = snapshot.local_snapshot_id;
    } catch (error) {
      setStatus(`Não foi possível preparar a cópia local: ${error.message}`, "error");
    } finally {
      preparing = false;
      finishPreparation();
      renderState();
    }
  });
  elements.continueDraft.addEventListener("click", () => {
    const nextDraft = Model.createDraft(captureDocument.problem_id, captureDocument);
    setDocument(nextDraft, pageIndex);
    setStatus("Nova versão editável criada; a cópia congelada permanece inalterada.");
    persist(nextDraft);
  });
  elements.previewWriting.addEventListener("click", async () => {
    if (resolutionMode !== "submission" || previewPending?.snapshot === captureDocument || captureDocument?.document_kind !== "local_snapshot"
        || !captureDocument.active_stroke_ids.length) return;
    const snapshot = captureDocument;
    const generation = ++previewGeneration;
    const clientPreviewId = Model.newId("preview");
    const snapshotJson = JSON.stringify(Model.exportClone(snapshot), null, 2);
    previewPending = { snapshot, generation };
    transientPreview = { snapshot, segments: [], message: "Reconhecendo...", loading: true, kind: "pending" };
    renderSubmission();
    try {
      const response = await fetch("/submissions/recognition-preview", {
        method: "POST", headers: { "Content-Type": "application/json" }, cache: "no-store",
        body: JSON.stringify({ snapshot_json: snapshotJson, client_preview_id: clientPreviewId }),
      });
      if (!response.ok) throw new Error("Não foi possível reconhecer esta versão. Tente novamente.");
      const result = await response.json();
      if (result.client_preview_id !== clientPreviewId || result.problem_id !== snapshot.problem_id
          || result.snapshot_id !== snapshot.local_snapshot_id || !/^[0-9a-f]{64}$/.test(result.snapshot_sha256)
          || result.page_count !== snapshot.pages.length
          || result.active_stroke_count !== snapshot.active_stroke_ids.length
          || !Array.isArray(result.result?.segments) || !result.result.segments.length) {
        throw new Error("A prévia não corresponde à versão preparada. Gere uma nova leitura.");
      }
      if (generation !== previewGeneration || captureDocument !== snapshot) return;
      transientPreview = { snapshot, snapshotHash: result.snapshot_sha256, segments: result.result.segments,
        message: "Prévia transitória. Confira se a leitura corresponde ao que você escreveu.", kind: "saved" };
    } catch (error) {
      if (generation === previewGeneration && captureDocument === snapshot) {
        transientPreview = { snapshot, segments: [], message: error.message, kind: "error" };
      }
    } finally {
      if (previewPending?.generation === generation) previewPending = null;
      renderSubmission();
    }
  });
  async function recognizeSubmittedSnapshot(snapshotId, receipt) {
    if (!receipt?.submission_id || recognitionBusy.has(receipt.submission_id)) return;
    const state = recognitionStates.get(snapshotId) || { attempt: 0 };
    recognitionBusy.add(receipt.submission_id);
    state.segments = [];
    state.failed = false;
    state.message = "Reconhecendo a solução enviada...";
    recognitionStates.set(snapshotId, state);
    renderSubmission();
    try {
      const response = await fetch(`/submissions/${encodeURIComponent(receipt.submission_id)}/recognitions`, {
        method: "POST", headers: { "Content-Type": "application/json" }, cache: "no-store",
        body: JSON.stringify({ provider: "mathpix", idempotency_key: `mathpix:${state.attempt}` }),
      });
      if (!response.ok) throw new Error("Reconhecedor indisponível. Confira a configuração do servidor.");
      const summary = await response.json();
      if (summary.status !== "NEEDS_REVIEW") {
        if (summary.status === "FAILED") state.attempt += 1;
        throw new Error("O reconhecimento falhou. Toque novamente para tentar uma nova leitura.");
      }
      const detail = await fetch(`/submissions/${encodeURIComponent(receipt.submission_id)}/recognitions/${encodeURIComponent(summary.recognizer_run_id)}`, { cache: "no-store" });
      if (!detail.ok) throw new Error("A transcrição foi registrada, mas não pôde ser carregada. Toque novamente para recuperá-la.");
      const run = await detail.json();
      if (run.status !== "NEEDS_REVIEW" || !Array.isArray(run.result?.segments)) throw new Error("Transcrição automática indisponível.");
      state.segments = run.result.segments;
      state.message = "Transcrição automática criada · aguarda conferência do professor.";
      const submission = submissionStates.get(snapshotId);
      if (submission?.receipt?.submission_id === receipt.submission_id) {
        submissionStates.set(snapshotId, { ...submission, message: "Solução enviada. Transcrição automática aguarda conferência do professor.", kind: "saved" });
      }
    } catch (_error) {
      state.failed = true;
      state.message = "Não foi possível gerar a transcrição automática. Toque para tentar novamente.";
      const submission = submissionStates.get(snapshotId);
      if (submission?.receipt?.submission_id === receipt.submission_id) {
        submissionStates.set(snapshotId, { ...submission, message: "Solução enviada. Não foi possível gerar a transcrição automática.", kind: "error" });
      }
    } finally {
      recognitionBusy.delete(receipt.submission_id);
      renderSubmission();
    }
  }

  elements.sendSolution.addEventListener("click", async () => {
    if (resolutionMode !== "submission" || !Sender || submissionBusy || captureDocument?.document_kind !== "local_snapshot" || submissionStates.get(captureDocument.local_snapshot_id)?.receipt) return;
    if (captureDocument.active_stroke_ids.length && !(transientPreview?.snapshot === captureDocument && transientPreview.segments?.length)) return;
    const snapshot = Model.exportClone(captureDocument);
    const id = snapshot.local_snapshot_id;
    submissionBusy = true;
    submissionStates.set(id, { message: "Enviando solução… aguarde o recibo do servidor.", kind: "pending" });
    renderSubmission();
    try {
      let receipt;
      try {
        receipt = await Sender.send(snapshot);
      } catch (error) {
        submissionStates.set(id, { message: error.message, kind: "error" });
        return;
      }
      submissionStates.set(id, { receipt, message: "Solução enviada. Gerando transcrição automática...", kind: "pending" });
      notifyContext(snapshot, receipt, "submission");
      renderSubmission();
      await recognizeSubmittedSnapshot(id, receipt);
    } finally {
      submissionBusy = false;
      renderSubmission();
      notifyContext();
    }
  });
  elements.recognizeWriting.addEventListener("click", async () => {
    const snapshotId = captureDocument?.local_snapshot_id;
    const receipt = submissionStates.get(snapshotId)?.receipt;
    if (resolutionMode !== "submission" || !receipt) return;
    await recognizeSubmittedSnapshot(snapshotId, receipt);
  });
  elements.exportJson.addEventListener("click", () => {
    const exported = Model.exportClone(captureDocument);
    const blob = new Blob([JSON.stringify(exported, null, 2)], { type: "application/json" });
    const id = safeFilename(documentStorageId(exported));
    download(blob, `${safeFilename(exported.problem_id)}-${id}-tracos.json`);
    setStatus("Documento de traços exportado a partir da versão aberta.", "saved");
  });
  elements.exportPng.addEventListener("click", async () => {
    try {
      const versionId = safeFilename(documentStorageId(captureDocument));
      const blob = await Canvas.pngBlob(captureDocument, currentPage().page_id);
      download(blob, `${safeFilename(captureDocument.problem_id)}-${versionId}-pagina-${pageIndex + 1}.png`);
      setStatus("PNG exportado a partir da mesma versão aberta, sem grade.", "saved");
    } catch (error) {
      setStatus(error.message, "error");
    }
  });

  if (typeof globalThis.ResizeObserver === "function") {
    const resizeObserver = new ResizeObserver(() => renderCanvas());
    resizeObserver.observe(elements.canvas);
    if (embedded) {
      const layoutObserver = new ResizeObserver(() => notifyContext());
      layoutObserver.observe(document.querySelector(".capture-shell"));
    }
  } else {
    globalThis.addEventListener("resize", renderCanvas);
  }
  globalThis.addEventListener("orientationchange", () => requestAnimationFrame(renderCanvas));
  initialize();
})();
