"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const desk=require("../hoshi-trading-desk.js");
const fs=require("node:fs");
const {fixture,expected,NOW,makePaperPlan}=require("./trading-desk.fixtures.cjs");
function storage(){const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)};}
test("checked WAIT remains without fabricated levels or probability",()=>assert.equal(desk.validate(fixture(),expected,NOW).paper_plan,null));
test("forged identity, risk, confidence, score, times and WAIT levels reject",()=>{
  const mutations=[d=>d.orders_enabled=true,d=>d.win_probability=.92,d=>d.symbol="NAS100",d=>d.expires_at_ms=NOW,d=>d.as_of_ms=NOW+6000,d=>d.confluence.score=100,d=>d.confluence.evidence.htf_trend.points=20,d=>d.assumptions.risk_pct=20,d=>d.timeframes["15m"].support=1001,d=>d.timeframes["1h"].last_close=NaN,d=>d.confluence.last_closed_at["1h"]=0,d=>d.paper_plan={entry:1000}];
  for(const mutate of mutations){const d=fixture();mutate(d);assert.throws(()=>desk.validate(d,expected,NOW));}
});
test("paper plan independently reconciles stop, sizing, costs and targets",()=>{
  const d=fixture();d.decision="paper_plan_only";d.confluence.score=100;d.confluence.decision="paper_watchlist_only";
  for(const e of Object.values(d.confluence.evidence)){e.passed=true;e.points=20;}
  d.setup.positive_families=6;d.setup.decision="paper_watchlist_only";
  for(const e of Object.values(d.setup.evidence))e.status="supports_watchlist";
  d.paper_plan=makePaperPlan();
  assert.equal(desk.validate(d,expected,NOW).decision,"paper_plan_only");
  const mutations=[
    p=>p.reference_stop+=1,p=>p.confirmed_support=980,
    p=>p.estimated_entry_with_slippage+=1,p=>p.estimated_stop_fill_with_slippage+=1,
    p=>p.estimated_quantity_base*=1.5,p=>p.estimated_notional_usdt*=.8,
    p=>p.estimated_stop_loss_including_costs_usdt=.01,
    p=>p.targets[0].estimated_net_reward_risk=100,
    p=>p.targets[1].estimated_net_pnl_usdt+=5,
    p=>p.stop_distance_pct=1
  ];
  for(const mutate of mutations){const forged=structuredClone(d);mutate(forged.paper_plan);assert.throws(()=>desk.validate(forged,expected,NOW));}
});
test("mixed or one-interval-lagging closed frames fail client verification",()=>{
  for(const tf of ["15m","1h","4h"]){
    const d=fixture(),step={"15m":900000,"1h":3600000,"4h":14400000}[tf];
    d.timeframes[tf].last_closed_at-=step;
    d.confluence.last_closed_at[tf]-=step;
    d.setup.last_closed_at[tf]-=step;
    assert.throws(()=>desk.validate(d,expected,NOW));
  }
  const valid=fixture();valid.as_of_ms=NOW+1;valid.confluence.as_of=NOW+1;
  assert.equal(desk.validate(valid,expected,NOW+1).decision,"wait");
});
test("browser rejects impossible preclose provider timestamps even when snapshot is fresh",()=>{
  // A cached/preclose source cannot contain the newly closed 15m/1h/4h
  // candles. The server rejects it; the client must independently fail closed
  // if a stale intermediary or tampered response bypasses the API guard.
  for(const age of [1,30,119]){
    const d=fixture();d.fetched_at=NOW/1000-age;
    assert.throws(()=>desk.validate(d,expected,NOW));
  }
  const d=fixture();d.decision="paper_plan_only";d.fetched_at=NOW/1000-1;
  d.confluence.score=100;d.confluence.decision="paper_watchlist_only";
  for(const e of Object.values(d.confluence.evidence)){e.passed=true;e.points=20;}
  d.setup.positive_families=6;d.setup.decision="paper_watchlist_only";
  for(const e of Object.values(d.setup.evidence))e.status="supports_watchlist";
  d.paper_plan=makePaperPlan();
  assert.throws(()=>desk.validate(d,expected,NOW));
  const valid=fixture();valid.as_of_ms=NOW+1;valid.confluence.as_of=NOW+1;
  assert.equal(desk.validate(valid,expected,NOW+1).decision,"wait");
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
