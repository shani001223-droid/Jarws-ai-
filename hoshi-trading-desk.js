(function (root) {
  "use strict";
  const VERSION = "hoshi-trading-desk-v1", STORE = "hoshiTradingJournalV1";
  const FRAMES = ["15m", "1h", "4h"], STEPS = {"15m":900000,"1h":3600000,"4h":14400000};
  const CHECKS = {htf_trend:"HTF trend",liquidity_target:"Liquidity reference + reclaim",location_order_block:"Discount + order-block overlap",fvg_retest:"FVG retest",killzone_time:"New York time window"};
  const FAMILIES = ["confirmed_structure","ema_trend","rsi_momentum","volume_participation","session_vwap","atr_volatility_guard"];
  const finite = n => typeof n === "number" && Number.isFinite(n);
  const positive = n => finite(n) && n > 0;
  const stamp = n => Number.isSafeInteger(n) && n >= 0;
  const sameKeys = (obj, keys) => obj && typeof obj === "object" && !Array.isArray(obj) && Object.keys(obj).length === keys.length && keys.every(k => Object.hasOwn(obj,k));
  const close = (a,b) => finite(a) && finite(b) && Math.abs(a-b) <= Math.max(1,Math.abs(a),Math.abs(b))*1e-8;
  function settings(values) {
    const out = {symbol:values.symbol,equity_usdt:Number(values.equity_usdt),risk_pct:Number(values.risk_pct),fee_bps:Number(values.fee_bps),slippage_bps:Number(values.slippage_bps)};
    if (!["BTCUSDT","ETHUSDT"].includes(out.symbol) || !finite(out.equity_usdt) || out.equity_usdt<10 || out.equity_usdt>100000 || !finite(out.risk_pct) || out.risk_pct<.1 || out.risk_pct>1 || !finite(out.fee_bps) || out.fee_bps<1 || out.fee_bps>100 || !finite(out.slippage_bps) || out.slippage_bps<1 || out.slippage_bps>100) throw new Error("Invalid paper settings");
    return out;
  }
  function apiBase(href) {
    const u=new URL(href);
    return u.protocol==="http:" && ["127.0.0.1","localhost"].includes(u.hostname) && u.searchParams.get("backend")==="local"
      ? "http://"+u.hostname+":8000" : "https://jarws-ai-2.onrender.com";
  }
  function validate(data, expected, now=Date.now()) {
    const fail = () => { throw new Error("Unverified or expired trading response"); };
    if (!data || data.version!==VERSION || data.symbol!==expected.symbol || data.market!=="spot" || data.mode!=="paper-assistant-only" || data.orders_enabled!==false || data.win_probability!==null || data.independently_cross_checked!==false || data.direction!=="long_study_only" || data.price_kind!=="last_closed_candle_not_live_quote" || data.knowledge_version!=="hoshi-trading-knowledge-v2" || data.v3_runtime_integration!=="pending") fail();
    if (!stamp(data.as_of_ms) || data.as_of_ms>now+5000 || data.as_of_ms<now-120000 || !stamp(data.fetched_at) || data.fetched_at*1000>data.as_of_ms+5000 || data.fetched_at*1000<data.as_of_ms-120000 || !stamp(data.expires_at_ms) || data.expires_at_ms<=now || data.expires_at_ms>data.as_of_ms+60000 || data.expires_at_ms>data.fetched_at*1000+120000) fail();
    const a=data.assumptions;
    if (!a || a.equity_usdt!==expected.equity_usdt || a.risk_pct!==expected.risk_pct || a.fee_bps_each_side!==expected.fee_bps || a.adverse_slippage_bps_each_side!==expected.slippage_bps || !sameKeys(data.timeframes,FRAMES)) fail();
    for (const tf of FRAMES) {
      const f=data.timeframes[tf];
      if (!f || !stamp(f.last_closed_at) || f.last_closed_at>=data.as_of_ms || data.as_of_ms-f.last_closed_at>STEPS[tf]+120000 || !positive(f.last_close) || !finite(f.rsi14) || f.rsi14<0 || f.rsi14>100 || !positive(f.ema20) || !positive(f.ema50) || !finite(f.atr14) || f.atr14<0 || (f.support!==null && (!positive(f.support)||f.support>f.last_close)) || (f.resistance!==null && (!positive(f.resistance)||f.resistance<f.last_close))) fail();
    }
    const c=data.confluence,s=data.setup;
    if (!c || c.version!=="hoshi-confluence-v2" || c.symbol!==data.symbol || c.market!=="spot" || c.orders_enabled!==false || c.win_probability!==null || c.direction!=="long" || c.as_of!==data.as_of_ms || c.score_semantics!=="weighted_rule_coverage_not_win_probability" || !sameKeys(c.evidence,Object.keys(CHECKS)) || !Number.isInteger(c.score) || c.score<0 || c.score>100 || c.score_max!==100) fail();
    let points=0;
    for (const key of Object.keys(CHECKS)) {const e=c.evidence[key];if (!e || typeof e.passed!=="boolean" || e.weight!==20 || e.points!==(e.passed?20:0)) fail();points+=e.points;}
    if (points!==c.score || c.decision!==(c.score===100?"paper_watchlist_only":"wait") || !s || s.version!=="spot-setup-assessment-v1" || s.symbol!==data.symbol || s.orders_enabled!==false || s.families_checked!==6 || !sameKeys(s.evidence,FAMILIES) || !Number.isInteger(s.positive_families)) fail();
    let count=0;
    for (const key of FAMILIES) {const e=s.evidence[key];if (!e || !["supports_watchlist","does_not_support"].includes(e.status)) fail();if(e.status==="supports_watchlist")count++;}
    if (count!==s.positive_families || s.decision!==(count===6?"paper_watchlist_only":"wait")) fail();
    for (const tf of FRAMES) if (!c.last_closed_at || !s.last_closed_at || c.last_closed_at[tf]!==data.timeframes[tf].last_closed_at || s.last_closed_at[tf]!==data.timeframes[tf].last_closed_at) fail();
    if (data.decision==="wait") {if (data.paper_plan!==null) fail();}
    else if (data.decision==="paper_plan_only") {
      const p=data.paper_plan;
      if (c.score!==100 || count!==6 || !p || p.side!=="long" || p.fills_simulated!==false || p.exchange_order_validated!==false || !close(p.reference_entry_close,data.timeframes["15m"].last_close) || !positive(p.reference_stop) || p.reference_stop>=p.reference_entry_close || !positive(p.estimated_entry_with_slippage) || !positive(p.estimated_quantity_base) || !positive(p.estimated_notional_usdt) || !positive(p.risk_budget_usdt) || !positive(p.estimated_stop_loss_including_costs_usdt) || p.equity_usdt!==expected.equity_usdt || p.risk_pct!==expected.risk_pct || p.assumed_fee_bps_each_side!==expected.fee_bps || p.assumed_adverse_slippage_bps_each_side!==expected.slippage_bps || !close(p.risk_budget_usdt,expected.equity_usdt*expected.risk_pct/100) || p.estimated_stop_loss_including_costs_usdt>p.risk_budget_usdt+1e-8 || p.estimated_notional_usdt>expected.equity_usdt+1e-8 || !Array.isArray(p.targets) || p.targets.length!==2) fail();
      for (let n=0;n<2;n++) {const t=p.targets[n];if (!t || t.multiple_before_costs!==n+1 || !close(t.reference_price,p.reference_entry_close+(n+1)*(p.reference_entry_close-p.reference_stop)) || !finite(t.estimated_net_pnl_usdt) || !finite(t.estimated_net_reward_risk)) fail();}
      if(p.targets[1].estimated_net_reward_risk<1)fail();
    } else fail();
    return data;
  }
  async function boundedJson(response) {
    const limit=160000, declared=response.headers.get("content-length");
    if (declared!==null && (!/^\d+$/.test(declared) || Number(declared)>limit)) throw new Error("Oversized response");
    if (response.body && response.body.getReader) {
      const reader=response.body.getReader();let size=0,text="";const decoder=new TextDecoder("utf-8",{fatal:true});
      try {for(;;){const part=await reader.read();if(part.done)break;size+=part.value.byteLength;if(size>limit)throw new Error("Oversized response");text+=decoder.decode(part.value,{stream:true});}text+=decoder.decode();return JSON.parse(text);}
      catch(error){try{await reader.cancel();}catch(_){}throw error;}
      finally{reader.releaseLock();}
    }
    const text=await response.text();if(new TextEncoder().encode(text).byteLength>limit)throw new Error("Oversized response");return JSON.parse(text);
  }
  function loadJournal(storage) {
    const raw=storage.getItem(STORE);if(raw===null)return [];
    if(raw.length>500000)throw new Error("Journal too large");
    const entries=JSON.parse(raw);if(!Array.isArray(entries)||entries.length>200)throw new Error("Invalid journal");
    return entries;
  }
  function saveJournal(storage,data,note,consent,now=Date.now()) {
    if(consent!==true)throw new Error("Saving permission required");
    if(!data || data.expires_at_ms<=now)throw new Error("Fresh snapshot required");
    const entries=loadJournal(storage);
    if(entries.length>=200)throw new Error("Journal full: export/delete first");
    if(typeof note!=="string"||note.length>500)throw new Error("Note too long");
    entries.push({saved_at:new Date(now).toISOString(),symbol:data.symbol,decision:data.decision,source:data.source,as_of_ms:data.as_of_ms,last_closed_at:Object.fromEntries(FRAMES.map(tf=>[tf,data.timeframes[tf].last_closed_at])),rule_coverage:data.confluence.score,win_probability:null,paper_only:true,orders_enabled:false,paper_plan:data.paper_plan,note});
    storage.setItem(STORE,JSON.stringify(entries));return entries.length;
  }
  const api={settings,apiBase,validate,boundedJson,loadJournal,saveJournal,STORE};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  root.HoshiTradingDesk=api;
  if(!root.document)return;
  const $=id=>document.getElementById(id);
  const API=apiBase(root.location.href);
  let sequence=0,controller=null,current=null,expiry=null;
  const fmt=n=>finite(n)?n.toLocaleString("en-US",{maximumFractionDigits:5}):"—";
  const date=n=>new Date(n).toLocaleString("en-GB",{timeZone:"Asia/Karachi",hour12:false})+" PKT";
  function clear(message) {current=null;clearTimeout(expiry);$("snapshot").hidden=true;$("plan").hidden=true;$("levels").replaceChildren();$("frames").replaceChildren();$("evidence").replaceChildren();$("decision").textContent="WAIT";$("score").textContent="No current snapshot";$("status").textContent=message;$("source").textContent="";$("save").disabled=true;}
  function stop(message) {sequence++;if(controller)controller.abort();controller=null;$("analyze").disabled=false;clear(message);}
  function render(data) {
    current=data;$("decision").textContent=data.decision==="paper_plan_only"?"PAPER PLAN":"WAIT";
    $("score").textContent=data.confluence.score+" / 100 rule coverage";
    $("status").textContent=data.decision==="paper_plan_only"?"Sirf hypothetical long study. Koi order place nahi hua.":"Setup ke tamam checks poore nahi. Abhi paper entry plan nahi.";
    $("source").textContent="Binance Spot · fetched "+date(data.fetched_at*1000)+" · analysis "+date(data.as_of_ms);
    $("frames").replaceChildren();
    for(const tf of FRAMES){const f=data.timeframes[tf],tr=document.createElement("tr");for(const value of [tf,fmt(f.last_close),fmt(f.support),fmt(f.resistance),fmt(f.rsi14)]){const td=document.createElement("td");td.textContent=value;tr.append(td);}tr.title="Candle close: "+date(f.last_closed_at);$("frames").append(tr);}
    $("evidence").replaceChildren();for(const [key,label] of Object.entries(CHECKS)){const passed=data.confluence.evidence[key].passed,li=document.createElement("li");li.className=passed?"pass":"miss";li.textContent=(passed?"✓ ":"○ ")+label;$("evidence").append(li);}
    $("setup").textContent="Long setup: "+data.setup.positive_families+" / 6 evidence families. Correlated checks; success probability nahi.";
    $("levels").replaceChildren();$("plan").hidden=data.paper_plan===null;
    if(data.paper_plan){const p=data.paper_plan;for(const [label,value] of [["Reference close",p.reference_entry_close],["Entry + assumed slippage",p.estimated_entry_with_slippage],["Reference stop",p.reference_stop],["1R target before costs",p.targets[0].reference_price],["2R target before costs",p.targets[1].reference_price],["Estimated stop loss incl. costs · USDT",p.estimated_stop_loss_including_costs_usdt],["Hypothetical base quantity",p.estimated_quantity_base]]){const dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=label;dd.textContent=fmt(value);$("levels").append(dt,dd);}}
    $("snapshot").hidden=false;$("save").disabled=!$("journalConsent").checked;
    expiry=setTimeout(()=>stop("Snapshot expire ho gaya. Dobara analyze karo."),Math.max(1,data.expires_at_ms-Date.now()));
  }
  $("deskForm").addEventListener("submit",async event=>{
    event.preventDefault();stop("Closed candles check ho rahe hain…");
    let expected;try{expected=settings({symbol:$("symbol").value,equity_usdt:$("equity").value,risk_pct:$("risk").value,fee_bps:$("fee").value,slippage_bps:$("slip").value});}catch(_){clear("Paper settings theek karo.");return;}
    const run=sequence;controller=new AbortController();const requestController=controller;
    const timeout=setTimeout(()=>{if(run===sequence)stop("Request timeout. WAIT — dobara manually try karo.");},45000);
    $("analyze").disabled=true;
    try{
      const response=await fetch(API+"/api/trading/desk?"+new URLSearchParams(expected),{method:"GET",cache:"no-store",credentials:"omit",signal:requestController.signal});
      if(!response.ok)throw new Error("Unavailable evidence");
      const data=await boundedJson(response);if(run!==sequence)return;
      render(validate(data,expected));
    }catch(_){if(run===sequence)clear("Data verify nahi hua / server unavailable. WAIT — koi plan nahi.");}
    finally{clearTimeout(timeout);if(run===sequence){$("analyze").disabled=false;controller=null;}}
  });
  $("stop").addEventListener("click",()=>stop("Analysis stop aur clear kar diya."));
  for(const id of ["symbol","equity","risk","fee","slip"])$(id).addEventListener("input",()=>stop("Settings change hui. Naya analysis zaroori hai."));
  document.addEventListener("visibilitychange",()=>{if(document.hidden)stop("Screen background mein gayi. Wapas aa kar fresh analysis karo.");});
  root.addEventListener("pagehide",()=>stop("Session closed."));
  $("journalConsent").addEventListener("change",()=>{$("save").disabled=!$("journalConsent").checked||!current;});
  $("save").addEventListener("click",()=>{try{const count=saveJournal(root.localStorage,current,$("journalNote").value,$("journalConsent").checked);$("journalStatus").textContent=count+" analysis snapshots is device par saved. Yeh executed trades/PnL nahi.";}catch(_){$("journalStatus").textContent="Save nahi hua. Consent, fresh snapshot aur storage space check karo.";}});
  $("export").addEventListener("click",()=>{try{if(!$("journalConsent").checked)throw new Error("Consent required");const entries=loadJournal(root.localStorage);const blob=new Blob([JSON.stringify({version:"hoshi-paper-journal-v1",entries},null,2)],{type:"application/json"});const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="hoshi-paper-journal.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$("journalStatus").textContent=entries.length+" snapshots export kiye.";}catch(_){$("journalStatus").textContent="Export nahi hua. Saving permission/storage check karo.";}});
  $("delete").addEventListener("click",()=>{try{root.localStorage.removeItem(STORE);$("journalStatus").textContent="Local journal delete kar diya.";}catch(_){$("journalStatus").textContent="Storage access unavailable.";}});
  $("analyze").disabled=false;
  $("status").textContent="Analyze dabao. Data aane se pehle koi plan nahi.";
})(typeof window!=="undefined"?window:globalThis);
