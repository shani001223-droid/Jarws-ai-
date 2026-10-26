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
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    await context.addInitScript(() => {
      try {
        localStorage.setItem("hoshiVoiceReplies", "false");
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
      };
      if (request.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers });
        return;
      }
      const endpoint = new URL(request.url()).pathname;
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
    assert.match(await page.locator('#draftStatus').innerText(), /Accessibility/);
    await page.locator('[data-tab="settings"]').click();
    assert.equal(await page.locator('#voicePanel').isVisible(), true);
    assert.equal(await page.locator('#stopSpeakingBtn').isVisible(), true);
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
    for(const tab of ['trading','influencer','outfit']){
      await page.locator('[data-tab="'+tab+'"]').click();
      assert.equal(await page.locator('[data-panel="'+tab+'"]').isVisible(),true);
      if(tab==='trading'){
        await page.waitForFunction(()=>document.querySelector('#tradePrice').textContent.includes('70,000.5'));
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
    await page.locator('[data-tab="outfit"]').click();
    assert.equal(await page.locator('button[data-outfit]').count(),15);
    await page.locator('button[data-outfit="winter"]').click();
    await page.waitForFunction(()=>document.querySelector('#nightroom').dataset.outfit==='winter');
    assert.equal(await page.locator('#nightSheet').isVisible(),false);
    assert.equal(await page.evaluate(()=>localStorage.getItem('hoshiOutfitV1')),'winter');
    const winterArt=await page.locator('#nightroom').evaluate(node=>node.style.backgroundImage);
    assert.match(winterArt,/assets\/outfits\/winter\.webp/);
    const winterSize=await page.locator('button[data-outfit="winter"] img').evaluate(async img=>{await img.decode();return [img.naturalWidth,img.naturalHeight]});
    assert.ok(winterSize[0]>=1024 && winterSize[1]>=1536,'Wardrobe must retain high-resolution source pixels');
    assert.match(await page.locator('#nightMood').innerText(),/Affectionate/);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>document.querySelector('#nightroom').dataset.outfit==='winter');
    await page.locator('[data-tab="outfit"]').click();
    await page.locator('button[data-outfit="techwear"]').click();
    await page.waitForFunction(()=>document.querySelector('#nightroom').dataset.outfit==='techwear');
    assert.notEqual(await page.locator('#nightroom').evaluate(node=>node.style.backgroundImage),winterArt,'Selecting another outfit must change actual main-screen art');
    const fashionSize=await page.locator('button[data-outfit="techwear"] img').evaluate(async img=>{await img.decode();return [img.naturalWidth,img.naturalHeight]});
    assert.ok(fashionSize[0]>=1024 && fashionSize[1]>=1536,'Fashion crop must retain restored source resolution');
    await page.locator('[data-tab="outfit"]').click();
    await page.locator('button[data-outfit="original"]').click();
    await page.waitForFunction(()=>document.querySelector('#nightroom').dataset.outfit==='original');
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
    await voiceContext.close();
    assert.deepEqual(pageErrors,[]);
    console.log('PASS — nightroom layout, chat, voice settings, tabs and narrow phone widths');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

