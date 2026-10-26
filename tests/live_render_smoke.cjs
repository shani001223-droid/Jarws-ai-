"use strict";

const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const DASHBOARD_URL = "https://jarws-ai-1.onrender.com/?live-smoke=" + Date.now();
const HEALTH_URL = "https://jarws-ai-2.onrender.com/health";

async function waitForPublicEndpoints() {
  let lastError = "";
  for (let attempt = 1; attempt <= 12; attempt++) {
    try {
      const health = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(10000) });
      const data = await health.json();
      if (health.ok && data.service === "hoshi-cloud-api" && data.version === "0.9.1") {
        const response = await fetch(DASHBOARD_URL, { signal: AbortSignal.timeout(15000) });
        const html = await response.text();
        if (response.ok && /HOSHI — AI Companion/.test(html) && html.includes('id="nightroom"') && html.includes('assets/outfits/') && html.includes('id="tradeDashboard"')) return;
        lastError = "Dashboard returned HTTP " + response.status + " or has not published the trading dashboard revision yet";
      } else {
        lastError = "Backend health check did not match expected HOSHI API: HTTP " + health.status;
      }
    } catch (error) {
      lastError = String(error && error.message || error);
    }
    if (attempt < 12) await new Promise(resolve => setTimeout(resolve, 5000));
  }
  throw new Error("Public Render endpoints did not become ready: " + lastError);
}

async function main() {
  await waitForPublicEndpoints();
  const browser = await chromium.launch({ headless: true });
  const pageErrors = [];
  const badResponses = [];
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      reducedMotion: "reduce",
      // Verify current network assets; SW install/controllerchange is a separate lifecycle.
      serviceWorkers: "block",
    });
    await context.addInitScript(() => {
      try { localStorage.setItem("hoshiVoiceReplies", "false"); } catch (_) {}
    });
    const page = await context.newPage();
    page.on("pageerror", error => pageErrors.push(error.message));
    page.on("response", response => {
      if (response.status() >= 400 && new URL(response.url()).hostname === "jarws-ai-1.onrender.com") {
        badResponses.push({ status: response.status(), url: response.url() });
      }
    });

    await page.goto(DASHBOARD_URL, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.locator(".nightroom").waitFor({ state: "visible", timeout: 20000 });
    assert.equal(await page.title(), "HOSHI — AI Companion");
    assert.equal(await page.locator('.night-tabs button').count(),5);
    assert.equal(await page.locator('#wakeBtn').isVisible(),true);
    assert.equal(await page.locator('.sidebar').isVisible(),false);
    await page.locator('[data-tab="settings"]').click();
    assert.equal(await page.locator('#voicePanel').isVisible(),true);
    await page.locator('.sheet-close').click();
    await page.locator('[data-tab="outfit"]').click();
    await page.locator('button[data-outfit="winter"]').click();
    await page.waitForFunction(()=>document.querySelector('#nightroom').dataset.outfit==='winter');
    assert.match(await page.locator('#nightroom').evaluate(n=>n.style.backgroundImage),/assets\/outfits\/winter\.webp/);
    const portraitSize=await page.locator('button[data-outfit="winter"] img').evaluate(async img=>{await img.decode();return [img.naturalWidth,img.naturalHeight]});
    assert.deepEqual(portraitSize,[1024,1536]);
    for(const width of [320,390,768]){
      await page.setViewportSize({width,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
    }
    await page.setViewportSize({width:390,height:844});
    await page.locator('[data-tab="trading"]').click();
    assert.equal(await page.locator('#tradeDashboard').isVisible(),true);
    for(const width of [320,390,768,1440]){
      await page.setViewportSize({width,height:900});
      assert.equal(await page.locator('#tradePair').isVisible(),true);
      assert.equal(await page.evaluate(()=>document.querySelector('#nightSheet').scrollWidth>document.querySelector('#nightSheet').clientWidth+1),false);
    }
    await page.setViewportSize({width:390,height:844});
    await page.locator('#nightSheet').evaluate(n=>n.scrollTop=0);
    // Let public fetches and image decoding settle before capturing this fixed viewport.
    await page.waitForFunction(()=>!document.querySelector('#tradeRefresh').disabled,{},{timeout:25000});
    await page.locator('.trade-companion img').evaluate(img=>{img.loading='eager'});
    await page.waitForFunction(()=>{const img=document.querySelector('.trade-companion img');return img.complete&&img.naturalWidth>0},{},{timeout:20000});
    assert.equal(await page.locator('#tradeDashboard').isVisible(),true);
    console.log('Live trading source status:',await page.locator('#tradeStatus').innerText());
    assert.deepEqual(badResponses, [], "The live dashboard should not return broken same-origin assets");
    assert.deepEqual(pageErrors, [], "The live dashboard should not throw uncaught browser errors");
    await page.screenshot({ path: "/tmp/hoshi-live-dashboard.png", fullPage: false, animations: "disabled", timeout: 45000 });
    assert.deepEqual(badResponses, [], "The live dashboard should not return broken same-origin assets");
    assert.deepEqual(pageErrors, [], "The live dashboard should not throw uncaught browser errors");
    console.log("PASS — live Render trading dashboard layout, wardrobe selection, core controls, responsive widths, and browser console.");
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

