"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webp": "image/webp",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

function startStaticServer() {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://" + (request.headers.host || "127.0.0.1"));
    const requested = decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname);
    const filePath = path.resolve(ROOT, "." + requested);
    if (filePath !== ROOT && !filePath.startsWith(ROOT + path.sep)) {
      response.writeHead(403).end("Forbidden");
      return;
    }
    fs.readFile(filePath, (error, contents) => {
      if (error) {
        response.writeHead(404).end("Not found");
        return;
      }
      response.writeHead(200, {
        "Content-Type": mimeTypes[path.extname(filePath).toLowerCase()] || "application/octet-stream",
        "Cache-Control": "no-store",
      });
      response.end(contents);
    });
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, url: "http://127.0.0.1:" + address.port + "/" });
    });
  });
}

async function main() {
  const { server, url } = await startStaticServer();
  let browser;
  const apiMessages = [];
  const pageErrors = [];
  let researchDelay=0,researchFail=false;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    await context.addInitScript(() => {
      try {
        localStorage.setItem("hoshiVoiceReplies", "false");
        // Existing full-workspace regression checks intentionally use legacy tabs.
        localStorage.setItem("hoshiFocusModeV1", "false");
      } catch (_) {}
      // Headless CI has no microphone. Keep the voice fallback deterministic.
      try {
        Object.defineProperty(window, "SpeechRecognition", { configurable: true, value: undefined });
        Object.defineProperty(window, "webkitSpeechRecognition", { configurable: true, value: undefined });
      } catch (_) {}
      try {
        Object.defineProperty(navigator, "serviceWorker", {
          configurable: true,
          value: {
            addEventListener() {},
            register: async () => ({ update: async () => {} }),
          },
        });
      } catch (_) {}
    });
    const page = await context.newPage();
    page.on("pageerror", error => pageErrors.push(error.message));

    await page.route("https://jarws-ai-2.onrender.com/**", async route => {
      const request = route.request();
      const headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
        "Access-Control-Expose-Headers": "X-Request-ID",
        "X-Request-ID": "a73a7fe6-5dbe-41a3-98f8-434ce5abb008",
      };
      if (request.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers });
        return;
      }
      const endpoint = new URL(request.url()).pathname;
      if(endpoint==='/api/trading/research'){
        const symbol=new URL(request.url()).searchParams.get('symbol');
        if(researchDelay)await new Promise(resolve=>setTimeout(resolve,researchDelay));
        const frame={regime:'range',support:69000,resistance:71000,last_closed_at:1793000000000,indicators:{ema20:70000,ema50:70010,rsi14:50,atr14:200}};
        try{await route.fulfill({status:researchFail?503:200,headers,body:JSON.stringify({symbol,source:'Binance Spot',fetched_at:1793000000,orders_enabled:false,mode:'research-only',decision:'wait',reason:'<img src=x onerror=alert(1)>',timeframes:{'15m':frame,'1h':frame,'4h':frame},proposals:[],note:'Spot only.'})});}catch(_){}
        return;
      }
      if(endpoint==='/api/trading/backtest'){
        const cfg=request.postDataJSON();
        assert.equal(cfg.symbol,'BTCUSDT');assert.ok(cfg.risk_pct<=1);
        await route.fulfill({status:200,headers,body:JSON.stringify({symbol:cfg.symbol,source:'Binance Spot',strategy:cfg.strategy,fetched_at:1793000000,orders_enabled:false,mode:'historical-paper-simulation',bars:499,initial_equity:1000,ending_equity:998,net_pnl:-2,trade_count:2,max_drawdown_pct:.5,fees_paid:1,win_rate_pct:50,expectancy:-1,profit_factor:.8,start_at:1792800000000,end_at:1793000000000,config:cfg,limitations:['Fixture only; not a profitability result.'],trades:[]})});
        return;
      }
      if (endpoint === "/health") {
        await route.fulfill({
          status: 200,
          headers,
          body: JSON.stringify({
            ok: true,
            ai_connected: true,
            service: "hoshi-cloud-api",
            version: "0.9.1",
          }),
        });
        return;
      }
      if (endpoint === "/api/public/market") {
        await route.fulfill({ status: 200, headers, body: JSON.stringify({
          symbol: "BTCUSDT", market: "spot", source: "Binance Spot", fetched_at: 1793000000,
          price: 70000.5, change_24h_pct: 1.25, volume_quote_24h: 2500000
        }) });
        return;
      }
      if (endpoint === "/api/public/candles") {
        const candles = Array.from({ length: 80 }, (_, i) => ({
          time: 1793000000 + i*300000, open: 70000+i, high: 70005+i,
          low: 69995+i, close: 70001+i, volume: 10
        }));
        await route.fulfill({ status: 200, headers, body: JSON.stringify({
          symbol: "BTCUSDT", interval: "5m", market: "spot", source: "Binance Spot",
          fetched_at: 1793000000, candles,
          indicators: { ema9: 70075, sma20: 70070.5, rsi14: 67.2 }
        }) });
        return;
      }
      if (endpoint === "/api/public/sentiment") {
        await route.fulfill({ status: 200, headers, body: JSON.stringify({
          source: "Alternative.me", fetched_at: 1793000000, value: 54, classification: "Neutral"
        }) });
        return;
      }
      if (endpoint === "/api/agent/execute") {
        const requestBody=request.postDataJSON();
        assert.equal(requestBody.task,"create_product_ads");
        assert.match(requestBody.message,/ads bana/i);
        await route.fulfill({status:200,headers,body:JSON.stringify({
          ok:true,completed:true,task:"create_product_ads",
          filename:"Flora_Product_Ads.zip",
          zip_base64:Buffer.from("PK\\x03\\x04MOCK").toString("base64"),
          preview_base64:null,
          products:[{product:"24K GOLD FACIAL KIT",price:"RS. 3,500",
            caption:"Flora 24K Gold Facial Kit, six products at Rs. 3,500."}]
        })});
        return;
      }
      if (endpoint === "/api/research/sources") {
        assert.equal(request.method(), "GET");
        assert.equal(new URL(request.url()).searchParams.get("topic"), "world");
        await route.fulfill({status:200,headers,body:JSON.stringify({
          topic:"world",publisher:"BBC News",retrieved_at:"2026-10-27T00:00:00+00:00",
          items:[{title:"<img src=x onerror=alert(1)>",summary:"Source headline only",
            publisher:"BBC News",published_at:"2026-10-26T23:00:00+00:00",
            citation_url:"https://www.bbc.com/news/articles/grounded?tracking=1"}]
        })});
        return;
      }
      if (endpoint !== "/api/assistant") {
        await route.fulfill({ status: 404, headers, body: JSON.stringify({ detail: "Unknown test route" }) });
        return;
      }

      const body = request.postDataJSON();
      apiMessages.push(body);
      if (body.message === "older slow request") {
        await new Promise(resolve => setTimeout(resolve, 500));
        try {
          await route.fulfill({
            status: 200,
            headers,
            body: JSON.stringify({ reply: "STALE RESPONSE", emotion: "sad", mode: "mock" }),
          });
        } catch (_) {
          // Expected if the frontend aborted this request after the newer message arrived.
        }
      } else {
        const reply = body.message === "newer fast request"
          ? "NEW RESPONSE"
          : "I can help you plan, explain, and create.";
        await route.fulfill({
          status: 200,
          headers,
          body: JSON.stringify({ reply, emotion: "affectionate", mode: "mock" }),
        });
      }
    });

    await page.goto(url, { waitUntil: 'domcontentloaded' });
    assert.equal(await page.title(), 'HOSHI — AI Companion');
    await page.locator('.nightroom').waitFor({state:'visible'});
    assert.equal(await page.locator('.night-tabs button').count(), 5);
    assert.equal(await page.locator('.room-life').count(),0,'Removed unwanted Hoshi room-life stage');
    assert.equal(await page.locator('.life-toggle').count(),0,'Removed room activity menu');
    assert.equal(await page.locator('#roomMotionToggle').count(),0,'Removed room animation setting');
    assert.equal(await page.locator('.sidebar').isVisible(), false);
    assert.equal(await page.locator('#voicePanel').isVisible(), false);
    assert.equal(await page.locator('#nightSheet').isVisible(), false);
    assert.equal(await page.locator('#wakeBtn').isVisible(), true);
    await page.locator('[data-tab="chat"]').click();
    await page.locator('#commandInput').fill('what time is it');
    await page.locator('#commandForm button').click();
    assert.match(await page.locator('#reply').innerText(), /waqt|time/i);
    await page.locator('#commandInput').fill('Tell me what you can help with');
    await page.locator('#commandForm button').click();
    await page.waitForFunction(()=>document.querySelector('#reply').textContent.includes('I can help'));
    assert.equal(apiMessages.at(-1).locale,'ur-PK');
    assert.equal(apiMessages.at(-1).fast,true,'Simple text questions use fast one-shot Groq path');
    // The voice/text ad intent executes an actual backend action, not a model response.
    await page.evaluate(()=>{
      window.__adSaved=[];
      window.JarvisBridge={
        saveAdZip:(payload,name)=>{window.__adSaved.push({size:payload.length,name});return true;}
      };
    });
    const beforeAdApi=apiMessages.length;
    await page.locator('#commandInput').fill('Mere products ke ads bana kar do');
    await page.locator('#commandForm button').click();
    await page.locator('#adStudioResult button').waitFor({state:'visible'});
    assert.match(await page.locator('#adStudioResult').innerText(),/24K GOLD FACIAL KIT/);
    await page.locator('#adStudioResult button').click();
    assert.deepEqual(await page.evaluate(()=>window.__adSaved.map(x=>x.name)),['Flora_Product_Ads.zip']);
    assert.equal(apiMessages.length,beforeAdApi,'Ads must call task API, not waste a chat-model request');
    // Unsupported multi-hour projects and chart screen actions are recognized,
    // but must never be faked or silently sent to the chat model as execution.
    const beforeUnsupported=apiMessages.length;
    for(const [command,expected] of [
      ['Mere liye ek puri game banaao','build_game'],
      ['Hindi Urdu anime 300 episodes 30 min each banaao','render_anime'],
      ['BTC chart analyse kro support resistance mark kro','chart_analysis']
    ]){
      await page.locator('#commandInput').fill(command);
      await page.locator('#commandForm button').click();
      assert.match(await page.locator('#status').innerText(),new RegExp('AGENT NOT READY.*'+expected,'i'));
      assert.match(await page.locator('#reply').innerText(),/nahi|available|verified/i);
      assert.equal(apiMessages.length,beforeUnsupported,'Unsupported agent must not be treated as completed AI task');
    }
    await page.locator('#commandInput').fill('How to create a game?');
    await page.locator('#commandForm button').click();
    await page.waitForFunction(()=>document.querySelector('#reply').textContent.includes('I can help'));
    assert.equal(apiMessages.length,beforeUnsupported+1,'Explanations should still use ordinary chat');
    // No cloud model should be called for concrete Android actions or writing drafts.
    await page.evaluate(() => {
      window.__phoneActions = [];
      window.JarvisBridge = {
        isEnabled: () => true,
        performAction: name => { window.__phoneActions.push(["screen",name]); return true; },
        openKnownApp: name => { window.__phoneActions.push(["open",name]); return true; },
        copyUserText: value => {window.__phoneActions.push(["copy",value]);return true;},
        shareUserDraft: value => {window.__phoneActions.push(["share",value]);return true;},
        requestSettings: () => window.__phoneActions.push(["permission"])
      };
    });
    const beforeLocalCommands=apiMessages.length;
    await page.locator('#commandInput').fill('open WhatsApp');
    await page.locator('#commandForm button').click();
    await page.locator('#commandInput').fill('phone back');
    await page.locator('#commandForm button').click();
    await page.locator('#commandInput').fill('note likho Kal subah meeting hai');
    await page.locator('#commandForm button').click();
    assert.equal(await page.locator('#hoshiDraft').inputValue(),'Kal subah meeting hai');
    await page.locator('#copyHoshiDraft').click();
    await page.locator('#shareHoshiDraft').click();
    await page.locator('#enablePhoneAccess').click();
    assert.equal(apiMessages.length,beforeLocalCommands,'No API requests for local actions');
    assert.deepEqual(await page.evaluate(()=>window.__phoneActions),[
      ['open','whatsapp'],['screen','back'],
      ['copy','Kal subah meeting hai'],['share','Kal subah meeting hai'],['permission']
    ]);
    // Task 23: native app handoff is explicitly user-initiated and status-only.
    await page.evaluate(()=>{
      window.__verifiedIntents=[];
      window.JarvisBridge.isEnabled=()=>false; // App launch must not need Accessibility.
      window.JarvisBridge.openKnownAppVerified=(name,id)=>{
        window.__verifiedIntents.push({name,id});return true;
      };
    });
    await page.locator('#commandInput').fill('open Telegram');
    await page.locator('#commandForm button').click();
    const intent=await page.evaluate(()=>window.__verifiedIntents.at(-1));
    assert.equal(intent.name,'telegram');
    assert.match(await page.locator('#reply').innerText(),/Requesting telegram app/);
    await page.evaluate(({id})=>window.hoshiKnownAppLaunchResult(id+1,'telegram',true),intent);
    assert.match(await page.locator('#reply').innerText(),/Requesting telegram app/,'Ignore stale callback');
    await page.evaluate(({id})=>window.hoshiKnownAppLaunchResult(id,'whatsapp',true),intent);
    assert.match(await page.locator('#reply').innerText(),/Requesting telegram app/,'Ignore mismatched app');
    await page.evaluate(({id})=>window.hoshiKnownAppLaunchResult(id,'telegram',false),intent);
    assert.match(await page.locator('#reply').innerText(),/Could not open telegram/);
    await page.locator('#commandInput').fill('open TradingView');
    await page.locator('#commandForm button').click();
    const secondIntent=await page.evaluate(()=>window.__verifiedIntents.at(-1));
    assert.equal(secondIntent.name,'tradingview');
    await page.evaluate(({id})=>window.hoshiKnownAppLaunchResult(id,'tradingview',true),secondIntent);
    assert.match(await page.locator('#reply').innerText(),/Android accepted tradingview launch request/);
    assert.equal(apiMessages.length,beforeLocalCommands,'Safe app intents never call AI');
    assert.match(await page.locator('#draftStatus').innerText(), /Accessibility/);
    await page.locator('[data-tab="settings"]').click();
    assert.equal(await page.locator('#voicePanel').isVisible(), true);
    assert.equal(await page.locator('#stopSpeakingBtn').isVisible(), true);
    await page.locator('#clientDiagnostics summary').click();
    await page.evaluate(()=>window.HoshiDiagnostics.record('uncaught_error',{filename:'https://example.test/index.html?key=PRIVATE-QUERY',lineno:18,message:'PRIVATE-CHAT',error:{stack:'PRIVATE-STACK'}}));
    await page.locator('#copyDiagnosticReport').click();
    const copiedDiagnostic=await page.evaluate(()=>window.__phoneActions.at(-1));
    assert.equal(copiedDiagnostic[0],'copy');
    assert.match(copiedDiagnostic[1],/a73a7fe6-5dbe-41a3-98f8-434ce5abb008/);
    assert.doesNotMatch(copiedDiagnostic[1],/PRIVATE|example.test|Tell me what you can help/);
    await page.locator('#clearDiagnosticReport').click();
    assert.deepEqual(await page.evaluate(()=>window.HoshiDiagnostics.snapshot().events),[]);
    assert.equal(await page.evaluate(()=>window.HoshiDiagnostics.snapshot().last_api_response),null);
    await page.locator('#clientDiagnostics summary').click();

    // Fast Urdu on an Android phone with installed ur-PK TTS should skip HTTP speech generation.
    await page.evaluate(()=>{
      window.__nativeSpoken=[];
      window.JarvisBridge.supportsUrduSpeech=()=>true;
      window.JarvisBridge.speakNative=(text,lang,pitch,rate)=>{
        window.__nativeSpoken.push({text,lang,pitch,rate});return true;
      };
      window.JarvisBridge.stopNativeSpeech=()=>true;
    });
    await page.locator('#previewVoiceBtn').click();
    assert.equal(await page.evaluate(()=>window.__nativeSpoken.length),1);
    assert.equal(await page.evaluate(()=>window.__nativeSpoken[0].lang),'ur-PK');
    await page.evaluate(()=>window.hoshiNativeSpeechStarted());
    assert.match(await page.locator('#voiceTiming').innerText(),/Awaaz [0-9.]+s/);
    await page.locator('#stopSpeakingBtn').click();
    await page.locator('.sheet-close').click();
    assert.equal(await page.locator('#nightSheet').isVisible(), false);
    for(const tab of ['trading','influencer']){
      await page.locator('[data-tab="'+tab+'"]').click();
      assert.equal(await page.locator('[data-panel="'+tab+'"]').isVisible(),true);
      if(tab==='trading'){
        await page.waitForFunction(()=>document.querySelector('#tradePrice').textContent.includes('70,000.5'));
        assert.equal(await page.locator('#tradeJournalConsent').isChecked(),false);
        await page.locator('#tradeResearchRun').click();
        await page.waitForFunction(()=>document.querySelector('#tradeResearchStatus').textContent.startsWith('Complete'));
        assert.match(await page.locator('#tradeResearchOutput').innerText(),/WAIT/);
        assert.equal(await page.locator('#tradeResearchOutput img').count(),0,'Upstream strings must be inert text');
        const downloadPromise=page.waitForEvent('download');await page.locator('#tradeResearchExport').click();
        const download=await downloadPromise;
        assert.match(download.suggestedFilename(),/Hoshi_BTCUSDT_research.json/);
        const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
        assert.equal(exported.orders_enabled,false);
        await page.locator('#tradeBacktestRun').click();
        await page.waitForFunction(()=>document.querySelector('#tradeResearchStatus').textContent.startsWith('Complete'));
        assert.match(await page.locator('#tradeResearchOutput').innerText(),/HISTORICAL SIMULATION/);
        assert.equal(await page.evaluate(()=>localStorage.getItem('hoshiPaperJournalV1')),null);
        await page.locator('#tradeJournalConsent').check();
        await page.locator('#tradeResearchSettings summary').click();
        await page.locator('#tradeStrategy').selectOption('breakout_retest');
        await page.locator('#tradeBacktestRun').click();
        await page.waitForFunction(()=>document.querySelector('#tradeResearchStatus').textContent.startsWith('Complete'));
        assert.equal(JSON.parse(await page.evaluate(()=>localStorage.getItem('hoshiPaperJournalV1'))).length,1);
        await page.locator('#tradeJournalClear').click();
        assert.equal(await page.evaluate(()=>localStorage.getItem('hoshiPaperJournalV1')),null);
        await page.locator('#tradeJournalConsent').uncheck();
        researchFail=true;await page.locator('#tradeResearchRun').click();
        await page.waitForFunction(()=>document.querySelector('#tradeResearchStatus').textContent.includes('(503)'));
        assert.equal(await page.locator('#tradeResearchExport').isDisabled(),true);
        assert.equal(await page.locator('#tradeResearchOutput').innerText(),'');researchFail=false;
        researchDelay=500;await page.locator('#tradeResearchRun').click();
        await page.locator('#tradePair').selectOption('ETHUSDT');
        await page.waitForTimeout(600);
        assert.equal(await page.locator('#tradeResearchOutput').innerText(),'','Late BTC result must not appear after selecting ETH');
        researchDelay=0;await page.locator('#tradePair').selectOption('BTCUSDT');
        await page.waitForFunction(()=>!document.querySelector('#tradeRefresh').disabled);
        assert.match(await page.locator('#tradeIndicators').innerText(), /RSI 14: 67.2/);
        assert.match(await page.locator('#tradeSentiment').innerText(), /Alternative.me/);
        assert.equal(await page.locator('#tradeChart [data-candle]').count(),80);
        assert.equal(await page.locator('#tradeGauge').getAttribute('aria-valuenow'),'54');
        await page.locator('#tradeLine').click();
        assert.equal(await page.locator('#tradeChart [data-candle]').count(),0);
        assert.equal(await page.locator('#tradeChart [data-close-line]').count(),1);
        await page.locator('#tradeRange').click();
        assert.equal(await page.locator('#tradeChart [data-range-level]').count(),2);
        await page.locator('#tradeCandles').click();
        await page.locator('#tradePair').selectOption('SOLUSDT');
        await page.waitForFunction(()=>!document.querySelector('#tradeRefresh').disabled);
        assert.match(await page.locator('#tradeExternal').getAttribute('href'),/SOLUSDT/);
        await page.locator('#tradeWatchToggle').click();
        assert.ok(JSON.parse(await page.evaluate(()=>localStorage.getItem('hoshiTradeWatchV1'))).includes('SOLUSDT'));
        await page.getByRole('button',{name:'Remove SOLUSDT from watchlist',exact:true}).click();
        assert.ok(!JSON.parse(await page.evaluate(()=>localStorage.getItem('hoshiTradeWatchV1'))).includes('SOLUSDT'));
        for(const width of [320,390,768,1440]){
          await page.setViewportSize({width,height:900});
          assert.equal(await page.evaluate(()=>document.querySelector('#nightSheet').scrollWidth>document.querySelector('#nightSheet').clientWidth+1),false,'Trading workspace must fit '+width+'px');
          assert.equal(await page.locator('#tradePair').isVisible(),true);
        }
        await page.setViewportSize({width:390,height:844});
        await page.locator('#nightSheet').evaluate(n=>n.scrollTop=0);
        await page.screenshot({path:'/tmp/hoshi-trading-mobile.png',fullPage:true});
        await page.locator('#tradeAsk').click();
        assert.equal(await page.locator('[data-panel="chat"]').isVisible(),true);
        assert.match(await page.locator('#commandInput').inputValue(),/SOLUSDT.*spot market/);
        await page.locator('[data-tab="trading"]').click();
        await page.waitForFunction(()=>!document.querySelector('#tradeRefresh').disabled);
        await page.route('https://jarws-ai-2.onrender.com/api/public/**',route=>route.fulfill({status:503,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:'{}'}));
        await page.locator('#tradeRefresh').click();
        await page.waitForFunction(()=>document.querySelector('#tradeStatus').textContent.includes('unavailable'));
        assert.equal(await page.locator('#tradePrice').innerText(),'—');
        assert.equal(await page.locator('#tradeChart [data-candle]').count(),0);
        assert.equal(await page.locator('#tradeGauge').getAttribute('aria-valuenow'),null);
        await page.unroute('https://jarws-ai-2.onrender.com/api/public/**');

      }
      await page.locator('.sheet-close').click();
    }
    // The approved main screen is a black holographic core, not the old wardrobe.
    assert.equal(await page.locator('[data-tab="outfit"]').isVisible(),false);
    assert.equal(await page.locator('#hoshiEnergy').isVisible(),true);
    await page.waitForFunction(()=>document.querySelector('#core-canvas').width>0);
    assert.equal(await page.locator('#nightroom').evaluate(el=>getComputedStyle(el).backgroundImage),'none');
    for(const width of [320,390,768]){
      await page.setViewportSize({width,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
      for(const selector of ['#wakeBtn','.night-tabs'])assert.equal(await page.locator(selector).isVisible(),true);
    }
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'/tmp/hoshi-nightroom-mobile.png',fullPage:true});
    // Reproduce the previous repeated-mic bug without relying on physical hardware.
    const voiceContext = await browser.newContext({viewport:{width:390,height:844}});
    await voiceContext.addInitScript(() => {
      localStorage.setItem("hoshiVoiceReplies","false");
      window.micStartCount = 0;
      window.MockRecognition = class {
        constructor(){window.lastMicInstance=this}
        start(){window.micStartCount++;this.onstart?.()}
        abort(){this.aborted=true}
      };
      window.SpeechRecognition = window.MockRecognition;
      window.webkitSpeechRecognition = window.MockRecognition;
      Object.defineProperty(navigator,"serviceWorker",{value:undefined,configurable:true});
    });
    const voicePage = await voiceContext.newPage();
    let heardRequests=0;
    await voicePage.route("https://jarws-ai-2.onrender.com/**", async route => {
      const path=new URL(route.request().url()).pathname;
      const headers={"Access-Control-Allow-Origin":"*","Content-Type":"application/json"};
      if(path==="/health"){await route.fulfill({status:200,headers,body:'{"ok":true,"ai_connected":true}'});return}
      if(path==="/api/assistant"){heardRequests++;await route.fulfill({status:200,headers,body:JSON.stringify({reply:"Hoshi heard you",speech_text:"ہوشی نے سنا",mode:"mock",emotion:"caring"})});return}
      await route.fulfill({status:404,headers,body:'{}'});
    });
    await voicePage.goto(url,{waitUntil:"domcontentloaded"});
    await voicePage.locator("#wakeBtn").click();
    await voicePage.evaluate(()=>{
      const mic=window.document.querySelector("#wakeBtn");
      assertMicState(mic);
      function assertMicState(node){if(!node.textContent.includes("Listening"))throw new Error("mic did not start")}
    });
    assert.equal(await voicePage.evaluate(()=>window.micStartCount),1);
    await voicePage.evaluate(()=>{
      const recognition=window.lastMicInstance;
      recognition.onresult({resultIndex:0,results:[{isFinal:true,0:{transcript:"Why is the sky blue"}}]});
      recognition.onresult?.({resultIndex:0,results:[{isFinal:true,0:{transcript:"Why is the sky blue"}}]});
      recognition.onend?.();
    });
    await voicePage.waitForFunction(()=>document.querySelector("#reply").textContent.includes("Hoshi heard you"));
    assert.equal(heardRequests,1,"One mic tap must produce exactly one cloud request");
    assert.equal(await voicePage.evaluate(()=>window.micStartCount),1,"Mic must never auto-restart");

    // Test real UI integration: the Urdu-script alternative should win only
    // when the user explicitly enabled the Hey Hoshi wake-word filter.
    await voicePage.evaluate(()=>document.querySelector('#wakeToggle').click());
    await voicePage.locator('#wakeBtn').click();
    const responseWithWake=voicePage.waitForResponse(r=>r.url().includes('/api/assistant'));
    await voicePage.evaluate(()=>{
      const recognition=window.lastMicInstance;
      recognition.onresult({resultIndex:0,results:[{
        isFinal:true,length:2,
        0:{transcript:'some random words'},
        1:{transcript:'ہے ہوشی, Why do stars shine'}
      }]});
      recognition.onend?.();
    });
    await responseWithWake;
    assert.equal(heardRequests,2,'Urdu wake word alternative should make one request');
    assert.equal(await voicePage.evaluate(()=>window.micStartCount),2);

    // Without the wake word, recognized speech must NOT trigger a provider call.
    await voicePage.locator('#wakeBtn').click();
    await voicePage.evaluate(()=>{
      window.lastMicInstance.onresult({resultIndex:0,results:[{
        isFinal:true,length:1,0:{transcript:'why is water wet'}
      }]});
    });
    assert.equal(heardRequests,2,'Wake mode rejects speech without an explicit wake word');
    assert.equal(await voicePage.evaluate(()=>document.querySelector('#status').textContent.includes('SAY HEY HOSHI')),true);
    // Stop Speaking must also cancel an in-flight cloud reply, so a stale
    // result cannot start new speech after the user explicitly interrupts.
    await voicePage.route('https://jarws-ai-2.onrender.com/api/assistant',async route=>{
      const data=route.request().postDataJSON();
      if(!String(data?.message||'').includes('delayed interruption test')){
        await route.fallback();return;
      }
      await new Promise(resolve=>setTimeout(resolve,450));
      try{
        await route.fulfill({
          status:200,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'},
          body:JSON.stringify({reply:'UNSAFE LATE REPLY',speech_text:'دیر سے جواب',mode:'mock',emotion:'happy'})
        });
      }catch(_){/* Fetch cancellation may close the route before delivery. */}
    });
    await voicePage.evaluate(()=>{
      document.querySelector('#commandInput').value='Explain delayed interruption test';
      document.querySelector('#commandForm').requestSubmit();
    });
    await voicePage.waitForFunction(()=>document.querySelector('#status').textContent.includes('AI THINKING'));
    await voicePage.evaluate(()=>document.querySelector('#stopSpeakingBtn').click());
    await voicePage.waitForTimeout(650);
    assert.equal(await voicePage.evaluate(()=>document.querySelector('#reply').textContent.includes('UNSAFE LATE REPLY')),false);
    assert.equal(await voicePage.evaluate(()=>document.querySelector('#status').textContent.includes('PENDING REPLY STOPPED')),true);
    await voiceContext.close();

    // Task 17: consent is OFF by default; no previous chat is silently stored.
    await page.locator('[data-tab="chat"]').click();
    assert.match(await page.locator('#memoryToggle').innerText(), /OFF/);
    assert.equal(await page.evaluate(()=>localStorage.getItem('hoshiConversationMemoryV1')),null);
    await page.locator('#memoryToggle').click();
    assert.match(await page.locator('#memoryToggle').innerText(), /ON/);
    await page.locator('[data-tab="chat"]').click();
    await page.locator('#commandInput').fill('Explain a calm evening');
    const firstMemoryReply=page.waitForResponse(r=>r.url().endsWith('/api/assistant')&&r.request().postDataJSON().message==='Explain a calm evening');
    await page.locator('#commandForm button').click();
    await firstMemoryReply;
    const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('hoshiConversationMemoryV1')));
    assert.ok(saved.some(item=>item.role==='user'&&item.content==='Explain a calm evening'));
    await page.evaluate(()=>localStorage.setItem('hoshiConversationMemoryV1',JSON.stringify([
      {role:'user',content:'Explain a calm evening',at:1},
      {role:'user',content:'my password is ABC',at:2}
    ])));
    const downloadPromise=page.waitForEvent('download');
    await page.locator('#exportMemoryBtn').click();
    const download=await downloadPromise;
    assert.equal(download.suggestedFilename(),'hoshi-local-memory.json');
    const exported=await download.createReadStream();
    const chunks=[];for await(const chunk of exported)chunks.push(chunk);
    const exportedData=JSON.parse(Buffer.concat(chunks).toString('utf8'));
    assert.deepEqual(exportedData.turns.map(item=>item.content),['Explain a calm evening']);
    await page.locator('#memoryToggle').click();
    assert.match(await page.locator('#memoryToggle').innerText(), /OFF/);
    assert.equal(await page.evaluate(()=>localStorage.getItem('hoshiConversationMemoryV1')),null);
    await page.locator('[data-tab="chat"]').click();
    await page.locator('#commandInput').fill('Explain the moon');
    const afterOptOutReply=page.waitForResponse(r=>r.url().endsWith('/api/assistant')&&r.request().postDataJSON().message==='Explain the moon');
    await page.locator('#commandForm button').click();
    await afterOptOutReply;
    assert.deepEqual(apiMessages.at(-1).context,[],'No prior chat sent after consent revoked');
    assert.equal(await page.evaluate(()=>localStorage.getItem('hoshiConversationMemoryV1')),null);
    // Explicit OCR must not forward screenshot text to the backend or execute HTML.
    await context.addInitScript(() => {
      window.__localOcrPickers = 0;
      window.__cancelQueuedActions = 0;
      window.JarvisBridge = {
        isEnabled: () => true, requestSettings: () => {},
        performAction: () => true,
        cancelQueuedActions: () => { window.__cancelQueuedActions++; return true; },
        chooseScreenshotForLocalOcr: () => { window.__localOcrPickers++; return true; },
        performLocalUiAction: (action,payload,id) => {
          setTimeout(() => window.hoshiLocalUiActionResult(id,
            window.hoshiExecuteLocalUiAction(action,payload,id)), 0);
          return true; // Native queues first, verifies DOM state asynchronously.
        }
      };
    });
    await page.reload();
    // OCR controls live in the Settings sheet; Chat does not expose this private tool.
    await page.locator('[data-tab="settings"]').click();
    assert.equal(await page.locator('#screenControlSection').isVisible(), true,
      'Native-only screen controls must be visible in Settings');
    await page.locator('#screenOcrBtn').click();
    assert.equal(await page.evaluate(() => window.__localOcrPickers), 1);
    const messagesBeforeOcr = apiMessages.length;
    await page.evaluate(() => window.hoshiLocalOcrResult(JSON.stringify({
      engine:'on-device-latin',width:1080,height:2400,
      blocks:[{text:'Roman Urdu screenshot',box:[10,20,300,50]},
              {text:'<img src=x onerror=alert(1)>',box:[10,60,400,100]}],
      truncated:false
    })));
    assert.match(await page.locator('#screenOcrOutput').innerText(), /Roman Urdu screenshot/);
    assert.equal(await page.locator('#screenOcrOutput img').count(), 0, 'OCR text must not render as HTML');
    assert.equal(apiMessages.length,messagesBeforeOcr,'OCR must not upload to backend');
    await page.locator('#screenOcrClearBtn').click();
    assert.equal(await page.locator('#screenOcrOutput').innerText(), '');
    await page.evaluate(() => window.hoshiLocalOcrResult(JSON.stringify({
      engine:'on-device-latin',blocks:[{text:'LATE SENSITIVE RESULT'}]
    })));
    assert.equal(await page.locator('#screenOcrOutput').innerText(), '', 'Clear must ignore late OCR results');
    await page.locator('#screenOcrBtn').click();
    await page.evaluate(() => window.hoshiLocalOcrError('No screenshot selected'));
    assert.match(await page.locator('#screenOcrStatus').innerText(), /No screenshot selected/);
    // Task 21: explicit native-bridge simulation only changes the local Hoshi UI.
    const messagesBeforeLocalActions=apiMessages.length;
    await page.locator('#localUiDraft').fill('Hoshi meri trading research ka draft');
    await page.locator('#localUiTypeBtn').click();
    await page.waitForFunction(()=>document.querySelector('#localUiStatus').textContent.includes('Verified:'));
    assert.equal(await page.locator('#commandInput').inputValue(),
      'Hoshi meri trading research ka draft');
    assert.equal(await page.locator('[data-tab="chat"]').getAttribute('aria-selected'),'true');
    assert.equal(apiMessages.length,messagesBeforeLocalActions,'Draft typing must not submit AI requests');
    await page.locator('[data-tab="settings"]').click();
    await page.locator('#localUiScrollDownBtn').click();
    await page.waitForFunction(()=>/Verified:|Not verified:/.test(document.querySelector('#localUiStatus').textContent));
    const beforeStale=await page.locator('#localUiStatus').textContent();
    await page.evaluate(()=>window.hoshiLocalUiActionResult(999999,true));
    assert.equal(await page.locator('#localUiStatus').textContent(),beforeStale,'Ignore stale action IDs');
    await page.locator('#localUiChatBtn').click();
    await page.waitForFunction(()=>document.querySelector('#localUiStatus').textContent.includes('Verified:'));
    assert.equal(await page.locator('[data-tab="chat"]').getAttribute('aria-selected'),'true');
    await page.locator('[data-tab="settings"]').click();
    await page.evaluate(()=>{window.JarvisBridge.isEnabled=()=>false});
    await page.locator('#localUiScrollUpBtn').click();
    assert.match(await page.locator('#localUiStatus').textContent(),/permission first/i);
    await page.evaluate(()=>window.hoshiLocalUiActionResult(999999,false));
    assert.match(await page.locator('#localUiStatus').textContent(),/permission first/i);
    assert.equal(apiMessages.length,messagesBeforeLocalActions);
    // Task 24: pause blocks new actions and records metadata, not draft content.
    await page.evaluate(()=>{window.JarvisBridge.isEnabled=()=>true});
    await page.locator('#actionPauseBtn').click();
    assert.match(await page.locator('#actionSafetyStatus').innerText(),/ACTIONS PAUSED/);
    await page.locator('#localUiScrollDownBtn').click();
    assert.match(await page.locator('#localUiStatus').innerText(),/paused or stopped/i);
    await page.locator('#actionResumeBtn').click();
    assert.match(await page.locator('#actionSafetyStatus').innerText(),/ACTIONS READY/);
    await page.evaluate(()=>{
      window.JarvisBridge.performLocalUiAction=(action,payload,id)=>{
        setTimeout(()=>window.hoshiLocalUiActionResult(id,
          window.hoshiExecuteLocalUiAction(action,payload,id)),650);
        return true;
      };
    });
    await page.locator('#localUiChatBtn').click();
    await page.locator('#actionEmergencyStopBtn').click();
    assert.match(await page.locator('#actionSafetyStatus').innerText(),/EMERGENCY STOP ACTIVE/);
    await page.waitForTimeout(800);
    assert.equal(await page.locator('[data-tab="settings"]').getAttribute('aria-selected'),'true',
      'Late native callback must not perform a stopped action');
    await page.locator('#localUiChatBtn').click();
    assert.match(await page.locator('#localUiStatus').innerText(),/paused or stopped/i);
    assert.ok(await page.evaluate(()=>window.__cancelQueuedActions)>=2,
      'Pause and stop must invalidate native queued action epoch');
    const historyText=await page.locator('#actionHistory').innerText();
    assert.match(historyText,/emergency stop/);
    assert.equal(historyText.includes('Hoshi meri trading research ka draft'),false,
      'History must not contain unsent draft payloads');
    assert.equal(apiMessages.length,messagesBeforeLocalActions,'Safety controls must not send AI requests');
    await page.evaluate(()=>{
      document.querySelector('#commandInput').value='Halted command should never reach AI';
      document.querySelector('#commandForm').requestSubmit();
      document.querySelector('#wakeBtn').click();
    });
    assert.match(await page.locator('#status').innerText(),/EMERGENCY STOP ACTIVE/);
    assert.equal(apiMessages.length,messagesBeforeLocalActions,'Halted assistant must not dispatch a new AI request');
    await page.reload();
    await page.locator('[data-tab="settings"]').click();
    assert.match(await page.locator('#actionSafetyStatus').innerText(),/EMERGENCY STOP ACTIVE/,
      'Emergency-stop latch must survive a page reload');
    await page.locator('#actionResumeBtn').click();
    await page.locator('#actionHistoryClearBtn').click();
    assert.equal(await page.locator('#actionHistory li').count(),0);
    // Task 31: news commands render source citations as inert links, never as HTML
    // or an uncited model reply, and do not call the assistant model.
    await page.locator('[data-tab="chat"]').click();
    const beforeSourceNews=apiMessages.length;
    await page.locator('#commandInput').fill('world news');
    await page.locator('#commandForm button').click();
    await page.locator('#sourceResearchResult a').waitFor();
    assert.equal(await page.locator('#sourceResearchResult a').count(),1);
    assert.equal(await page.locator('#sourceResearchResult img').count(),0);
    assert.equal(await page.locator('#sourceResearchResult a').getAttribute('href'),
      'https://www.bbc.com/news/articles/grounded');
    assert.equal(await page.locator('#sourceResearchResult a').innerText(),
      '<img src=x onerror=alert(1)>');
    assert.equal(apiMessages.length,beforeSourceNews,'Fixed-source news must not call LLM');
    // Focus Home must work on an actual narrow mobile browser independently
    // of existing full-workspace tests. No external assets are required to
    // render the CSS orb; existing tools are preserved behind Settings.
    const focusContext=await browser.newContext({viewport:{width:390,height:844}});
    await focusContext.addInitScript(()=>{
      try{localStorage.setItem('hoshiVoiceReplies','false')}catch(_){}
    });
    await focusContext.route('https://jarws-ai-2.onrender.com/**',route=>{
      const endpoint=new URL(route.request().url()).pathname;
      return route.fulfill({status:200,headers:{'Access-Control-Allow-Origin':'*','Content-Type':'application/json'},body:JSON.stringify(endpoint==='/health'?{ok:true,ai_connected:true}:{})});
    });
    const focusPage=await focusContext.newPage();
    focusPage.on('pageerror',error=>pageErrors.push(error.message));
    await focusPage.goto(url,{waitUntil:'domcontentloaded'});
    await focusPage.locator('.focus-core').waitFor({state:'visible'});
    assert.equal(await focusPage.locator('.nightroom.focus-mode').count(),1);
    assert.equal(await focusPage.locator('[data-tab="chat"]').isVisible(),false);
    assert.equal(await focusPage.locator('[data-tab="settings"]').isVisible(),true);
    const focusBackground=await focusPage.evaluate(()=>getComputedStyle(document.querySelector('#nightroom')).backgroundImage);
    assert.equal(focusBackground.includes('url('),false,'Focus mode must not download or display room/character images');
    await focusPage.locator('[data-tab="settings"]').click();
    // Confirm the selected panel before interacting with its child. If a
    // browser regression hides it, report actual DOM/CSS state rather than
    // masking the problem with a forced click on the hidden control.
    console.log('Focus settings state:',await focusPage.evaluate(()=>{
      const panel=document.querySelector('[data-panel="settings"]');
      const sheet=document.querySelector('#nightSheet');
      return {sheetHidden:sheet.hidden,panelHidden:panel.hidden,
        selected:document.querySelector('[data-tab="settings"]').getAttribute('aria-selected'),
        display:getComputedStyle(panel).display};
    }));
    await focusPage.locator('#nightSheet:not([hidden]) [data-panel="settings"]:not([hidden])').waitFor({state:'visible'});
    assert.match(await focusPage.locator('#focusModeToggle').innerText(),/ON/);
    await focusPage.locator('#focusModeToggle').click();
    assert.equal(await focusPage.locator('.nightroom.focus-mode').count(),0);
    assert.equal(await focusPage.locator('[data-tab="chat"]').isVisible(),true);
    await focusPage.locator('[data-tab="chat"]').click();
    assert.equal(await focusPage.locator('#commandInput').isVisible(),true);
    await focusContext.close();
    assert.deepEqual(pageErrors,[]);
    console.log('PASS — minimal black animated focus home and full tool access on mobile');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});


