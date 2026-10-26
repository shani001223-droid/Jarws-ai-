"use strict";
const test=require("node:test"), assert=require("node:assert/strict"), fs=require("node:fs");
const vm=require("node:vm"), path=require("node:path");
const host={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,"..","hoshi-room.js"),"utf8"),{window:host,globalThis:host});
const life=host.HoshiRoomLife;
test("room-life exposes safe known scene states",()=>{
  assert.deepEqual(Array.from(life.ACTIVITIES),["idle","gaming","reels","dance","sleep"]);
  assert.equal(life.validateActivity("dance"),"dance");
  assert.equal(life.validateActivity("__proto__"),"idle");
  assert.equal(life.validateEmotion("shy"),"shy");
  assert.equal(life.validateEmotion("access-password"),"neutral");
});
test("Roman Urdu and English voice commands select scene without cloud trade actions",()=>{
  for(const [input,expected] of [
    ["game khelo","gaming"],["Hoshi gaming karo","gaming"],
    ["mobile chalao","reels"],["reels dekho","reels"],
    ["dance karo","dance"],["music chalao","dance"],["stop music","idle"],
    ["so jao","sleep"],["normal ho jao","idle"]
  ])assert.equal(life.parseActivityCommand(input),expected,input);
  for(const command of ["take screenshot","open Binance","send message","show passwords","buy BTC","analyze chart"])
    assert.equal(life.parseActivityCommand(command),null,command);
});
test("approved expression sprite and no surveillance endpoints",()=>{
  const script=fs.readFileSync(path.join(__dirname,"..","hoshi-room.js"),"utf8");
  const css=fs.readFileSync(path.join(__dirname,"..","hoshi-room.css"),"utf8");
  assert.ok(css.includes("assets/hoshi-expressions.webp"));
  assert.ok(!/navigator\.mediaDevices|getDisplayMedia|MediaProjection|captureScreen|screenCapture|canvas\.toDataURL/.test(script));
  assert.ok(css.includes("prefers-reduced-motion"));
  assert.ok(script.includes('localStorage.getItem("hoshiRoomSuggestions")==="true"'));
});
