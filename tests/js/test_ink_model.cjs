const test = require("node:test");
const assert = require("node:assert/strict");

const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");

function stroke(pageId, x = 10) {
  return {
    stroke_id: Model.newId("stroke"),
    page_id: pageId,
    pointer_type: "mouse",
    color: "#17355c",
    width: 4,
    interrupted: false,
    points: [
      { x, y: 20, t_ms: 0, pressure_reported: null },
      { x: x + 20, y: 30, t_ms: 10, pressure_reported: null },
    ],
  };
}

test("erase, undo and redo reconstruct the exact active state", () => {
  let document = Model.createDraft("ITA2025F2Q1");
  const first = stroke(document.pages[0].page_id);
  document = Model.addStroke(document, first);
  assert.deepEqual(document.active_stroke_ids, [first.stroke_id]);

  document = Model.eraseStroke(document, first.stroke_id);
  assert.deepEqual(document.active_stroke_ids, []);

  document = Model.undo(document);
  assert.deepEqual(document.active_stroke_ids, [first.stroke_id]);

  document = Model.redo(document);
  assert.deepEqual(document.active_stroke_ids, []);
  assert.deepEqual(Model.reconstructActive(document), document.active_stroke_ids);
});

test("pages keep their strokes isolated", () => {
  let document = Model.createDraft("ITA2025F2Q1");
  document = Model.addPage(document);
  const first = stroke(document.pages[0].page_id, 10);
  const second = stroke(document.pages[1].page_id, 100);
  document = Model.addStroke(document, first);
  document = Model.addStroke(document, second);

  assert.deepEqual(Model.activeStrokes(document, document.pages[0].page_id).map((item) => item.stroke_id), [first.stroke_id]);
  assert.deepEqual(Model.activeStrokes(document, document.pages[1].page_id).map((item) => item.stroke_id), [second.stroke_id]);
});

test("a frozen snapshot is independent from a continued draft", () => {
  let original = Model.createDraft("ITA2025F2Q1");
  original = Model.addStroke(original, stroke(original.pages[0].page_id));
  const snapshot = Model.freeze(original);
  let continued = Model.createDraft(snapshot.problem_id, snapshot);
  continued = Model.addStroke(continued, stroke(continued.pages[0].page_id, 300));

  assert.equal(snapshot.document_kind, "local_snapshot");
  assert.equal(snapshot.strokes.length, 1);
  assert.equal(continued.document_kind, "draft");
  assert.equal(continued.strokes.length, 2);
  assert.notEqual(continued.draft_id, snapshot.draft_id);
  assert.ok(snapshot.local_snapshot_id);
  assert.equal(continued.local_snapshot_id, null);
});

test("drafts for different questions have distinct identities and content", () => {
  let first = Model.createDraft("ITA2025F2Q1");
  first = Model.addStroke(first, stroke(first.pages[0].page_id));
  const second = Model.createDraft("ITA2025F2Q8");

  assert.notEqual(first.draft_id, second.draft_id);
  assert.equal(first.problem_id, "ITA2025F2Q1");
  assert.equal(second.problem_id, "ITA2025F2Q8");
  assert.equal(first.strokes.length, 1);
  assert.equal(second.strokes.length, 0);
});
