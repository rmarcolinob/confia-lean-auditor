(function expose(root, factory) {
  "use strict";
  const model = factory();
  if (typeof module === "object" && module.exports) module.exports = model;
  else root.ConfiaTMEScan = model;
})(globalThis, function () {
  "use strict";
  const maxPages = 3;
  const formats = new Set(["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]);
  function validate(file) {
    if (!file || !formats.has(file.type) || !file.size || file.size > 8 * 1024 * 1024)
      throw new Error("Escolha uma imagem JPEG, PNG, WebP ou HEIC de até 8 MB.");
  }
  function photo(file, url, capturedAt) { validate(file); return { file, url, capturedAt, rotation: 0, confirmed: false }; }
  function add(pages, item) { if (pages.length >= maxPages) throw new Error("Limite de três páginas."); pages.push(item); }
  function replace(pages, index, item) { if (!pages[index]) throw new Error("Página inexistente."); const old = pages[index]; pages[index] = item; return old; }
  function remove(pages, index) { if (!pages[index]) throw new Error("Página inexistente."); return pages.splice(index, 1)[0]; }
  function move(pages, index, direction) {
    const other = index + direction;
    if (!pages[index] || !pages[other] || Math.abs(direction) !== 1) return false;
    [pages[index], pages[other]] = [pages[other], pages[index]]; return true;
  }
  function rotate(item) { item.rotation = (item.rotation + 90) % 360; item.confirmed = false; }
  function confirm(item) { item.confirmed = true; }
  function ready(pages) { return pages.length > 0 && pages.length <= maxPages && pages.every(p => p.confirmed); }
  async function derive(item, bitmapFactory, canvasFactory) {
    let bitmap;
    try { bitmap = await bitmapFactory(item.file, { imageOrientation: "from-image" }); }
    catch (_) { throw new Error("Este formato não pôde ser aberto neste dispositivo. Selecione JPEG ou PNG."); }
    try {
      const scale = Math.min(1, 2048 / Math.max(bitmap.width, bitmap.height));
      const w = Math.max(1, Math.round(bitmap.width * scale)), h = Math.max(1, Math.round(bitmap.height * scale));
      const turn = item.rotation % 180 !== 0, canvas = canvasFactory();
      canvas.width = turn ? h : w; canvas.height = turn ? w : h;
      const ctx = canvas.getContext("2d"); ctx.fillStyle = "white"; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.translate(canvas.width / 2, canvas.height / 2); ctx.rotate(item.rotation * Math.PI / 180);
      ctx.drawImage(bitmap, -w / 2, -h / 2, w, h);
      const base64 = canvas.toDataURL("image/png").split(",")[1];
      if (!base64 || base64.length > 11_200_000) throw new Error("A página derivada excede 8 MB. Tente uma foto menor.");
      return { derived_png_base64: base64, derived_width: canvas.width, derived_height: canvas.height };
    } finally { bitmap.close?.(); }
  }
  return { maxPages, validate, photo, add, replace, remove, move, rotate, confirm, ready, derive };
});
