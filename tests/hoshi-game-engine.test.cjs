const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { pathToFileURL } = require("node:url");
const { resolve } = require("node:path");
const root = resolve(__dirname, "..");
const manifest = JSON.parse(readFileSync(resolve(root, "game-studio/levels.json"), "utf8"));
const engine = import(pathToFileURL(resolve(root, "game-studio/engine.mjs")).href);

test("Task 50 template uses the six immutable design levels", async () => {
  const { validateManifest, ENGINE_VERSION } = await engine;
  const levels = validateManifest(manifest);
  assert.equal(ENGINE_VERSION, "canvas-preview-v1");
  assert.equal(levels.length, 6);
  assert.deepEqual(levels.map(x => x.minimum_moves), [8,8,8,16,16,12]);
  assert.ok(Object.isFrozen(levels[0].rows));
  assert.equal(manifest.status, "design_only_not_playable");
});

test("malformed or forged level manifests fail closed", async () => {
  const { validateManifest } = await engine;
  for (const mutate of [
    m => { m.version = "fake"; },
    m => { m.levels[0].rows[0] = "......."; },
    m => { m.levels[0].rows[1] = "#S.X.E#"; },
    m => { m.levels[0].rows[1] = "#SS..E#"; },
    m => { m.levels[0].minimum_moves = -1; },
    m => { m.levels[0].stars = 99; },
    m => { m.levels[1].id = 1; }
  ]) {
    const copy = structuredClone(manifest);
    mutate(copy);
    assert.throws(() => validateManifest(copy));
  }
});

test("real canvas drawing contract creates pixels without moving player", async () => {
  const { paintPreview, validateManifest } = await engine;
  const calls = [];
  const ctx = Object.fromEntries(["setTransform","fillRect","beginPath","arc","fill","moveTo","lineTo","closePath"].map(k=>[k,(...args)=>calls.push([k,...args])]));
  const canvas = { getContext: name => name === "2d" ? ctx : null };
  const result = paintPreview(canvas, validateManifest(manifest)[0], 3);
  assert.deepEqual(result, {width:700,height:700,playable:false});
  assert.ok(calls.filter(x=>x[0]==="fillRect").length >= 50);
  assert.ok(calls.some(x=>x[0]==="arc"));
  assert.ok(calls.some(x=>x[0]==="lineTo"));
  assert.throws(()=>paintPreview({getContext:()=>null},validateManifest(manifest)[0]));
});

test("Task 51 original geometric sprites reject untrusted art input", async () => {
  const { drawOriginalTile } = await import(pathToFileURL(resolve(root, "game-studio/art.mjs")).href);
  const calls = [];
  const ctx = Object.fromEntries(["fillRect","beginPath","arc","fill","moveTo","lineTo","closePath"]
    .map(k => [k, (...args) => calls.push([k, ...args])]));
  for (const tile of ["#", ".", "S", "C", "E"]) drawOriginalTile(ctx, tile, 0, 0, 50, 0.25);
  assert.ok(calls.filter(call => call[0] === "arc").length >= 6);
  assert.ok(calls.some(call => call[0] === "lineTo"));
  assert.throws(() => drawOriginalTile(ctx, "X", 0, 0, 50));
  assert.throws(() => drawOriginalTile(ctx, "C", 0, 0, 50, NaN));
  assert.throws(() => drawOriginalTile(ctx, "C", 0, 0, 50, -0.1));
  const { paintPreview, validateManifest } = await engine;
  assert.throws(() => paintPreview({getContext:()=>ctx}, validateManifest(manifest)[0], 1, Infinity));
});

test("Task 51 animation is opt-in, throttled and cancels queued frames", async () => {
  const { createPreviewAnimation } = await import(pathToFileURL(resolve(root, "game-studio/animation.mjs")).href);
  let allowed = false, next = 0;
  const pending = new Map(), phases = [];
  const controller = createPreviewAnimation({
    requestFrame: fn => { const id = ++next; pending.set(id, fn); return id; },
    cancelFrame: id => pending.delete(id),
    render: phase => phases.push(phase),
    shouldRun: () => allowed
  });
  assert.equal(controller.start(), false);
  allowed = true;
  assert.equal(controller.start(), true);
  assert.equal(controller.start(), false);
  const tick = timestamp => {
    const [id, fn] = pending.entries().next().value;
    pending.delete(id);
    fn(timestamp);
  };
  tick(0); tick(5); tick(50);
  assert.equal(phases.length, 2);
  assert.ok(phases.every(phase => phase >= 0 && phase < 1));
  allowed = false;
  tick(100);
  assert.equal(controller.running, false);
  assert.equal(pending.size, 0);
  allowed = true;
  controller.start();
  controller.stop();
  assert.equal(pending.size, 0);
});
