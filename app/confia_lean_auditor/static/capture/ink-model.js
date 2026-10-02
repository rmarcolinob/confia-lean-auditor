(function exposeInkModel(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.ConfiaInkModel = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function makeInkModel() {
  "use strict";

  const CONFIG = Object.freeze({
    schemaVersion: "1.0",
    maxPages: 3,
    maxStrokes: 2000,
    maxPointsPerStroke: 20000,
    maxTotalPoints: 200000,
    maxOperations: 10000,
    logicalWidth: 1200,
    logicalHeight: 1600,
    penWidth: 4,
    strokeColor: "#17355c",
  });

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function newId(prefix) {
    const random = globalThis.crypto && typeof globalThis.crypto.randomUUID === "function"
      ? globalThis.crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    return `${prefix}:${random}`;
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function rendererConfig() {
    return {
      renderer: "confia_canvas_polyline",
      renderer_version: "1.0.0",
      pressure_used_for_width: false,
      line_cap: "round",
      line_join: "round",
      png_background: "#ffffff",
      png_includes_grid: false,
    };
  }

  function makePage(index) {
    return {
      page_id: newId("page"),
      index,
      logical_width: CONFIG.logicalWidth,
      logical_height: CONFIG.logicalHeight,
      coordinate_system: "top_left_css_pixels",
    };
  }

  function createDraft(problemId, sourceDocument) {
    const timestamp = nowIso();
    if (sourceDocument) {
      const draft = clone(sourceDocument);
      draft.document_kind = "draft";
      draft.draft_id = newId("draft");
      draft.local_snapshot_id = null;
      draft.problem_id = problemId || sourceDocument.problem_id;
      draft.client_created_at = timestamp;
      draft.client_updated_at = timestamp;
      return draft;
    }
    return {
      schema_version: CONFIG.schemaVersion,
      document_kind: "draft",
      draft_id: newId("draft"),
      local_snapshot_id: null,
      problem_id: problemId,
      input_mode: "tablet_ink",
      origin: "experimental_local",
      pages: [makePage(0)],
      strokes: [],
      operations: [],
      active_stroke_ids: [],
      renderer: rendererConfig(),
      client_created_at: timestamp,
      client_updated_at: timestamp,
    };
  }

  function addPage(document) {
    if (document.document_kind !== "draft") throw new Error("Snapshots locais são somente leitura.");
    if (document.pages.length >= CONFIG.maxPages) throw new Error("Limite de três páginas atingido.");
    const next = clone(document);
    next.pages.push(makePage(next.pages.length));
    next.client_updated_at = nowIso();
    return next;
  }

  function operationEffect(operation, effects) {
    if (operation.kind === "add") return true;
    if (operation.kind === "erase") return false;
    return !effects.get(operation.target_operation_id);
  }

  function reconstructActive(document) {
    const active = new Set();
    const effects = new Map();
    for (const operation of document.operations) {
      const effect = operationEffect(operation, effects);
      effects.set(operation.operation_id, effect);
      if (effect) active.add(operation.stroke_id);
      else active.delete(operation.stroke_id);
    }
    return Array.from(active);
  }

  function appendOperation(document, kind, strokeId, targetOperationId) {
    if (document.operations.length >= CONFIG.maxOperations) {
      throw new Error("Limite de operações atingido. Prepare e exporte esta versão.");
    }
    const next = clone(document);
    next.operations.push({
      operation_id: newId("operation"),
      kind,
      stroke_id: strokeId,
      target_operation_id: targetOperationId || null,
      client_time: nowIso(),
    });
    next.active_stroke_ids = reconstructActive(next);
    next.client_updated_at = nowIso();
    return next;
  }

  function addStroke(document, stroke) {
    if (document.document_kind !== "draft") throw new Error("Snapshots locais são somente leitura.");
    if (document.strokes.length >= CONFIG.maxStrokes) throw new Error("Limite de traços atingido.");
    if (!document.pages.some((page) => page.page_id === stroke.page_id)) {
      throw new Error("A página do traço não existe.");
    }
    if (!Array.isArray(stroke.points) || stroke.points.length === 0) return document;
    if (stroke.points.length > CONFIG.maxPointsPerStroke) throw new Error("Traço longo demais.");
    const total = document.strokes.reduce((sum, item) => sum + item.points.length, 0);
    if (total + stroke.points.length > CONFIG.maxTotalPoints) throw new Error("Limite de pontos atingido.");
    const next = clone(document);
    const normalizedStroke = {
      stroke_id: stroke.stroke_id || newId("stroke"),
      page_id: stroke.page_id,
      pointer_type: stroke.pointer_type,
      color: stroke.color || CONFIG.strokeColor,
      width: stroke.width || CONFIG.penWidth,
      interrupted: Boolean(stroke.interrupted),
      points: clone(stroke.points),
    };
    next.strokes.push(normalizedStroke);
    return appendOperation(next, "add", normalizedStroke.stroke_id, null);
  }

  function eraseStroke(document, strokeId) {
    if (document.document_kind !== "draft") throw new Error("Snapshots locais são somente leitura.");
    if (!document.active_stroke_ids.includes(strokeId)) return document;
    return appendOperation(document, "erase", strokeId, null);
  }

  function historyStacks(document) {
    const undo = [];
    const redo = [];
    for (const operation of document.operations) {
      if (operation.kind === "add" || operation.kind === "erase") {
        undo.push(operation.operation_id);
        redo.length = 0;
      } else if (operation.kind === "undo") {
        const index = undo.lastIndexOf(operation.target_operation_id);
        if (index >= 0) undo.splice(index, 1);
        redo.push(operation.operation_id);
      } else if (operation.kind === "redo") {
        const index = redo.lastIndexOf(operation.target_operation_id);
        if (index >= 0) redo.splice(index, 1);
        undo.push(operation.operation_id);
      }
    }
    return { undo, redo };
  }

  function operationById(document, operationId) {
    return document.operations.find((operation) => operation.operation_id === operationId);
  }

  function undo(document) {
    if (document.document_kind !== "draft") throw new Error("Snapshots locais são somente leitura.");
    const stacks = historyStacks(document);
    const targetId = stacks.undo.at(-1);
    if (!targetId) return document;
    const target = operationById(document, targetId);
    return appendOperation(document, "undo", target.stroke_id, targetId);
  }

  function redo(document) {
    if (document.document_kind !== "draft") throw new Error("Snapshots locais são somente leitura.");
    const stacks = historyStacks(document);
    const targetId = stacks.redo.at(-1);
    if (!targetId) return document;
    const target = operationById(document, targetId);
    return appendOperation(document, "redo", target.stroke_id, targetId);
  }

  function freeze(document) {
    if (document.document_kind !== "draft") throw new Error("A versão já está congelada.");
    const snapshot = clone(document);
    snapshot.document_kind = "local_snapshot";
    snapshot.local_snapshot_id = newId("snapshot");
    snapshot.client_updated_at = nowIso();
    return snapshot;
  }

  function activeStrokes(document, pageId) {
    const active = new Set(document.active_stroke_ids);
    return document.strokes.filter(
      (stroke) => active.has(stroke.stroke_id) && (!pageId || stroke.page_id === pageId)
    );
  }

  function exportClone(document) {
    const exported = clone(document);
    exported.active_stroke_ids = reconstructActive(exported);
    return exported;
  }

  return {
    CONFIG,
    activeStrokes,
    addPage,
    addStroke,
    clone,
    createDraft,
    eraseStroke,
    exportClone,
    freeze,
    historyStacks,
    newId,
    reconstructActive,
    redo,
    undo,
  };
});
