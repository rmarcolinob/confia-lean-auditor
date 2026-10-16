const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");
const source = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/capture/tablet.js"), "utf8");
const recognitionView = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/recognition-view.js"), "utf8");
const flush = () => new Promise((resolve) => setImmediate(resolve));

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function element() {
  return {
    value: "", textContent: "", dataset: {}, hidden: false, disabled: false,
    attributes: {}, listeners: {}, children: [],
    classList: { toggle() {} },
    addEventListener(event, handler) { this.listeners[event] = handler; },
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name]; },
    replaceChildren() { this.children = []; this.value = ""; },
    appendChild(child) {
      this.children.push(child);
      if (this.children.length === 1) this.value = child.value;
    },
    click() { return this.listeners.click?.(); },
  };
}

async function page(options = {}) {
  const elements = new Map();
  const saves = [];
  const mathRenders = [];
  const canvasRenders = [];
  const events = {};
  const messages = [];
  const parent = { postMessage: message => messages.push(message) };
  const mathContexts = [];
  let stored = options.initialDocument || null;
  const getElement = (selector) => {
    if (!elements.has(selector)) {
      const control = element();
      // Mirror the initial HTML state of the expanded sticky statement.
      if (selector === "#toggle-problem") control.setAttribute("aria-expanded", "true");
      elements.set(selector, control);
    }
    return elements.get(selector);
  };
  const Store = {
    storageId: (document) => document.local_snapshot_id || document.draft_id,
    list: async () => {
      if (options.listError) throw new Error("Armazenamento indisponível");
      return stored ? [{ storage_id: Store.storageId(stored), document_kind: stored.document_kind, client_updated_at: stored.client_updated_at }] : [];
    },
    get: async () => stored,
    save(document) {
      if (options.autoSave) { saves.push({ document }); return Promise.resolve(); }
      const operation = deferred();
      saves.push({ document, ...operation });
      return operation.promise;
    },
  };
  const context = {
    ConfiaInkModel: Model,
    ConfiaInkCanvas: { render(target, document, pageId) { canvasRenders.push({ document, pageId }); } },
    ConfiaDraftStore: Store,
    ConfiaSubmissionClient: options.sender ? { create: () => options.sender } : undefined,
    ConfiaProblemMath: { render(target, message, presentation) {
      mathRenders.push(target.textContent);
      mathContexts.push(presentation);
    } },
    document: { body: { dataset: {} }, querySelector: getElement, querySelectorAll: () => [], createElement: element },
    fetch: async (url, init) => {
      if (options.fetch && url.startsWith("/submissions/")) return options.fetch(url, init);
      if (url === "/static/problem-presentations/registry.json") {
        if (options.registryError) throw new Error("Apresentação indisponível");
        return { ok: true, json: async () => options.registry || [] };
      }
      assert.equal(url, "/problems");
      return options.catalogResponse || { ok: true, json: async () => options.problems || [{ problem_id: "ITA2025Q1", title: "Questão", statement: "Enunciado" }] };
    },
    addEventListener(name, handler) { events[name] = handler; }, requestAnimationFrame(callback) { callback(); },
    Blob, URL: { createObjectURL: () => "blob:test", revokeObjectURL() {} }, setTimeout() {},
    katex: { render(latex, target) { target.textContent = `rendered:${latex}`; } },
  };
  if (options.embedded) Object.assign(context, { parent, location: { search: options.search || "?embedded=1&problem_id=ITA2025Q1&mode=practice", origin: "http://confia.test" }, URLSearchParams });
  vm.runInNewContext(recognitionView, context);
  vm.runInNewContext(source, context);
  await flush();
  return {
    saves, messages, events, context, get: getElement, parent,
    async command(values) {
      events.message({ origin: "http://confia.test", source: parent, data: { type: "confia-workspace-command", action: "configure", ...values } });
      await flush();
    },
    mathRenders, canvasRenders,
    mathContexts,
    statement: getElement("#problem-statement"),
    statementWrap: getElement("#problem-statement-wrap"),
    indicator: getElement("#draft-persistence"),
    sendButton: getElement("#send-solution"),
    sendMessage: getElement("#submission-message"),
    receipt: getElement("#submission-receipt"),
    snapshotMessage: getElement("#snapshot-message"),
    click: (id) => getElement(`#${id}`).click(),
    async changeProblem(id) {
      const select = getElement("#problem-select");
      select.value = id;
      const changing = select.listeners.change();
      await flush();
      saves.at(-1).resolve();
      await changing;
    },
    async recover(document) {
      stored = document;
      getElement("#saved-document-select").value = Store.storageId(document);
      const recovery = getElement("#open-document").click();
      await flush();
      saves.at(-1).resolve();
      await recovery;
    },
  };
}

module.exports = { page, flush, deferred };
