const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");

const source = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/capture/ink-canvas.js"), "utf8");

function canvas(width = 1200) {
  const commands = [];
  const context = {
    setTransform() {}, clearRect() {}, fillRect() {}, beginPath() {},
    moveTo(...args) { commands.push(["moveTo", ...args]); },
    lineTo(...args) { commands.push(["lineTo", ...args]); },
    arc(...args) { commands.push(["arc", ...args]); },
    stroke() { commands.push(["stroke", this.lineWidth, this.strokeStyle]); },
    fill() { commands.push(["fill", this.fillStyle]); },
  };
  return {
    style: {}, commands,
    getBoundingClientRect: () => ({ width, height: width * 4 / 3 }),
    getContext: () => context,
    toBlob(callback, type) { callback({ type }); },
  };
}

for (const singlePoint of [false, true]) {
  test(`canvas, preview and PNG share thinner ${singlePoint ? "dots" : "lines"} without changing saved data`, async () => {
    const pngCanvas = canvas();
    const runtime = {
      ConfiaInkModel: Model,
      devicePixelRatio: 2,
      document: { createElement: () => pngCanvas },
    };
    vm.runInNewContext(source, runtime);
    let document = Model.createDraft("ITA2025Q1");
    const pageId = document.pages[0].page_id;
    const points = [{ x: 120, y: 180, t_ms: 0, pressure_reported: 0.5 }];
    if (!singlePoint) points.push({ x: 240, y: 300, t_ms: 10, pressure_reported: 0.7 });
    document = Model.addStroke(document, {
      stroke_id: "stroke:test", page_id: pageId, pointer_type: "pen",
      color: "#17355c", width: Model.CONFIG.penWidth, points,
    });
    document = Model.freeze(document);
    const originalJson = JSON.stringify(document);

    // Different CSS sizes and DPR must keep the same logical drawing geometry.
    const notebook = canvas(900);
    const preview = canvas(360);
    runtime.ConfiaInkCanvas.render(notebook, document, pageId, { grid: false });
    runtime.ConfiaInkCanvas.render(preview, document, pageId, { grid: false });
    const png = await runtime.ConfiaInkCanvas.pngBlob(document, pageId);

    assert.deepEqual(notebook.commands, preview.commands);
    assert.deepEqual(notebook.commands, pngCanvas.commands);
    assert.equal(png.type, "image/png");
    if (singlePoint) {
      assert.deepEqual(notebook.commands[0], ["arc", 120, 180, 1.5, 0, Math.PI * 2]);
    } else {
      assert.deepEqual(notebook.commands, [
        ["moveTo", 120, 180], ["lineTo", 240, 300], ["stroke", 3, "#17355c"],
      ]);
    }
    assert.equal(JSON.stringify(document), originalJson);
    assert.equal(document.strokes[0].width, 4);
  });
}

test("the live stroke uses the same visual width before it is committed", () => {
  const runtime = { ConfiaInkModel: Model, devicePixelRatio: 1 };
  vm.runInNewContext(source, runtime);
  const document = Model.createDraft("ITA2025Q1");
  const target = canvas();
  const stroke = {
    width: 4, color: "#17355c",
    points: [{ x: 10, y: 20 }, { x: 30, y: 40 }],
  };
  runtime.ConfiaInkCanvas.render(target, document, document.pages[0].page_id, {
    grid: false, transientStroke: stroke,
  });
  assert.deepEqual(target.commands.at(-1), ["stroke", 3, "#17355c"]);
  assert.equal(stroke.width, 4);
});

test("viewport resizing and scrolling preserve logical pointer alignment and reported pressure", () => {
  const runtime = { ConfiaInkModel: Model };
  vm.runInNewContext(source, runtime);
  const page = Model.createDraft("ITA2025Q1").pages[0];
  for (const width of [323, 701, 965, 1121]) {
    const height = width * 4 / 3;
    for (const top of [700, -200]) {
      const target = { getBoundingClientRect: () => ({ left: 22, top, width, height }) };
      const point = runtime.ConfiaInkCanvas.eventPoint({
        clientX: 22 + width / 4, clientY: top + height / 2,
        timeStamp: 150, pointerType: "pen", pressure: 0.37,
      }, target, page, 100);
      assert.ok(Math.abs(point.x - 300) < 1e-9);
      assert.ok(Math.abs(point.y - 800) < 1e-9);
      assert.equal(point.t_ms, 50);
      assert.equal(point.pressure_reported, 0.37);
    }
  }
});
