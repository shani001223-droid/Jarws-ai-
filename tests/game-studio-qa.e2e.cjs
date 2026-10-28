"use strict";
// Task 53: real Chromium gameplay/crash acceptance on local-only static files.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require("playwright");
const root = path.resolve(__dirname,"..","game-studio");
const mime={".html":"text/html; charset=utf-8",".mjs":"text/javascript; charset=utf-8",".json":"application/json"};
const manifest=JSON.parse(fs.readFileSync(path.join(root,"levels.json"),"utf8"));
const directions=["up","down","left","right"];

function shortestPath(level) {
  const start=level.rows.join("").indexOf("S"),stars=[];
  for(let y=0;y<7;y++)for(let x=0;x<7;x++)if(level.rows[y][x]==="C")stars.push(y*7+x);
  const queue=[{x:start%7,y:Math.floor(start/7),mask:0,path:[]}],seen=new Set();
  for(let i=0;i<queue.length;i++) {
    const state=queue[i],key=[state.x,state.y,state.mask].join(",");
    if(seen.has(key))continue;
    seen.add(key);
    if(level.rows[state.y][state.x]==="E" && state.mask===(1<<stars.length)-1)return state.path;
    for(const [dir,dx,dy] of [["up",0,-1],["down",0,1],["left",-1,0],["right",1,0]]) {
      const x=state.x+dx,y=state.y+dy;
      if(x<0||x>6||y<0||y>6||level.rows[y][x]==="#")continue;
      const starIndex=stars.indexOf(y*7+x);
      queue.push({x,y,mask:starIndex<0?state.mask:state.mask|(1<<starIndex),path:[...state.path,dir]});
    }
    assert.ok(queue.length<5000,"bounded solver");
  }
  throw new Error("unsolvable_"+level.id);
}

async function main() {
  const server=http.createServer((req,res)=>{
    let pathname;
    try{pathname=decodeURIComponent(new URL(req.url,"http://127.0.0.1").pathname);}
    catch{return res.writeHead(400).end();}
    const file=path.resolve(root,"."+(pathname==="/"?"/index.html":pathname));
    if(!file.startsWith(root+path.sep))return res.writeHead(403).end();
    fs.readFile(file,(err,data)=>{
      if(err)return res.writeHead(404).end();
      res.writeHead(200,{"Content-Type":mime[path.extname(file)]||"text/plain","Cache-Control":"no-store"}).end(data);
    });
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  const origin="http://127.0.0.1:"+server.address().port;
  let browser;
  try{
    browser=await chromium.launch({headless:true});
    const context=await browser.newContext({viewport:{width:320,height:720},deviceScaleFactor:2});
    const page=await context.newPage(),errors=[],external=[];
    page.on("pageerror",e=>errors.push(e.message));
    page.on("request",req=>{if(!req.url().startsWith(origin+"/"))external.push(req.url());});
    await page.goto(origin+"/index.html",{waitUntil:"networkidle"});
    assert.equal(await page.locator("#level").isEnabled(),true);
    assert.equal(await page.locator("#save").isChecked(),false,"storage opt-in is off");
    assert.equal(await page.evaluate(()=>localStorage.length),0,"fresh page does not save");
    const started=Date.now();
    for(const level of manifest.levels){
      if(level.id>1)await page.locator("#level").selectOption(String(level.id));
      const pathToWin=shortestPath(level);
      assert.equal(pathToWin.length,level.minimum_moves);
      for(const dir of pathToWin)await page.locator('[data-dir="'+dir+'"]').click();
      assert.match(await page.locator("#status").innerText(),new RegExp("Shabash! Level "+level.id+" complete"));
      assert.equal(await page.locator('[data-dir="up"]').isDisabled(),true,"won board is terminal");
      assert.equal(await page.locator("#save").isChecked(),false);
      assert.equal(await page.evaluate(()=>localStorage.length),0,"no persistence without consent");
      if(level.id<6)assert.equal(await page.locator('#level option[value="'+(level.id+1)+'"]').isEnabled(),true);
    }
    const elapsed=Date.now()-started;
    assert.ok(elapsed<90000,"browser game loop timed out: "+elapsed+"ms");
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    assert.deepEqual(errors,[],"no uncaught gameplay errors");
    assert.deepEqual(external,[],"game never sends external requests");
    await context.close();

    // Corrupt/failed manifest must leave movement and selector disabled.
    const broken=await browser.newContext({viewport:{width:390,height:720}});
    const brokenPage=await broken.newPage(),brokenErrors=[];
    brokenPage.on("pageerror",e=>brokenErrors.push(e.message));
    await brokenPage.route("**/levels.json",route=>route.fulfill({status:200,contentType:"application/json",body:'{"version":"fake","levels":[]}'}));
    await brokenPage.goto(origin+"/index.html",{waitUntil:"networkidle"});
    assert.match(await brokenPage.locator("#status").innerText(),/Local game unavailable/);
    assert.equal(await brokenPage.locator("#level").isDisabled(),true);
    assert.equal(await brokenPage.locator('[data-dir="up"]').isDisabled(),true);
    assert.deepEqual(brokenErrors,[]);
    await broken.close();

    // Browser storage denial is recoverable; no fake saved state.
    const denied=await browser.newContext({viewport:{width:320,height:720}});
    await denied.addInitScript(()=>{
      Object.defineProperty(window,"localStorage",{configurable:true,get(){throw new Error("storage_blocked");}});
    });
    const deniedPage=await denied.newPage(),deniedErrors=[];
    deniedPage.on("pageerror",e=>deniedErrors.push(e.message));
    await deniedPage.goto(origin+"/index.html",{waitUntil:"networkidle"});
    await deniedPage.locator("#save").check();
    assert.equal(await deniedPage.locator("#save").isChecked(),false);
    assert.match(await deniedPage.locator("#status").innerText(),/storage unavailable/i);
    assert.equal(await deniedPage.locator('[data-dir="right"]').isEnabled(),true,"game stays playable");
    assert.deepEqual(deniedErrors,[]);
    await denied.close();
    console.log("Task 53: all 6 Chromium gameplay levels, invalid manifest, blocked storage, no external traffic passed; browser loop "+elapsed+"ms (not phone FPS)");
  } finally {
    if(browser)await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
