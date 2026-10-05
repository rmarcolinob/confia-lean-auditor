const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");

const { page, flush, deferred } = require("./capture-dom.cjs");

test("automatic page changes show saving until the store confirms success", async () => {
  const ui = await page();
  assert.equal(ui.indicator.dataset.state, "idle");
  assert.equal(ui.saves.length, 0);
  ui.click("add-page");
  assert.equal(ui.indicator.textContent, "Salvando...");
  await flush();
  assert.equal(ui.saves.length, 1);
  ui.saves[0].resolve();
  await flush();
  assert.equal(ui.indicator.textContent, "Rascunho salvo neste dispositivo");
});

test("legacy and delimited math render on load/change and survive collapse/expand", async () => {
  const first = "Texto comum x^57+ax^14";
  const second = String.raw`Outro enunciado \[\frac{1}{2}\]`;
  const problems = [
    { problem_id: "ITA2025Q1", title: "Questão 1", statement: first },
    { problem_id: "ITA2025Q3", title: "Questão 3", statement: second },
  ];
  const ui = await page({ problems });
  assert.deepEqual(ui.mathRenders, [first]);
  ui.click("toggle-problem");
  assert.equal(ui.statementWrap.hidden, true);
  assert.equal(ui.statement.textContent, first);
  ui.click("toggle-problem");
  assert.equal(ui.statementWrap.hidden, false);
  assert.equal(ui.statement.textContent, first);
  assert.deepEqual(ui.mathRenders, [first]);
  await ui.changeProblem("ITA2025Q3");
  assert.deepEqual(ui.mathRenders, [first, second]);
  ui.click("toggle-problem");
  ui.click("toggle-problem");
  assert.equal(ui.statementWrap.hidden, false);
  assert.equal(ui.statement.textContent, second);
  assert.equal(problems[0].statement, first);
  assert.equal(problems[1].statement, second);
});

test("failed saves stay visible and exporting does not imply local persistence", async () => {
  const ui = await page();
  ui.click("add-page");
  await flush();
  ui.saves[0].reject(new Error("Quota excedida"));
  await flush();
  assert.equal(ui.indicator.textContent, "Não foi possível salvar o rascunho");
  ui.click("export-json");
  assert.equal(ui.indicator.dataset.state, "error");
  assert.equal(ui.indicator.textContent, "Não foi possível salvar o rascunho");
});

test("an earlier completed save cannot mark newer pending changes as saved", async () => {
  const ui = await page();
  ui.click("add-page");
  await flush();
  ui.click("add-page");
  ui.saves[0].resolve();
  await flush();
  assert.equal(ui.saves.length, 2);
  assert.equal(ui.indicator.textContent, "Salvando...");
  ui.saves[1].resolve();
  await flush();
  assert.equal(ui.indicator.textContent, "Rascunho salvo neste dispositivo");
});

test("recovery confirms persistence and a new unsaved draft resets the indicator", async () => {
  const ui = await page();
  await ui.recover(Model.createDraft("ITA2025Q1"));
  assert.equal(ui.indicator.textContent, "Rascunho salvo neste dispositivo");
  const creating = ui.click("new-draft");
  await flush();
  ui.saves.at(-1).resolve();
  await creating;
  assert.equal(ui.indicator.dataset.state, "idle");
  assert.equal(ui.indicator.textContent, "Comece a escrever — salvamento automático");
});

test("a recovered frozen copy is not labelled as an editable draft", async () => {
  const ui = await page();
  await ui.recover(Model.freeze(Model.createDraft("ITA2025Q1")));
  assert.equal(ui.indicator.textContent, "Cópia local salva neste dispositivo");
});

test("unavailable storage is visible even before the first edit", async () => {
  const ui = await page({ listError: true });
  assert.equal(ui.indicator.textContent, "Armazenamento local indisponível");
  ui.click("add-page");
  await flush();
  ui.saves[0].reject(new Error("IndexedDB indisponível"));
  await flush();
  assert.equal(ui.indicator.textContent, "Não foi possível salvar o rascunho");
});

