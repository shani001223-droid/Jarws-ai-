"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {readFileSync} = require("node:fs");
const {resolve} = require("node:path");
const {pathToFileURL} = require("node:url");
const root = resolve(__dirname,"..");
const manifest = JSON.parse(readFileSync(resolve(root,"game-studio/levels.json"),"utf8"));
const engine = import(pathToFileURL(resolve(root,"game-studio/engine.mjs")).href);
const gameplay = import(pathToFileURL(resolve(root,"game-studio/gameplay.mjs")).href);
const dirs = ["up","down","left","right"];

test("Task 52 every playable level is solvable at its canonical shortest move count",async()=>{
  const {validateManifest} = await engine;
  const {createGameState,moveGame} = await gameplay;
  for(const level of validateManifest(manifest)){
    const start = createGameState(level),queue = [start],seen = new Set();
    let solution = null;
    for(let head=0;head<queue.length;head++){
      const state = queue[head],key=[state.x,state.y,state.collected].join(",");
      if(seen.has(key))continue;
      seen.add(key);
      if(state.won){solution=state;break;}
      for(const direction of dirs){
        const next=moveGame(state,direction);
        if(next!==state)queue.push(next);
      }
      assert.ok(queue.length<5000,"finite six-level state graph");
    }
    assert.ok(solution,"level "+level.id+" is playable");
    assert.equal(solution.moves,level.minimum_moves,"level "+level.id+" shortest path");
    assert.equal(solution.collected,(1<<level.stars)-1);
    assert.equal(moveGame(solution,"left"),solution,"won state is terminal");
  }
});

test("walls do not consume moves; premature exit cannot win; undo is one move",async()=>{
  const {validateManifest}=await engine;
  const {createGameState,moveGame,undoGame,restartGame}=await gameplay;
  const level=validateManifest(manifest)[0],start=createGameState(level);
  assert.equal(moveGame(start,"up"),start);
  assert.equal(moveGame(start,"left"),start);
  assert.throws(()=>moveGame(start,"__proto__"),/invalid_game_move/);
  let state=start;
  for(let i=0;i<4;i++)state=moveGame(state,"right");
  assert.equal(state.level.rows[state.y][state.x],"E");
  assert.equal(state.won,false,"exit before collection must not win");
  assert.equal(state.moves,4);
  const prior=undoGame(state);
  assert.equal(prior.moves,3);
  assert.equal(prior.x,4);
  assert.equal(prior.undo,null);
  assert.equal(undoGame(prior),prior,"only last move is undoable");
  assert.deepEqual([restartGame(state).x,restartGame(state).y],[start.x,start.y]);
  assert.equal(restartGame(state).moves,0);
});

test("collectible is restored by undo; local progress unlocks only after winning",async()=>{
  const {validateManifest}=await engine;
  const {createGameState,moveGame,undoGame,unlockProgress,DEFAULT_PROGRESS}=await gameplay;
  let state=createGameState(validateManifest(manifest)[0]);
  state=moveGame(moveGame(state,"down"),"down");
  state=moveGame(moveGame(state,"right"),"right");
  assert.equal(state.collected,1);
  assert.equal(undoGame(state).collected,0);
  state=moveGame(state,"right");
  assert.equal(unlockProgress(DEFAULT_PROGRESS,state).highest_unlocked,1);
  state=moveGame(moveGame(state,"up"),"up");
  state=moveGame(moveGame(state,"right"),"right");
  assert.equal(state.won,true);
  assert.equal(unlockProgress(DEFAULT_PROGRESS,state).highest_unlocked,2);
});

test("local save validates exact bounded schema and fails closed on corruption",async()=>{
  const {DEFAULT_PROGRESS,SAVE_KEY,validateProgress,readSavedProgress,writeSavedProgress,clearSavedProgress}=await gameplay;
  const entries=new Map();
  const storage={getItem:key=>entries.get(key)??null,setItem:(key,value)=>entries.set(key,value),removeItem:key=>entries.delete(key)};
  assert.equal(readSavedProgress(storage),null);
  assert.equal(writeSavedProgress(storage,DEFAULT_PROGRESS),true);
  assert.deepEqual(readSavedProgress(storage),DEFAULT_PROGRESS);
  assert.equal(clearSavedProgress(storage),true);
  assert.equal(readSavedProgress(storage),null);
  for(const bad of [{version:1,highest_unlocked:7,muted:true},
    {version:1,highest_unlocked:1,muted:false,token:"secret"},
    {version:1,highest_unlocked:1,muted:"false"},{version:2,highest_unlocked:1,muted:true}]){
    assert.throws(()=>validateProgress(bad));
    entries.set(SAVE_KEY,JSON.stringify(bad));
    assert.equal(readSavedProgress(storage),null);
  }
  entries.set(SAVE_KEY,"{broken");
  assert.equal(readSavedProgress(storage),null);
  entries.set(SAVE_KEY,"x".repeat(300));
  assert.equal(readSavedProgress(storage),null);
  const denied={getItem:()=>{throw Error("blocked");},setItem:()=>{throw Error("blocked");},removeItem:()=>{throw Error("blocked");}};
  assert.equal(readSavedProgress(denied),null);
  assert.equal(writeSavedProgress(denied,DEFAULT_PROGRESS),false);
  assert.equal(clearSavedProgress(denied),false);
});
