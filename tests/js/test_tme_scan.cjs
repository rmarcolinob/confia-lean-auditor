const test = require("node:test");
const assert = require("node:assert/strict");
const Scan = require("../../app/confia_lean_auditor/static/tme/scan-model.js");

const file = (type = "image/jpeg", size = 100) => ({ type, size });
const photo = id => Scan.photo(file(), `blob:${id}`, "2026-10-19T12:00:00Z");

test("mobile photo review supports add, confirm, reorder, rotate, replace and remove", () => {
  const pages = [];
  const a = photo("a"), b = photo("b"), c = photo("c");
  Scan.add(pages, a); Scan.add(pages, b);
  assert.equal(Scan.ready(pages), false);
  Scan.confirm(a); Scan.confirm(b);
  assert.equal(Scan.ready(pages), true);
  assert.equal(Scan.move(pages, 1, -1), true);
  assert.deepEqual(pages.map(p => p.url), ["blob:b", "blob:a"]);
  Scan.rotate(b);
  assert.equal(b.rotation, 90);
  assert.equal(Scan.ready(pages), false);
  Scan.confirm(b);
  assert.equal(Scan.replace(pages, 1, c), a);
  assert.equal(Scan.ready(pages), false);
  Scan.confirm(c);
  assert.equal(Scan.remove(pages, 0), b);
  assert.deepEqual(pages, [c]);
});

test("photo limits and unsupported formats fail before upload", () => {
  for (const invalid of [file("image/gif"), file("image/jpeg", 0), file("image/png", 9 * 1024 * 1024)])
    assert.throws(() => Scan.validate(invalid));
  const pages = [photo("1"), photo("2"), photo("3")];
  assert.throws(() => Scan.add(pages, photo("4")), /três páginas/);
  assert.equal(pages.length, 3);
});

test("OCR PNG is physically rotated and resized without changing the original", async () => {
  const original = file("image/heic", 123);
  const item = Scan.photo(original, "blob:original", "2026-10-19T12:00:00Z");
  Scan.rotate(item);
  const operations = [];
  let canvas;
  const derived = await Scan.derive(item, async (received, options) => {
    assert.equal(received, original);
    assert.equal(options.imageOrientation, "from-image");
    return { width: 4000, height: 2000, close: () => operations.push("close") };
  }, () => canvas = { getContext: () => ({
    fillRect: (...args) => operations.push(["fill", ...args]),
    translate: (...args) => operations.push(["translate", ...args]),
    rotate: degrees => operations.push(["rotate", degrees]),
    drawImage: (...args) => operations.push(["draw", ...args.slice(1)]),
  }), toDataURL: () => "data:image/png;base64,cG5n" });
  assert.deepEqual(derived, { derived_png_base64: "cG5n", derived_width: 1024, derived_height: 2048 });
  assert.equal(canvas.width, 1024);
  assert.deepEqual(operations.find(op => op[0] === "rotate"), ["rotate", Math.PI / 2]);
  assert.equal(item.file, original);
  assert.equal(item.rotation, 90);
  assert.equal(operations.at(-1), "close");
});

test("failed decode leaves the selected original and review state intact", async () => {
  const item = photo("kept"); Scan.confirm(item);
  await assert.rejects(Scan.derive(item, async () => { throw Error("decoder"); }, () => {}), /JPEG ou PNG/);
  assert.equal(item.url, "blob:kept");
  assert.equal(item.confirmed, true);
});
