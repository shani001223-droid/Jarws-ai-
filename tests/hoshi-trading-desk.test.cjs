"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const desk=require("../hoshi-trading-desk.js");
const fs=require("node:fs");
const {fixture,expected,NOW}=require("./trading-desk.fixtures.cjs");
function storage(){const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)};}
test("checked WAIT remains without fabricated levels or probability",()=>assert.equal(desk.validate(fixture(),expected,NOW).paper_plan,null));
test("forged identity, risk, confidence, score, times and WAIT levels reject",()=>{
  const mutations=[d=>d.orders_enabled=true,d=>d.win_probability=.92,d=>d.symbol="NAS100",d=>d.expires_at_ms=NOW,d=>d.as_of_ms=NOW+6000,d=>d.confluence.score=100,d=>d.confluence.evidence.htf_trend.points=20,d=>d.assumptions.risk_pct=20,d=>d.timeframes["15m"].support=1001,d=>d.timeframes["1h"].last_close=NaN,d=>d.confluence.last_closed_at["1h"]=0,d=>d.paper_plan={entry:1000}];
  for(const mutate of mutations){const d=fixture();mutate(d);assert.throws(()=>desk.validate(d,expected,NOW));}
});
test("invalid paper settings reject before a URL is built",()=>{for(const change of [{symbol:"SOLUSDT"},{risk_pct:2},{equity_usdt:0},{fee_bps:0},{slippage_bps:Infinity}])assert.throws(()=>desk.settings({...expected,...change}));});
test("local operator mode is loopback-only; public pages cannot redirect the API",()=>{
  assert.equal(desk.apiBase("http://127.0.0.1:8765/trading.html?backend=local"),"http://127.0.0.1:8000");
  assert.equal(desk.apiBase("https://jarws-ai-1.onrender.com/trading.html?backend=local"),"https://jarws-ai-2.onrender.com");
  assert.equal(desk.apiBase("http://127.0.0.1:8765/trading.html?backend=https://attacker.example"),"https://jarws-ai-2.onrender.com");
});
test("bounded response rejects dishonest sizes and cancels its reader",async()=>{
  let cancelled=false;
  const response={headers:new Headers(),body:{getReader:()=>({read:async()=>({done:false,value:new Uint8Array(160001)}),cancel:async()=>{cancelled=true;},releaseLock(){}})}};
  await assert.rejects(desk.boundedJson(response));assert.equal(cancelled,true);
});
test("valid bounded JSON uses its stream, malformed declared length rejects",async()=>{
  const payload=JSON.stringify({ok:true});assert.deepEqual(await desk.boundedJson(new Response(payload)),{ok:true});
  await assert.rejects(desk.boundedJson(new Response(payload,{headers:{"content-length":"bad"}})));
});
test("journal requires consent and a fresh snapshot; notes stay data",()=>{
  const s=storage(),d=fixture();assert.throws(()=>desk.saveJournal(s,d,"",false,NOW));assert.equal(s.getItem(desk.STORE),null);
  desk.saveJournal(s,d,"<script>not executable</script>",true,NOW);
  const records=desk.loadJournal(s);assert.equal(records.length,1);assert.equal(records[0].note,"<script>not executable</script>");assert.equal(records[0].orders_enabled,false);assert.equal(records[0].win_probability,null);
  assert.throws(()=>desk.saveJournal(s,d,"",true,NOW+60000));
});
test("journal malformed/oversized storage and full cap cannot silently discard history",()=>{
  const s=storage();s.setItem(desk.STORE,"bad-json");assert.throws(()=>desk.loadJournal(s));s.setItem(desk.STORE,JSON.stringify(Array(200).fill({paper_only:true})));assert.throws(()=>desk.saveJournal(s,fixture(),"",true,NOW));assert.equal(desk.loadJournal(s).length,200);
});
test("trading document cannot replace the cached main shell",()=>{
  const sw=fs.readFileSync(require("node:path").join(__dirname,"../sw.js"),"utf8");assert.match(sw,/if \(isMainDocument\) cache\.put\(shellURL/);
  const html=fs.readFileSync(require("node:path").join(__dirname,"../trading.html"),"utf8");assert.match(html,/Content-Security-Policy/);assert.doesNotMatch(html,/<script[^>]*>\s*[^<\s]/);
});
