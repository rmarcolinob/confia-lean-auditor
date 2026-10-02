const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/submissions/teacher.js"), "utf8");
const id = "sub_" + "a".repeat(32);
const record = { submission_id: id, problem_id: "ITA2025Q1", snapshot_id: "snapshot:1", received_at: "2026-10-01T12:00:00Z", status: "RECEIVED", source: "tablet", capture_schema_version: "1.0",
  student_reference: "<img src=x onerror=unsafe> (teste)", page_images: [{ filename: "page_1.png", page_index: 0 }] };
const detailData = (matches = true) => ({ submission: record, receipt: record, integrity: [
  { filename: "snapshot.json", expected_sha256: "a".repeat(64), actual_sha256: "a".repeat(64), matches: true },
  { filename: "page_1.png", expected_sha256: "b".repeat(64), actual_sha256: matches ? "b".repeat(64) : null, matches },
] });
const transcriptionId = "tr_" + "b".repeat(32);
const revision = { transcription_id: transcriptionId, submission_id: id, created_at: "2026-10-01T13:00:00Z", source: "manual", recognizer: null, recognizer_version: null,
  revision_number: 1, based_on_revision_number: null, reviewer_reference: "professor-teste-01", reviewer_identity_verified: false,
  change_type: "initial_transcription", change_reason: null, status: "NEEDS_REVIEW", segments: [
    { segment_id: "seg:1", page_index: 0, order: 0, kind: "math", text: null, latex: "2 + 2 = 5", confidence: null, source_region: null, source_stroke_refs: null },
  ] };
const summary = { transcription: { transcription_id: transcriptionId, submission_id: id, created_at: revision.created_at, source: "manual", recognizer: null, recognizer_version: null }, latest_revision: revision };
const history = { transcription: summary.transcription, revisions: [revision], acceptances: [] };
const flush = () => new Promise(resolve => setImmediate(resolve));
function element(tag) {
  return { tag, textContent: "", children: [], hidden: false, attributes: {}, listeners: {}, dataset: {},
    setAttribute(k, v) { this.attributes[k] = v; },
    appendChild(child) { this.children.push(child); },
    replaceChildren() { this.children = []; },
    addEventListener(event, fn) { this.listeners[event] = fn; },
    click() { return this.listeners.click?.(); },
  };
}
function page(transport, search = "") {
  const elements = new Map(), calls = [];
  const get = (selector) => {
    if (!elements.has(selector)) elements.set(selector, element("control"));
    return elements.get(selector);
  };
  get("#teacher-text-prototype").hidden = true;
  get("#manuscript-detail").hidden = true;
  vm.runInNewContext(source, {
    document: { querySelector: get, createElement: element },
    location: { search }, URLSearchParams,
    fetch: async (url, options) => { calls.push({ url, options }); return transport(url, options); },
  });
  return { get, calls };
}
function descendants(node) { return [node, ...node.children.flatMap(descendants)]; }
function transportFor(matches = true, withTranscription = false) {
  return async url => ({ ok: true, json: async () => {
    if (url === "/submissions") return [record];
    if (url.endsWith("/transcriptions")) return withTranscription ? [summary] : [];
    if (url.startsWith("/transcriptions/")) return history;
    return detailData(matches);
  } });
}

test("teacher opens server inbox lazily, lists metadata and shows only original PNGs plus integrity", async () => {
  const ui = page(transportFor());
  assert.equal(ui.calls.length, 0);
  await ui.get('[data-tab-target="teacher-area"]').click();
  await flush();
  const button = ui.get("#manuscript-list").children[0];
  assert.match(button.textContent, /ITA2025Q1.*RECEIVED.*sub_a{32}/);
  await button.click();
  const tree = descendants(ui.get("#manuscript-detail"));
  const image = tree.find(n => n.tag === "img");
  assert.equal(image.src, `/submissions/${id}/pages/0`);
  assert.match(tree.map(n => n.textContent).join(" "), /hashes SHA-256 conferem/);
  assert.match(tree.find(n => n.textContent.includes("Referência não verificada")).textContent, /<img src=x onerror=unsafe>/);
  assert.equal(tree.filter(n => n.tag === "img").length, 1); // Reference stayed text, not HTML.
  assert.equal(ui.get("#manuscript-detail").hidden, false);
  assert.equal(ui.get("#teacher-text-prototype").hidden, true);
  assert(ui.calls.every(c => c.url.startsWith("/submissions") && c.options.cache === "no-store"));
});

test("corrupt PNG is not loaded and divergence is explained", async () => {
  const ui = page(transportFor(false));
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  const tree = descendants(ui.get("#manuscript-detail"));
  assert.equal(tree.some(n => n.tag === "img"), false);
  assert.match(tree.map(n => n.textContent).join(" "), /hash divergente/);
});

