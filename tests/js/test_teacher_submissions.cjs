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
const flush = () => new Promise(resolve => setImmediate(resolve));
function element(tag) {
  return { tag, textContent: "", children: [], hidden: false, attributes: {}, listeners: {},
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
    fetch: async (url, options) => { calls.push({ url, options }); return transport(url); },
  });
  return { get, calls };
}
function descendants(node) { return [node, ...node.children.flatMap(descendants)]; }

test("teacher opens server inbox lazily, lists metadata and shows only original PNGs plus integrity", async () => {
  const ui = page(async url => ({ ok: true, json: async () => url === "/submissions" ? [record] : detailData() }));
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
  const ui = page(async url => ({ ok: true, json: async () => url === "/submissions" ? [record] : detailData(false) }));
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
  const ui = page(async url => fail ? { ok: false, status: 503 } : ({ ok: true, json: async () => url === "/submissions" ? [record] : detailData() }));
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
  const ui = page(async url => ({ ok: true, json: async () => url === "/submissions" ? [record] : pending }));
  await ui.get("#refresh-manuscripts").click();
  const opening = ui.get("#manuscript-list").children[0].click();
  await ui.get("#refresh-manuscripts").click();
  resolve(detailData());
  await opening;
  assert.equal(ui.get("#manuscript-detail").hidden, true);
  assert.equal(ui.get("#manuscript-detail").children.length, 0);
});
