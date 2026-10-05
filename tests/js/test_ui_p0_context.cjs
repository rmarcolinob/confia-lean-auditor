const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { element, descendants, flush, deferred } = require("./ui-dom.cjs");
const source = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/app.js"), "utf8");
const problems = ["A", "B"].map(id => ({ problem_id: id, title: `Questão ${id}`, statement: `Enunciado ${id}`, examples: [{ key: "correct", label: "Exemplo" }] }));
const report = (id, summary = `Relatório ${id}`) => ({ problem_id: id, pedagogical_report: { result: "insuficiente", summary, score: 1, max_score: 10, evidence_items: [], attention_points: [] } });
const response = data => ({ ok: true, json: async () => data });
async function page(auditTransport, submissions = []) {
  const nodes = new Map(), calls = [], logs = [];
  const get = selector => {
    if (!nodes.has(selector)) nodes.set(selector, element(selector.endsWith("-select") ? "select" : "control"));
    return nodes.get(selector);
  };
  const areas = ["student-area", "teacher-area", "management-area"];
  const tabs = areas.map(id => { const button = element("button"); button.dataset.tabTarget = id; return button; });
  const panels = areas.map(id => { const panel = get(`#${id}`); panel.id = id; return panel; });
  const modes = ["study", "submit"].map(mode => { const button = element("button"); button.dataset.studentMode = mode; return button; });
  const store = new Map([["confia_student_submissions", JSON.stringify(submissions)]]);
  vm.runInNewContext(source, {
    document: { querySelector: get, createElement: element, querySelectorAll: selector => selector === "[data-tab-target]" ? tabs : selector === ".tab-panel" ? panels : modes },
    console: { error: (...args) => logs.push(args) },
    localStorage: { getItem: key => store.get(key), setItem: (key, value) => store.set(key, value) },
    fetch: async (url, options) => {
      calls.push({ url, options });
      if (url === "/problems") return response(problems);
      return auditTransport(url, options);
    },
  });
  await flush();
  return { get, tabs, modes, store, calls, logs };
}
const localSubmissions = ["A", "B"].map(id => ({ id: `local-${id}`, student_name: `Aluno ${id}`, problem_id: id, solution: `Solução ${id}`, status: "pendente", submitted_at: "2026-10-03T12:00:00Z" }));
function write(ui, text) { ui.get("#solution-input").value = text; return ui.get("#solution-input").emit("input"); }
function select(ui, id) { ui.get("#problem-select").value = id; return ui.get("#problem-select").emit("change"); }
function text(ui, selector = "#result-panel") { return ui.get(selector).textContent; }

test("student request and report retain original problem and solution when selection changes during analysis", async () => {
  const pending = deferred();
  const ui = await page(() => pending.promise);
  await write(ui, "Solução original A");
  await ui.get("#audit-button").click();
  assert.deepEqual(JSON.parse(ui.calls.at(-1).options.body), { problem_id: "A", solution: "Solução original A" });
  assert.equal(ui.get("#problem-select").disabled, false);
  await select(ui, "B");
  await write(ui, "Solução B");
  pending.resolve(response(report("A")));
  await flush();
  assert.match(text(ui), /Análise de versão anterior.*Questão analisada: A/);
  assert.match(text(ui), /Solução original A/);
  assert.equal(ui.get("#problem-title").textContent, "Questão B");
  assert.equal(ui.get("#solution-input").value, "Solução B");
  assert.equal(ui.get("#audit-button").textContent, "Analisar novamente");
});

test("editing after analysis marks the preserved report as stale and reanalysis restores current state", async () => {
  const ui = await page((url, options) => response(report(JSON.parse(options.body).problem_id)));
  await write(ui, "Primeira versão");
  await ui.get("#audit-button").click(); await flush();
  assert.match(text(ui), /Análise atual/);
  await write(ui, "Segunda versão");
  assert.match(text(ui), /Análise de versão anterior/);
  assert.match(text(ui), /Primeira versão/);
  await ui.get("#audit-button").click(); await flush();
  assert.match(text(ui), /Análise atual/);
  assert.doesNotMatch(text(ui), /Análise de versão anterior|Primeira versão/);
  assert.match(text(ui), /Segunda versão/);
});

test("changing the problem after a completed analysis marks the result stale", async () => {
  const ui = await page(() => response(report("A")));
  await write(ui, "Solução"); await ui.get("#audit-button").click(); await flush();
  await select(ui, "B");
  assert.match(text(ui), /Análise de versão anterior.*Questão analisada: A/);
});

