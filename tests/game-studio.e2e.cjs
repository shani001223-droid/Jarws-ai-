"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");
const root = path.resolve(__dirname, "..", "game-studio");
const mime = { ".html":"text/html", ".mjs":"text/javascript", ".json":"application/json" };
async function main() {
  const server = http.createServer((req,res)=>{
    const url = new URL(req.url,"http://127.0.0.1");
    const file = path.resolve(root, "." + (url.pathname === "/" ? "/index.html" : url.pathname));
    if (!file.startsWith(root + path.sep)) return res.writeHead(403).end();
    fs.readFile(file,(err,data)=>{
      if(err) return res.writeHead(404).end();
      res.writeHead(200,{"Content-Type":mime[path.extname(file)]||"text/plain","Cache-Control":"no-store"}).end(data);
    });
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  let browser;
  try {
    browser=await chromium.launch({headless:true});
    for(const width of [320,390]) {
      const context=await browser.newContext({viewport:{width,height:720},deviceScaleFactor:2});
      const page=await context.newPage();
      const errors=[], external=[];
      page.on("pageerror",error=>errors.push(error.message));
      page.on("request",request=>{
        if(!request.url().startsWith("http://127.0.0.1:")) external.push(request.url());
      });
      await page.goto("http://127.0.0.1:"+server.address().port+"/index.html",{waitUntil:"networkidle"});
      await page.locator("#level").waitFor({state:"visible"});
      assert.equal(await page.locator("#level").isEnabled(),true);
      assert.match(await page.locator("#status").innerText(),/Level 1: 1 stars/);
      await page.locator("#level").selectOption("6");
      assert.match(await page.locator("#status").innerText(),/Level 6: 3 stars/);
      const board=await page.locator("#board").evaluate(canvas=>({
        width:canvas.width,height:canvas.height,
        sample:Array.from(canvas.getContext("2d").getImageData(175,175,1,1).data)
      }));
      assert.deepEqual([board.width,board.height],[700,700]);
      assert.ok(board.sample[3]>0,"real canvas pixels drawn");
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,"no horizontal overflow");
      assert.deepEqual(errors,[]);
      assert.deepEqual(external,[]);
      await context.close();
    }
    console.log("Task 50 Canvas preview: Chromium 320px/390px passed");
  } finally {
    if(browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
