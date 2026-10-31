// Task 51: bounded, explicitly opted-in preview animation; no gameplay or timers.
export function createPreviewAnimation({ requestFrame, cancelFrame, render, shouldRun }) {
  if (![requestFrame, cancelFrame, render, shouldRun].every(fn => typeof fn === "function")) {
    throw new Error("invalid_animation_dependencies");
  }
  let active = false;
  let frameId = null;
  let last = -Infinity;
  const tick = timestamp => {
    frameId = null;
    if (!active) return;
    if (!shouldRun()) { stop(); return; }
    if (Number.isFinite(timestamp) && timestamp - last >= 1000 / 24) {
      last = timestamp;
      render(((timestamp % 2400) + 2400) % 2400 / 2400);
    }
    frameId = requestFrame(tick);
  };
  function start() {
    if (active || !shouldRun()) return false;
    active = true;
    last = -Infinity;
    frameId = requestFrame(tick);
    return true;
  }
  function stop() {
    active = false;
    if (frameId !== null) cancelFrame(frameId);
    frameId = null;
    last = -Infinity;
  }
  return Object.freeze({ start, stop, get running() { return active; } });
}
