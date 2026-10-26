"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const mimeTypes = {
  ".html": "text/html; charset=utf-8",
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
    await page.locator('[data-tab="settings"]').click();
    assert.equal(await page.locator('#voicePanel').isVisible(), true);
    assert.equal(await page.locator('#stopSpeakingBtn').isVisible(), true);
    await page.locator('.sheet-close').click();
    assert.equal(await page.locator('#nightSheet').isVisible(), false);
    for(const tab of ['trading','influencer','outfit']){
      await page.locator('[data-tab="'+tab+'"]').click();
      assert.equal(await page.locator('[data-panel="'+tab+'"]').isVisible(),true);
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
