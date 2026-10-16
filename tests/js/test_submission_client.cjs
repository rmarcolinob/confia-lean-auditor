const test = require("node:test");
const assert = require("node:assert/strict");
const Client = require("../../app/confia_lean_auditor/static/capture/submission-client.js");
const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");
const snapshot = () => Model.freeze(Model.addPage(Model.createDraft("ITA2025Q1")));
function receipt(document) {
  return { submission_id: "sub_" + "a".repeat(32), status: "RECEIVED", source: "tablet", receipt_version: "1.0", capture_schema_version: "1.0",
    problem_id: document.problem_id, snapshot_id: document.local_snapshot_id, received_at: "2026-10-01T12:00:00Z",
    snapshot: { sha256: "b".repeat(64) }, page_images: document.pages.map(page => ({ page_id: page.page_id, page_index: page.index, sha256: "c".repeat(64) })) };
}

test("only frozen snapshots can be sent; no draft upload/render", async () => {
  const client = Client.create({ pngBlob() { throw Error("must not render draft"); } }, () => { throw Error("must not send"); });
  await assert.rejects(client.send(Model.createDraft("ITA2025Q1")), /Prepare/);
});

test("all pages use the existing renderer and original JSON/PNG bytes are transported without mutation", async () => {
  const document = snapshot();
  const original = JSON.stringify(document);
  const rendered = [];
  const requests = [];
  const client = Client.create({ async pngBlob(copy, id) {
    assert.notEqual(copy, document);
    assert.equal(JSON.stringify(copy), original);
    rendered.push(id);
    return new Blob([`original PNG bytes:${id}`], { type: "image/png" });
  } }, async (url, options) => {
    assert.equal(url, "/submissions");
    requests.push(options);
    return { ok: true, status: 201, json: async () => receipt(document) };
  });
  const result = await client.send(document);
  assert.equal(result.snapshot_id, document.local_snapshot_id);
  assert.equal(JSON.stringify(document), original);
  assert.deepEqual(rendered, document.pages.map(p => p.page_id));
  const body = JSON.parse(requests[0].body);
  assert.equal(body.snapshot_json, JSON.stringify(document, null, 2));
  assert.equal(body.pages.length, 2);
  body.pages.forEach(p => assert.equal(Buffer.from(p.png_base64, "base64").toString(), `original PNG bytes:${p.page_id}`));
  assert.equal(requests[0].method, "POST");
  assert.equal(requests[0].headers["Content-Type"], "application/json");
});

test("lost response retry reuses identical snapshot and PNG bytes, without another render", async () => {
  const document = snapshot();
  const bodies = [];
  let renderCount = 0;
  const client = Client.create({ async pngBlob() { renderCount++; return new Blob([String(renderCount)]); } }, async (_, options) => {
    bodies.push(options.body);
    if (bodies.length === 1) throw Error("lost response");
    return { ok: true, status: 200, json: async () => receipt(document) };
  });
  await assert.rejects(client.send(document), /preservada/);
  await client.send(document);
  assert.equal(bodies[0], bodies[1]);
  assert.equal(renderCount, document.pages.length);
});

test("another frozen snapshot rebuilds its own artifacts instead of reusing the previous version", async () => {
  let renders = 0;
  const client = Client.create({ async pngBlob() { renders++; return new Blob(["png"]); } }, async (_, options) => {
    return { ok: true, status: 201, json: async () => receipt(JSON.parse(JSON.parse(options.body).snapshot_json)) };
  });
  const first = snapshot(), second = snapshot();
  assert.notEqual(first.local_snapshot_id, second.local_snapshot_id);
  await client.send(first);
  const result = await client.send(second);
  assert.equal(result.snapshot_id, second.local_snapshot_id);
  assert.equal(renders, 4);
});

test("a conflict or server failure is never treated as a receipt", async () => {
  for (const status of [409, 422, 413, 503]) {
    const client = Client.create({ pngBlob: async () => new Blob(["png"]) }, async () => ({ ok: false, status }));
    await assert.rejects(client.send(snapshot()), status === 409 ? /Conflito/ : /não confirmou/);
  }
});

test("malformed successful response, mismatched ids, status and missing hashes are not success", async () => {
  const document = snapshot();
  for (const bad of [null, {}, { ...receipt(document), snapshot_id: "other" }, { ...receipt(document), status: "PENDING" },
    { ...receipt(document), problem_id: "other" }, { ...receipt(document), page_images: [] }, { ...receipt(document), snapshot: {} }]) {
    const client = Client.create({ pngBlob: async () => new Blob(["png"]) }, async () => ({ ok: true, status: 200, json: async () => bad }));
    await assert.rejects(client.send(document), /sem recibo válido/);
  }
});

test("HTTP 202 is not a received receipt even if the payload looks complete", async () => {
  const document = snapshot();
  const client = Client.create({ pngBlob: async () => new Blob(["png"]) }, async () => ({ ok: true, status: 202, json: async () => receipt(document) }));
  await assert.rejects(client.send(document), /sem recibo válido/);
});

test("concurrent repeated click does not create two requests", async () => {
  const document = snapshot();
  let complete, count = 0;
  const pending = new Promise(resolve => { complete = resolve; });
  const client = Client.create({ pngBlob: async () => new Blob(["png"]) }, async () => { count++; await pending; return { ok: true, status: 201, json: async () => receipt(document) }; });
  const first = client.send(document);
  await assert.rejects(client.send(document), /Aguarde/);
  complete();
  await first;
  assert.equal(count, 1);
});

test("Assessment sender uses item endpoint and checks server-derived binding", async () => {
  const document = snapshot();
  const assessmentId = "asmt_" + "a".repeat(32), itemId = "ait_" + "b".repeat(32);
  const target = `/assessments/${assessmentId}/items/${itemId}/submissions`;
  const calls = [];
  const client = Client.create({ pngBlob: async () => new Blob(["png"]) }, async (url, options) => {
    calls.push({ url, options });
    return { ok: true, status: 201, json: async () => ({ ...receipt(document), assessment_id: assessmentId, assessment_item_id: itemId }) };
  });
  assert.equal((await client.send(document, target)).assessment_item_id, itemId);
  assert.equal(calls[0].url, target);
  assert.equal(Object.hasOwn(JSON.parse(calls[0].options.body), "assessment_id"), false);
  await assert.rejects(client.send(document, "/assessments/other/items/other/submissions"), /Destino/);
  const bad = Client.create({ pngBlob: async () => new Blob(["png"]) }, async () => ({
    ok: true, status: 201, json: async () => ({ ...receipt(document), assessment_id: assessmentId, assessment_item_id: "ait_" + "c".repeat(32) }),
  }));
  await assert.rejects(bad.send(document, target), /não corresponde/);
});
