const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/submissions/teacher.js"), "utf8");
const recognitionView = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/recognition-view.js"), "utf8");
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
const { element, descendants, flush, deferred } = require("./ui-dom.cjs");
function page(transport, search = "") {
  const elements = new Map(), calls = [];
  const get = (selector) => {
    if (!elements.has(selector)) elements.set(selector, element("control"));
    return elements.get(selector);
  };
  get("#teacher-text-prototype").hidden = true;
  get("#manuscript-detail").hidden = true;
  const logs = [], reports = [];
  const context = {
    console: { error: (...args) => logs.push(args) },
    window: { addEventListener() {}, ConfIAReport: { render(data, target, options) {
      reports.push({ data, target, options });
      target.appendChild(element("p")).textContent = data.pedagogical_report?.summary || "Resultado do auditor";
    } } },
    document: { querySelector: get, createElement: element },
    location: { search }, URLSearchParams,
    fetch: async (url, options) => { calls.push({ url, options }); return transport(url, options); },
    katex: { render(latex, target) { target.textContent = `rendered:${latex}`; } },
  };
  vm.runInNewContext(recognitionView, context);
  vm.runInNewContext(source, context);
  return { get, calls, logs, reports };
}
function transportFor(matches = true, withTranscription = false) {
  return async url => ({ ok: true, json: async () => {
    if (url === "/submissions") return [record];
    if (url.endsWith("/audits")) return [];
    if (url.endsWith("/transcriptions")) return withTranscription ? [summary] : [];
    if (url.startsWith("/transcriptions/")) return history;
    return detailData(matches);
  } });
}

function primaryText(n) {
  if (n.tag === "details") return n.children[0]?.textContent || "";
  if (!n.children.length) return n.textContent;
  return n.children.map(primaryText).join(" ");
}
module.exports = { id, record, detailData, transcriptionId, revision, summary, history, page, transportFor, element, descendants, flush, deferred, primaryText };
