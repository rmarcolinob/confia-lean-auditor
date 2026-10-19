// Small DOM harness for UI event/transport tests; browser checks cover CSS/layout.
function element(tag) {
  let text = "";
  const value = {
    tag, children: [], hidden: false, disabled: false, value: "", attributes: {}, listeners: {}, dataset: {},
    classList: { toggle() {} },
    style: { setProperty(key, value) { this[key] = value; }, getPropertyValue(key) { return this[key] || ""; } },
    getBoundingClientRect() { return { height: this.mockHeight || 0 }; },
    get textContent() { return text + this.children.map(child => child.textContent).join(""); },
    set textContent(content) { this.replaceChildren(); text = String(content); },
    get childNodes() { return this.children; },
    get firstChild() { return this.children[0] || null; },
    querySelectorAll(selector) { const tags = selector.split(",").map(tag => tag.trim()); return descendants(this).slice(1).filter(node => tags.includes(node.tag)); },
    setAttribute(key, content) { this.attributes[key] = String(content); },
    getAttribute(key) { return this.attributes[key] ?? null; },
    appendChild(child) {
      if (child.parentNode) child.parentNode.removeChild(child);
      child.parentNode = this;
      this.children.push(child);
      if (tag === "select" && this.children.length === 1) this.value = child.value;
      return child;
    },
    removeChild(child) {
      this.children.splice(this.children.indexOf(child), 1);
      child.parentNode = null;
      if (tag === "select" && !this.children.length) this.value = "";
      return child;
    },
    replaceChildren(...children) {
      for (const child of this.children) child.parentNode = null;
      this.children = []; text = "";
      for (const child of children) this.appendChild(child);
    },
    addEventListener(event, fn) { (this.listeners[event] ||= []).push(fn); },
    emit(event, data = {}) { return Promise.all((this.listeners[event] || []).map(fn => fn(data))); },
    click() { if (!this.disabled) return this.emit("click"); },
    focus() { if (!this.disabled) this.focused = true; },
  };
  return value;
}
const descendants = node => [node, ...node.children.flatMap(descendants)];
const flush = () => new Promise(resolve => setImmediate(resolve));
const deferred = () => { let resolve; const promise = new Promise(yes => { resolve = yes; }); return { promise, resolve }; };
module.exports = { element, descendants, flush, deferred };
