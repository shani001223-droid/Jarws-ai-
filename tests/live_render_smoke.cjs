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
        if (response.ok && /HOSHI — AI Companion/.test(html) && html.includes('id="nightroom"') && html.includes('assets/outfits/')) return;
        lastError = "Dashboard returned HTTP " + response.status + " or has not published the high-resolution wardrobe revision yet";
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
    await page.screenshot({ path: "/tmp/hoshi-live-dashboard.png", fullPage: true });
    assert.deepEqual(badResponses, [], "The live dashboard should not return broken same-origin assets");
    assert.deepEqual(pageErrors, [], "The live dashboard should not throw uncaught browser errors");
    console.log("PASS — live Render high-resolution wardrobe selection, 1024x1536 portrait, core controls, responsive widths, and browser console.");
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