test("teacher response for A does not update B and remains available when returning to A", async () => {
  const pending = deferred();
  const ui = await page(() => pending.promise, localSubmissions);
  const analysis = ui.get("#teacher-audit-button").click();
  const rowB = ui.get("#real-submission-list").children[1];
  await rowB.click();
  assert.equal(ui.get("#teacher-student-name").textContent, "Aluno B");
  assert.equal(ui.get("#teacher-audit-button").disabled, false);
  assert.match(text(ui, "#teacher-correction-panel"), /ainda não realizada/);
  pending.resolve(response(report("A", "Resposta exclusiva A")));
  await analysis;
  assert.doesNotMatch(text(ui, "#teacher-correction-panel"), /Resposta exclusiva A/);
  assert.match(ui.get("#teacher-submission-status").textContent, /Demonstração textual local/);
  await ui.get("#real-submission-list").children[0].click();
  assert.match(text(ui, "#teacher-correction-panel"), /Questão analisada: A.*Resposta exclusiva A/);
  assert.deepEqual(JSON.parse(ui.store.get("confia_student_submissions")), localSubmissions);
});

test("teacher concurrent A and B analyses keep independent processing and results", async () => {
  const requests = { A: deferred(), B: deferred() };
  const ui = await page((url, options) => requests[JSON.parse(options.body).problem_id].promise, localSubmissions);
  const runA = ui.get("#teacher-audit-button").click();
  await ui.get("#real-submission-list").children[1].click();
  const runB = ui.get("#teacher-audit-button").click();
  requests.A.resolve(response(report("A", "Resposta A"))); await runA;
  assert.equal(ui.get("#teacher-audit-button").disabled, true);
  assert.match(ui.get("#teacher-analysis-status").textContent, /Processando/);
  requests.B.resolve(response(report("B", "Resposta B"))); await runB;
  assert.match(text(ui, "#teacher-correction-panel"), /Resposta B/);
  assert.doesNotMatch(text(ui, "#teacher-correction-panel"), /Resposta A/);
  await ui.get("#real-submission-list").children[0].click();
  assert.match(text(ui, "#teacher-correction-panel"), /Resposta A/);
});

test("teacher failure for A never replaces the selected B report", async () => {
  const pending = deferred();
  const ui = await page(() => pending.promise, localSubmissions);
  const running = ui.get("#teacher-audit-button").click();
  await ui.get("#real-submission-list").children[1].click();
  pending.resolve({ ok: false, status: 500, text: async () => '{"error_code":"FAILED"}' });
  await running;
  assert.match(text(ui, "#teacher-correction-panel"), /ainda não realizada/);
  await ui.get("#real-submission-list").children[0].click();
  assert.match(text(ui, "#teacher-correction-panel"), /Não foi possível analisar esta solução agora/);
  assert.doesNotMatch(text(ui, "#teacher-correction-panel"), /HTTP|FAILED|error_code/);
  assert.equal(ui.logs.length, 1);
});

test("text submission explicitly describes local demonstration and keeps localStorage-only transport", async () => {
  const ui = await page(() => { throw Error("Unexpected transport"); });
  await ui.modes[1].click();
  assert.match(ui.get("#audit-button").textContent, /demonstração neste navegador/);
  ui.get("#student-name-input").value = "Aluno fictício";
  await write(ui, "Texto de teste");
  await ui.get("#audit-button").click();
  assert.match(text(ui), /Registro salvo neste navegador.*ainda não envia a solução ao servidor/);
  assert.equal(JSON.parse(ui.store.get("confia_student_submissions")).length, 1);
  assert.equal(ui.calls.filter(call => call.options?.method === "POST").length, 0);
});

test("audit error is translated, logged and leaves previous report intact on retry", async () => {
  let fail = false;
  const ui = await page(() => fail ? { ok: false, status: 422, text: async () => '{"detail":"technical error_code"}' } : response(report("A")));
  await write(ui, "Primeira solução"); await ui.get("#audit-button").click(); await flush();
  await write(ui, "Nova solução"); fail = true;
  await ui.get("#audit-button").click(); await flush();
  assert.match(text(ui), /Primeira solução/);
  assert.match(ui.get("#student-validation-message").textContent, /Não foi possível analisar/);
  assert.doesNotMatch(ui.get("#student-validation-message").textContent, /HTTP|detail|error_code/);
  assert.equal(ui.logs.length, 1);
});

