(function startCapturePage() {
  "use strict";

  const Model = globalThis.ConfiaInkModel;
  const Canvas = globalThis.ConfiaInkCanvas;
  const Store = globalThis.ConfiaDraftStore;

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
    elements.prepareSnapshot.disabled = frozen;
    elements.continueDraft.hidden = !frozen;
    elements.inputHint.textContent = frozen
      ? "Esta cópia está congelada. Para editar, crie uma nova versão de rascunho."
      : inputMode === "pen"
        ? "Modo caneta: toque e mouse não desenham. A rejeição de palma depende do dispositivo e ainda precisa de teste físico."
        : "Modo mouse ativado explicitamente para teste em computador. Toque não desenha.";
    renderCanvas();
  }

  async function refreshSavedDocuments() {
    const problemId = elements.problemSelect.value;
    elements.savedSelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Selecione uma versão salva";
    elements.savedSelect.appendChild(placeholder);
    try {
      const records = await Store.list(problemId);
      for (const record of records) {
        const option = document.createElement("option");
        option.value = record.storage_id;
        const kind = record.document_kind === "local_snapshot" ? "cópia congelada" : "rascunho";
        option.textContent = `${kind} · ${new Date(record.client_updated_at).toLocaleString("pt-BR")} · ${record.storage_id.slice(-8)}`;
        elements.savedSelect.appendChild(option);
      }
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
      })
      .catch((error) => {
        if (captureDocument && documentStorageId(captureDocument) === savedId && request === persistenceRequest) {
          elements.storageState.textContent = "Falha ao salvar";
          setPersistenceState("error");
          setStatus(`Não foi possível salvar localmente: ${error.message} Exporte os traços para não perder esta versão.`, "error");
        }
      });
    return saveQueue;
  }

  function setDocument(nextDocument, nextPageIndex) {
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
    if (captureDocument && captureDocument.document_kind === "draft") await persist(captureDocument, { announce: false });
    elements.problemSelect.value = problemId;
    renderProblem();
    setDocument(Model.createDraft(problemId), 0);
    await refreshSavedDocuments();
    setStatus("Novo rascunho local. Ele será salvo após a primeira operação concluída.");
  }

  function mutate(nextDocument, statusText) {
    if (nextDocument === captureDocument) return;
    captureDocument = nextDocument;
    elements.storageState.textContent = "Salvando…";
    renderState();
    persist(captureDocument, { announce: !statusText });
    if (statusText) setStatus(statusText);
  }

  function allowedPointer(event) {
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
      renderProblem();
      setDocument(Model.createDraft(elements.problemSelect.value), 0);
      await refreshSavedDocuments();
      setStatus("Escolha uma versão salva ou comece um novo rascunho.");
    } catch (error) {
      setStatus(error.message, "error");
      for (const button of document.querySelectorAll("button")) button.disabled = true;
    }
  }

  elements.problemSelect.addEventListener("change", () => changeProblem(elements.problemSelect.value));
  elements.toggleProblem.addEventListener("click", () => {
    setProblemExpanded(elements.toggleProblem.getAttribute("aria-expanded") !== "true");
  });
  elements.technicalDetails.addEventListener("toggle", () => {
    if (elements.technicalDetails.open) requestAnimationFrame(renderCanvas);
  });
  elements.newDraft.addEventListener("click", async () => {
    if (captureDocument && captureDocument.document_kind === "draft") await persist(captureDocument, { announce: false });
    setDocument(Model.createDraft(elements.problemSelect.value), 0);
    setStatus("Novo rascunho criado sem substituir as versões anteriores.");
  });
  elements.openDocument.addEventListener("click", async () => {
    const id = elements.savedSelect.value;
    if (!id) {
      setStatus("Selecione uma versão salva para abrir.", "error");
      return;
    }
    if (captureDocument && captureDocument.document_kind === "draft") await persist(captureDocument, { announce: false });
    try {
      const stored = await Store.get(id);
      if (!stored) throw new Error("A versão selecionada não foi encontrada.");
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
    try {
      await persist(captureDocument, { announce: false });
      const snapshot = Model.freeze(captureDocument);
      await Store.save(snapshot);
      setDocument(snapshot, pageIndex);
      elements.storageState.textContent = "Cópia congelada neste dispositivo";
      setPersistenceState("saved");
      elements.snapshotMessage.textContent = "Versão preparada localmente; ainda não enviada.";
      setStatus("A cópia congelada foi salva localmente. Não houve envio ao servidor.", "saved");
      await refreshSavedDocuments();
      elements.savedSelect.value = snapshot.local_snapshot_id;
    } catch (error) {
      setStatus(`Não foi possível preparar a cópia local: ${error.message}`, "error");
    }
  });
  elements.continueDraft.addEventListener("click", () => {
    const nextDraft = Model.createDraft(captureDocument.problem_id, captureDocument);
    setDocument(nextDraft, pageIndex);
    setStatus("Nova versão editável criada; a cópia congelada permanece inalterada.");
    persist(nextDraft);
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
  } else {
    globalThis.addEventListener("resize", renderCanvas);
  }
  globalThis.addEventListener("orientationchange", () => requestAnimationFrame(renderCanvas));
  initialize();
})();
