(function () {
  "use strict";
  const root = document.querySelector("#app");
  const state = { cases: [], current: null, history: null, audit: null, photos: [], message: "",
    feedback: null, busy: false, adjusting: false, cache: new Map(), view: "home", homePeriod: "today", generation: 0, filters: { cases: {}, results: {} } };
  const Home = window.ConfiaTmeHome;
  const Workspace = window.ConfiaCorrectionWorkspace;
  const Views = window.ConfiaTmeViews;
  let fullExam;
  const viewNames = {home:"home",queue:"cases",cases:"cases",new:"new",results:"results",exams:"exams"};
  let currentURL = "", returnTo = {view:"cases",params:{}};
  function locationRoute() {
    const query = new URLSearchParams(window.location.search || "");
    if(query.get("case_id")) return {view:"workspace",caseId:query.get("case_id")};
    if(query.get("exam_submission_id")) return {view:"workspace",examId:query.get("exam_submission_id"),attemptId:query.get("question_attempt_id")};
    const params={};for(const key of ["search","question","status","source","origin","sample","exam","page"]) if(query.get(key))params[key]=query.get(key);
    return {view:viewNames[query.get("view")] || "home",params};
  }
  function writeRoute(view, params={}, caseId=null, replace=false) {
    const query=new URLSearchParams();
    if(params.exam_submission_id){query.set("exam_submission_id",params.exam_submission_id);if(params.question_attempt_id)query.set("question_attempt_id",params.question_attempt_id);}
    else if(caseId) query.set("case_id",caseId);
    else { if(view!=="home")query.set("view",view==="cases"?"queue":view);for(const key of ["search","question","status","source","origin","sample","exam","page"])if(params[key]&&!(key==="page"&&String(params[key])==="1"))query.set(key,params[key]); }
    const url="/tme"+(query.toString()?`?${query}`:"");
    const changed=url!==currentURL;
    if(changed || replace)window.history?.[replace?"replaceState":"pushState"]?.({tme:true,origin:returnTo},"",url);
    currentURL=url;
    return changed;
  }
  const route = id => writeRoute("workspace",{},id);
  function navigate(view, params, record=true) {
    if(state.busy)return;
    fullExam?.cancel();
    view=viewNames[view] || "home";
    if(view==="cases"||view==="exams"){
      state.filters[view]=params ? {...params} : {...(state.filters[view]||{})};
      params=state.filters[view];
    }else params={};
    if(record && !writeRoute(view,params) && state.view===view && state.navigationPending)return state.navigationPending;
    window.scrollTo(0,0);document.querySelector("#main")?.scrollTo?.(0,0);
    const pending=Promise.resolve(view==="home"?home():view==="new"?newCase():listing(view)).catch(showError)
      .finally(()=>{if(state.navigationPending===pending)state.navigationPending=null;});
    state.navigationPending=pending;return pending;
  }
  async function restoreRoute(){
    const target=locationRoute();
    if(state.busy){window.history?.replaceState?.({tme:true,origin:returnTo},"",currentURL);return;}
    currentURL="/tme"+(window.location.search||"");
    returnTo=window.history?.state?.origin||{view:"cases",params:{}};
    if(target.examId)return openExam(target.examId,target.attemptId,false);
    if(target.caseId)return openCase(target.caseId,false).catch(showError);
    return navigate(target.view,target.params,false);
  }
  window.addEventListener("popstate",restoreRoute);
  async function home() {
    state.view = "home";
    const generation = ++state.generation;
    let summary;
    const render = status => {
      if (generation !== state.generation) return;
      show(Home.TmeHome({ summary, state: status, period: state.homePeriod,
        changePeriod: async value => { state.homePeriod = value; await home(); document.querySelector(".home-overview select")?.focus(); }, navigate,
        open: id => openCase(id).catch(showError), retry: home }));
    };
    render("loading");
    try { summary = await api(`/tme/home-summary?period=${encodeURIComponent(state.homePeriod)}`); render("success"); } catch (_) { summary = undefined; render("error"); }
  }
  const Scan = window.ConfiaTMEScan;
  const maxPages = Scan.maxPages;
  const node = (tag, value, className) => {
    const item = document.createElement(tag);
    if (value !== undefined) item.textContent = value;
    if (className) item.className = className;
    return item;
  };
  const btn = (label, action, cls = "") => {
    const item = node("button", label, cls); item.type = "button"; item.addEventListener("click", action); return item;
  };
  const card = (title) => { const item = node("section", undefined, "card"); if (title) item.appendChild(node("h2", title)); return item; };
  const actions = (...children) => { const item = node("div", undefined, "actions"); item.append(...children); return item; };
  const field = (title, control) => { const label = node("label", title); label.appendChild(control); return label; };
  const show = (...children) => { root.dataset.view = state.view; if (document.body) document.body.dataset.view = state.view; root.replaceChildren(...children); renderRecentCases(); };
  const note = (message, error = false) => { const p = node("p", message, `message${error ? " error" : ""}`); p.setAttribute("role", "status"); p.setAttribute("aria-live", "polite"); return p; };
  async function api(path, options = {}) {
    const response = await fetch(path, { cache: "no-store", credentials: "same-origin", ...options,
      headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) } });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const captureError = path.startsWith("/tme/exam-submissions") && ({
        409: "A prova ou associação mudou. Reabra a prova e confira os dados antes de tentar novamente.",
        413: "A prova excede o limite de envio. Use até 40 MiB de originais.",
        422: "Confira o código e os arquivos: PDF íntegro e sem senha, ou imagens válidas, até 50 páginas e 20 MiB por arquivo."
      })[response.status];
      const error = new Error(response.status === 401 ? "A sessão não está disponível. Acesse novamente para continuar." : captureError || "Não foi possível concluir esta etapa. Tente novamente.");
      error.code = data?.error_code; throw error;
    }
    return data;
  }
  const post = (path, value) => api(path, { method: "POST", body: JSON.stringify(value) });
  const problemPresentation = p => {
    const id = p.problem_id || p.id;
    const match = /^(ITA|TME)(\d{4})(?:F(\d+))?([QP])(\d+)$/.exec(id);
    if (!match) return { id, group: "Outras questões", label: id, number: 0 };
    const [, competition, year, explicitPhase, type, number] = match;
    const phase = Number(explicitPhase || (competition === "TME" ? 2 : 1));
    return { id, group: `${competition === "TME" ? "TME²" : competition} ${year} — ${phase}ª fase`,
      label: `${type === "P" ? "Problema" : "Questão"} ${Number(number)}`, number: Number(number) };
  };
  async function refreshCases() {
    if (!state.caseRequest) state.caseRequest = api("/tme/cases").finally(() => { state.caseRequest = null; });
    state.cases = await state.caseRequest; state.casesLoaded = true;
  }
  const local = c => {
    if (!state.cache.has(c.case_id)) state.cache.set(c.case_id, { page: 0, zoom: 1, rotation: 0, tab: c.data_origin === "synthetic_demo" ? "transcript" : "original", draft: {}, editors: {}, audits: null, history: null, decision: undefined, detail: null, feedback: null });
    return state.cache.get(c.case_id);
  };
  const questionNumber = c => c.question_order || c.problem_id.match(/[QP](\d+)$/)?.[1];
  function renderRecentCases() {
    const recent = document.querySelector("#recent-cases"); if (!recent) return;
    recent.replaceChildren();
    const entries = state.current ? [state.current, ...state.cases.filter(c => c.case_id !== state.current.case_id)] : state.cases;
    for (const c of entries.slice(0, 8)) {
      const item = btn("", () => { if (!state.busy) openCase(c.case_id).catch(showError); }, "recent-case");
      item.title = `${c.external_candidate_ref} · ${c.problem_id} · ${caseStatus(c)}`;
      item.setAttribute("aria-label", `Abrir ${item.title}`);
      item.setAttribute("aria-current", state.view === "workspace" && state.current?.case_id === c.case_id ? "page" : "false");
      const indicator = node("span", "", "case-dot"); indicator.dataset.status = caseStatus(c); indicator.setAttribute("aria-hidden", "true");
      item.append(indicator, node("span", c.external_candidate_ref, "recent-code"), node("span", questionNumber(c) ? `Q${questionNumber(c)}` : c.problem_id, "recent-question")); recent.appendChild(item);
    }
    for (const link of document.querySelectorAll("nav [data-view]")) link.setAttribute("aria-current", link.dataset.view === (state.view === "exams" ? "results" : state.view === "workspace" ? "cases" : state.view) ? "page" : "false");
  }
  const origin = c => c.source_mode === "IMAGE_SCAN" ? "Foto / scan" : "Escrita digital";
  const runFor = c => {
    const saved = local(c);
    if(c.exam_submission_id)return saved.audits?.find(r=>!r.stale);
    if (saved.decision?.audit_run_id) return saved.audits?.find(r => r.audit_run_id === saved.decision.audit_run_id);
    return saved.audits?.find(r => !r.stale && r.status === "COMPLETED") || saved.audits?.[0];
  };
  function caseStatus(c) {
    const saved = local(c), run = runFor(c);
    if (c.exam_submission_id) {
      const status=c.review_state || saved.examReview?.state || "PENDING";
      return {PENDING:"Pendente",READY:"Pronta",REVIEW:"Revisão necessária",CONFIRMED:"Finalizada"}[status];
    }
    if (saved.decision || c.status === "DECIDED") return "Finalizada";
    if (saved.processing === "audit") return "Analisando";
    if (saved.processing === "recognition") return "Reconhecendo";
    if (run?.status === "FAILED" || saved.feedback?.state === "FAILED") return "Falha técnica";
    if (run?.stale) return "Aguardando análise";
    if (run?.result) return run.result.score == null ? "Inconclusiva" : "Aguardando decisão";
    return saved.history ? "Aguardando análise" : "Aguardando reconhecimento";
  }
  async function loadCaseData(c, force = false) {
    const saved = local(c), base = `/tme/cases/${c.case_id}`;
    if(c.exam_submission_id){
      if(force || !saved.loaded){
        const review=await api(`/tme/question-attempts/${c.case_id}/workspace`);
        if(saved.examPages?.map(p=>p.exam_page_id).join()!==review.pages.map(p=>p.exam_page_id).join())saved.originalPages=new Map();
        Object.assign(c,review.question_attempt);
        Object.assign(saved,{examReview:review,examPages:review.pages,history:review.history,audits:review.audits,
          detail:{submission:{page_images:review.pages.map((p,index)=>({page_index:index}))}},loaded:true,loadError:false});
        for(const item of saved.fullExam?.question_attempts||[])item.review_state=review.question_states?.[item.case_id]||"PENDING";
        const sibling=saved.fullExam?.question_attempts.find(item=>item.case_id===c.case_id);
        if(sibling)sibling.review_state=review.state;c.review_state=review.state;
      }
      return saved;
    }
    if (!c.submission_id) return saved;
    if (force || !saved.loaded) {
      const [summaries, audits, decision, detail, feedback] = await Promise.all([
        api(`${base}/transcriptions`), api(`${base}/audits`), api(`${base}/decision`),
        saved.detail ? Promise.resolve(saved.detail) : api(`${base}/submission`), c.data_origin === "synthetic_demo" ? Promise.resolve(null) : api(`${base}/recognition-status`),
      ]);
      saved.history = summaries.length ? await api(`${base}/transcriptions/${summaries[0].transcription.transcription_id}`) : null;
      Object.assign(saved, { audits, decision, detail, feedback, loaded: true, loadError: false });
    }
    return saved;
  }
  async function listing(view) {
    state.view=view;const generation=++state.generation;
    const isQueue=view==="cases",isExams=view==="exams",values=state.filters[view]||{};
    const title=isQueue?(values.exam?`Questões da prova ${Workspace.displayExamName(values.exam)}`:"Fila de correções"):isExams?"Progresso por prova":"Resultados";
    const subtitle=isQueue?"Acompanhe, filtre e continue suas correções.":isExams?"Acompanhe a situação das questões de cada prova.":"Acompanhe o andamento das correções do piloto.";
    const box=Views.Page(title,subtitle),content=node("div",undefined,"tme-page-content");content.append(Views.Loading());box.append(content);show(box);
    const reload=()=>listing(view),change=(key,value)=>navigate(view,{...values,[key]:value,page:1});
    const query=new URLSearchParams({view:isQueue?"queue":view,size:"50",...values});
    try {
      const [data,summary]=await Promise.all([api(`/tme/cases?${query}`),isQueue?api("/tme/home-summary?period=all"):Promise.resolve(null)]);
      if(generation!==state.generation)return;
      content.replaceChildren();
      if(isQueue){const cta=Home.PrimaryCorrectionCTA(summary.priority_cases,id=>openCase(id).catch(showError),"success");cta.classList.add("tme-next");box.heading.append(cta);}
      if(isQueue||isExams){
        content.append(Views.Filters(values,data.questions,change,reload,isExams));
        if(values.exam)content.append(btn("Todas as provas",()=>navigate("exams"),"home-text-button"));
        content.append(data.items.length?(isQueue?Views.QueueRows(data.items,id=>openCase(id).catch(showError)):Views.Exams(data.items,navigate)):Views.Empty(isQueue?"Nenhuma correção encontrada.":"Nenhuma prova disponível."));
        content.append(Views.Pagination(data,page=>navigate(view,{...values,page})));
      }else content.append(Views.Results(data,navigate));
      if(isQueue && fullExam && !values.exam) await fullExam.list(content).catch(()=>content.prepend(note("Não foi possível carregar as provas recebidas. Atualize a fila.",true)));
    }catch(_){if(generation!==state.generation)return;content.replaceChildren(Views.ErrorState(isQueue?"Não foi possível carregar a fila.":isExams?"Não foi possível carregar o progresso das provas.":"Não foi possível carregar os resultados.",reload));}
  }
  const cases=()=>navigate("cases");
  const showError = () => show(note("Não foi possível carregar esta etapa. Tente novamente.", true), actions(btn("Correções", () => cases().catch(showError))));
  async function newCase() {
    if(fullExam){++state.generation;state.view="new";return fullExam.newCorrection();}
    return newSingleCase();
  }
  async function openExam(examId,attemptId=null,record=true){
    if(state.busy || !fullExam)return;
    ++state.generation;state.view="workspace";state.current=null;
    if(record)writeRoute("workspace",{exam_submission_id:examId,question_attempt_id:attemptId});
    window.scrollTo(0,0);return fullExam.open(examId,attemptId);
  }
  async function newSingleCase() {
    state.view = "new"; const generation=++state.generation;
    const box = Views.Page("Nova correção","Localize uma prova e escolha a forma de entrada da solução."); const form = node("form",undefined,"tme-new-form");
    const skeleton=Views.Loading();box.append(skeleton);show(box);
    const select = node("select"); select.required = true;
    const placeholder = node("option", "Selecione uma questão"); placeholder.value = ""; select.appendChild(placeholder);
    try {
      const entries = (await api("/tme/problems")).map(problemPresentation)
        .sort((a,b) => a.group.localeCompare(b.group,"pt-BR",{numeric:true}) || a.number-b.number);
      const groups = new Map();
      for (const p of entries) {
        if (!groups.has(p.group)) {
          const group = node("optgroup"); group.label = p.group;
          groups.set(p.group,group); select.appendChild(group);
        }
        const option = node("option",p.label); option.value = p.id; groups.get(p.group).appendChild(option);
      }
    }
    catch (_) { if(generation===state.generation){box.replaceChildren(box.heading,Views.ErrorState("Não foi possível carregar as questões.",newCase));}return; }
    if(generation!==state.generation)return;
    box.replaceChildren(box.heading);
    const code = node("input"); code.required = true; code.maxLength = 80; code.pattern = "[A-Za-z0-9._:/-]+"; code.autocomplete = "off"; code.placeholder = "Ex.: PROVA-2026-0001";
    form.append(field("Código da prova", code), field("Questão", select), node("p", "Use um código pseudônimo; não informe o nome do participante.", "muted"));
    form.appendChild(node("h2", "Forma de entrada"));
    const choices = node("div", undefined, "choice-row"); let mode = null;
    for (const [name, value] of [["Foto / scan", "IMAGE_SCAN"], ["Escrever no tablet", "DIGITAL_INK"]]) {
      const choice = btn(name, () => { mode = value; for (const item of choices.children) { item.classList.toggle("selected", item === choice);item.setAttribute("aria-pressed",String(item===choice)); } }, "choice"); choice.setAttribute("aria-pressed","false");choice.prepend(Home.icon(value==="IMAGE_SCAN"?"camera":"tablet"));choices.appendChild(choice);
    }
    const continueButton=btn("Continuar", async () => {
      if (state.busy || !form.reportValidity()) return;
      if (!mode) { error.textContent = "Escolha uma forma de entrada."; return; }
      state.busy=true;continueButton.disabled=true;
      try { const c = await post("/tme/cases", { problem_id: select.value, external_candidate_ref: code.value.trim(), source_mode: mode }); state.busy=false;await openCase(c.case_id); }
      catch (e) { error.textContent = e.message; }
      finally {state.busy=false;continueButton.disabled=false;}
    }); const error = node("p", "", "field-error");error.setAttribute("role","alert");form.append(choices,actions(continueButton),error);form.addEventListener("submit",event=>{event.preventDefault();continueButton.click();});box.appendChild(form); show(box);
  }
  function steps(active) {
    const list = node("ol", undefined, "steps"); list.setAttribute("aria-label", "Progresso da correção");
    ["Entrada", "Transcrição", "Análise", "Decisão"].forEach((label, i) => {
      const item = node("li", label, i === active ? "active" : ""); item.dataset.state=i<active?"complete":i===active?"current":"upcoming"; if (i === active) item.setAttribute("aria-current", "step"); list.appendChild(item);
    }); return list;
  }
  function context(c, active) {
    return Workspace.CorrectionHeader({ c, cases: c.exam_submission_id ? local(c).fullExam.question_attempts : state.cases, status: item => c.exam_submission_id || item.case_id === c.case_id || local(item).loaded || item.status === "DECIDED" ? caseStatus(item) : "Disponível",
      open: id => { if (!state.busy) (c.exam_submission_id ? openExam(c.exam_submission_id,id) : openCase(id)).catch(showError); }, back: () => c.exam_submission_id ? openExam(c.exam_submission_id) : navigate(returnTo.view,returnTo.params), steps, active, busy: state.busy });
  }
  async function loadWorkspaceContext() {
    if (!state.problemRequest) state.problemRequest = api("/tme/problems").catch(() => { state.problemRequest = null; return []; });
    if (!state.presentationRequest) state.presentationRequest = api("/static/problem-presentations/registry.json").catch(() => { state.presentationRequest = null; return []; });
    const [problems, presentations] = await Promise.all([state.problemRequest, state.presentationRequest, state.casesLoaded ? Promise.resolve() : refreshCases().catch(() => {})]);
    state.problems = problems; state.presentations = Array.isArray(presentations) ? presentations : [];
  }
  async function openCase(caseId, record=true) {
    if (state.busy) return;
    if(record){if(state.view!=="workspace")returnTo={view:state.view==="new"?"cases":state.view,params:{...(state.filters[state.view]||{})}};route(caseId);}
    state.view = "workspace"; const generation = ++state.generation;
    show(loading("Carregando solução…")); window.scrollTo(0,0);
    const c = await api(`/tme/cases/${caseId}`);
    if (generation !== state.generation) return;
    if(c.exam_submission_id && fullExam)return openExam(c.exam_submission_id,c.case_id,record);
    if (state.current?.case_id !== caseId) { for (const photo of state.photos) URL.revokeObjectURL(photo.url); state.photos = []; }
    state.current = c; state.message = ""; state.adjusting = false; state.feedback = local(c).feedback;
    await loadWorkspaceContext();
    if (generation !== state.generation) return;
    if (!c.submission_id) return c.source_mode === "IMAGE_SCAN" ? renderScan() : renderInk();
    try { await loadCaseData(c); if (generation === state.generation) await renderCorrection(); }
    catch (_) { if (generation === state.generation) show(context(c,0),note("Não foi possível carregar a solução. Seus dados permanecem preservados."),actions(btn("Tentar novamente",()=>openCase(caseId).catch(showError)))); }
  }
  function renderInk() {
    const c = state.current, box = card("Escrever no tablet");
    box.classList.add("tme-entry-panel");
    box.append(node("p", `${c.external_candidate_ref} · ${c.problem_id}`, "muted"));
    const frame = node("iframe", undefined, "frame"); frame.title = "Caderno de escrita digital ConfIA";
    frame.src = `/tme/cases/${c.case_id}/capture?embedded=1&tme_case_id=${encodeURIComponent(c.case_id)}&problem_id=${encodeURIComponent(c.problem_id)}&submission_target=${encodeURIComponent(`/tme/cases/${c.case_id}/digital-submission`)}`;
    frame.addEventListener("load", () => { state.captureWindow = frame.contentWindow; });
    box.append(frame, actions(btn("Atualizar correção", () => openCase(c.case_id), "secondary"))); show(context(c, 0), box);
  }
  function imageInput(capture, onFile) {
    const input = node("input"); input.type = "file"; input.accept = "image/*"; if (capture) input.setAttribute("capture", "environment");
    input.className = "sr-only"; input.addEventListener("change", () => { if (input.files?.[0]) onFile(input.files[0]); input.value = ""; });
    return input;
  }
  function acceptFile(file, index = null) {
    let photo;
    try { Scan.validate(file); photo = Scan.photo(file, URL.createObjectURL(file), new Date().toISOString());
      if (index === null) Scan.add(state.photos, photo);
      else URL.revokeObjectURL(Scan.replace(state.photos, index, photo).url);
    } catch (e) {
      if (photo) URL.revokeObjectURL(photo.url);
      state.message = e.message; return renderScan();
    }
    state.message = "Confira a página e selecione Usar esta página."; renderScan();
  }
  function renderScan() {
    const c = state.current, box = card("Fotografar solução"); box.classList.add("tme-entry-panel");box.append(node("p", `${c.external_candidate_ref} · ${c.problem_id}`),
      node("p", "Fotografe a folha inteira, evite sombras, mantenha a câmera paralela ao papel e confira se a escrita está legível.", "muted"));
    box.appendChild(scanStatus("WAITING"));
    if (state.adjusting) box.appendChild(note("Ao continuar, será criada uma nova correção com as páginas ajustadas. Esta versão e seus originais ficam preservados."));
    const camera = imageInput(true, f => acceptFile(f)); const existing = imageInput(false, f => acceptFile(f));
    const cameraButton = btn("Fotografar página", () => camera.click());
    const existingButton = btn("Selecionar imagem", () => existing.click(), "secondary");
    cameraButton.disabled = existingButton.disabled = state.photos.length >= maxPages;
    box.append(camera, existing, actions(cameraButton, existingButton));
    if (state.photos.length) {
      const grid = node("div", undefined, "scan-grid");
      state.photos.forEach((photo, i) => {
        const item = node("div", undefined, "photo"); item.append(node("h2", `Página ${i + 1}`));
        const img = node("img"); img.src = photo.url; img.alt = `Prévia da página ${i + 1}`; img.style.transform = `rotate(${photo.rotation}deg)`; item.appendChild(img);
        const replace = imageInput(true, f => acceptFile(f, i)); item.appendChild(replace);
        item.append(actions(btn("Repetir foto", () => replace.click(), "secondary"),
          btn("Girar 90°", () => { Scan.rotate(photo); renderScan(); }, "secondary"),
          btn("Usar esta página", () => { Scan.confirm(photo); renderScan(); }),
          btn("Remover", () => { URL.revokeObjectURL(Scan.remove(state.photos, i).url); renderScan(); }, "danger"),
          btn("Mover para cima", () => movePhoto(i, -1), "secondary"), btn("Mover para baixo", () => movePhoto(i, 1), "secondary")));
        item.appendChild(node("p", photo.confirmed ? "Página confirmada" : "Aguardando conferência", "muted")); grid.appendChild(item);
      }); box.appendChild(grid);
    }
    if (state.photos.length < maxPages) box.appendChild(actions(btn("Adicionar página", () => camera.click(), "secondary")));
    const continueButton = btn("Continuar", uploadScan); continueButton.disabled = !Scan.ready(state.photos);
    box.append(actions(continueButton));
    if (state.adjusting) box.appendChild(actions(btn("Voltar à versão preservada", () => openCase(c.case_id), "secondary")));
    if (state.message) box.appendChild(note(state.message, /erro|não|inválid|indisponível/i.test(state.message)));
    if (state.busy) for (const control of box.querySelectorAll("button,input")) control.disabled = true;
    show(context(c, 0), box);
  }
  function movePhoto(index, direction) { Scan.move(state.photos, index, direction); renderScan(); }
  async function fileBase64(file) {
    return new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.onerror = () => reject(new Error("Não foi possível ler a foto.")); reader.readAsDataURL(file); });
  }
  const derive = photo => Scan.derive(photo, (...args) => createImageBitmap(...args), () => document.createElement("canvas"));
  async function uploadScan() {
    let c = state.current;
    if (state.busy || !Scan.ready(state.photos)) return;
    state.busy = true;
    state.message = "Preservando originais e preparando reconhecimento…"; renderScan();
    try {
      const pages = await Promise.all(state.photos.map(async p => ({ original_base64: await fileBase64(p.file),
        original_mime: p.file.type, captured_at: p.capturedAt, rotation_degrees: p.rotation, ...await derive(p) })));
      if (state.adjusting) {
        c = await post("/tme/cases", { problem_id: c.problem_id,
          external_candidate_ref: c.external_candidate_ref, source_mode: "IMAGE_SCAN" });
        state.current = c; state.adjusting = false; route(c.case_id);
      }
      await post(`/tme/cases/${c.case_id}/scan`, { pages });
      state.current = await api(`/tme/cases/${c.case_id}`);
      state.message = "Páginas preservadas."; state.busy = false;
      await recognize();
    } catch (e) {
      state.busy = false; state.message = e.message;
      // A lost upload response may still have bound the immutable source.
      state.current = await api(`/tme/cases/${c.case_id}`).catch(() => c);
      if (state.current.submission_id && !state.adjusting) await renderCorrection(); else renderScan();
    }
  }
  function scanStatus(value) {
    const labels = { WAITING: "Aguardando reconhecimento", RECOGNIZING: "Reconhecendo", RECOGNIZED: "Reconhecida", FAILED: "Falha de reconhecimento" };
    const status = node("p", labels[value] || labels.WAITING, "status status-pill");
    status.dataset.kind = value === "FAILED" ? "error" : value === "RECOGNIZED" ? "success" : "pending";
    status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite"); return status;
  }
  async function adjustPages() {
    if (state.busy) return;
    const c = state.current, restored = [];
    try {
      const manifest = await api(`/tme/cases/${c.case_id}/scan-manifest`);
      for (const page of [...manifest.pages].sort((a, b) => a.index - b.index)) {
        const response = await fetch(`/tme/cases/${c.case_id}/originals/${page.index}`, { cache: "no-store", credentials: "same-origin" });
        if (!response.ok) throw new Error("Não foi possível recuperar as páginas preservadas. Tente novamente.");
        const file = new File([await response.blob()], `pagina-${page.index + 1}`, { type: page.original_mime });
        const photo = Scan.photo(file, URL.createObjectURL(file), page.captured_at);
        photo.rotation = page.rotation_degrees; restored.push(photo);
      }
      for (const photo of state.photos) URL.revokeObjectURL(photo.url);
      state.photos = restored; state.adjusting = true;
      state.message = "Ajuste as páginas e confirme cada uma antes de continuar."; renderScan();
    } catch (e) {
      for (const photo of restored) URL.revokeObjectURL(photo.url);
      state.message = e.message; await renderCorrection();
    }
  }
  async function recognize() {
    if (state.busy) return;
    const c = state.current;
    state.busy = true; local(c).processing = "recognition"; state.message = "";
    state.feedback = { state: "RECOGNIZING", message: "Reconhecendo as páginas preservadas…" };
    try {
      await renderCorrection();
      const run = await post(`/tme/cases/${c.case_id}/recognize`, {});
      if (state.current?.case_id !== c.case_id) return;
      state.feedback = await api(`/tme/cases/${c.case_id}/recognition-status`);
      state.message = run.status === "FAILED" ? "" : "Transcrição automática disponível.";
    } catch (error) {
      if (state.current?.case_id !== c.case_id) return;
      state.feedback = { state: "FAILED", error_code: error.code,
        message: error.code ? error.message : "Não foi possível reconhecer esta solução agora. As páginas foram preservadas." };
    } finally { state.busy = false; local(c).processing = null; local(c).loaded = false; }
    if (state.current?.case_id === c.case_id && state.view === "workspace") await renderCorrection();
  }
  function manuscriptPage(c, index) {
    const saved = local(c); saved.originalPages ||= new Map();
    if (saved.originalPages.has(index)) return saved.originalPages.get(index);
    const page = node("div", undefined, "page-review"); page.appendChild(node("h3", `Página ${index + 1}`));
    const examPage=saved.examPages?.[index];
    const examAsset=examPage && saved.fullExam.submission.original_documents.find(a=>a.asset_id===examPage.original_asset_id);
    if(examPage)page.children[0].textContent=`Página ${examPage.page_number} da prova`;
    const originalUrl = examPage ? `/tme/exam-submissions/${c.exam_submission_id}/assets/${examPage.original_asset_id}` : c.source_mode === "IMAGE_SCAN" ? `/tme/cases/${c.case_id}/originals/${index}` : `/tme/cases/${c.case_id}/pages/${index}`;
    const img = node("img"); img.src = examPage && examAsset?.media_type==="application/pdf" ? `/tme/exam-submissions/${c.exam_submission_id}/assets/${examPage.preview_asset_id}` : originalUrl; img.alt = `Manuscrito original da página ${index + 1}`;
    if(examPage)img.alt=`Página ${examPage.page_number} da prova`;
    const imageState = note("Carregando solução…"); page.appendChild(imageState);
    img.onload = () => { imageState.hidden = true; saved.updateOriginal?.(); };
    img.draggable = false;
    img.onerror = () => {
      img.onerror = () => { imageState.hidden = false; imageState.textContent = "Não foi possível carregar a solução."; };
      if (c.source_mode === "IMAGE_SCAN" && !examPage) {
        img.src = `/tme/cases/${c.case_id}/pages/${index}`; img.alt = `Prévia normalizada da página ${index + 1}`;
        page.appendChild(node("p", "Este navegador exibe a prévia normalizada. O original continua preservado.", "muted"));
      }
    };
    const surface=node("div",undefined,"manuscript-surface"); surface.appendChild(img); page.appendChild(surface);
    if (c.source_mode === "IMAGE_SCAN") {
      const link = node("a", "Abrir original preservado"); link.href = originalUrl + (examPage && examAsset?.media_type==="application/pdf" ? `#page=${examPage.original_page_number}` : ""); link.target = "_blank"; link.rel = "noopener";
      page.appendChild(link);
    }
    saved.originalPages.set(index, page); return page;
  }
  function loading(message) {
    const box = node("div", undefined, "processing-state"); box.appendChild(note(message));
    const skeleton = node("div", undefined, "skeleton-lines"); skeleton.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 3; i++) skeleton.appendChild(node("span")); box.appendChild(skeleton); return box;
  }
  async function renderCorrection() {
    const c = state.current, saved = await loadCaseData(c);
    if (state.current !== c || state.view !== "workspace") return;
    state.history = saved.history; root.dataset.decisionState=saved.decision?"finalized":"active";
    const latest = saved.history?.revisions.at(-1), run = runFor(c);
    const layout = node("div", undefined, "correction-workspace"), solution = card(), right = node("aside", undefined, "analysis-column");
    solution.classList.add("solution-panel"); solution.id = "solution-pane"; right.id = "analysis-pane"; right.setAttribute("aria-label", "Análise ConfIA");
    const solutionHeading = node("header", undefined, "pane-header"); solutionHeading.appendChild(node("h2", "Solução do participante"));
    const expandSolution = btn("⤢", () => { saved.solutionExpanded=!saved.solutionExpanded;updateExpanded(); }, "secondary expand-solution");
    const updateExpanded=()=>{layout.dataset.solutionExpanded=String(Boolean(saved.solutionExpanded));const label=saved.solutionExpanded?"Restaurar análise":"Expandir solução";expandSolution.setAttribute("aria-label",label);expandSolution.title=label;expandSolution.replaceChildren(window.ConfiaTmeHome.icon(saved.solutionExpanded?"collapse":"expand"));expandSolution.setAttribute("aria-expanded",String(Boolean(saved.solutionExpanded)));};
    expandSolution.setAttribute("aria-controls","solution-pane analysis-pane");updateExpanded();solutionHeading.appendChild(expandSolution);
    const tabs = node("div", undefined, "solution-tabs"), views = node("div", undefined, "solution-views"); views.id = "solution-views"; views.setAttribute("role", "tabpanel"); views.tabIndex = 0;
    tabs.setAttribute("aria-label", "Visualização da solução"); tabs.setAttribute("role", "tablist");
    const original = node("section", undefined, "original-document"), transcript = node("section", undefined, "transcript-document");
    original.setAttribute("aria-label", "Original"); transcript.setAttribute("aria-label", "Transcrição");
    if(c.data_origin === "synthetic_demo") transcript.appendChild(note("Texto sintético importado. A aceitação registra fidelidade ao texto fornecido, sem avaliação humana."));
    else if (!c.exam_submission_id && /^TME2026P[1-5]$/.test(c.problem_id)) transcript.appendChild(note("Identifique cada item em uma linha própria: [a], [b], [c] ou [d], conforme a questão. Confira e aceite a transcrição antes da análise."));
    const pages = [...new Set([...(saved.detail?.submission?.page_images || []).map(p => p.page_index), ...(latest?.segments || []).map(s => s.page_index)])].sort((a,b) => a-b);
    const pageNodes = pages.map(index => manuscriptPage(c, index)); original.append(...pageNodes);
    Workspace.attachPan(original,saved);
    if(c.data_origin === "synthetic_demo") original.prepend(note("CASO SINTÉTICO — fonte textual importada. Consulte a transcrição aceita."));
    if (!pages.length) original.appendChild(note("Nenhuma página original disponível."));
    saved.page = Math.min(saved.page, Math.max(0, pages.length - 1));
    const pagination = node("span", "", "page-position");
    const updatePages = () => {
      pageNodes.forEach((page, i) => { page.hidden = i !== saved.page; const img = page.querySelectorAll("img")[0]; Workspace.layoutOriginal(page,img,original,saved); });
      fit.value=Workspace.originalFitMode(saved);
      pagination.textContent = `${Math.round(saved.zoom * 100)}% · Página ${pages.length ? saved.page + 1 : 0}/${pages.length}${c.exam_submission_id && pages.length ? ` · folha ${saved.examPages[saved.page].page_number} da prova` : ""}`;
    };
    saved.updateOriginal = updatePages;
    const resetFit = mode => { saved.fitMode=mode; saved.zoom=1; delete saved.customWidth; original.scrollTop=0; original.scrollLeft=0; updatePages(); };
    const manualZoom = delta => {
      if(Workspace.originalFitMode(saved)!=="custom") saved.customWidth=parseFloat(pageNodes[saved.page]?.querySelectorAll("img")[0]?.style.width)||0;
      saved.fitMode="custom";saved.zoom=Math.max(.5,Math.min(3,saved.zoom+delta));updatePages();
    };
    const toolbar = actions(btn("Zoom −", () => manualZoom(-.25), "secondary"), pagination,
      btn("Zoom +", () => manualZoom(.25), "secondary"),
      btn("Anterior", () => { saved.page = Math.max(0, saved.page - 1); updatePages(); }, "secondary"),
      btn("Próxima", () => { saved.page = Math.min(Math.max(0, pages.length - 1), saved.page + 1); updatePages(); }, "secondary"),
      btn("Rotacionar", () => { saved.rotation = (saved.rotation + 90) % 360; if(Workspace.isDesktop()) resetFit("page"); else updatePages(); }, "secondary"));
    for (const [control,label,symbol] of [[toolbar.children[0],"Zoom −","minus"],[toolbar.children[2],"Zoom +","plus"],[toolbar.children[3],"Anterior","previous"],[toolbar.children[4],"Próxima","chevron"],[toolbar.children[5],"Rotacionar","rotate"]]) { control.replaceChildren(window.ConfiaTmeHome.icon(symbol));control.setAttribute("aria-label",label);control.title=label; }
    const fit = node("select",undefined,"viewer-fit");fit.setAttribute("aria-label","Ajuste da solução");
    for(const [value,label] of [["page","Ajustar à página"],["width","Ajustar à largura"],["custom","Zoom manual"]]) {const option=node("option",label);option.value=value;option.disabled=value==="custom";fit.appendChild(option);}
    fit.value=Workspace.originalFitMode(saved);
    fit.addEventListener("change",()=>{if(fit.value!=="custom") resetFit(fit.value);});
    toolbar.appendChild(fit);
    toolbar.classList.add("viewer-commands"); toolbar.setAttribute("aria-label", "Comandos do original"); updatePages();
    const editor = node("div", undefined, "transcription-editor"); editor.hidden = !saved.editing;
    const documentView = node("div"); documentView.hidden = Boolean(saved.editing);
    if (latest || c.exam_submission_id && pages.length) {
      for (const index of pages) {
        const segments = (latest?.segments||[]).filter(s => s.page_index === index).sort((a,b) => a.order-b.order);
        const text = segments.map(s => s.text || s.latex || "").join("\n\n");
        const doc = node("div", undefined, "document"); doc.setAttribute("role", "document"); doc.setAttribute("aria-label", `Transcrição da página ${index + 1}`);
        for (const segment of segments) { const block = node("div"); window.ConfiaRecognitionView.renderMathText(block, segment.text || segment.latex || "", !segment.text && Boolean(segment.latex) || segment.kind === "math"); doc.appendChild(block); } documentView.appendChild(doc);
        const area = node("textarea"); area.value = saved.editors[index] ?? text; area.maxLength=20000;area.addEventListener("input", () => { saved.editors[index] = area.value; if(c.exam_submission_id)saved.readingDirty=true; });
        editor.appendChild(field(`Editar página ${index + 1}`, area));
      }
      editor.append(note(c.exam_submission_id ? "Rascunho não salvo: fica nesta sessão ao trocar de questão. Salvar cria uma nova versão e preserva a leitura anterior." : "Cada salvamento cria uma revisão. Preserve a matemática escrita pelo participante."), actions(btn("Salvar nova revisão", () => saveRevision(c, editor)), btn("Cancelar edição", () => { saved.editing = false; if(c.exam_submission_id){saved.loaded=false;saved.editors={};saved.readingDirty=false;delete saved.editingBase;return renderCorrection();} editor.hidden = true; documentView.hidden = false; }, "secondary")));
      if(!latest)documentView.append(note("Nenhuma transcrição registrada. Digite a leitura, importe a captura disponível ou use o reconhecimento existente."));
    } else documentView.appendChild(note(saved.processing === "recognition" ? "Reconhecendo solução…" : saved.feedback?.state === "FAILED" ? "Falha de reconhecimento. Isso não indica erro na solução do participante." : "Reconhecimento não concluído. A transcrição aparecerá após o reconhecimento automático."));
    transcript.append(documentView, editor);
    let transcriptionStatus, metadata;
    const setTab = value => {
      saved.tab = value; solution.dataset.tab=value; layout.dataset.solutionTab=value; original.dataset.layout=value==="original"?"full-page":"bounded"; original.hidden = value === "transcript"; transcript.hidden = value === "original"; toolbar.hidden = value === "transcript";
      if(transcriptionStatus) transcriptionStatus.hidden=value!=="transcript" || Boolean(latest);
      if(metadata) metadata.hidden=c.exam_submission_id ? value==="original" : value!=="transcript";
      views.classList.toggle("compare", value === "compare"); views.setAttribute("aria-labelledby", `tab-${value}`);
      for (const button of tabs.children) { button.setAttribute("aria-selected", String(button.dataset.tab === value)); button.tabIndex = button.dataset.tab === value ? 0 : -1; }
      updatePages();
    };
    for (const [value, label] of [["original", "Original"], ["transcript", "Transcrição"], ["compare", "Comparar"]]) {
      const button = btn(label, () => setTab(value), "secondary"); button.id = `tab-${value}`; button.dataset.tab = value; button.setAttribute("role", "tab"); button.setAttribute("aria-controls", "solution-views");
      button.addEventListener("keydown", event => {
        const list = Array.from(tabs.children), i = list.indexOf(button);
        const next = { ArrowRight: (i + 1) % 3, ArrowLeft: (i + 2) % 3, Home: 0, End: 2 }[event.key];
        if (next !== undefined) { event.preventDefault(); setTab(list[next].dataset.tab); list[next].focus(); }
      }); tabs.appendChild(button);
    }
    views.append(original, transcript); setTab(saved.tab);
    const secondary = actions(); secondary.classList.add("transcript-commands");
    if (latest || c.exam_submission_id && pages.length) {
      secondary.append(btn(c.exam_submission_id ? latest ? "Corrigir leitura" : "Digitar transcrição" : "Editar", () => { saved.editing = true; if(c.exam_submission_id && primary)primary.disabled=true; saved.editingBase ??= latest?.revision_number || 0; editor.hidden = false; documentView.hidden = true; setTab("transcript"); }, "secondary"));
      if(c.data_origin !== "synthetic_demo" && !c.exam_submission_id) secondary.append(btn("Reprocessar", recognize, "secondary"));
    }
    if(c.exam_submission_id && saved.examReview.capture_candidate_available)secondary.append(btn("Importar leitura da captura",()=>importCapture(c),"secondary"));
    for (const button of secondary.children) button.disabled = state.busy;
    transcript.prepend(secondary);
    const provenance = node("details", undefined, "transcription-metadata"); provenance.appendChild(node("summary", "Originais e histórico"));
    if(c.source_mode==="IMAGE_SCAN" && !c.exam_submission_id) for(const index of pages) {const link=node("a",`Abrir original preservado · página ${index+1}`,"desktop-original-link");link.href=`/tme/cases/${c.case_id}/originals/${index}`;link.target="_blank";link.rel="noopener";provenance.appendChild(link);}
    if(c.exam_submission_id){
      provenance.append(node("p",saved.fullExam.submission.source==="PDF"?"O visualizador representa as páginas do PDF. Abra o documento original preservado nos links abaixo.":"O visualizador exibe as imagens originais preservadas.","muted"));
      for(const page of saved.examPages){const link=node("a",`Abrir original preservado · página ${page.page_number}`,"desktop-original-link");link.href=`/tme/exam-submissions/${c.exam_submission_id}/assets/${page.original_asset_id}#page=${page.original_page_number}`;link.target="_blank";link.rel="noopener";provenance.append(link);}
    }
    const meta = saved.history?.transcription;
    if (meta && !c.exam_submission_id) provenance.appendChild(node("p", `${meta.provider || meta.recognizer || "Provider não registrado"} · ${meta.recognizer_version || "Versão não registrada"} · ${meta.created_at ? new Date(meta.created_at).toLocaleString("pt-BR") : "Horário não registrado"}`));
    if (c.source_mode === "IMAGE_SCAN" && !c.exam_submission_id) { const adjust = btn("Voltar e ajustar páginas", adjustPages, "secondary"); adjust.disabled = state.busy; provenance.appendChild(adjust); }
    if(c.exam_submission_id)for(const version of saved.examReview.versions){
      const entry=node("details"),label=node("summary",`Versão ${version.version_number} · ${readingOrigin(version.origin)}${version.current?" · corrente":" · preservada"}`);
      entry.append(label,node("p",new Date(version.created_at).toLocaleString("pt-BR"),"muted"));
      const content=node("div",undefined,"document");window.ConfiaRecognitionView.renderMathText(content,version.text);entry.append(content);provenance.append(entry);
    }
    const technical = node("details", undefined, "technical-details"); technical.append(node("summary", "Detalhes técnicos da transcrição"), node("pre", JSON.stringify({ transcription: saved.history, recognition: saved.feedback }, window.ConfIAReport.publicTechnicalValue, 2))); provenance.appendChild(technical);
    transcriptionStatus = node("p", saved.processing === "recognition" ? "Reconhecendo solução…" : latest ? "Transcrição disponível" : saved.feedback?.state === "FAILED" ? "Falha de reconhecimento" : "Reconhecimento não concluído", "transcription-status"); transcriptionStatus.setAttribute("role","status");
    const provider = meta?.provider || meta?.recognizer || meta?.source;
    metadata = node("p", undefined,"transcription-caption");
    const compactCaption=node("span",c.exam_submission_id ? latest ? `Versão ${latest.revision_number} · ${readingOrigin(saved.examReview.current_version.origin)}${saved.editing?" · edição não salva":""}` : "Sem transcrição · originais preservados" : c.data_origin === "synthetic_demo" && latest ? `Transcrição importada · revisão ${latest.revision_number}${latest.status === "ACCEPTED" ? " · aceita" : ""}` : latest?`Transcrição automática${provider?` · ${/^mathpix/i.test(provider)?"Mathpix":provider}`:""} · revisão ${latest.revision_number}`:"As páginas originais permanecem preservadas.","caption-compact");
    metadata.append(compactCaption);
    setTab(saved.tab);
    const topline=node("div",undefined,"solution-topline");topline.append(solutionHeading,tabs);
    solution.append(topline, transcriptionStatus, metadata, toolbar, views, provenance);
    const analysis = node("section", undefined, "analysis-panel"), analysisHeading = node("header", undefined, "pane-header"); analysisHeading.appendChild(node("h2", "ANÁLISE CONFIA"));
    const analysisBody = node("div"); analysisBody.id = "analysis-content"; analysisBody.hidden = Boolean(saved.analysisCollapsed);
    const collapse = btn(saved.analysisCollapsed ? "Expandir análise" : "Recolher análise", () => {
      saved.analysisCollapsed = !saved.analysisCollapsed; analysisBody.hidden = saved.analysisCollapsed;
      collapse.textContent = saved.analysisCollapsed ? "Expandir análise" : "Recolher análise"; collapse.setAttribute("aria-expanded", String(!saved.analysisCollapsed));
    }, "secondary"); collapse.setAttribute("aria-controls", "analysis-content"); collapse.setAttribute("aria-expanded", String(!saved.analysisCollapsed));
    analysisHeading.appendChild(collapse); analysis.append(analysisHeading, analysisBody);
    if (saved.processing === "audit") analysisBody.appendChild(loading("Analisando matemática · executando verificações…"));
    if(c.exam_submission_id){
      const onOriginal=e=>{const index=saved.examPages.findIndex(p=>p.exam_page_id===e.exam_page_id);if(index<0)return;saved.page=index;setTab("original");drawer(false);solution.scrollIntoView({block:"start",behavior:"smooth"});};
      if(run){const report=node("div");window.ConfiaWorkspaceReport.renderQuestion(run,report,{onOriginal});analysisBody.append(report);}
      const comparison=saved.examReview.audit_comparison;
      const previousAudit=saved.examReview.previous_audit || (saved.audits||[]).find(r=>r.stale);
      const scoreText=(value,max)=>value==null?"não determinada":`${String(value).replace(".",",")} / ${max}`;
      if(comparison){
        const update=node("details");update.append(node("summary",run.status==="FAILED"?"Tentativa após correção da leitura":"Atualizado após correção da leitura"),
          node("p",`Sugestão anterior: ${scoreText(comparison.previous_suggested_score,comparison.previous_max_score)}`),
          node("p",`Sugestão atual: ${scoreText(comparison.current_suggested_score,run.max_score)}`),
          node("p",`Leitura anterior: ${comparison.previous_transcription_version_id} · leitura atual: ${comparison.current_transcription_version_id}`,"muted"));analysisBody.prepend(update);
      }else if(previousAudit && !run)analysisBody.append(note(`Sugestão anterior: ${scoreText(previousAudit.suggested_score,previousAudit.max_score)} · preservada no histórico.`));
      if(run?.status==="FAILED" && saved.examReview.reanalysis_required)analysisBody.prepend(note("Não foi possível concluir a reanálise. A leitura atual e as análises anteriores foram preservadas."));
      if(!run && !saved.processing)analysisBody.append(note("Aguardando análise. Nenhuma pontuação foi calculada para esta leitura."));
      const previous=(saved.audits||[]).filter(r=>r!==run);
      if(previous.length){const history=node("details");history.append(node("summary",`Histórico de análises (${previous.length})`));
        for(const old of previous){const entry=node("details"),content=node("div");entry.append(node("summary",`Análise anterior · versão ${old.revision_number} · ${scoreText(old.suggested_score,old.max_score)} · ${old.status==="FAILED"?"Falha técnica":old.review_required?"Revisar":"Concluída"}${old.completed_at?` · ${new Date(old.completed_at).toLocaleString("pt-BR")}`:""}`));window.ConfiaWorkspaceReport.renderQuestion(old,content,{onOriginal,historical:true});entry.append(content);history.append(entry);}analysisBody.append(history);}
    } else if (run) {
      if (run.stale) analysisBody.appendChild(note("Análise de uma revisão anterior. Analise a revisão atual antes de vincular a decisão."));
      if (run.result) { const report = node("div"); window.ConfIAReport.render(run.result, report, { context: "evaluator", auditRun: run, workspace: true, uiState: saved }); analysisBody.appendChild(report); }
      else analysisBody.appendChild(note("Não foi possível concluir a análise. A decisão humana permanece disponível."));
    } else if (!saved.processing) analysisBody.appendChild(note(c.exam_submission_id ? "Aguardando análise. Nenhuma pontuação foi calculada para esta leitura." : "Reconheça a solução e analise para consultar critérios, evidências e verificações."));
    if(c.exam_submission_id && saved.examReview.reanalysis_required)analysisBody.prepend(note("Leitura alterada — reanálise necessária. A leitura foi corrigida. Reanalise esta questão para atualizar a sugestão. Análises anteriores permanecem no histórico."));
    const openDrawer = btn("Abrir análise", () => drawer(true), "secondary drawer-trigger"); openDrawer.setAttribute("aria-controls", "analysis-pane");
    const closeDrawer = btn("Fechar análise", () => { drawer(false); openDrawer.focus(); }, "secondary drawer-close");
    const drawer = open => { saved.drawerOpen = open; right.dataset.open = String(open); openDrawer.setAttribute("aria-expanded", String(open)); if (open) { right.scrollIntoView({block:"start",behavior:"smooth"}); closeDrawer.focus(); } };
    right.dataset.open = String(Boolean(saved.drawerOpen)); openDrawer.setAttribute("aria-expanded", String(Boolean(saved.drawerOpen)));
    right.addEventListener("keydown", event => { if (event.key === "Escape") { drawer(false); openDrawer.focus(); } });
    right.append(closeDrawer, analysis);
    const divider = node("div", undefined, "pane-splitter"); layout.append(solution, divider, right); window.ConfiaWorkspaceControls.attachSplitter(layout, divider);
    const decisionBox = c.exam_submission_id ? node("div") : decisionPanel(c, saved, run?.status === "COMPLETED" && (!run.stale || saved.decision) ? run : null);if(c.exam_submission_id)decisionBox.hidden=true;
    const actionbar = node("div", undefined, "workspace-actions");
    const progress = saved.processing === "audit" ? "Analisando matemática · executando verificações…" : saved.processing === "recognition" ? "Reconhecendo solução…" : state.message || (run?.status === "FAILED" ? "Não foi possível concluir a análise matemática." : run ? "Análise concluída." : latest ? c.exam_submission_id ? "Transcrição disponível." : "Transcrição automática disponível." : saved.feedback?.state === "FAILED" ? saved.feedback.message : "Aguardando reconhecimento");
    actionbar.appendChild(note(progress));
    actionbar.dataset.quiet=String(!c.exam_submission_id && !state.message && !saved.processing && run?.status==="COMPLETED" && !run.stale);
    let primary;
    if (!latest && (!c.exam_submission_id || pages.length)) primary = btn(saved.feedback?.state === "FAILED" ? "Tentar novamente" : "Reconhecer", recognize);
    else if(c.exam_submission_id && latest) primary=btn(run?.status==="FAILED"?"Tentar novamente":saved.examReview.reanalysis_required?"Reanalisar questão":run?"Executar nova análise":"Analisar com ConfIA",audit);
    else if (!c.exam_submission_id && (!run || run.stale || run.status === "FAILED")) primary = btn("Analisar com ConfIA", audit);
    if (primary) { primary.disabled = state.busy || Boolean(c.exam_submission_id && saved.editing); actionbar.appendChild(primary); }
    if (saved.processing === "recognition") actionbar.appendChild(loading("Reconhecendo…"));
    const heading = context(c, saved.decision ? 3 : run ? 2 : latest ? 1 : 0); heading.appendChild(openDrawer);
    if(c.exam_submission_id){
      const info=Array.from(heading.children).find(el=>el.className==="case-information");
      info?.append(node("span",`${saved.fullExam.assessment.assessment.title} · Pontuação máxima: ${c.max_score}`));
      const partial=saved.examReview.partial_suggestion;
      if(partial)info?.append(node("span",`Sugestão ConfIA${partial.complete?"":" parcial"}: ${String(partial.suggested_score).replace(".",",")} / ${partial.max_score} · ${partial.analyzed_questions}/${partial.total_questions} questões${partial.awaiting_reanalysis?` · ${partial.awaiting_reanalysis} aguardando reanálise`:""}`));
      if(!pages.length)heading.append(note("Associe páginas a esta questão antes de registrar a leitura."));
    }
    const problem = state.problems?.find(p => (p.problem_id || p.id) === c.problem_id);
    const statement = Workspace.ProblemStatement(problem,saved,state.presentations);
    show(heading, statement, layout, actionbar, decisionBox);
    let sticky;
    const updateClearance=()=>Workspace.reserveDecisionSpace(root,decisionBox,sticky);
    saved.resizeObserver?.disconnect();
    if (window.ResizeObserver) { saved.resizeObserver=new window.ResizeObserver(()=>{updatePages();statement.updateStatementLayout();updateClearance();});saved.resizeObserver.observe(original);saved.resizeObserver.observe(statement.richContent);saved.resizeObserver.observe(decisionBox); }
    updatePages(); statement.updateStatementLayout();
    if (!saved.decision && !c.exam_submission_id) {
      sticky = node("div", undefined, "correction-action-bar"); sticky.setAttribute("aria-label","Ação da correção");
      if (primary) { const action = btn(primary.textContent,()=>primary.click()); action.disabled=state.busy; sticky.append(node("span",saved.processing ? "Processando…" : latest ? "Transcrição disponível" : "Solução preservada"),action); }
      else { sticky.append(node("span",run?.result?.score == null ? "Sugestão não determinada" : `Sugestão ${String(run.result.score).replace(".",",")}`,"sticky-suggestion"),btn("Ajustar",()=>saved.adjustDecision(),"secondary"),btn("Finalizar",()=>saved.submitDecision())); }
      for(const control of sticky.querySelectorAll("button")) control.disabled=state.busy;
      root.appendChild(sticky);saved.resizeObserver?.observe(sticky);
    }
    updateClearance();
  }
  const readingOrigin=value=>({human:"Humana",capture:"Automática · captura importada",automatic:"Automática",digital_ink:"Escrita digital"})[value]||value;
  async function openExamQuestion(c, detail) {
    const generation=state.generation;
    await loadWorkspaceContext();if(generation!==state.generation)return;
    state.current=c;state.message="";
    const saved=local(c);saved.fullExam=detail;saved.loaded=false;
    await renderCorrection();
  }
  async function importCapture(c){
    if(state.busy)return;state.busy=true;
    const saved=local(c);
    try{await post(`/tme/cases/${c.case_id}/transcriptions`,{origin:"capture",expected_mapping_version:saved.examReview.mapping_version});
      saved.loaded=false;saved.tab="transcript";state.message="Leitura importada como versão 1. Confira com o original.";
    }catch(e){state.message=e.message;}finally{state.busy=false;}
    if(state.current===c)await renderCorrection();
  }
  async function saveQuestionReading(c,editor){
    const saved=local(c),latest=saved.history?.revisions.at(-1),base=saved.editingBase??latest?.revision_number??0;
    const areas=Array.from(editor.querySelectorAll("textarea"));
    const segments=[];
    areas.forEach((area,index)=>{
      const old=latest?.segments.filter(s=>s.page_index===index).sort((a,b)=>a.order-b.order)||[];
      const text=area.value.trim();if(!text)return;
      const previous=old.map(s=>s.text||s.latex||"").join("\n\n");
      if(text===previous)segments.push(...old);
      else segments.push({segment_id:`review-page:${index}`,page_index:index,order:0,kind:"text",text});
    });
    if(!segments.length){state.message="Informe a leitura de pelo menos uma página.";return renderCorrection();}
    if(latest && base===latest.revision_number && JSON.stringify(segments)===JSON.stringify(latest.segments)){
      saved.editing=false;saved.readingDirty=false;saved.editors={};delete saved.editingBase;state.message="A leitura não mudou. Nenhuma versão adicional foi criada.";return renderCorrection();
    }
    state.busy=true;for(const control of editor.querySelectorAll("button,textarea"))control.disabled=true;
    try{
      if(base===0)await post(`/tme/cases/${c.case_id}/transcriptions`,{origin:"manual",expected_mapping_version:saved.examReview.mapping_version,segments});
      else await post(`/tme/cases/${c.case_id}/transcriptions/${saved.history.transcription.transcription_id}/revisions`,{based_on_revision_number:base,change_type:"reading_correction",status:"NEEDS_REVIEW",segments});
      saved.loaded=false;saved.editing=false;saved.readingDirty=false;saved.editors={};delete saved.editingBase;
      state.message="Nova versão salva. A leitura anterior e os originais foram preservados.";
    }catch(e){state.message="Não foi possível salvar. Seu rascunho foi mantido; confira se outra revisão foi salva antes de tentar novamente.";}
    finally{state.busy=false;}
    if(state.current===c)await renderCorrection();
  }
  window.addEventListener("beforeunload",event=>{
    if([...state.cache.values()].some(s=>s.readingDirty)){event.preventDefault();event.returnValue="";}
  });
  async function saveRevision(c, editor) {
    if (state.busy) return;
    if(c.exam_submission_id)return saveQuestionReading(c,editor);
    const saved = local(c), history = saved.history, latest = history.revisions.at(-1);
    const areas = Array.from(editor.querySelectorAll("textarea")), pages = [...new Set(latest.segments.map(s => s.page_index))].sort((a,b) => a-b);
    if (areas.some(area => !area.value.trim())) { state.message = "Todas as páginas precisam de transcrição."; return renderCorrection(); }
    state.busy = true;
    try {
      await post(`/tme/cases/${c.case_id}/transcriptions/${history.transcription.transcription_id}/revisions`, {
        based_on_revision_number: latest.revision_number, reviewer_identity_verified: false, change_type: "reading_correction", status: "NEEDS_REVIEW",
        segments: pages.map((index, i) => ({ segment_id: `tme-page:${index}`, page_index: index, order: 0, kind: "text", text: areas[i].value.trim() })) });
      saved.loaded = false; saved.editing = false; saved.editors = {}; state.message = "Nova revisão salva. A leitura anterior foi preservada.";
    } catch (_) { state.message = "Não foi possível salvar a revisão. Seu texto foi preservado; tente novamente."; }
    finally { state.busy = false; }
    if (state.current === c) await renderCorrection();
  }
  async function audit() {
    if (state.busy) return;
    const c = state.current, saved = local(c), history = saved.history, latest = history?.revisions.at(-1);
    if (!latest || c.exam_submission_id && saved.editing) return;
    const reanalysis=Boolean(c.exam_submission_id && saved.examReview.reanalysis_required);
    state.busy = true; saved.processing = "audit"; await renderCorrection();
    try {
      const accepted = await ensureAcceptance(c, history, latest);
      const request={transcription_id:history.transcription.transcription_id,revision_number:latest.revision_number,acceptance_id:accepted.acceptance_id};
      if(c.exam_submission_id){
        const version=`${history.transcription.transcription_id}:${latest.revision_number}`;
        if(saved.auditRequestVersion!==version){delete saved.auditRequestKey;saved.auditRequestVersion=version;}
        saved.auditRequestKey ||= window.crypto.randomUUID();request.execution_key=saved.auditRequestKey;
      }
      const run = await post(`/tme/cases/${c.case_id}/audits`, request);
      if(c.exam_submission_id){delete saved.auditRequestKey;saved.loaded=false;}
      saved.audits = [run, ...(saved.audits || []).filter(r => r.audit_run_id !== run.audit_run_id)]; state.message = run.stale ? "A leitura mudou durante a análise. O resultado foi preservado no histórico; reanalise a versão atual." : run.status === "COMPLETED" ? "Análise concluída." : reanalysis ? "Não foi possível concluir a reanálise." : "Não foi possível concluir a análise matemática.";
    } catch (_) { if(c.exam_submission_id)saved.loaded=false;state.message = reanalysis ? "Não foi possível concluir a reanálise. Confira a versão atual e tente novamente." : "Não foi possível concluir a análise matemática. A solução permanece preservada; tente novamente."; }
    finally { state.busy = false; saved.processing = null; }
    if (state.current === c && state.view === "workspace") await renderCorrection();
  }
  async function ensureAcceptance(c, history, latest) {
    let accepted = history.acceptances.find(a => a.revision_number === latest.revision_number);
    if (!accepted) {
      const receipt = await post(`/tme/cases/${c.case_id}/transcriptions/${history.transcription.transcription_id}/accept`, { revision_number: latest.revision_number, reviewer_identity_verified: false, acceptance_note: "Vinculação automática da revisão para análise ou decisão a pedido do avaliador; sem conferência humana obrigatória." });
      accepted = receipt.acceptance; history.acceptances.push(accepted);
    } return accepted;
  }
  async function nextCorrection(c) {
    if (state.busy) return;
    const summary = await api("/tme/home-summary?period=all");
    const next = summary.priority_cases.find(item => item.case_id !== c.case_id);
    if (next) return openCase(next.case_id);
    await cases(); root.prepend(note("Não há outra correção pendente na fila."));
  }
  function decisionPanel(c, saved, run) {
    const box = node("section", undefined, "decision-bar"); box.setAttribute("aria-label", "Decisão do avaliador"); box.id="evaluator-decision";
    box.appendChild(node("h2","Decisão do avaliador"));
    const suggestion = node("div", undefined, "decision-suggestion"); suggestion.append(node("span", "Sugestão ConfIA", "quiet-label"), node("strong", run?.result?.score == null ? "Não determinada" : `${String(run.result.score).replace(".", ",")} / ${run.result.max_score}`)); box.appendChild(suggestion);
    if (saved.decision) {
      const success=note("Correção registrada");success.classList.add("decision-success");
      box.append(success,node("strong", `Pontuação final do avaliador: ${saved.decision.final_points} / ${saved.decision.max_points}`), node("span", "Finalizada", "status"));
      const detail = node("details"); detail.append(node("summary", "Observação registrada"), node("p", saved.decision.feedback || "Sem comentário.")); box.append(detail,actions(btn("Corrigir próxima",()=>nextCorrection(c).catch(showError)),btn("Voltar para fila",()=>navigate("cases"),"secondary")));return box;
    }
    const form = node("form"), controls = {}, extras = node("details", undefined, "decision-observation"); extras.open = Boolean(saved.observationOpen);
    const observationFields = node("div", undefined, "observation-fields");
    extras.append(node("summary", "Adicionar observação"), observationFields); extras.addEventListener("toggle", () => { saved.observationOpen = extras.open; });
    const expected = () => run?.result?.score == null || !Number(run?.result?.max_score) ? null : Math.round((run.result.score / run.result.max_score * Number(controls.max.value) + Number.EPSILON) * 100) / 100;
    const reveal = () => { extras.open=true; saved.observationOpen=true; };
    // Mirrors audit_snapshot's existing eligibility; technical failures never
    // create a compulsory override reason that the server does not require.
    const result=run?.result;
    const suggestionEligible=result && result.rubric_assessment?.assessment_status!=="indeterminate" && !(result.rubric_assessment?.items||[]).some(item=>item.verification_status==="technical_error") && !(result.microclaims||[]).some(item=>item.verification_status==="technical_error") && result.pedagogical_report?.verification_status!=="technical_error";
    const validateReason = () => { const value=expected();const differs=suggestionEligible && value!==null && controls.final.value!=="" && Number(controls.final.value)!==value;controls.reason.required=differs;if(differs)reveal(); };
    for (const [name, label] of [["max", "Pontuação máxima"], ["final", "Pontuação final"], ["feedback", "Justificativa / devolutiva"], ["reason", "Motivo para divergir da sugestão"]]) {
      const input = node(["max", "final"].includes(name) ? "input" : "textarea"); controls[name] = input; input.name = name; if(name==="final") input.placeholder="—";
      if (["max", "final"].includes(name)) { input.type = "number"; input.min = name === "max" ? "0.01" : "0"; input.max = "1000"; input.step = "0.01"; input.required = true; }
      else input.maxLength=name==="reason"?2000:10000;
      input.value = saved.draft[name] ?? (name === "max" ? String(run?.result?.max_score || 10) : "");
      input.addEventListener("input", () => { saved.draft[name] = input.value; validateReason(); });
      (name === "final" ? form : observationFields).appendChild(field(label, input));
    }
    validateReason();
    const use = btn("Usar sugestão", () => { if (expected() != null) { controls.final.value = String(expected()); saved.draft.final = controls.final.value; validateReason(); controls.final.focus(); } }, "secondary"); use.disabled = state.busy || run?.result?.score == null;
    const adjust = btn("Ajustar", () => { reveal(); controls.final.focus(); box.scrollIntoView({block:"center",behavior:"smooth"}); }, "secondary ghost"); saved.adjustDecision=()=>adjust.click();
    const error = note(""); error.classList.add("decision-error");
    const submit = btn("Finalizar correção", async () => {
      if (state.busy) return;
      if (!controls.max.checkValidity()) { reveal(); controls.max.reportValidity(); return; }
      if (!controls.final.reportValidity()) return;
      if (Number(controls.final.value) > Number(controls.max.value)) { error.textContent = "A pontuação final não pode superar a máxima."; return; }
      validateReason();
      if (controls.reason.required && !controls.reason.value.trim()) { reveal(); controls.reason.focus(); controls.reason.scrollIntoView({block:"center"}); error.textContent="Informe o motivo para divergir da sugestão ConfIA."; return; }
      if (!saved.history?.revisions.length) { error.textContent="Reconheça a solução para vincular a decisão à transcrição preservada."; return; }
      state.busy = true; submit.disabled = true; use.disabled = true; adjust.disabled=true;
      try {
        await ensureAcceptance(c,saved.history,saved.history.revisions.at(-1));
        saved.decision = await post(`/tme/cases/${c.case_id}/decision`, { audit_run_id: run?.audit_run_id || null, max_points: Number(controls.max.value), final_points: Number(controls.final.value), feedback: controls.feedback.value, override_reason: controls.reason.value.trim() || null });
        saved.draft = {}; state.message = "Correção registrada."; c.status="DECIDED";
      } catch (_) { reveal(); error.textContent = "Não foi possível registrar a decisão. Confira a justificativa e tente novamente."; }
      finally { state.busy = false; submit.disabled = false; use.disabled = run?.result?.score == null; adjust.disabled=false; }
      if (saved.decision && state.current === c && state.view === "workspace") await renderCorrection();
    }, run ? "" : "secondary"); submit.disabled = state.busy; adjust.disabled=state.busy;
    saved.submitDecision=()=>{box.scrollIntoView({block:"center",behavior:"smooth"});return submit.click();};
    form.addEventListener("submit", event => { event.preventDefault(); submit.click(); }); form.append(use, adjust, extras, submit, error); box.appendChild(form); return box;
  }
  fullExam=window.ConfiaFullExam?.create({node,btn,api,post,show,openExam,openQuestion:openExamQuestion,legacy:newSingleCase,setBusy:value=>{state.busy=value;}});
  if(document.body)document.body.dataset.tmeShell="modern";
  Home.HomeHeader();
  const bottomNav = document.querySelector("#home-bottom-nav");
  if (bottomNav) Home.MobileBottomNav(bottomNav, navigate);
  for (const item of document.querySelectorAll("#workspace-nav [data-view]")) item.addEventListener("click", () => navigate(item.dataset.view));
  window.addEventListener("message", event => {
    if (event.origin !== window.location.origin || event.data?.type !== "confia-notebook-context") return;
    if (event.data.context?.tmeRecognitionFinished && event.source === state.captureWindow && state.current?.source_mode === "DIGITAL_INK") {
      local(state.current).loaded = false;
      openCase(state.current.case_id).catch(showError);
    }
  });
  const toggle = document.querySelector("#sidebar-toggle"), sidebar = document.querySelector("#sidebar");
  const setSidebar = collapsed => {
    toggle.setAttribute("aria-expanded", String(!collapsed)); toggle.setAttribute("aria-label", collapsed ? "Expandir menu" : "Recolher menu"); toggle.textContent = collapsed ? "›" : "‹";
    sidebar.classList.toggle("collapsed", collapsed);
    try { window.localStorage.setItem("confia.correction.sidebar-collapsed", String(collapsed)); } catch (_) { /* Optional preference. */ }
  };
  toggle?.addEventListener("click", () => setSidebar(toggle.getAttribute("aria-expanded") === "true"));
  try { if (window.localStorage.getItem("confia.correction.sidebar-collapsed") === "true") setSidebar(true); } catch (_) { /* Default expanded. */ }
  (async () => {
    const label = document.querySelector("#session-label"), detail = document.querySelector("#session-detail"), logout = document.querySelector("#logout");
    try {
      const user = await api("/auth/me"); label.textContent = user.display_name || user.login; const homeSession = document.querySelector("#home-session"); if (homeSession) homeSession.textContent = user.display_name || user.login || "Avaliador ConfIA"; detail.textContent = "Sessão autenticada · Avaliador"; logout.hidden = false;
      logout.addEventListener("click", async () => { const response = await fetch("/auth/logout", { method: "POST", credentials: "same-origin" }); if (response.ok) window.location.assign("/auth"); else detail.textContent = "Não foi possível encerrar a sessão."; });
    } catch (_) { if (detail) detail.textContent = "Sessão do piloto · acesso conforme configuração do servidor"; }
  })();
  currentURL="/tme"+(window.location.search||"");
  returnTo=window.history?.state?.origin||returnTo;
  window.history?.replaceState?.({tme:true,origin:returnTo},"",currentURL);
  restoreRoute();
})();
