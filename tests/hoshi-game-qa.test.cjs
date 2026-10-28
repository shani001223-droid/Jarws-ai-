"use strict";
// Task 53: deterministic offline crash/transition QA; no live accounts or storage.
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const { pathToFileURL } = require("node:url");
const root = resolve(__dirname, "..");
const manifest = JSON.parse(readFileSync(resolve(root, "game-studio/levels.json"), "utf8"));
const load = name => import(pathToFileURL(resolve(root, "game-studio", name)).href);
const directions = ["up", "down", "left", "right"];

function solution(level, createGameState, moveGame) {
  const queue = [{state:createGameState(level), path:[]}], seen = new Set();
  for(let index=0;index<queue.length;index++) {
    const {state,path} = queue[index];
    const key = [state.x,state.y,state.collected].join(":");
    if(seen.has(key)) continue;
    seen.add(key);
    if(state.won) return {state,path,visited:seen.size};
    for(const direction of directions) {
      const next = moveGame(state,direction);
      if(next !== state) queue.push({state:next,path:[...path,direction]});
    }
    assert.ok(queue.length < 5000, "bounded graph traversal");
  }
  throw new Error("unsolvable_level_" + level.id);
}

test("Task 53: every level survives shortest solution, restart, undo and terminal replay", async () => {
  const {validateManifest} = await load("engine.mjs");
  const {createGameState,moveGame,undoGame,restartGame,unlockProgress,DEFAULT_PROGRESS} = await load("gameplay.mjs");
  const levels = validateManifest(manifest);
  let progress = DEFAULT_PROGRESS;
  for(const level of levels) {
    const {path,visited} = solution(level,createGameState,moveGame);
    assert.equal(path.length,level.minimum_moves, "minimum move count for level "+level.id);
    assert.ok(visited <= 49 * (1 << level.stars));
    let state = createGameState(level);
    for(const direction of path) {
      const previous = state;
      state = moveGame(state,direction);
      assert.notEqual(state,previous);
      const restored = undoGame(state);
      assert.deepEqual([restored.x,restored.y,restored.collected,restored.moves,restored.won],
        [previous.x,previous.y,previous.collected,previous.moves,previous.won]);
    }
    assert.equal(state.won,true);
    assert.equal(moveGame(state,"up"),state,"terminal win cannot move");
    progress = unlockProgress(progress,state);
    assert.equal(progress.highest_unlocked,Math.min(6,level.id+1));
    const reset = restartGame(state);
    assert.equal(reset.won,false);
    assert.equal(reset.moves,0);
    assert.equal(reset.undo,null);
  }
});

test("Task 53: 24,000 seeded random moves preserve immutable state, wall and undo invariants", async () => {
  const {validateManifest} = await load("engine.mjs");
  const {createGameState,moveGame,undoGame,restartGame} = await load("gameplay.mjs");
  const levels = validateManifest(manifest);
  let seed = 0x12345678;
  const nextRandom = () => {
    seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
    return seed >>> 0;
  };
  const started = Date.now();
  for(const level of levels) {
    let state = createGameState(level);
    for(let i=0;i<4000;i++) {
      if(state.won || i % 317 === 0) state = restartGame(state);
      const before = state;
      const after = moveGame(state,directions[nextRandom() % 4]);
      assert.ok(Object.isFrozen(after));
      assert.equal(after.level,level);
      assert.ok(after.x>=1 && after.x<=5 && after.y>=1 && after.y<=5);
      assert.notEqual(level.rows[after.y][after.x],"#");
      assert.ok(after.collected>=0 && after.collected < (1 << level.stars));
      assert.ok(after.moves>=0 && after.moves<=4000);
      if(after === before) {
        assert.equal(after.moves,before.moves);
      } else {
        assert.equal(after.moves,before.moves+1);
        const undo = undoGame(after);
        assert.deepEqual([undo.x,undo.y,undo.collected,undo.moves,undo.won],
          [before.x,before.y,before.collected,before.moves,before.won]);
        assert.equal(undo.undo,null);
      }
      state=after;
    }
  }
  const duration = Date.now()-started;
  // Generous runaway guard, not a claim about Android FPS or user latency.
  assert.ok(duration < 20000, "offline rules regression exceeded 20s: "+duration+"ms");
});

test("Task 53: malformed storage, frozen objects and invalid directions fail closed", async () => {
  const {validateManifest} = await load("engine.mjs");
  const {createGameState,moveGame,validateProgress,readSavedProgress,writeSavedProgress,clearSavedProgress,DEFAULT_PROGRESS,SAVE_KEY} = await load("gameplay.mjs");
  const state=createGameState(validateManifest(manifest)[0]);
  for(const invalid of ["constructor","toString","__proto__","UP","",null,42]) {
    assert.throws(()=>moveGame(state,invalid),/invalid_game_move/);
  }
  assert.throws(()=>{state.x=99;},TypeError);
  assert.throws(()=>{state.level.rows[0]=".......";},TypeError);
  for(const bad of [null,[],{}, {version:1,highest_unlocked:0,muted:true},
    {version:1,highest_unlocked:6,muted:true,secret:"x"}]) {
    assert.throws(()=>validateProgress(bad));
  }
  const storage={
    getItem:()=>"{invalid",setItem:()=>{throw new Error("quota");},
    removeItem:()=>{throw new Error("permission");}
  };
  assert.equal(readSavedProgress(storage),null);
  assert.equal(writeSavedProgress(storage,DEFAULT_PROGRESS),false);
  assert.equal(clearSavedProgress(storage),false);
  const entries=new Map([[SAVE_KEY,JSON.stringify(DEFAULT_PROGRESS)]]);
  const valid={getItem:key=>entries.get(key)??null,setItem:(key,value)=>entries.set(key,value),removeItem:key=>entries.delete(key)};
  assert.deepEqual(readSavedProgress(valid),DEFAULT_PROGRESS);
  assert.equal(clearSavedProgress(valid),true);
  assert.equal(entries.has(SAVE_KEY),false);
});
