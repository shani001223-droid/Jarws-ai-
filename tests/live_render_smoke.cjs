"use strict";

const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const DASHBOARD_URL = "https://jarws-ai-1.onrender.com/?live-smoke=1";
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
        if (response.ok && /HOSHI — AI Companion/.test(html)) return;
        lastError = "Dashboard returned HTTP " + response.status;
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
    await page.locator("#orb").waitFor({ state: "visible", timeout: 20000 });
    assert.equal(await page.title(), "HOSHI — AI Companion");
    assert.equal(await page.locator("#commandForm").count(), 1);
    assert.equal(await page.locator("#stopSpeakingBtn").count(), 1);
    assert.equal(await page.locator("#memoryToggle").count(), 1);
    assert.equal(await page.locator("[data-ui-action]").count(), 5,
      "The deployed dashboard must include Chat / Voice / Vision / Create / More shortcuts");

    const avatar = await page.locator("#orb .companion-avatar").evaluate(node => {
      const style = getComputedStyle(node);
      return { backgroundImage: style.backgroundImage, backgroundSize: style.backgroundSize };
    });
    assert.match(avatar.backgroundImage, /hoshi-expressions\.webp/,
      "The final HOSHI expression sprite should be applied to the avatar");

    const pageText = await page.locator("body").innerText();
    assert.doesNotMatch(pageText, /\bBTC\b|Bitcoin/i,
      "The dashboard must not show the removed BTC/floating crypto panel");

    for (const viewport of [{ width: 768, height: 1024 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      const overflow = await page.evaluate(() =>
        document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
      );
      assert.equal(overflow, false, "No horizontal overflow at " + viewport.width + "px");
      assert.equal(await page.locator('[data-ui-action="chat"]').isVisible(), true,
        "Hero actions must remain visible at " + viewport.width + "px");
    }

    await page.screenshot({ path: "/tmp/hoshi-live-dashboard.png", fullPage: true });
    assert.deepEqual(badResponses, [], "The live dashboard should not return broken same-origin assets");
    assert.deepEqual(pageErrors, [], "The live dashboard should not throw uncaught browser errors");
    console.log("PASS — live Render dashboard title, core controls, hero shortcuts, expression sprite, crypto-panel removal, responsive widths, and browser console.");
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
