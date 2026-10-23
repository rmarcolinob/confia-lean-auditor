/* UI-only split state. No case or audit data is written to browser storage. */
(function (root) {
  "use strict";
  const key = "confia.correction.split-percent.v1";
  const clamp = value => Math.min(70, Math.max(45, Number(value) || 60));
  function attachSplitter(layout, handle) {
    let value = 60, dragging = false;
    try { value = clamp(root.localStorage.getItem(key)); } catch (_) { /* Storage may be disabled. */ }
    const update = (next, persist = true) => {
      value = clamp(next); layout.style.setProperty("--solution-share", `${value}%`);
      layout.style.setProperty("--solution-track", `${value}fr`);
      layout.style.setProperty("--analysis-track", `${100 - value}fr`);
      handle.setAttribute("aria-valuenow", String(Math.round(value)));
      handle.setAttribute("aria-valuetext", `Solução ${Math.round(value)}%, análise ${100 - Math.round(value)}%`);
      if (persist) try { root.localStorage.setItem(key, String(value)); } catch (_) { /* In-memory resize still works. */ }
    };
    handle.tabIndex = 0;
    for (const [name, content] of Object.entries({ role: "separator", "aria-label": "Redimensionar solução e análise", "aria-orientation": "vertical", "aria-valuemin": "45", "aria-valuemax": "70", "aria-controls": "solution-pane analysis-pane" })) handle.setAttribute(name, content);
    handle.title = "Arraste ou use as setas. Home: 45%; End: 70%; duplo clique: 60%.";
    handle.addEventListener("keydown", event => {
      const next = { ArrowLeft: value - 2, ArrowRight: value + 2, Home: 45, End: 70 }[event.key];
      if (next !== undefined) { event.preventDefault(); update(next); }
    });
    handle.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      dragging = true; handle.setPointerCapture(event.pointerId); handle.classList.add("dragging"); event.preventDefault();
    });
    handle.addEventListener("pointermove", event => {
      if (!dragging) return;
      const bounds = layout.getBoundingClientRect();
      if (bounds.width) update((event.clientX - bounds.left) / bounds.width * 100, false);
    });
    const finish = () => { if (dragging) update(value); dragging = false; handle.classList.remove("dragging"); };
    handle.addEventListener("pointerup", finish); handle.addEventListener("pointercancel", finish);
    handle.addEventListener("lostpointercapture", finish); handle.addEventListener("dblclick", () => update(60));
    update(value, false);
  }
  root.ConfiaWorkspaceControls = { attachSplitter };
})(window);
