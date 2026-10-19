/* Session-only pedagogical chat UI. The adapter returns declared DEMO responses. */
(function tutoriaChat() {
  "use strict";
  const demo = window.ConfIATutoriaChatDemo;
  if (!demo) return;
  const conversations = new Map();
  const MAX_MESSAGE_LENGTH = 2000;
  let currentKey = null, mounted = null;
  const node = (parent, tag, text, className = "") => {
    const element = document.createElement(tag); element.className = className;
    if (text !== undefined) element.textContent = text;
    parent?.appendChild(element); return element;
  };
  const button = (parent, text, action, className = "secondary-action") => {
    const control = node(parent, "button", text, className); control.type = "button";
    control.addEventListener("click", action); return control;
  };
  function math(parent, text) {
    const body = node(parent, "div", undefined, "tutoria-chat-text");
    if (globalThis.ConfiaRecognitionView) globalThis.ConfiaRecognitionView.renderMathText(body, text);
    else body.textContent = text;
  }
  function createConversation(context, messages) {
    return { context, messages: messages.map(message => ({ ...message })), initialMessages: messages,
      draft: "", pending: false, hintIndex: 0 };
  }

  function intentFor(text) {
    const normalized = text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    if (/coeficiente angular/.test(normalized)) return "angular";
    if (/exemplo/.test(normalized)) return "example";
    if (/pista/.test(normalized)) return "hint";
    if (/comec|inici/.test(normalized)) return "start";
    if (/raciocinio|passo|certo|sentido/.test(normalized)) return "reasoning";
    if (/expli|outro jeito|nao entendi/.test(normalized)) return "explain";
    return "fallback";
  }
  // Replace this adapter only when an independently authorized pedagogical service exists.
  // Future request boundary: message, allowlisted study context, previousMessages.
  // No student identity, institutional records, external transport or persistent memory here.
  const adapter = {
    reply({ message, context, intent, hintIndex }) {
      const selected = intent || intentFor(message);
      const responses = context.kind === "content" && context.theme === "Funções" ? demo.replies.functions : demo.replies[context.kind] || demo.replies.content;
      const value = selected === "angular" ? demo.angularCoefficient : responses[selected] || responses.fallback;
      return Promise.resolve({ origin: "DEMO", text: Array.isArray(value) ? value[Math.min(hintIndex, value.length - 1)] : value });
    },
  };
  function appendMessage(log, message) {
    const article = node(log, "article", undefined, `tutoria-chat-message tutoria-chat-${message.role}`);
    article.dataset.origin = message.origin;
    const author = message.role === "tutor" ? "TutorIA" : message.origin === "DEMO" ? "Aluno · exemplo" : "Você";
    const authorLine = node(article, "p", undefined, "tutoria-chat-author");
    node(authorLine, "span", author); math(article, message.text);
  }
  function updateControls(view) {
    const conversation = view.conversation;
    view.send.disabled = conversation.pending || !conversation.draft.trim();
    view.input.disabled = conversation.pending;
    view.reset.disabled = conversation.pending;
    view.quickButtons.forEach(control => { control.disabled = conversation.pending; });
    view.form.setAttribute("aria-busy", String(conversation.pending));
  }
  async function send(view, text, intent) {
    const conversation = view.conversation;
    if (conversation.pending || !view.allowed()) return;
    const message = text.trim();
    if (!message) { view.status.textContent = "Digite sua dúvida para continuar."; view.input.focus(); return; }
    if (message.length > MAX_MESSAGE_LENGTH) {
      view.status.textContent = `Use até ${MAX_MESSAGE_LENGTH} caracteres por mensagem.`; view.input.focus(); return;
    }
    const previousMessages = conversation.messages.map(item => ({ role: item.role, text: item.text, origin: item.origin }));
    const entry = { role: "student", text: message, origin: "REAL" };
    conversation.messages.push(entry); conversation.draft = ""; conversation.pending = true;
    view.input.value = ""; view.status.textContent = "Preparando resposta demonstrativa…";
    appendMessage(view.log, entry); updateControls(view);
    const selectedIntent = intent || intentFor(message);
    try {
      const response = await adapter.reply({ message, context: { ...conversation.context }, previousMessages,
        intent: selectedIntent, hintIndex: conversation.hintIndex });
      if (selectedIntent === "hint") conversation.hintIndex += 1;
      const reply = { role: "tutor", text: response.text, origin: "DEMO" };
      conversation.messages.push(reply);
      if (mounted?.conversation === conversation && mounted.allowed()) {
        appendMessage(mounted.log, reply); mounted.status.textContent = "Resposta demonstrativa adicionada.";
      }
    } catch (_) {
      if (mounted?.conversation === conversation && mounted.allowed()) mounted.status.textContent = "Não foi possível preparar a resposta. Tente novamente.";
    } finally {
      conversation.pending = false;
      if (mounted?.conversation === conversation && mounted.allowed()) {
        updateControls(mounted); mounted.log.scrollTop = mounted.log.scrollHeight; mounted.input.focus({ preventScroll: true });
      }
    }
  }
  function contextLine(context) {
    if (context.kind === "question" && context.problemId) return `Você está trabalhando na questão ${context.problemId}.`;
    if (context.kind === "attempt") return "Você está revisando uma tentativa.";
    if (context.kind === "content" && (context.contentTitle || context.theme)) return `Você está estudando: ${context.contentTitle || context.theme}.`;
    if (context.kind === "bank") return context.theme ? `Você está explorando questões de ${context.theme}.` : "Você está explorando o banco de questões.";
    return "Como posso ajudar nos seus estudos?";
  }
  function contextCard(parent, context) {
    const details = node(parent, "details", undefined, "card tutoria-chat-context"); details.open = false;
    node(details, "summary", contextLine(context));
    const content = node(details, "div", undefined, "tutoria-chat-context-body");
    node(content, "span", context.origin === "REAL" ? "Contexto desta sessão" : "Contexto ilustrativo", "status");
    content.dataset.origin = context.origin;
    for (const [label, value] of [["Tema", context.theme], ["Conteúdo", context.contentTitle], ["Questão atual", context.problemId ? `${context.problemId} · ${context.problemTitle}` : context.problemTitle]]) {
      if (value) { node(content, "h3", label); node(content, "p", value); }
    }
    if (context.problemId) node(content, "p", "Você está estudando esta questão.", "form-help");
    if (context.attemptText) {
      const attempt = node(content, "details"); node(attempt, "summary", context.origin === "REAL" ? "Ver tentativa compartilhada" : "Ver tentativa ilustrativa");
      math(attempt, context.attemptText);
    }
    node(content, "p", "As respostas desta experiência são predefinidas. O contexto permanece somente nesta sessão.", "form-help");
    return details;
  }
  function mount(host, { allowed = () => window.ConfIATutoriaAssistant?.isAllowed() === true } = {}) {
    if (!allowed() || !conversations.has(currentKey)) return;
    const conversation = conversations.get(currentKey);
    const root = node(host, "section", undefined, "tutoria-chat"); root.dataset.origin = "DEMO";
    const layout = node(root, "div", undefined, "tutoria-chat-layout");
    const context = contextCard(layout, conversation.context);
    const panel = node(layout, "section", undefined, "card tutoria-chat-conversation");
    const panelHeading = node(panel, "div", undefined, "tutoria-chat-panel-heading");
    const heading = node(panelHeading, "h3", "Conversa sobre seu estudo"); heading.tabIndex = -1;
    const reset = button(panelHeading, "Nova conversa", () => {
      if (conversation.pending) return;
      conversation.messages = conversation.initialMessages.map(message => ({ ...message })); conversation.draft = ""; conversation.hintIndex = 0;
      host.replaceChildren(); mount(host, { allowed }); mounted.input.focus({ preventScroll: true });
    });
    reset.disabled = conversation.pending;
    const log = node(panel, "div", undefined, "tutoria-chat-messages");
    log.setAttribute("role", "log"); log.setAttribute("aria-label", "Conversa com TutorIA");
    log.setAttribute("aria-live", "polite"); log.setAttribute("aria-relevant", "additions"); log.tabIndex = 0;
    conversation.messages.forEach(message => appendMessage(log, message));
    const quick = node(panel, "div", undefined, "tutoria-chat-quick"); quick.setAttribute("role", "group"); quick.setAttribute("aria-label", "Sugestões de mensagem");
    const form = node(panel, "form", undefined, "tutoria-chat-composer");
    const prefix = "tutoria-drawer-chat";
    const label = node(form, "label", "Sua dúvida", "form-field"); label.setAttribute("for", `${prefix}-input`);
    const input = node(label, "textarea"); input.id = `${prefix}-input`; input.rows = 2; input.maxLength = MAX_MESSAGE_LENGTH;
    input.placeholder = "Digite sua dúvida..."; input.value = conversation.draft;
    input.setAttribute("aria-describedby", `${prefix}-message-status ${prefix}-session-note`);
    const submit = node(form, "button", "Enviar", "primary-action"); submit.type = "submit";
    const status = node(panel, "p", "", "action-message"); status.id = `${prefix}-message-status`; status.setAttribute("role", "status");
    node(panel, "p", "Respostas predefinidas · conversa nesta sessão.", "form-help").id = `${prefix}-session-note`;
    const view = { host, conversation, heading, context, log, form, input, send: submit, reset, quickButtons: [], status, allowed };
    mounted = view;
    view.quickButtons = demo.quickPrompts.map(prompt => button(quick, prompt.label, () => send(view, prompt.label, prompt.id)));
    input.addEventListener("input", () => { conversation.draft = input.value; updateControls(view); });
    input.addEventListener("keydown", event => {
      if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(view, input.value); }
    });
    form.addEventListener("submit", event => { event.preventDefault(); send(view, input.value); });
    updateControls(view); log.scrollTop = log.scrollHeight;
  }
  function selectContext(study) {
    // Explicit allowlist: never spread a submission, analysis response or identity into context.
    const context = { kind: ["home", "content", "bank", "question", "attempt"].includes(study?.kind) ? study.kind : "home",
      origin: study?.origin === "REAL" ? "REAL" : "DEMO" };
    for (const key of ["theme", "contentId", "contentTitle", "problemId", "problemTitle", "attemptText"]) {
      if (typeof study?.[key] === "string" && study[key]) context[key] = study[key];
    }
    currentKey = `study:${JSON.stringify(context)}`;
    if (!conversations.has(currentKey)) {
      const greeting = contextLine(context) + (context.kind === "question" ? " Qual informação do enunciado parece mais útil para começar?"
        : context.kind === "attempt" ? " Qual passagem gera dúvida?" : context.kind === "content" ? " Qual ideia você gostaria de compreender melhor?" : "");
      conversations.set(currentKey, createConversation(context, [{ role: "tutor", text: greeting, origin: "DEMO" }]));
    }
    return currentKey;
  }
  window.ConfIATutoriaChat = {
    mount, selectContext,
    unmount(host) { if (!host || mounted?.host === host) mounted = null; },
  };
})();
