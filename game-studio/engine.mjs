// Task 50: free, dependency-free HTML5 Canvas preview engine. NOT playable.
export const ENGINE_VERSION = "canvas-preview-v1";
const SIZE = 7;
const TILES = new Set(["#", ".", "S", "C", "E"]);

export function validateManifest(manifest) {
  if (!manifest || manifest.version !== "gdd-v1" || !Array.isArray(manifest.levels) ||
      manifest.levels.length !== 6 || manifest.status !== "design_only_not_playable") {
    throw new Error("invalid_game_manifest");
  }
  return manifest.levels.map((level, index) => {
    if (!level || level.id !== index + 1 || !Array.isArray(level.rows) ||
        level.rows.length !== SIZE || !Number.isInteger(level.minimum_moves) ||
        level.minimum_moves < 1 || level.minimum_moves > 30) {
      throw new Error("invalid_level_metadata");
    }
    let starts = 0, exits = 0, stars = 0;
    const rows = level.rows.map((row, y) => {
      if (typeof row !== "string" || row.length !== SIZE) throw new Error("invalid_level_dimensions");
      for (let x = 0; x < SIZE; x++) {
        const tile = row[x];
        if (!TILES.has(tile)) throw new Error("invalid_level_tile");
        if ((x === 0 || x === SIZE - 1 || y === 0 || y === SIZE - 1) && tile !== "#") {
          throw new Error("open_level_boundary");
        }
        starts += Number(tile === "S");
        exits += Number(tile === "E");
        stars += Number(tile === "C");
      }
      return row;
    });
    if (starts !== 1 || exits !== 1 || stars < 1 || stars > 3 || stars !== level.stars) {
      throw new Error("invalid_level_entities");
    }
    return Object.freeze({ id: level.id, rows: Object.freeze(rows), stars,
      minimum_moves: level.minimum_moves });
  });
}

function star(ctx, cx, cy, radius) {
  ctx.beginPath();
  for (let point = 0; point < 10; point++) {
    const angle = -Math.PI / 2 + point * Math.PI / 5;
    const r = point % 2 ? radius * 0.46 : radius;
    const x = cx + Math.cos(angle) * r, y = cy + Math.sin(angle) * r;
    if (point === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fill();
}

export function paintPreview(canvas, level, deviceScale = 1) {
  if (!canvas || typeof canvas.getContext !== "function" || !level ||
      !Array.isArray(level.rows) || level.rows.length !== SIZE) {
    throw new Error("invalid_preview_target");
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("canvas_unavailable");
  const scale = Number.isFinite(deviceScale) ? Math.min(2, Math.max(1, deviceScale)) : 1;
  const width = 350;
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(width * scale);
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  ctx.fillStyle = "#060d1d";
  ctx.fillRect(0, 0, width, width);
  const cell = width / SIZE;
  level.rows.forEach((row, y) => {
    for (let x = 0; x < SIZE; x++) {
      const tile = row[x], px = x * cell, py = y * cell;
      ctx.fillStyle = tile === "#" ? "#203450" : "#101f35";
      ctx.fillRect(px + 1, py + 1, cell - 2, cell - 2);
      if (tile === "S" || tile === "E") {
        ctx.fillStyle = tile === "S" ? "#73dcff" : "#b2f5d4";
        ctx.beginPath();
        ctx.arc(px + cell / 2, py + cell / 2, cell * 0.24, 0, Math.PI * 2);
        ctx.fill();
      } else if (tile === "C") {
        ctx.fillStyle = "#ffe7a0";
        star(ctx, px + cell / 2, py + cell / 2, cell * 0.27);
      }
    }
  });
  return { width: canvas.width, height: canvas.height, playable: false };
}