test("capture supplies the shared curated registry and current problem id on load/change", async () => {
  const registry = JSON.parse(fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/problem-presentations/registry.json"), "utf8"));
  const problems = registry.map(entry => ({ problem_id: entry.problem_id, title: entry.problem_id, statement: entry.source_statement }));
  const ui = await page({ registry, problems });
  assert.equal(ui.mathContexts[0].problemId, "ITA2025Q1");
  assert.equal(ui.mathContexts[0].registry, registry);
  await ui.changeProblem("ITA2025Q5");
  assert.equal(ui.mathContexts.at(-1).problemId, "ITA2025Q5");
  assert.equal(ui.mathContexts.at(-1).registry, registry);
  assert.equal(ui.statement.textContent, problems.find(problem => problem.problem_id === "ITA2025Q5").statement);
  ui.click("toggle-problem");
  ui.click("toggle-problem");
  assert.equal(ui.statementWrap.hidden, false);
  assert.equal(ui.mathContexts.length, 2);
});

test("a failed presentation fetch does not disable capture or automatic saving", async () => {
  const ui = await page({ registryError: true });
  assert.equal(ui.mathContexts[0].registry.length, 0);
  ui.click("add-page");
  await flush();
  assert.equal(ui.saves.length, 1);
  ui.saves[0].resolve();
  await flush();
  assert.equal(ui.indicator.textContent, "Rascunho salvo neste dispositivo");
});

test("submission is disabled for drafts and receipt is shown only after the server confirms", async () => {
  const response = deferred();
  let sent = null;
  const ui = await page({ sender: { send(snapshot) { sent = snapshot; return response.promise; } } });
  assert.equal(ui.sendButton.disabled, true);
  const snapshot = Model.freeze(Model.createDraft("ITA2025Q1"));
  await ui.recover(snapshot);
  assert.equal(ui.sendButton.disabled, false);
  assert.equal(ui.receipt.hidden, true);
  assert.equal(ui.indicator.textContent, "Cópia local salva neste dispositivo");
  const sending = ui.click("send-solution");
  assert.equal(ui.sendButton.disabled, true);
  assert.match(ui.sendMessage.textContent, /Enviando/);
  assert.equal(ui.receipt.hidden, true);
  assert.equal(sent.local_snapshot_id, snapshot.local_snapshot_id);
  assert.notEqual(sent, snapshot);
  response.resolve({ submission_id: "sub_" + "a".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" });
  await sending;
  assert.equal(ui.sendMessage.textContent, "Solução recebida pelo ConfIA");
  assert.equal(ui.receipt.hidden, false);
  assert.equal(ui.snapshotMessage.textContent, "Versão congelada preservada neste dispositivo.");
  assert.match(ui.receipt.textContent, /sub_a{32}/);
  assert.equal(ui.indicator.textContent, "Cópia local salva neste dispositivo");
});

test("failed submission preserves snapshot/local status and allows a retry", async () => {
  const calls = [];
  const ui = await page({ sender: { async send(snapshot) { calls.push(snapshot); throw new Error("Sem confirmação do servidor"); } } });
  const snapshot = Model.freeze(Model.createDraft("ITA2025Q1"));
  await ui.recover(snapshot);
  const localSaveCount = ui.saves.length;
  await ui.click("send-solution");
  assert.match(ui.sendMessage.textContent, /Sem confirmação/);
  assert.equal(ui.receipt.hidden, true);
  assert.equal(ui.sendButton.disabled, false);
  assert.match(ui.snapshotMessage.textContent, /recebimento pelo servidor ainda não confirmado/);
  await ui.click("send-solution");
  assert.equal(calls.length, 2);
  assert.equal(calls[0].local_snapshot_id, calls[1].local_snapshot_id);
  assert.equal(ui.saves.length, localSaveCount);
  assert.equal(ui.indicator.textContent, "Cópia local salva neste dispositivo");
});

test("receipt for an earlier snapshot cannot appear on a new editable draft", async () => {
  const response = deferred();
  const ui = await page({ sender: { send: () => response.promise } });
  await ui.recover(Model.freeze(Model.createDraft("ITA2025Q1")));
  const sending = ui.click("send-solution");
  ui.click("continue-draft");
  response.resolve({ submission_id: "sub_" + "b".repeat(32), received_at: "2026-10-01T12:00:00Z", problem_id: "ITA2025Q1" });
  await sending;
  assert.equal(ui.receipt.hidden, true);
  assert.equal(ui.sendButton.disabled, true);
  assert.doesNotMatch(ui.sendMessage.textContent, /Solução recebida/);
  await flush();
  ui.saves.at(-1).resolve();
  await flush();
});
