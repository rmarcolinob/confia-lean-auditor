/* Contextual, session-only companion. Never sends commands to the notebook. */
(function tutoriaAssistant() {
  "use strict";
  const get = id => document.querySelector(`#${id}`);
  const rail = get("tutoria-assistant-rail"), toggle = get("tutoria-assistant-toggle");
  const drawer = get("tutoria-assistant-drawer"), host = get("tutoria-assistant-content");
  const chat = window.ConfIATutoriaChat;
  if (!rail || !drawer || !chat) return;
  let opened = false, renderedKey = null, returnFocus = null;
  function isAllowed() {
    const route = window.ConfIAShell?.current;
    const workspace = window.ConfIAWorkspace;
    if (document.body.classList?.contains("auth-enabled") && window.ConfIAAuthProfile !== "student") return false;
    return route?.profile === "student" && (route.view === "tutoria"
      || /^tutoria\/(content|questions|practice|feedback|trails|progress|attempts)$/.test(route.view))
      && workspace?.experience !== "EXAM" && workspace?.mode !== "submission";
  }
  function available() { return isAllowed(); }
  function studyContext() {
    const view = window.ConfIAShell.current.view;
    if (view === "tutoria/practice") {
      return window.ConfIAWorkspace?.studyContext() || { kind: "home", origin: "REAL" };
    }
    return window.ConfIATutoria?.studyContext() || { kind: "home", origin: "REAL" };
  }
  function layout() {
    const enabled = available();
    document.body.dataset.tutoriaAssistantAvailable = String(enabled);
    document.body.dataset.tutoriaAssistantOpen = String(opened && enabled);
    rail.hidden = !enabled || opened;
    drawer.hidden = !enabled || !opened;
    toggle.setAttribute("aria-expanded", String(opened && enabled));
  }
  function close({ restoreFocus = false } = {}) {
    opened = false; renderedKey = null;
    chat.unmount(host); host.replaceChildren(); layout();
    if (restoreFocus && available()) {
      (returnFocus?.isConnected ? returnFocus : toggle).focus({ preventScroll: true });
    }
  }
  function render(study) {
    const key = chat.selectContext(study);
    if (renderedKey === key) return;
    chat.unmount(host); host.replaceChildren();
    chat.mount(host, { allowed: () => opened && available() });
    renderedKey = key;
  }
  function sync() {
    if (!available()) { close(); return; }
    layout();
    if (opened) render(studyContext());
  }
  function open() {
    if (!available()) return false;
    returnFocus = document.activeElement;
    opened = true; layout(); render(studyContext());
    get("tutoria-assistant-title").focus({ preventScroll: true });
    return true;
  }
  toggle.addEventListener("click", () => open());
  get("tutoria-assistant-close").addEventListener("click", () => close({ restoreFocus: true }));
  drawer.addEventListener("keydown", event => {
    if (event.key === "Escape") { event.preventDefault(); close({ restoreFocus: true }); }
  });
  window.ConfIATutoriaAssistant = { isAllowed, sync, open, close };
})();
