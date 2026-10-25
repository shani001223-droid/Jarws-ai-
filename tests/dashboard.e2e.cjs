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
      // Keep this smoke test deterministic without installing a real service worker.
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

    await page.goto(url, { waitUntil: "domcontentloaded" });
    assert.equal(await page.title(), "HOSHI — AI Companion");
    await page.waitForFunction(() => document.querySelector("#connection")?.textContent === "AI KEYS CONFIGURED", undefined, { timeout: 5000 });

    // Local command path should work without a cloud call.
    await page.locator('[data-cmd="what time is it"]').click();
    await page.waitForFunction(() => /Abhi waqt|The time is/.test(document.querySelector("#reply")?.textContent || ""), undefined, { timeout: 3000 });

    // Cloud chat should display the reply and change the expression.
    await page.locator("#commandInput").fill("How can you help me?");
    await page.locator('#commandForm button[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector("#reply")?.textContent === "I can help you plan, explain, and create.", undefined, { timeout: 5000 });
    assert.equal(await page.locator("#orb").getAttribute("data-emotion"), "affectionate");
    const firstRequest = apiMessages.find(item => item.message === "How can you help me?");
    assert.ok(firstRequest, "Expected the chat to reach the mocked cloud API");
    assert.ok(!(firstRequest.context || []).includes("user: How can you help me?"),
      "Current user message must not be duplicated in recent context");
    assert.ok((await page.locator("#chatHistory").innerText()).includes("How can you help me?"),
      "The saved conversation should appear in history");

    // A delayed earlier request must not overwrite the newer reply.
    const oldRequest = page.waitForRequest(request =>
      request.url().endsWith("/api/assistant") && (request.postData() || "").includes("older slow request"),
      { timeout: 3000 });
    await page.locator("#commandInput").fill("older slow request");
    await page.locator('#commandForm button[type="submit"]').click();
    await oldRequest;
    await page.locator("#commandInput").fill("newer fast request");
    await page.locator('#commandForm button[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector("#reply")?.textContent === "NEW RESPONSE", undefined, { timeout: 5000 });
    await page.waitForTimeout(650);
    assert.equal(await page.locator("#reply").innerText(), "NEW RESPONSE",
      "A late response from an earlier request must not replace the latest reply");

    // Memory off should disclose the state and clear local conversation history.
    await page.locator("#memoryToggle").click();
    assert.match(await page.locator("#chatHistory").innerText(), /Local memory is off/);
    assert.equal(await page.evaluate(() => localStorage.getItem("hoshiConversationMemoryV1")), null,
      "Turning memory off should clear stored conversation history");

    // Unsupported native bridge action should fail clearly instead of throwing.
    await page.locator("#screenshotQuickBtn").click();
    assert.match(await page.locator("#status").innerText(), /NEEDS THE HOSHI ANDROID APP/);

    assert.deepEqual(pageErrors, [], "Dashboard should not throw uncaught browser errors");
    console.log("PASS — dashboard loaded; local command, cloud chat, emotion, context privacy, request ordering, memory toggle, and graceful fallback worked.");
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
