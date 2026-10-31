"use strict";
// Real Chromium UI + synthetic market fixtures. No exchange/model calls.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),http=require("node:http");
const {chromium}=require("playwright");
const {fixture}=require("./trading-desk.fixtures.cjs");
const ROOT=path.resolve(__dirname,"..");
function body(mode){
  const d=fixture(),now=Date.now();d.as_of_ms=now;d.fetched_at=Math.floor(now/1000);d.expires_at_ms=now+60000;d.confluence.as_of=now;
  for(const tf of Object.keys(d.timeframes)){d.timeframes[tf].last_closed_at=now-1000;d.confluence.last_closed_at[tf]=now-1000;d.setup.last_closed_at[tf]=now-1000;}
  if(["plan","expiry"].includes(mode)){
    d.decision="paper_plan_only";d.confluence.score=100;d.confluence.decision="paper_watchlist_only";
    for(const e of Object.values(d.confluence.evidence)){e.passed=true;e.points=20;}
    d.setup.positive_families=6;d.setup.decision="paper_watchlist_only";for(const e of Object.values(d.setup.evidence))e.status="supports_watchlist";
    d.paper_plan={side:"long",fills_simulated:false,exchange_order_validated:false,reference_entry_close:1000,estimated_entry_with_slippage:1000.5,reference_stop:990,estimated_quantity_base:.02,estimated_notional_usdt:20.01,risk_budget_usdt:.5,estimated_stop_loss_including_costs_usdt:.3,equity_usdt:100,risk_pct:.5,assumed_fee_bps_each_side:10,assumed_adverse_slippage_bps_each_side:5,targets:[{multiple_before_costs:1,reference_price:1010,estimated_net_pnl_usdt:.15,estimated_net_reward_risk:.5},{multiple_before_costs:2,reference_price:1020,estimated_net_pnl_usdt:.45,estimated_net_reward_risk:1.5}]};
  }
  if(mode==="expiry")d.expires_at_ms=now+700;
  if(mode==="forged")d.win_probability=.92;
  if(mode==="stale")d.expires_at_ms=now-1;
  return d;
}
async function run(){
  const server=http.createServer((req,res)=>{
    const name=new URL(req.url,"http://localhost").pathname,file=path.resolve(ROOT,"."+decodeURIComponent(name==="/"?"/index.html":name));
    if(!file.startsWith(ROOT+path.sep)){res.writeHead(403).end();return;}
    fs.readFile(file,(error,b)=>{if(error){res.writeHead(404).end();return;}const ext=path.extname(file);res.writeHead(200,{"Content-Type":({".html":"text/html",".js":"application/javascript",".mjs":"application/javascript",".css":"text/css",".json":"application/json",".svg":"image/svg+xml",".webp":"image/webp"})[ext]||"application/octet-stream","Cache-Control":"no-store"});res.end(b);});
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  let browser;
  try{
    browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,acceptDownloads:true});
    let mode="wait",requests=0,release=null;const errors=[],requestPaths=[];
    await context.route("**/*",async route=>{
      const target=new URL(route.request().url());requestPaths.push(target.origin+target.pathname);
      if(["127.0.0.1","localhost"].includes(target.hostname)){await route.continue();return;}
      if(target.origin!=="https://jarws-ai-2.onrender.com"||target.pathname!=="/api/trading/desk"){await route.abort();return;}
      requests++;assert.equal(route.request().method(),"GET");const selected=mode;
      if(selected==="delayed")await new Promise(resolve=>{release=resolve;});
      try{await route.fulfill({status:selected==="error"?503:200,headers:{"Access-Control-Allow-Origin":"*","Content-Type":"application/json"},body:JSON.stringify(body(selected))});}catch(_){}
    });
    const page=await context.newPage();page.on("pageerror",e=>errors.push(e.message));
    const browserMessages=[];page.on("console",m=>{if(m.type()==="error")browserMessages.push(m.text().slice(0,240));});
    const base="http://127.0.0.1:"+server.address().port;
    await page.goto(base+"/trading.html");assert.equal(requests,0);
    assert.equal(await page.locator("#decision").textContent(),"WAIT");assert.equal(await page.locator("#save").isDisabled(),true);
    await page.locator("#analyze").click();await page.waitForFunction(()=>!document.querySelector("#analyze").disabled);
    const initialState=await page.evaluate(({data})=>{let validation;try{HoshiTradingDesk.validate(data,{symbol:"BTCUSDT",equity_usdt:100,risk_pct:.5,fee_bps:10,slippage_bps:5});validation="passed";}catch(e){validation=e.message;}return {status:document.querySelector("#status").textContent,validation};},{data:body("wait")});
    assert.equal(await page.locator("#snapshot").isVisible(),true,JSON.stringify({initialState,requests,requestPaths,errors,browserMessages}));assert.equal(await page.locator("#decision").textContent(),"WAIT");assert.equal(await page.locator("#plan").isVisible(),false);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    mode="plan";await page.locator("#analyze").click();await page.waitForFunction(()=>document.querySelector("#decision").textContent==="PAPER PLAN");
    assert.equal(await page.locator("#plan").isVisible(),true);assert.equal(await page.locator("#save").isDisabled(),true);
    await page.locator("#journalConsent").check();await page.locator("#journalNote").fill("<img src=x onerror=alert(1)> is only a note");await page.locator("#save").click();
    const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem("hoshiTradingJournalV1")));assert.equal(stored.length,1);assert.equal(stored[0].orders_enabled,false);assert.equal(stored[0].win_probability,null);
    const download=page.waitForEvent("download");await page.locator("#export").click();const stream=await(await download).createReadStream();let exported="";for await(const part of stream)exported+=part;assert.equal(JSON.parse(exported).entries.length,1);
    await page.locator("#delete").click();assert.equal(await page.evaluate(()=>localStorage.getItem("hoshiTradingJournalV1")),null);
    for(const bad of ["forged","stale","error"]){mode=bad;await page.locator("#analyze").click();await page.waitForFunction(()=>document.querySelector("#status").textContent.includes("Data verify"));assert.equal(await page.locator("#plan").isVisible(),false);assert.equal(await page.locator("#decision").textContent(),"WAIT");}
    mode="delayed";await page.locator("#analyze").click();{const until=Date.now()+6000;while(!release&&Date.now()<until)await new Promise(r=>setTimeout(r,10));assert.ok(release,JSON.stringify({requests,requestPaths,status:await page.locator("#status").textContent()}));}await page.locator("#stop").click();release();await page.waitForTimeout(100);assert.equal(await page.locator("#snapshot").isVisible(),false);
    release=null;await page.locator("#analyze").click();{const until=Date.now()+6000;while(!release&&Date.now()<until)await new Promise(r=>setTimeout(r,10));assert.ok(release,JSON.stringify({requests,requestPaths,status:await page.locator("#status").textContent()}));}await page.locator("#symbol").selectOption("ETHUSDT");release();await page.waitForTimeout(100);assert.equal(await page.locator("#snapshot").isVisible(),false);await page.locator("#symbol").selectOption("BTCUSDT");
    mode="expiry";await page.locator("#analyze").click();await page.waitForFunction(()=>document.querySelector("#decision").textContent==="PAPER PLAN");await page.waitForFunction(()=>document.querySelector("#status").textContent.includes("expire"));assert.equal(await page.locator("#levels").textContent(),"");
    // Use the REAL service worker: a trading navigation must not poison index.
    await page.evaluate(async()=>{await navigator.serviceWorker.register("/sw.js");await navigator.serviceWorker.ready;});
    await page.reload();await page.evaluate(()=>fetch("/index.html",{cache:"reload"}));await page.reload();
    const mainSource=fs.readFileSync(path.join(ROOT,"index.html"),"utf8");
    await page.waitForFunction(async expected=>{const cache=await caches.open("hoshi-shell-v37"),r=await cache.match(new URL("/index.html",location.origin).href);return r&&await r.text()===expected;},mainSource);
    await page.waitForTimeout(200);
    assert.equal(await page.evaluate(async()=>{const r=await(await caches.open("hoshi-shell-v37")).match(new URL("/index.html",location.origin).href);return r.text();}),mainSource);
    await context.setOffline(true);await context.unroute("**/*");await page.reload();await page.waitForFunction(()=>!!window.HoshiTradingDesk&&!document.querySelector("#analyze").disabled);await page.locator("#analyze").click();await page.waitForFunction(()=>document.querySelector("#status").textContent.includes("Data verify"));assert.equal(await page.locator("#plan").isVisible(),false);
    assert.deepEqual(errors,[]);console.log("Trading desk Chromium mobile: WAIT/plan, tampering, Stop/races, expiry, consent/export/delete and real SW offline checks passed.");
  }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