test("inbox and existing correction prototype are mutually exclusive without new audit requests", async () => {
  const ui = page(async () => ({ ok: true, json: async () => [] }));
  ui.get("#show-text-prototype").click();
  assert.equal(ui.get("#teacher-text-prototype").hidden, false);
  assert.equal(ui.get("#manuscript-inbox").hidden, true);
  assert.equal(ui.calls.length, 0);
  ui.get("#show-manuscripts").click();
  await flush();
  assert.equal(ui.get("#teacher-text-prototype").hidden, true);
  assert.equal(ui.get("#manuscript-inbox").hidden, false);
  assert.match(ui.get("#manuscript-message").textContent, /Nenhuma submissão/);
});

test("failed list and detail requests do not leave stale received artifacts on screen", async () => {
  let fail = false;
  const ui = page(async url => fail ? { ok: false, status: 503, json: async () => ({}) } : transportFor()(url));
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  assert.equal(ui.get("#manuscript-detail").hidden, false);
  fail = true;
  await ui.get("#manuscript-list").children[0].click();
  assert.equal(ui.get("#manuscript-detail").hidden, true);
  assert.equal(ui.get("#manuscript-detail").children.length, 0);
  await ui.get("#refresh-manuscripts").click();
  assert.equal(ui.get("#manuscript-list").children.length, 0);
  assert.match(ui.get("#manuscript-message").textContent, /HTTP 503/);
});

test("refresh invalidates an older pending detail response", async () => {
  let resolve;
  const pending = new Promise(yes => { resolve = yes; });
  const ui = page(async url => ({ ok: true, json: async () => url === "/submissions" ? [record] : url.endsWith("/transcriptions") ? [] : pending }));
  await ui.get("#refresh-manuscripts").click();
  const opening = ui.get("#manuscript-list").children[0].click();
  await ui.get("#refresh-manuscripts").click();
  resolve(detailData());
  await opening;
  assert.equal(ui.get("#manuscript-detail").hidden, true);
  assert.equal(ui.get("#manuscript-detail").children.length, 0);
});

test("teacher shows original and editable transcription side by side with history and no audit call", async () => {
  const ui = page(transportFor(true, true));
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  const tree = descendants(ui.get("#manuscript-detail"));
  assert(tree.some(n => n.className === "transcription-workspace"));
  assert(tree.some(n => n.className === "original-manuscript-panel"));
  assert(tree.some(n => n.className === "transcription-panel"));
  assert.match(tree.map(n => n.textContent).join(" "), /2 \+ 2 = 5/);
  assert.match(tree.map(n => n.textContent).join(" "), /ACCEPTED.*não significa solução correta/);
  assert(ui.calls.some(c => c.url === `/transcriptions/${transcriptionId}`), JSON.stringify(ui.calls));
  assert(ui.calls.every(c => c.url !== "/audit"));
});

test("teacher creates a manual transcription and accepts fidelity without an audit request", async () => {
  let created = false;
  let accepted = false;
  let savedRevision = null;
  const localSummary = { ...summary, latest_revision: { ...revision } };
  const localHistory = { ...history, revisions: [{ ...revision }], acceptances: [] };
  const transport = async (url, options = {}) => {
    if (options.method === "POST" && url.endsWith("/transcriptions")) {
      const body = JSON.parse(options.body);
      assert.equal(body.source, "manual");
      assert.equal(body.segments[0].latex, "2 + 2 = 5");
      savedRevision = { ...revision, segments: body.segments };
      localSummary.latest_revision = savedRevision;
      localHistory.revisions = [savedRevision];
      created = true;
      return { ok: true, json: async () => savedRevision };
    }
    if (options.method === "POST" && url.endsWith("/accept")) {
      const body = JSON.parse(options.body);
      assert.equal(body.revision_number, 1);
      assert.equal(body.reviewer_identity_verified, false);
      accepted = true;
      localHistory.revisions = [{ ...savedRevision, status: "ACCEPTED" }];
      return { ok: true, json: async () => ({ revision: localHistory.revisions[0], acceptance: { mathematical_validity_assessed: false } }) };
    }
    return { ok: true, json: async () => {
      if (url === "/submissions") return [record];
      if (url.endsWith("/transcriptions")) return created ? [localSummary] : [];
      if (url.startsWith("/transcriptions/")) return localHistory;
      return detailData();
    } };
  };
  const ui = page(transport);
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  let tree = descendants(ui.get("#manuscript-detail"));
  tree.find(n => n.tag === "textarea" && /LaTeX/.test(n.placeholder)).value = "2 + 2 = 5";
  await tree.find(n => n.textContent === "Criar transcrição manual").click();
  assert.equal(created, true);
  tree = descendants(ui.get("#manuscript-detail"));
  await tree.find(n => n.textContent === "Aceitar como fiel ao manuscrito").click();
  assert.equal(accepted, true);
  assert(ui.calls.every(c => c.url !== "/audit"));
});
