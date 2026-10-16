const test = require("node:test");
const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");
const { page, flush, deferred } = require("./capture-dom.cjs");

function inkSnapshot() {
  const draft = Model.createDraft("ITA2025Q1");
  const written = Model.addStroke(draft, {
    page_id: draft.pages[0].page_id, pointer_type: "pen",
    points: [{ x: 10, y: 20, t_ms: 0, pressure_reported: 0.5 }],
  });
  return Model.freeze(written);
}

function previewResponse(init) {
  const body = JSON.parse(init.body);
  const snapshot = JSON.parse(body.snapshot_json);
  return { ok: true, json: async () => ({
    client_preview_id: body.client_preview_id, problem_id: snapshot.problem_id,
    snapshot_id: snapshot.local_snapshot_id,
    snapshot_sha256: createHash("sha256").update(body.snapshot_json).digest("hex"),
    page_count: snapshot.pages.length, active_stroke_count: snapshot.active_stroke_ids.length,
    result: { segments: [{ page_index: 0, order: 0, kind: "math", latex: "2 + 2 = 5" }] },
  }) };
}

test("successful send automatically starts official recognition and shows its review result", async () => {
  const calls = [];
  const pending = deferred();
  const receipt = { submission_id: "sub_" + "a".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" };
  const ui = await page({
    sender: { async send() { return receipt; } },
    fetch: async (url, init) => {
      if (url === "/submissions/recognition-preview") return previewResponse(init);
      calls.push({ url, init });
      if (init?.method === "POST") return pending.promise;
      return { ok: true, json: async () => ({ status: "NEEDS_REVIEW", result: { segments: [
        { page_index: 0, text: "2 + 2 = 5", latex: "2 + 2 = 5" },
      ] } }) };
    },
  });
  await ui.recover(inkSnapshot());
  assert.equal(ui.get("#recognize-writing").disabled, true);
  assert.equal(ui.get("#send-solution").disabled, true);
  await ui.click("preview-writing");
  const sending = ui.click("send-solution");
  await flush();
  assert.equal(ui.get("#recognition-message").textContent, "Reconhecendo a solução enviada...");
  assert.equal(ui.get("#recognize-writing").disabled, true);
  assert.equal(calls.length, 1);
  const body = JSON.parse(calls[0].init.body);
  assert.equal(body.provider, "mathpix");
  assert.equal(body.idempotency_key, "mathpix:0");
  pending.resolve({ ok: true, json: async () => ({ status: "NEEDS_REVIEW", recognizer_run_id: "run_" + "b".repeat(32) }) });
  await sending;
  assert.equal(calls.length, 2);
  assert.match(ui.get("#recognition-message").textContent, /aguarda conferência/);
  const preview = ui.get("#recognition-preview").children[0];
  assert.match(preview.children[0].textContent, /Página 1/);
  assert.equal(preview.children[1].textContent, "rendered:2 + 2 = 5");
  assert.equal(preview.children[2].children[1].textContent, "2 + 2 = 5");
  assert.equal(ui.get("#recognize-writing").disabled, true);
  assert.equal(ui.get("#recognize-writing").textContent, "Transcrição gerada");
});

test("automatic failure preserves receipt; retry reuses a lost key and advances a failed run", async () => {
  const keys = [];
  let mode = "network";
  const ui = await page({
    sender: { async send() { return { submission_id: "sub_" + "c".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" }; } },
    fetch: async (url, init) => {
      if (url === "/submissions/recognition-preview") return previewResponse(init);
      keys.push(JSON.parse(init.body).idempotency_key);
      if (mode === "network") throw new Error("network error");
      return { ok: true, json: async () => ({ status: "FAILED" }) };
    },
  });
  await ui.recover(inkSnapshot());
  await ui.click("preview-writing");
  await ui.click("send-solution");
  assert.match(ui.get("#submission-message").textContent, /Solução enviada.*Não foi possível gerar/);
  assert.equal(ui.get("#submission-receipt").hidden, false);
  assert.match(ui.get("#recognition-message").textContent, /Toque para tentar novamente/);
  await Promise.all([ui.click("recognize-writing"), ui.click("recognize-writing")]);
  assert.equal(keys.length, 2); // Automatic attempt plus one retry despite a double tap.
  mode = "failed";
  await ui.click("recognize-writing");
  await ui.click("recognize-writing");
  assert.equal(keys[0], keys[1]);
  assert.equal(keys[1], keys[2]);
  assert.notEqual(keys[2], keys[3]);
  assert.equal(ui.get("#recognition-preview").children.length, 0);
  await flush();
});

test("embedded controls use the capture handlers and reject stale or foreign commands", async () => {
  const calls = [];
  const receipt = { submission_id: "sub_" + "d".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" };
  const ui = await page({embedded:true,autoSave:true,search:"?embedded=1&problem_id=ITA2025Q1&mode=submission",
    sender:{ async send(snapshot) { calls.push({kind:"send",snapshot}); return receipt; } },
    fetch:async (url,init) => {
      calls.push({kind:init?.method === "POST" ? "recognize" : "read",url});
      if (init?.method === "POST") return {ok:true,json:async () => ({status:"NEEDS_REVIEW",recognizer_run_id:"run_"+"e".repeat(32)})};
      return {ok:true,json:async () => ({status:"NEEDS_REVIEW",result:{segments:[{page_index:0,text:"x = 2",latex:"x=2"}]}})};
    },
  });
  const initial = ui.messages.at(-1).context;
  assert.equal(initial.controls.can_prepare,true);
  const actionValues = {problem_id:"ITA2025Q1",mode:"submission",document_id:initial.controls.document_id};
  await ui.command({action:"mouse-mode",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.input_mode,"mouse");
  await ui.command({action:"pen-mode",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.input_mode,"pen");
  await ui.command({action:"erase-tool",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.active_tool,"erase");
  await ui.command({action:"draw-tool",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.active_tool,"draw");
  await ui.command({action:"add-page",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.page_count,2);
  assert.equal(ui.messages.at(-1).context.controls.page_index,1);
  await ui.command({action:"previous-page",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.page_index,0);
  await ui.command({action:"next-page",...actionValues});
  assert.equal(ui.messages.at(-1).context.controls.page_index,1);
  await ui.command({action:"undo",...actionValues});
  await ui.command({action:"redo",...actionValues});
  ui.events.message({origin:"https://foreign.test",source:ui.parent,data:{type:"confia-workspace-command",action:"prepare-snapshot",problem_id:"ITA2025Q1",mode:"submission",document_id:initial.controls.document_id}});
  await ui.command({action:"prepare-snapshot",problem_id:"ITA2025Q1",mode:"submission",document_id:"stale"});
  assert.equal(ui.messages.at(-1).context.controls.frozen,false);
  await ui.command({action:"prepare-snapshot",problem_id:"ITA2025Q1",mode:"submission",document_id:initial.controls.document_id});
  await flush();
  const frozen = ui.messages.at(-1).context;
  assert.equal(frozen.controls.frozen,true);
  assert.equal(frozen.controls.can_send,true);
  await ui.command({action:"send-solution",problem_id:"ITA2025Q1",mode:"submission",document_id:frozen.controls.document_id});
  await flush();
  assert.equal(calls.filter(call => call.kind === "send").length,1);
  assert.equal(calls.filter(call => call.kind === "recognize").length,1);
  await ui.command({action:"recognize-writing",problem_id:"ITA2025Q1",mode:"submission",document_id:frozen.controls.document_id});
  assert.equal(calls.filter(call => call.kind === "recognize").length,1);
  await ui.command({action:"continue-draft",problem_id:"ITA2025Q1",mode:"submission",document_id:frozen.controls.document_id});
  assert.equal(ui.messages.at(-1).context.controls.frozen,false);
});

test("embedded recognition reports loading, review preview and retry through the bridge", async () => {
  const snapshot = inkSnapshot();
  const receipt = { submission_id: "sub_" + "f".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" };
  const keys = [];
  let failed = true;
  const ui = await page({ embedded:true, autoSave:true, initialDocument:snapshot,
    search:`?embedded=1&problem_id=ITA2025Q1&mode=submission&draft_id=${snapshot.local_snapshot_id}`,
    sender:{ async send() { return receipt; } },
    fetch:async (url,init) => {
      if (url === "/submissions/recognition-preview") return previewResponse(init);
      if (init?.method === "POST") {
        keys.push(JSON.parse(init.body).idempotency_key);
        if (failed) return {ok:true,json:async () => ({status:"FAILED"})};
        return {ok:true,json:async () => ({status:"NEEDS_REVIEW",recognizer_run_id:"run_"+"a".repeat(32)})};
      }
      return {ok:true,json:async () => ({status:"NEEDS_REVIEW",result:{segments:[{page_index:0,text:"x = 2",latex:"x=2"}]}})};
    },
  });
  const values = {problem_id:"ITA2025Q1",mode:"submission",document_id:snapshot.local_snapshot_id};
  await ui.command({action:"preview-writing",...values}); await flush();
  await ui.command({action:"send-solution",...values}); await flush();
  assert.match(ui.messages.at(-1).context.controls.submission_message,/Solução enviada.*Não foi possível gerar/);
  assert.equal(ui.messages.at(-1).context.controls.can_recognize,true);
  failed = false;
  await ui.command({action:"recognize-writing",...values}); await flush();
  const controls = ui.messages.at(-1).context.controls;
  assert.match(controls.recognition_message,/aguarda conferência/);
  assert.equal(controls.recognition_segments[0].latex,"x=2");
  assert.deepEqual(keys,["mathpix:0","mathpix:1"]);
});

test("reload resends the same snapshot but replays the same official execution key", async () => {
  const snapshot = inkSnapshot();
  const receipt = { submission_id: "sub_" + "9".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" };
  const keys = [];
  const options = { initialDocument: snapshot,
    sender: { async send() { return receipt; } },
    fetch: async (url, init) => {
      if (url === "/submissions/recognition-preview") return previewResponse(init);
      if (init?.method === "POST") {
        keys.push(JSON.parse(init.body).idempotency_key);
        return { ok: true, json: async () => ({ status: "NEEDS_REVIEW", recognizer_run_id: "run_" + "8".repeat(32) }) };
      }
      return { ok: true, json: async () => ({ status: "NEEDS_REVIEW", result: { segments: [
        { page_index: 0, order: 0, kind: "math", latex: "x=1" },
      ] } }) };
    },
  };
  const first = await page(options);
  await first.recover(snapshot);
  await first.click("preview-writing");
  await first.click("send-solution");
  const reloaded = await page(options);
  await reloaded.recover(snapshot);
  await reloaded.click("preview-writing");
  await reloaded.click("send-solution");
  assert.deepEqual(keys, ["mathpix:0", "mathpix:0"]);
  assert.equal(reloaded.get("#recognition-preview").children[0].children[1].textContent, "rendered:x=1");
});
