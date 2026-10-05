const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const Model = require("../../app/confia_lean_auditor/static/capture/ink-model.js");

const source = fs.readFileSync(path.join(__dirname, "../../app/confia_lean_auditor/static/capture/ink-canvas.js"), "utf8");

function canvas(width = 1200) {
  const commands = [];
  const transforms = [];
  const context = {
    setTransform(...args) { transforms.push(args); }, clearRect() {}, fillRect() {}, beginPath() {},
    moveTo(...args) { commands.push(["moveTo", ...args]); },
    lineTo(...args) { commands.push(["lineTo", ...args]); },
    arc(...args) { commands.push(["arc", ...args]); },
    stroke() { commands.push(["stroke", this.lineWidth, this.strokeStyle]); },
    fill() { commands.push(["fill", this.fillStyle]); },
  };
  return {
    style: {}, commands, transforms,
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

test("landscape/portrait rotation keeps recovered ink, pointer alignment and PNG geometry", async () => {
  const pngCanvas = canvas();
  const runtime = { ConfiaInkModel: Model, devicePixelRatio: 2, document: { createElement: () => pngCanvas } };
  vm.runInNewContext(source, runtime);
  let draft = Model.createDraft("ITA2025Q1");
  const page = draft.pages[0];
  draft = Model.addStroke(draft, {stroke_id:"stroke:recovered",page_id:page.page_id,pointer_type:"pen",color:"#17355c",width:4,
    points:[{x:30,y:50,t_ms:0,pressure_reported:.3},{x:900,y:1500,t_ms:10,pressure_reported:.8}]});
  // Existing persisted documents have the same schema; CSS cannot rewrite them.
  const persisted = JSON.stringify(draft);
  draft = JSON.parse(persisted);
  const target = canvas();
  const expected = [["moveTo",30,50],["lineTo",900,1500],["stroke",3,"#17355c"]];
  // Canvas widths measured in the requested responsive layouts, then back to landscape.
  for (const width of [896,1152,632,278,896]) {
    for (const top of [283,-400]) {
      const rect = {left:42,top,width,height:width * 4 / 3};
      target.getBoundingClientRect = () => rect;
      target.commands.length = 0;
      runtime.ConfiaInkCanvas.render(target,draft,page.page_id,{grid:false});
      assert.deepEqual(target.commands,expected);
      assert.equal(target.width,Math.round(rect.width * 2));
      assert.equal(target.height,Math.round(rect.height * 2));
      assert.deepEqual(target.transforms.at(-1),[target.width/1200,0,0,target.height/1600,0,0]);
      for (const [x,y] of [[0,0],[30,50],[900,1500],[1200,1600]]) {
        const mapped = runtime.ConfiaInkCanvas.eventPoint({clientX:rect.left+x/1200*rect.width,clientY:rect.top+y/1600*rect.height,
          pointerType:"pen",pressure:.6,timeStamp:10},target,page,0);
        assert.ok(Math.abs(mapped.x-x)<1e-9);
        assert.ok(Math.abs(mapped.y-y)<1e-9);
      }
      assert.equal(JSON.stringify(draft),persisted);
    }
  }
  const png = await runtime.ConfiaInkCanvas.pngBlob(draft,page.page_id);
  assert.equal(png.type,"image/png");
  assert.equal(pngCanvas.width,1200);
  assert.equal(pngCanvas.height,1600);
  assert.deepEqual(pngCanvas.commands,expected);
  assert.equal(JSON.stringify(draft),persisted);
});
