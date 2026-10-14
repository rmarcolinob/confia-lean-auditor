const test = require("node:test");
const assert = require("node:assert/strict");
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

test("explicit recognition waits for receipt and shows the review preview", async () => {
  const calls = [];
  const pending = deferred();
  const receipt = { submission_id: "sub_" + "a".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" };
  const ui = await page({
    sender: { async send() { return receipt; } },
    fetch: async (url, init) => {
      calls.push({ url, init });
      if (init?.method === "POST") return pending.promise;
      return { ok: true, json: async () => ({ status: "NEEDS_REVIEW", result: { segments: [
        { page_index: 0, text: "2 + 2 = 5", latex: "2 + 2 = 5" },
      ] } }) };
    },
  });
  await ui.recover(inkSnapshot());
  assert.equal(ui.get("#recognize-writing").disabled, true);
  await ui.click("send-solution");
  assert.equal(ui.get("#recognize-writing").disabled, false);
  assert.equal(calls.length, 0);
  const recognition = ui.click("recognize-writing");
  assert.equal(ui.get("#recognition-message").textContent, "Reconhecendo...");
  assert.equal(ui.get("#recognize-writing").disabled, true);
  assert.equal(calls.length, 1);
  const body = JSON.parse(calls[0].init.body);
  assert.equal(body.provider, "mathpix");
  assert.equal(body.idempotency_key, "mathpix:0");
  pending.resolve({ ok: true, json: async () => ({ status: "NEEDS_REVIEW", recognizer_run_id: "run_" + "b".repeat(32) }) });
  await recognition;
  assert.equal(calls.length, 2);
  assert.match(ui.get("#recognition-message").textContent, /precisa de revisão/);
  const preview = ui.get("#recognition-preview").children[0];
  assert.equal(preview.children[0].textContent, "Página 1");
  assert.equal(preview.children[1].textContent, "2 + 2 = 5");
  assert.equal(preview.children[2].textContent, "2 + 2 = 5");
  assert.equal(ui.get("#recognize-writing").disabled, false);
});

test("failed provider increments attempt, while lost response reuses request key", async () => {
  const keys = [];
  let mode = "network";
  const ui = await page({
    sender: { async send() { return { submission_id: "sub_" + "c".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" }; } },
    fetch: async (_, init) => {
      keys.push(JSON.parse(init.body).idempotency_key);
      if (mode === "network") throw new Error("network error");
      return { ok: true, json: async () => ({ status: "FAILED" }) };
    },
  });
  await ui.recover(inkSnapshot());
  await ui.click("send-solution");
  await ui.click("recognize-writing");
  assert.match(ui.get("#recognition-message").textContent, /network error/);
  mode = "failed";
  await ui.click("recognize-writing");
  await ui.click("recognize-writing");
  assert.equal(keys[0], keys[1]);
  assert.notEqual(keys[1], keys[2]);
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
  assert.equal(ui.messages.at(-1).context.controls.can_recognize,false); // Empty snapshot has no ink.
  await ui.command({action:"recognize-writing",problem_id:"ITA2025Q1",mode:"submission",document_id:frozen.controls.document_id});
  assert.equal(calls.some(call => call.kind === "recognize"),false);
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
    fetch:async (_url,init) => {
      if (init?.method === "POST") {
        keys.push(JSON.parse(init.body).idempotency_key);
        if (failed) return {ok:true,json:async () => ({status:"FAILED"})};
        return {ok:true,json:async () => ({status:"NEEDS_REVIEW",recognizer_run_id:"run_"+"a".repeat(32)})};
      }
      return {ok:true,json:async () => ({status:"NEEDS_REVIEW",result:{segments:[{page_index:0,text:"x = 2",latex:"x=2"}]}})};
    },
  });
  const values = {problem_id:"ITA2025Q1",mode:"submission",document_id:snapshot.local_snapshot_id};
  await ui.command({action:"send-solution",...values}); await flush();
  assert.equal(ui.messages.at(-1).context.controls.can_recognize,true);
  await ui.command({action:"recognize-writing",...values}); await flush();
  assert.match(ui.messages.at(-1).context.controls.recognition_message,/tentar uma nova leitura/);
  assert.equal(ui.messages.some(message => message.context.controls?.recognition_message === "Reconhecendo..."),true);
  assert.equal(ui.messages.at(-1).context.controls.can_recognize,true);
  failed = false;
  await ui.command({action:"recognize-writing",...values}); await flush();
  const controls = ui.messages.at(-1).context.controls;
  assert.match(controls.recognition_message,/precisa de revisão/);
  assert.equal(controls.recognition_segments[0].latex,"x=2");
  assert.deepEqual(keys,["mathpix:0","mathpix:1"]);
});
