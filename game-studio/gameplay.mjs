// Task 52: deterministic, offline-only Hoshi Star Trail rules and opt-in progress.
// No timers, network, audio, account access or automatic persistence.
export const SAVE_KEY = "hoshi-star-trail-progress-v1";
export const DEFAULT_PROGRESS = Object.freeze({ version: 1, highest_unlocked: 1, muted: true });
const DIRECTIONS = Object.freeze({ up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] });

function immutableState(fields) {
  if (fields.undo) Object.freeze(fields.undo);
  return Object.freeze(fields);
}

export function createGameState(level) {
  if (!level || !Number.isInteger(level.id) || level.id < 1 || level.id > 6 ||
      !Array.isArray(level.rows) || level.rows.length !== 7 ||
      !Number.isInteger(level.stars) || level.stars < 1 || level.stars > 3) {
    throw new Error("invalid_game_level");
  }
  const stars = [];
  let start = null, exits = 0;
  for (let y = 0; y < 7; y++) {
    const row = level.rows[y];
    if (typeof row !== "string" || row.length !== 7) throw new Error("invalid_game_rows");
    for (let x = 0; x < 7; x++) {
      const tile = row[x];
      if (!"#.SCE".includes(tile)) throw new Error("invalid_game_tile");
      if (tile === "S") {
        if (start) throw new Error("invalid_game_start");
        start = { x, y };
      }
      if (tile === "E") exits++;
      if (tile === "C") stars.push(y * 7 + x);
    }
  }
  if (!start || exits !== 1 || stars.length !== level.stars) throw new Error("invalid_game_entities");
  return immutableState({ level, x: start.x, y: start.y, collected: 0,
    moves: 0, won: false, undo: null });
}

export function moveGame(state, direction) {
  if (!state || !Object.hasOwn(DIRECTIONS, direction)) throw new Error("invalid_game_move");
  if (state.won) return state;
  const [dx, dy] = DIRECTIONS[direction];
  const x = state.x + dx, y = state.y + dy;
  if (x < 0 || x > 6 || y < 0 || y > 6 || state.level.rows[y][x] === "#") return state;
  let collected = state.collected;
  let starIndex = 0;
  for (let sy = 0; sy < 7; sy++) {
    for (let sx = 0; sx < 7; sx++) {
      if (state.level.rows[sy][sx] === "C") {
        if (sx === x && sy === y) collected |= 1 << starIndex;
        starIndex++;
      }
    }
  }
  const won = state.level.rows[y][x] === "E" && collected === (1 << state.level.stars) - 1;
  return immutableState({ level: state.level, x, y, collected,
    moves: state.moves + 1, won,
    undo: { x: state.x, y: state.y, collected: state.collected, moves: state.moves, won: state.won } });
}

export function undoGame(state) {
  if (!state || !state.level) throw new Error("invalid_game_state");
  if (!state.undo) return state;
  return immutableState({ level: state.level, ...state.undo, undo: null });
}

export function restartGame(state) {
  if (!state || !state.level) throw new Error("invalid_game_state");
  return createGameState(state.level);
}

export function validateProgress(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).sort().join(",") !== "highest_unlocked,muted,version" ||
      value.version !== 1 || !Number.isInteger(value.highest_unlocked) ||
      value.highest_unlocked < 1 || value.highest_unlocked > 6 ||
      typeof value.muted !== "boolean") throw new Error("invalid_game_progress");
  return Object.freeze({ version: 1, highest_unlocked: value.highest_unlocked, muted: value.muted });
}

export function unlockProgress(progress, state) {
  const valid = validateProgress(progress);
  if (!state || !state.won || !state.level || !Number.isInteger(state.level.id)) return valid;
  return validateProgress({ ...valid, highest_unlocked: Math.max(valid.highest_unlocked, Math.min(6, state.level.id + 1)) });
}

export function readSavedProgress(storage) {
  try {
    const raw = storage.getItem(SAVE_KEY);
    if (typeof raw !== "string" || raw.length > 256) return null;
    return validateProgress(JSON.parse(raw));
  } catch { return null; }
}

export function writeSavedProgress(storage, progress) {
  const valid = validateProgress(progress);
  try { storage.setItem(SAVE_KEY, JSON.stringify(valid)); return true; }
  catch { return false; }
}

export function clearSavedProgress(storage) {
  try { storage.removeItem(SAVE_KEY); return true; }
  catch { return false; }
}
