(function exposeDraftStore(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.ConfiaDraftStore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function makeDraftStore() {
  "use strict";

  const DB_NAME = "confia-capture-p2-cap-01";
  const DB_VERSION = 1;
  const STORE_NAME = "documents";

  function storageId(document) {
    return document.document_kind === "local_snapshot"
      ? document.local_snapshot_id
      : document.draft_id;
  }

  function openDatabase() {
    return new Promise((resolve, reject) => {
      if (!globalThis.indexedDB) {
        reject(new Error("IndexedDB não está disponível neste navegador."));
        return;
      }
      const request = globalThis.indexedDB.open(DB_NAME, DB_VERSION);
      request.onerror = () => reject(request.error || new Error("Falha ao abrir IndexedDB."));
      request.onupgradeneeded = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains(STORE_NAME)) {
          const store = database.createObjectStore(STORE_NAME, { keyPath: "storage_id" });
          store.createIndex("problem_id", "problem_id", { unique: false });
          store.createIndex("client_updated_at", "client_updated_at", { unique: false });
        }
      };
      request.onsuccess = () => resolve(request.result);
    });
  }

  async function transact(mode, action) {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, mode);
      const store = transaction.objectStore(STORE_NAME);
      let request;
      try {
        request = action(store);
      } catch (error) {
        database.close();
        reject(error);
        return;
      }
      transaction.oncomplete = () => {
        database.close();
        resolve(request ? request.result : undefined);
      };
      transaction.onerror = () => {
        database.close();
        reject(transaction.error || new Error("Falha ao acessar o armazenamento local."));
      };
      transaction.onabort = transaction.onerror;
    });
  }

  function save(document) {
    const id = storageId(document);
    if (!id) return Promise.reject(new Error("Documento sem identificador local."));
    const record = {
      storage_id: id,
      problem_id: document.problem_id,
      document_kind: document.document_kind,
      client_updated_at: document.client_updated_at,
      document: JSON.parse(JSON.stringify(document)),
    };
    return transact("readwrite", (store) => store.put(record));
  }

  async function get(id) {
    const record = await transact("readonly", (store) => store.get(id));
    return record ? record.document : null;
  }

  async function list(problemId) {
    const records = await transact("readonly", (store) => store.getAll());
    return records
      .filter((record) => !problemId || record.problem_id === problemId)
      .sort((left, right) => right.client_updated_at.localeCompare(left.client_updated_at))
      .map((record) => ({
        storage_id: record.storage_id,
        problem_id: record.problem_id,
        document_kind: record.document_kind,
        client_updated_at: record.client_updated_at,
      }));
  }

  return { DB_NAME, DB_VERSION, STORE_NAME, get, list, save, storageId };
});
