// Task 51: original procedural vector sprites. No downloaded or third-party assets.
const TAU = Math.PI * 2;

function disk(ctx, x, y, radius, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, TAU);
  ctx.fill();
}

function star(ctx, x, y, radius, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  for (let point = 0; point < 10; point++) {
    const angle = -Math.PI / 2 + point * Math.PI / 5;
    const r = point % 2 ? radius * 0.46 : radius;
    if (point === 0) ctx.moveTo(x + Math.cos(angle) * r, y + Math.sin(angle) * r);
    else ctx.lineTo(x + Math.cos(angle) * r, y + Math.sin(angle) * r);
  }
  ctx.closePath();
  ctx.fill();
}

export function drawOriginalTile(ctx, tile, px, py, cell, phase = 0) {
  if (!ctx || !Number.isFinite(px) || !Number.isFinite(py) ||
      !Number.isFinite(cell) || cell <= 0 || !Number.isFinite(phase) ||
      phase < 0 || phase > 1 || !["#", ".", "S", "C", "E"].includes(tile)) {
    throw new Error("invalid_original_art_input");
  }
  const cx = px + cell / 2, cy = py + cell / 2;
  const wave = Math.sin(TAU * phase);
  if (tile === "#") {
    ctx.fillStyle = "#2c4766";
    ctx.fillRect(px + 4, py + 4, cell - 8, 2);
  } else if (tile === ".") {
    disk(ctx, cx, cy, cell * 0.026, "#355777");
  } else if (tile === "S") {
    disk(ctx, cx, cy, cell * (0.30 + 0.025 * wave), "#204e70");
    disk(ctx, cx, cy, cell * 0.21, "#75e4ff");
    star(ctx, cx, cy, cell * 0.13, "#f0fdff");
  } else if (tile === "C") {
    disk(ctx, cx, cy, cell * (0.31 + 0.03 * wave), "#574d31");
    star(ctx, cx, cy, cell * (0.24 + 0.025 * wave), "#ffdc84");
    disk(ctx, cx, cy, cell * 0.045, "#fff9df");
  } else if (tile === "E") {
    disk(ctx, cx, cy, cell * (0.30 + 0.025 * wave), "#23564e");
    disk(ctx, cx, cy, cell * 0.21, "#92f5d0");
    disk(ctx, cx, cy, cell * 0.12, "#0e342f");
    star(ctx, cx, cy, cell * 0.065, "#e8fff4");
  }
}
