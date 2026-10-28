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
      assert.match(await page.locator("#status").innerText(),/Level 1: 1 stars baqi/);
      assert.equal(await page.locator("#level option[value=6]").isDisabled(),true,"locked levels cannot be selected");
      const animate=page.locator("#animate");
      assert.equal(await animate.isEnabled(),true,"animation is available only by opt-in");
      const before=await page.locator("#board").evaluate(canvas=>canvas.toDataURL());
      await animate.click();
      assert.equal(await animate.getAttribute("aria-pressed"),"true");
      await page.waitForTimeout(180);
      const after=await page.locator("#board").evaluate(canvas=>canvas.toDataURL());
      assert.notEqual(after,before,"original star/portal artwork animates on request");
      await animate.click();
      assert.equal(await animate.getAttribute("aria-pressed"),"false");
      const board=await page.locator("#board").evaluate(canvas=>({
        width:canvas.width,height:canvas.height,
        sample:Array.from(canvas.getContext("2d").getImageData(175,175,1,1).data)
      }));
      assert.deepEqual([board.width,board.height],[700,700]);
      assert.ok(board.sample[3]>0,"real canvas pixels drawn");
      const save=page.locator("#save");
      await save.check();
      assert.equal(await page.evaluate(()=>Boolean(localStorage.getItem("hoshi-star-trail-progress-v1"))),true);
      const tap=async(direction,count=1)=>{for(let n=0;n<count;n++)await page.locator('[data-dir="'+direction+'"]').click();};
      await tap("up");
      assert.match(await page.locator("#status").innerText(),/0 moves/,"wall must not consume moves");
      await tap("down",2);
      await tap("right",2);
      assert.match(await page.locator("#status").innerText(),/0 stars baqi/);
      await page.locator("#undo").click();
      assert.match(await page.locator("#status").innerText(),/1 stars baqi/);
      await tap("right");
      await tap("up",2);
      await tap("right",2);
      assert.match(await page.locator("#status").innerText(),/Shabash! Level 1 complete/);
      assert.equal(await page.locator("#level option[value=2]").isEnabled(),true);
      assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem("hoshi-star-trail-progress-v1")).highest_unlocked),2);
      await page.locator("#level").selectOption("2");
      await page.keyboard.press("ArrowDown");
      assert.match(await page.locator("#status").innerText(),/1 moves/);
      await page.locator("#pause").click();
      assert.equal(await page.locator('[data-dir="right"]').isDisabled(),true);
      await page.locator("#pause").click();
      await page.locator("#restart").click();
      assert.match(await page.locator("#status").innerText(),/0 moves/);
      await save.uncheck();
      assert.equal(await page.evaluate(()=>localStorage.getItem("hoshi-star-trail-progress-v1")),null);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,"no horizontal overflow");
      assert.deepEqual(errors,[]);
      assert.deepEqual(external,[]);
      await context.close();
    }
    const reduced=await browser.newContext({viewport:{width:320,height:720},reducedMotion:"reduce"});
    const reducedPage=await reduced.newPage();
    const reducedErrors=[];
    reducedPage.on("pageerror",error=>reducedErrors.push(error.message));
    await reducedPage.goto("http://127.0.0.1:"+server.address().port+"/index.html",{waitUntil:"networkidle"});
    assert.equal(await reducedPage.locator("#level").isEnabled(),true);
    assert.equal(await reducedPage.locator("#animate").isDisabled(),true,"OS reduced motion prevents animation");
    assert.equal(await reducedPage.locator("#animate").getAttribute("aria-pressed"),"false");
    assert.deepEqual(reducedErrors,[]);
    await reduced.close();
    console.log("Tasks 50-52 playable offline Canvas, opt-in saves and animation: Chromium 320px/390px/reduced-motion passed");
  } finally {
    if(browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