test("validation marks the field, announces error and clears it after correction", async () => {
  const ui = await page(() => response(report("A")));
  await ui.get("#audit-button").click();
  assert.equal(ui.get("#solution-input").attributes["aria-invalid"], "true");
  assert.match(ui.get("#student-validation-message").textContent, /Digite ou carregue/);
  await write(ui, "Solução");
  assert.equal(ui.get("#solution-input").attributes["aria-invalid"], "false");
});

test("example loading cannot overwrite text edited during its request", async () => {
  const pending = deferred();
  const ui = await page(() => pending.promise);
  const loading = ui.get("#load-example").click();
  await write(ui, "Texto novo");
  pending.resolve(response({ solution: "Exemplo antigo" })); await loading;
  assert.equal(ui.get("#solution-input").value, "Texto novo");
  assert.match(ui.get("#service-status").textContent, /Exemplo não aplicado/);
});

test("changing mode during audit preserves its result for return to study", async () => {
  const pending = deferred();
  const ui = await page(() => pending.promise);
  await write(ui, "Solução A"); await ui.get("#audit-button").click();
  await ui.modes[1].click();
  pending.resolve(response(report("A"))); await flush();
  assert.match(text(ui), /Envio de demonstração local/);
  await ui.modes[0].click();
  assert.match(text(ui), /Questão analisada: A/);
});

test("continued editing does not rebuild an already stale report", async () => {
  const ui = await page(() => response(report("A")));
  await write(ui, "Primeira solução"); await ui.get("#audit-button").click(); await flush();
  await write(ui, "Segunda solução");
  const contextBlock = ui.get("#result-panel").children[0];
  await write(ui, "Segunda solução com mais texto");
  assert.equal(ui.get("#result-panel").children[0], contextBlock);
});

test("mismatched response is rejected and cannot be presented as the requested question", async () => {
  const ui = await page(() => response(report("B")));
  await write(ui, "Solução A"); await ui.get("#audit-button").click(); await flush();
  assert.match(text(ui), /Não foi possível analisar/);
  assert.doesNotMatch(text(ui), /Relatório B/);
  assert.equal(ui.logs.length, 1);
});

test("teacher retry failure keeps the earlier report and announces unavailable analysis", async () => {
  let fail = false;
  const ui = await page(() => fail ? { ok: false, status: 503, text: async () => "FAILED" } : response(report("A", "Relatório anterior A")), localSubmissions);
  await ui.get("#teacher-audit-button").click(); fail = true;
  await ui.get("#teacher-audit-button").click();
  assert.match(text(ui, "#teacher-correction-panel"), /Relatório anterior A/);
  assert.match(text(ui, "#teacher-correction-panel"), /Não foi possível analisar/);
  assert.match(ui.get("#teacher-analysis-status").textContent, /Não foi possível concluir/);
});

test("student response compares current field values even if an external edit emits no input event", async () => {
  const pending = deferred();
  const ui = await page(() => pending.promise);
  await write(ui, "Texto enviado A"); await ui.get("#audit-button").click();
  ui.get("#problem-select").value = "B";
  ui.get("#solution-input").value = "Texto atual B";
  pending.resolve(response(report("A"))); await flush();
  assert.match(text(ui), /Análise de versão anterior.*Questão analisada: A/);
});

test('UI-03 text analysis states reflect actual mocked requests and never change local evaluation data', async () => {
  const pending = deferred();
  let fail = false;
  let complete = false;
  const ui = await page(() => fail ? { ok: false, status: 503, text: async () => 'unavailable' } : complete ? response(report('A')) : pending.promise, localSubmissions);
  const status = ui.get('#teacher-analysis-status');
  assert.equal(status.dataset.analysisState, 'not-run');
  assert.equal(status.textContent, 'Análise ConfIA: Não executada');
  assert.equal(ui.calls.some(c => c.url === '/audit'), false);
  const run = ui.get('#teacher-audit-button').click();
  assert.equal(status.dataset.analysisState, 'processing');
  assert.equal(status.textContent, 'Análise ConfIA: Processando');
  pending.resolve(response(report('A'))); await run;
  complete = true;
  assert.equal(status.dataset.analysisState, 'completed');
  assert.equal(status.textContent, 'Análise ConfIA: Concluída');
  fail = true; await ui.get('#teacher-audit-button').click();
  assert.equal(status.dataset.analysisState, 'failed');
  assert.equal(status.textContent, 'Análise ConfIA: Não foi possível concluir');
  assert.deepEqual(JSON.parse(ui.store.get('confia_student_submissions')), localSubmissions);
});
