"use strict";
const assert=require("node:assert/strict");
const test=require("node:test");
const fs=require("node:fs");
const vm=require("node:vm");

const context={};
vm.runInNewContext(fs.readFileSync("hoshi-task-router.js","utf8"),context);
const classify=context.HoshiTaskRouter.classify;
const clean=result=>JSON.parse(JSON.stringify(result));

test("normal conversation and explanations never get silently executed",()=>{
 for(const prompt of ["Hoshi tum kaisi ho?", "How to create a game?", "BTC chart kaise analyse karte hain?", ""]){
   assert.equal(classify(prompt).mode,"chat",prompt);
 }
});
test("real ad intent remains a backend tool and no worker is faked",()=>{
 const r=clean(classify("Mere Flora products ke ads banao"));
 assert.equal(r.mode,"backend_tool");
 assert.equal(r.intent,"create_product_ads");
 assert.equal(r.ready,true);
});
test("game and anime projects recognized but not misreported as finished",()=>{
 for(const [prompt,intent] of [
   ["Mere liye ek puri game banaao","build_game"],
   ["Hindi Urdu anime 300 episodes 30 min each banaao","render_anime"]
 ]){
   const r=clean(classify(prompt));
   assert.equal(r.mode,"backend_project");
   assert.equal(r.intent,intent);
   assert.equal(r.ready,false);
   assert.match(r.reason,/nahi|available/i);
 }
});
test("chart and unrecognized device control require a verified agent",()=>{
 const chart=clean(classify("BTC chart analyse kro support resistance mark kro"));
 assert.equal(chart.mode,"screen_agent");
 assert.equal(chart.intent,"chart_analysis");
 assert.equal(chart.ready,false);
 const device=clean(classify("tap on my phone screen"));
 assert.equal(device.mode,"screen_agent");
 assert.equal(device.intent,"device_action");
 assert.equal(device.ready,false);
});
test("no raw user text or secret is included in routing result",()=>{
 const r=clean(classify("make a game with password sk-proj-supersecret"));
 assert.equal(r.intent,"build_game");
 assert.doesNotMatch(JSON.stringify(r),/sk-proj-supersecret/);
});
test("frontend loads classifier and checks unavailable route before cloud",()=>{
 const html=fs.readFileSync("index.html","utf8");
 assert.match(html,/<script src="\.\/hoshi-task-router\.js"><\/script>/);
 const dispatch=html.indexOf("window.HoshiTaskRouter.classify(text)");
 const ask=html.indexOf("askCloud(text,fastRequest)");
 assert.ok(dispatch>=0&&ask>dispatch);
 assert.match(html,/if\(routed&&!routed\.ready&&routed\.reason\)/);
});
