/* Presentation components for the existing CorrectionCase flow. No audit inference. */
(function (root) {
  "use strict";
  const n = (tag, text, cls) => { const e = document.createElement(tag); if (text != null) e.textContent = text; if (cls) e.className = cls; return e; };
  const button = (label, action, cls = "secondary") => { const e = n("button", label, cls); e.type = "button"; e.addEventListener("click", action); return e; };
  const displayExamName = value => {
    const code=String(value ?? "").trim(), numbered=code.match(/^prova[ _-]*(\d+)$/i);
    return numbered ? `Prova ${numbered[1]}` : code ? `Prova ${code}` : "Prova";
  };
  const question = c => c.question_order || c.problem_id.match(/[QP](\d+)$/)?.[1];
  function relatedCases(c, cases) {
    const family = c.problem_id.replace(/[QP]\d+$/, "");
    const unique = new Map();
    for (const item of [c, ...cases]) if (item.external_candidate_ref === c.external_candidate_ref && item.problem_id.replace(/[QP]\d+$/, "") === family && !unique.has(item.problem_id)) unique.set(item.problem_id, item);
    return [...unique.values()].sort((a,b) => a.problem_id.localeCompare(b.problem_id, undefined, {numeric:true}));
  }
  function QuestionNavigator(c, siblings, status, open, busy) {
    const nav = n("nav", null, "question-navigator"); nav.setAttribute("aria-label", "Questões disponíveis desta prova");
    siblings.forEach(item => {
      const current = item.case_id === c.case_id, label = question(item) ? `Q${question(item)}` : item.problem_id;
      const state = status(item), symbol = current ? "●" : state === "Finalizada" ? "✓" : ["Inconclusiva","Revisão necessária"].includes(state) ? "?" : "○";
      const control = button(`${label} ${symbol}`, () => open(item.case_id)); control.dataset.state = current ? "current" : state === "Finalizada" ? "done" : ["Inconclusiva","Revisão necessária"].includes(state) ? "pending" : "available";
      control.setAttribute("aria-label", `${label} · ${current ? "Questão atual" : state}`); control.setAttribute("aria-current", current ? "step" : "false"); control.disabled = busy;
      nav.append(control);
    }); return nav;
  }
  function CorrectionHeader({c, cases, status, open, back, steps, active, busy}) {
    const header = n("header", null, "case-context"), siblings = c.exam_submission_id ? cases.filter(item=>item.exam_submission_id===c.exam_submission_id).sort((a,b)=>a.question_order-b.question_order) : relatedCases(c,cases), line = n("div",null,"case-title-line");
    const goBack = button("←",back,"workspace-back secondary"); goBack.setAttribute("aria-label",c.exam_submission_id?"Voltar às páginas e associações":"Voltar para fila"); goBack.disabled=busy; goBack.replaceChildren(root.ConfiaTmeHome.icon("back"));
    const pill = n("span",status(c),"status"); pill.dataset.kind = status(c)==="Finalizada"?"success":status(c)==="Inconclusiva"?"pending":"info";
    line.append(goBack,n("h1",displayExamName(c.external_candidate_ref)),pill);
    if(c.data_origin==="synthetic_demo")line.append(n("small","CASO SINTÉTICO · transcrição importada"));
    if(c.demo_sample_groups?.length)line.append(n("small","AMOSTRA VISUAL · "+c.demo_sample_groups.join(", ")));
    const info = n("div",null,"case-information");
    // The catalog is not a roster: count only real, distinct CorrectionCases.
    info.append(n("strong",`Questão ${question(c)||c.problem_id}`),n("span",`${siblings.length} ${siblings.length===1?"questão disponível":"questões disponíveis"}`,"known-questions"),n("span",c.problem_id),n("span",c.exam_submission_id?"Prova completa":c.source_mode==="IMAGE_SCAN"?"Foto / scan":"Escrita digital","case-source"));
    header.dataset.questionCount=String(siblings.length);
    header.append(line,info,QuestionNavigator(c,siblings,status,open,busy),steps(active)); return header;
  }
  function ProblemStatement(problem, saved, registry = []) {
    const section=n("section",null,"problem-statement"), heading=n("div",null,"problem-heading"), content=n("div",null,"problem-content"), rich=n("div",null,"problem-rich-text"); content.id="problem-statement";
    const source=problem?.statement||"Enunciado não disponível no catálogo desta questão.";
    const renderText=(target,value)=>{
      if (root.ConfiaProblemMath) root.ConfiaProblemMath.renderContent(target,value,{problemId:problem?.problem_id||problem?.id,registry});
      else target.textContent=value;
    };
    if (Array.isArray(problem?.statement_blocks) && problem.statement_blocks.length) {
      for (const block of problem.statement_blocks) {
        if (block.type === "text") {
          const paragraph=n("p"); renderText(paragraph,block.text); rich.appendChild(paragraph);
        } else if (block.type === "figure") {
          const asset=problem.figures?.find(f=>f.id===block.figure_id);
          // Only versioned, local problem assets; never inject catalog HTML.
          if (!asset || !/^\/static\/problem-assets\/TME2026P[1-5]\/[a-z0-9-]+\.png$/.test(asset.src)) continue;
          const figure=n("figure",null,"problem-figure"),img=n("img");
          img.src=asset.src;img.alt=asset.alt;img.width=asset.width;img.height=asset.height;
          figure.appendChild(img);rich.appendChild(figure);
        }
      }
    } else renderText(rich,source);
    content.appendChild(rich);
    // Keep the same rendered subtree expanded/collapsed. At a compact boundary,
    // move the cutoff before a formula instead of slicing its fractions/glyphs.
    section.richContent=rich;
    section.updateStatementLayout=()=>{
      if (!content.isConnected || !root.getComputedStyle) return;
      const top=rich.getBoundingClientRect().top, full=rich.getBoundingClientRect().height;
      const compact=Boolean(root.matchMedia?.("(max-width: 767px)").matches);
      let limit=parseFloat(root.getComputedStyle(content).fontSize)*(compact?4.65:6);
      for (const math of rich.querySelectorAll(".katex")) {
        const box=math.getBoundingClientRect(), start=box.top-top, end=box.bottom-top;
        if (start<limit && end>limit) limit=start>1?start:end;
      }
      content.style.maxHeight=saved.statementOpen?"none":`${limit}px`;
      content.dataset.clipped=String(!saved.statementOpen && full>limit+1);
    };
    const toggle=button("",()=>{saved.statementOpen=!saved.statementOpen;update();});
    const update=()=>{content.classList.toggle("expanded",Boolean(saved.statementOpen));toggle.textContent=saved.statementOpen?"Recolher enunciado":"Ver enunciado completo";toggle.setAttribute("aria-expanded",String(Boolean(saved.statementOpen)));section.updateStatementLayout();};
    toggle.setAttribute("aria-controls",content.id);update();heading.append(n("h2","Enunciado"),toggle);section.append(heading,content);return section;
  }
  const isDesktop = () => Boolean(root.matchMedia?.("(min-width: 1100px)").matches);
  const originalFitMode = saved => saved.fitMode || (isDesktop() ? "page" : "width");
  function layoutOriginal(page,img,viewport,saved) {
    const availableWidth=Math.max(1,(viewport.clientWidth||600)-4),ratio=img.naturalHeight&&img.naturalWidth?img.naturalHeight/img.naturalWidth:1.4,z=saved.zoom,r=saved.rotation;
    const desktop=isDesktop(), mode=originalFitMode(saved), rotated=r===90||r===270;
    const fullPage=desktop && viewport.dataset?.layout==="full-page";
    let width=desktop?availableWidth/(rotated?ratio:1):availableWidth;
    if(desktop && !fullPage && mode==="page" && viewport.clientHeight) width=Math.min(width,Math.max(1,viewport.clientHeight-4)/(rotated?1:ratio));
    // Manual zoom freezes its base size; automatic fits follow viewport changes.
    if(desktop && mode==="custom" && saved.customWidth>0) width=saved.customWidth;
    const height=width*ratio;
    // Normal desktop Original belongs to the document flow. Keep a scrollable
    // viewport only for manual enlargement, comparison and smaller breakpoints.
    if(viewport.dataset && !page.hidden) viewport.dataset.scrollMode=fullPage && z<=1 && (rotated?height:width)*z<=availableWidth+.5?"document":"viewer";
    const surface=page.querySelectorAll("div").find ? page.querySelectorAll("div").find(e=>e.className==="manuscript-surface") : page.querySelector(".manuscript-surface");
    const turned=r===90||r===270;
    if(surface){surface.style.width=`${(turned?height:width)*z}px`;surface.style.height=`${(turned?width:height)*z}px`;}
    page.style.paddingTop=desktop && !fullPage?`${Math.max(0,((viewport.clientHeight||0)-(turned?width:height)*z)/2)}px`:"";
    page.style.width=`${Math.max(availableWidth,(turned?height:width)*z)}px`;img.style.width=`${width}px`;
    const x=r===90?height*z:r===180?width*z:0,y=r===180?height*z:r===270?width*z:0;
    img.style.transform=`translate(${x}px, ${y}px) scale(${z}) rotate(${r}deg)`;
  }
  function reserveDecisionSpace(host, decision, action) {
    // Use actual rendered heights so wrapped labels and safe-area padding remain covered.
    const decisionHeight=Math.ceil(decision.getBoundingClientRect().height||0);
    const actionHeight=Math.ceil(action?.getBoundingClientRect().height||0);
    if(decisionHeight) host.style.setProperty("--decision-clearance",`${decisionHeight}px`);
    if(actionHeight) host.style.setProperty("--action-clearance",`${actionHeight}px`);
  }
  function attachPan(viewport, saved) {
    let start=null;
    viewport.setAttribute("aria-label","Original ampliável; use as barras de rolagem ou arraste para mover"); viewport.tabIndex=0;
    viewport.addEventListener("pointerdown",event=>{if(event.button!==0||saved.zoom<=1||event.target?.tagName==="A")return;start={x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};viewport.setPointerCapture(event.pointerId);event.preventDefault();});
    viewport.addEventListener("pointermove",event=>{if(start){viewport.scrollLeft=start.left+start.x-event.clientX;viewport.scrollTop=start.top+start.y-event.clientY;}});
    const stop=()=>{start=null;}; for(const event of ["pointerup","pointercancel","lostpointercapture"])viewport.addEventListener(event,stop);
  }
  root.ConfiaCorrectionWorkspace={displayExamName,reserveDecisionSpace,CorrectionHeader,QuestionNavigator,ProblemStatement,attachPan,layoutOriginal,relatedCases,originalFitMode,isDesktop};
})(window);
