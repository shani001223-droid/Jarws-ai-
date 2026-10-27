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
        const knowledge = await fetch("https://jarws-ai-2.onrender.com/learn", { signal: AbortSignal.timeout(15000) });
        const index = await knowledge.json();
        if (!knowledge.ok || index.version !== "hoshi-trading-knowledge-v2" || index.lessons?.length !== 11) {
          throw new Error("Trading V2 knowledge is not yet deployed");
        }
        const response = await fetch(DASHBOARD_URL, { signal: AbortSignal.timeout(15000) });
        const html = await response.text();
        if (response.ok && /HOSHI — AI Companion/.test(html) && html.includes('id="hoshiEnergy"') && html.includes('id="focusModeToggle"') && html.includes('id="tradeDashboard"') && html.includes('id="clientDiagnostics"')) return;
        lastError = "Dashboard returned HTTP " + response.status + " or has not published the client diagnostics revision yet";
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
  const history = await fetch("https://jarws-ai-2.onrender.com/history", { signal: AbortSignal.timeout(15000) });
  const timeline = await history.json();
  assert.equal(history.status, 200);
  assert.equal(timeline.id, "history");
  assert.equal(timeline.orders_enabled, false);
  assert.match(timeline.content, /1602/);
  const unsupported = await fetch("https://jarws-ai-2.onrender.com/confluence_score?symbol=SOLUSDT", { signal: AbortSignal.timeout(15000) });
  assert.equal(unsupported.status, 422, "V2 rejects unsupported pairs before source access");
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
    assert.equal(await page.locator('#hoshiEnergy').isVisible(),true);
    assert.equal(await page.locator('[data-tab="chat"]').isVisible(),false);
    assert.equal(await page.locator('[data-tab="outfit"]').isVisible(),false);
    await page.waitForFunction(()=>document.querySelector('#core-canvas').width>0);
    assert.equal((await page.locator('#nightroom').evaluate(n=>getComputedStyle(n).backgroundImage)).includes('url('),false);
    await page.locator('[data-tab="settings"]').click();
    assert.equal(await page.locator('#voicePanel').isVisible(),true);
    await page.waitForFunction(()=>Boolean(window.HoshiDiagnostics&&window.HoshiDiagnostics.snapshot().last_api_response),{},{timeout:20000});
    await page.locator('#clientDiagnostics summary').click();
    // details.toggle is queued: wait for its report update before parsing.
    await page.waitForFunction(()=>{try{return Boolean(JSON.parse(document.querySelector('#clientDiagnosticReport').textContent).last_api_response)}catch(_){return false}});
    const safeReport=JSON.parse(await page.locator('#clientDiagnosticReport').innerText());
    assert.equal(safeReport.scope,'this_page_only');
    assert.match(safeReport.last_api_response.request_id,/^[0-9a-f-]{36}$/);
    await page.locator('#clearDiagnosticReport').click();
    assert.deepEqual(await page.evaluate(()=>window.HoshiDiagnostics.snapshot().events),[]);
    await page.locator('#clientDiagnostics summary').click();

    // Existing tools are available through Settings; keep the approved core
    // and never restore the removed wardrobe as a default-screen assertion.
    await page.locator('#focusModeToggle').click();
    assert.equal(await page.locator('.nightroom.focus-mode').count(),0);
    await page.locator('.sheet-close').click();
    assert.equal(await page.locator('[data-tab="chat"]').isVisible(),true);
    assert.equal(await page.locator('#hoshiEnergy').isVisible(),true);
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
    console.log("PASS — live Render V2 lessons/history, approved core, Settings tools, trading layout, responsive widths and browser console.");
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});


