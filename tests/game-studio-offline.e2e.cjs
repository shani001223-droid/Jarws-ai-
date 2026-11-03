"use strict";
// Task 54: verify the actual packaged HTML via file:// with Chromium offline.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {execFileSync} = require("node:child_process");
const {pathToFileURL} = require("node:url");
const {chromium} = require("playwright");
const root = path.resolve(__dirname, "..");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "game-studio/levels.json"), "utf8"));

function shortestPath(level) {
  const start = level.rows.join("").indexOf("S"), stars = [];
  for(let y=0;y<7;y++)for(let x=0;x<7;x++)if(level.rows[y][x]==="C")stars.push(y*7+x);
  const queue = [{x:start%7,y:Math.floor(start/7),mask:0,path:[]}],seen = new Set();
  for(let i=0;i<queue.length;i++){
    const s=queue[i],key=[s.x,s.y,s.mask].join(",");
    if(seen.has(key))continue;
    seen.add(key);
    if(level.rows[s.y][s.x]==="E" && s.mask===(1<<stars.length)-1)return s.path;
    for(const [dir,dx,dy] of [["up",0,-1],["down",0,1],["left",-1,0],["right",1,0]]){
      const x=s.x+dx,y=s.y+dy;
      if(x<0||x>6||y<0||y>6||level.rows[y][x]==="#")continue;
      const index=stars.indexOf(y*7+x);
      queue.push({x,y,mask:index<0?s.mask:s.mask|(1<<index),path:[...s.path,dir]});
    }
    assert.ok(queue.length<5000,"bounded shortest-path solver");
  }
  throw new Error("unsolvable level "+level.id);
}

async function main(){
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),"hoshi-offline-"));
  let browser;
  try{
    execFileSync("python",["scripts/package_hoshi_game.py","--out",directory],{cwd:root,stdio:"pipe"});
    execFileSync("python",["scripts/package_hoshi_game.py","--verify",
      path.join(directory,"Hoshi-Star-Trail-offline.zip")],{cwd:root,stdio:"pipe"});
    const url=pathToFileURL(path.join(directory,"Hoshi-Star-Trail-offline.html")).href;
    browser=await chromium.launch({headless:true});
    for(const width of [320,390]){
      const context=await browser.newContext({viewport:{width,height:720},deviceScaleFactor:2});
      await context.setOffline(true);
      const page=await context.newPage(),errors=[],network=[];
      page.on("pageerror",error=>errors.push(error.message));
      page.on("request",request=>{if(!request.url().startsWith("file://"))network.push(request.url());});
      await page.route(/^https?:/,route=>route.abort());
      await page.goto(url,{waitUntil:"load"});
      assert.equal(await page.locator("#level").isEnabled(),true,"file:// game must initialize offline");
      assert.equal(await page.locator("#save").isChecked(),false,"local saving defaults OFF");
      assert.match(await page.locator("#status").innerText(),/Level 1:/);
      const levels=width===320?manifest.levels:manifest.levels.slice(0,1);
      for(const level of levels){
        if(level.id>1)await page.locator("#level").selectOption(String(level.id));
        const moves=shortestPath(level);
        assert.equal(moves.length,level.minimum_moves);
        for(const direction of moves)await page.locator('[data-dir="'+direction+'"]').click();
        assert.match(await page.locator("#status").innerText(),
          new RegExp("Shabash! Level "+level.id+" complete"));
      }
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      assert.deepEqual(errors,[],"no file:// JavaScript errors");
      assert.deepEqual(network,[],"offline package must never request network");
      await context.close();
    }
    console.log("Task 54: real offline file:// HTML, six-level Chromium play, 320/390px, no network passed");
  }finally{
    if(browser)await browser.close();
    fs.rmSync(directory,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
