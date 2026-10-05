const test = require("node:test");
const assert = require("node:assert/strict");
const { id, record, detailData, transcriptionId, revision, summary, history, page, transportFor, descendants, flush, deferred, primaryText } = require("./teacher-dom.cjs");

test("teacher opens server inbox lazily, lists metadata and shows only original PNGs plus integrity", async () => {
  const ui = page(transportFor());
  assert.equal(ui.calls.length, 0);
  await ui.get('[data-tab-target="teacher-area"]').click();
  await flush();
  const button = ui.get("#manuscript-list").children[0];
  assert.match(button.textContent, /ITA2025Q1.*Recebida pelo ConfIA.*Transcrição: Ainda não criada.*Análise ConfIA: Não executada.*Abrir/);
  await button.click();
  const tree = descendants(ui.get("#manuscript-detail"));
  const image = tree.find(n => n.tag === "img");
  assert.equal(image.src, `/submissions/${id}/pages/0`);
  assert.match(tree.map(n => n.textContent).join(" "), /Arquivos originais conferidos e preservados/);
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
  assert.match(tree.map(n => n.textContent).join(" "), /arquivos originais desta solução precisam ser conferidos/);
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
  assert.match(ui.get("#manuscript-message").textContent, /Nenhuma solução/);
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
  assert.match(ui.get("#manuscript-message").textContent, /Não foi possível consultar as soluções/);
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
  assert.match(tree.map(n => n.textContent).join(" "), /Transcrição conferida.*não significa solução correta/);
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

test("teacher development action labels artificial recognition and opens NEEDS_REVIEW without accepting", async () => {
  let generated = false;
  const automatic = { ...revision, source: "automatic", provider: "fake_test", recognizer: "confia_fake_test", recognizer_version: "1.0.0", recognizer_run_id: "run_" + "c".repeat(32), reviewer_reference: "automatic:pending-human-review" };
  const transport = async (url, options = {}) => {
    if (url === "/submissions/recognition-providers") return { ok: true, json: async () => [{ provider: "fake_test", label: "Reconhecedor de teste" }] };
    if (options.method === "POST" && url.endsWith("/recognitions")) {
      const body = JSON.parse(options.body);
      assert.equal(body.provider, "fake_test");
      assert.match(body.idempotency_key, /^teacher:/);
      assert.equal(body.status, undefined);
      generated = true;
      return { ok: true, json: async () => ({ recognizer_run_id: automatic.recognizer_run_id, status: "NEEDS_REVIEW", transcription_id: transcriptionId, revision_number: 1 }) };
    }
    return { ok: true, json: async () => {
      if (url === "/submissions") return [record];
      if (url.endsWith("/transcriptions")) return generated ? [{ transcription: { ...summary.transcription, source: "automatic" }, latest_revision: automatic }] : [];
      if (url.startsWith("/transcriptions/")) return { transcription: { ...summary.transcription, source: "automatic" }, revisions: [automatic], acceptances: [] };
      return detailData();
    } };
  };
  const ui = page(transport);
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  let tree = descendants(ui.get("#manuscript-detail"));
  assert(tree.some(n => /não é OCR real/.test(n.textContent)));
  await tree.find(n => n.tag === "button" && /Gerar transcrição automática/.test(n.textContent)).click();
  tree = descendants(ui.get("#manuscript-detail"));
  assert(generated);
  assert(tree.some(n => /Origem automática.*fake_test.*run_c/.test(n.textContent)));
  assert(tree.some(n => /Aguardando conferência/.test(n.textContent)));
  assert.equal(tree.find(n => n.tag === "input").value, "professor-teste-01");
  assert(ui.calls.every(c => c.url !== "/audit" && !c.url.endsWith("/accept")));
});

test("teacher hides recognition action when no provider is enabled and disables it for corrupt source", async () => {
  for (const available of [false, true]) {
    const base = transportFor(false);
    const ui = page(async (url, options) => url === "/submissions/recognition-providers"
      ? { ok: true, json: async () => available ? [{ provider: "fake_test", label: "Reconhecedor de teste" }] : [] }
      : base(url, options));
    await ui.get("#refresh-manuscripts").click();
    await ui.get("#manuscript-list").children[0].click();
    const button = descendants(ui.get("#manuscript-detail")).find(n => n.tag === "button" && /Gerar transcrição automática/.test(n.textContent));
    assert.equal(Boolean(button), available);
    if (available) assert.equal(button.disabled, true);
  }
});

test("teacher preserves retry key and explains provider failure", async () => {
  const keys = [];
  const base = transportFor();
  const ui = page(async (url, options = {}) => {
    if (url === "/submissions/recognition-providers") return { ok: true, json: async () => [{ provider: "fake_test", label: "Reconhecedor de teste" }] };
    if (url.endsWith("/recognitions")) {
      keys.push(JSON.parse(options.body).idempotency_key);
      return { ok: true, json: async () => ({ status: "FAILED", error_code: "PROVIDER_FAILED" }) };
    }
    return base(url, options);
  });
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  const tree = descendants(ui.get("#manuscript-detail"));
  const button = tree.find(n => n.tag === "button" && /Gerar transcrição automática/.test(n.textContent));
  await button.click();
  assert.equal(button.disabled, false);
  assert(tree.some(n => /Nenhuma transcrição criada/.test(n.textContent)));
  await button.click();
  assert.equal(keys[0], keys[1]);
});

const editorTree = ui => descendants(ui.get("#manuscript-detail"));
const control = (ui, text) => editorTree(ui).find(n => n.tag === "button" && n.textContent === text);
async function opened(transport = transportFor(true, true)) {
  const ui = page(transport);
  await ui.get("#refresh-manuscripts").click();
  await ui.get("#manuscript-list").children[0].click();
  return ui;
}
function editLatex(ui, content = "2 + 2 = 6") {
  const textarea = editorTree(ui).find(n => n.tag === "textarea" && /LaTeX/.test(n.placeholder));
  textarea.value = content;
  textarea.emit("input");
  return textarea;
}

test("ACCEPTED is presented as Transcrição conferida and RECEIVED as Recebida pelo ConfIA", async () => {
  const base = transportFor(true, true);
  const ui = await opened(async url => url.startsWith("/transcriptions/")
    ? { ok: true, json: async () => ({ ...history, revisions: [{ ...revision, status: "ACCEPTED" }] }) }
    : base(url));
  assert.match(ui.get("#manuscript-list").textContent, /Recebida pelo ConfIA/);
  assert.match(ui.get("#manuscript-detail").textContent, /Transcrição conferida/);
  assert.doesNotMatch(primaryText(ui.get("#manuscript-detail")), /ACCEPTED|RECEIVED|solução aprovada/);
  assert.equal(control(ui, "Aceitar como fiel ao manuscrito").disabled, true);
});

test("edited transcription detects unsaved changes, blocks acceptance and preserves content when refresh is blocked", async () => {
  const ui = await opened();
  const edited = editLatex(ui);
  assert.match(ui.get("#manuscript-detail").textContent, /Alterações não salvas/);
  assert.equal(control(ui, "Aceitar como fiel ao manuscrito").disabled, true);
  const count = ui.calls.length;
  // Exercise the defensive handler even if a caller bypasses the disabled control.
  await control(ui, "Aceitar como fiel ao manuscrito").emit("click");
  await ui.get("#refresh-manuscripts").click();
  assert.equal(ui.calls.length, count);
  assert.equal(edited.value, "2 + 2 = 6");
  assert.equal(ui.get("#manuscript-detail").hidden, false);
  assert.match(ui.get("#manuscript-message").textContent, /Alterações não salvas.*antes de trocar o contexto/);
});

test("submission switch and mode switch are blocked while transcription is dirty", async () => {
  const idB = "sub_" + "c".repeat(32);
  const base = transportFor(true, true);
  const ui = await opened(async url => url === "/submissions"
    ? { ok: true, json: async () => [record, { ...record, submission_id: idB }] }
    : base(url));
  const edited = editLatex(ui);
  const count = ui.calls.length;
  await ui.get("#manuscript-list").children[1].click();
  await ui.get("#show-text-prototype").click();
  assert.equal(ui.calls.length, count);
  assert.equal(ui.get("#manuscript-inbox").hidden, false);
  assert.equal(edited.value, "2 + 2 = 6");
  assert.match(ui.get("#manuscript-message").textContent, /Alterações não salvas/);
});

test("explicit discard permits context switch and opens only the selected submission", async () => {
  const idB = "sub_" + "c".repeat(32);
  const base = transportFor(true, true);
  const ui = await opened(async url => {
    if (url === "/submissions") return { ok: true, json: async () => [record, { ...record, submission_id: idB }] };
    if (url === `/submissions/${idB}`) return { ok: true, json: async () => ({ ...detailData(), submission: { ...record, submission_id: idB, problem_id: "ITA2025Q4" } }) };
    if (url === `/submissions/${idB}/transcriptions`) return { ok: true, json: async () => [] };
    return base(url);
  });
  editLatex(ui);
  await control(ui, "Descartar alterações não salvas").click();
  await ui.get("#manuscript-list").children[1].click();
  assert.match(ui.get("#manuscript-detail").textContent, /ITA2025Q4/);
  assert.doesNotMatch(ui.get("#manuscript-detail").textContent, /2 \+ 2 = 6/);
});

test("discard restores the persisted revision and acceptance sends only its revision number", async () => {
  const ui = await opened();
  editLatex(ui);
  await control(ui, "Descartar alterações não salvas").click();
  assert.equal(editorTree(ui).find(n => n.tag === "textarea" && /LaTeX/.test(n.placeholder)).value, "2 + 2 = 5");
  assert.equal(control(ui, "Aceitar como fiel ao manuscrito").disabled, false);
  await control(ui, "Aceitar como fiel ao manuscrito").click();
  const call = ui.calls.find(c => c.url.endsWith("/accept"));
  const payload = JSON.parse(call.options.body);
  assert.equal(payload.revision_number, 1);
  assert.equal(payload.segments, undefined);
});

test("save creates a persisted revision before that revision can be accepted", async () => {
  let saved = revision;
  const base = transportFor(true, true);
  const ui = await opened(async (url, options = {}) => {
    if (options.method === "POST" && url.endsWith("/revisions")) {
      const body = JSON.parse(options.body);
      assert.equal(body.based_on_revision_number, 1);
      saved = { ...revision, revision_number: 2, segments: body.segments };
      return { ok: true, json: async () => saved };
    }
    if (url.startsWith("/transcriptions/") && !options.method) return { ok: true, json: async () => ({ ...history, revisions: [revision, saved] }) };
    return base(url, options);
  });
  editLatex(ui);
  await control(ui, "Salvar como nova revisão").click();
  assert.equal(control(ui, "Aceitar como fiel ao manuscrito").disabled, false);
  assert.match(ui.get("#manuscript-detail").textContent, /revisão persistida 2/);
  await control(ui, "Aceitar como fiel ao manuscrito").click();
  assert.equal(JSON.parse(ui.calls.find(c => c.url.endsWith("/accept")).options.body).revision_number, 2);
});

test("all editable transcription fields and added segments mark pending changes", async () => {
  for (const field of ["reviewer", "reason", "kind", "page", "text", "latex", "add"]) {
    const ui = await opened();
    const tree = editorTree(ui);
    let item;
    if (field === "add") await control(ui, "Adicionar segmento").click();
    else {
      if (field === "reviewer" || field === "reason") item = tree.filter(n => n.tag === "input")[field === "reviewer" ? 0 : 1];
      else item = tree.find(n => n.className === "transcription-segment").controls[field];
      item.value += " "; // Raw edits, including whitespace, must be detected.
      await item.emit("input");
    }
    assert.equal(control(ui, "Aceitar como fiel ao manuscrito").disabled, true, field);
    assert.match(tree.find(n => n.className === "transcription-dirty-message").textContent, /Alterações não salvas/);
  }
});

test("404 and revision conflict are translated while diagnostics stay in the console log", async () => {
  const base = transportFor(true, true);
  const ui404 = page(async url => url === "/submissions" ? base(url) : { ok: false, status: 404, json: async () => ({ detail: "missing_internal_record" }) });
  await ui404.get("#refresh-manuscripts").click();
  await ui404.get("#manuscript-list").children[0].click();
  assert.match(ui404.get("#manuscript-message").textContent, /Ela pode não estar mais disponível/);
  assert.doesNotMatch(ui404.get("#manuscript-message").textContent, /HTTP|missing_internal_record/);
  assert(ui404.logs.length >= 1);
  const ui409 = await opened(async (url, options = {}) => options.method === "POST"
    ? { ok: false, status: 409, json: async () => ({ detail: "revision_conflict" }) }
    : base(url));
  const edited = editLatex(ui409);
  await control(ui409, "Salvar como nova revisão").click();
  assert.match(ui409.get("#manuscript-detail").textContent, /Existe uma revisão mais recente da transcrição/);
  assert.doesNotMatch(ui409.get("#manuscript-detail").textContent, /HTTP|revision_conflict/);
  assert.equal(edited.value, "2 + 2 = 6");
  assert.equal(control(ui409, "Aceitar como fiel ao manuscrito").disabled, true);
});

test("switching transcription is guarded before loading another persisted history", async () => {
  const otherId = "tr_" + "d".repeat(32);
  const base = transportFor(true, true);
  const ui = await opened(async url => url.endsWith("/transcriptions")
    ? { ok: true, json: async () => [summary, { ...summary, transcription: { ...summary.transcription, transcription_id: otherId } }] }
    : base(url));
  const selection = editorTree(ui).find(n => n.tag === "select" && n.children.some(child => child.value === otherId));
  editLatex(ui);
  const count = ui.calls.length;
  selection.value = otherId;
  await selection.emit("change");
  assert.equal(selection.value, transcriptionId);
  assert.equal(ui.calls.length, count);
  assert.match(ui.get("#manuscript-message").textContent, /Alterações não salvas/);
});

test("pending save locks only incompatible editor changes and blocks a context refresh", async () => {
  const pending = deferred();
  const base = transportFor(true, true);
  const ui = await opened(async (url, options = {}) => options.method === "POST" ? pending.promise : base(url));
  const textarea = editLatex(ui);
  const saving = control(ui, "Salvar como nova revisão").click();
  assert.equal(textarea.disabled, true);
  assert.equal(control(ui, "Aceitar como fiel ao manuscrito").disabled, true);
  const count = ui.calls.length;
  await ui.get("#refresh-manuscripts").click();
  assert.equal(ui.calls.length, count);
  assert.match(ui.get("#manuscript-message").textContent, /Aguarde a operação/);
  pending.resolve({ ok: false, status: 503, json: async () => ({}) }); await saving;
  assert.equal(textarea.disabled, false);
});
