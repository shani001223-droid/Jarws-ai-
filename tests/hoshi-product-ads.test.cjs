"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),
 fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const browser={};
vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,"../hoshi-product-ads.js"),"utf8"),
 {window:browser,globalThis:browser});
const studio=browser.HoshiAdStudio;

test("Roman Urdu product-ad commands select the actual backend task",()=>{
 for(const query of [
  "Mere products ke ads bana kar do",
  "Hoshi mera 24K gold facial kit ka ad banao",
  "shampoo ka poster bana do",
  "Make ads for my products",
  "create product advertisement"
 ])assert.equal(studio.isIntent(query),true,query);
});
test("normal chats, research questions and trading orders are not hijacked",()=>{
 for(const query of [
  "hello hoshi", "Why do brands advertise?",
  "how to create an ad", "ads kya hoti hain",
  "open youtube", "buy BTC", "analyze the chart", "kitne orders aaye"
 ])assert.equal(studio.isIntent(query),false,query);
});
test("frontend only requests allowlisted user-initiated API and downloads locally",()=>{
 const source=fs.readFileSync(path.resolve(__dirname,"../hoshi-product-ads.js"),"utf8");
 assert.ok(source.includes("/api/agent/execute"));
 assert.ok(source.includes('task:"create_product_ads"'));
 assert.ok(source.includes("saveAdZip"));
 assert.ok(source.includes("new Blob("));
 for(const bad of ["autoPost(", "autoPublish(", "screenCapture(", "MediaProjection", "paymentKey"])
   assert.equal(source.includes(bad),false);
});
