"use strict";
const assert=require("node:assert/strict");
const {test}=require("node:test");
require("../hoshi-annotated-chart.js");
const validate=globalThis.HoshiAnnotatedChart.validate;
const step=900000,start=1790000000000-Math.floor(1790000000000%step);
function fixture(){
 const candles=Array.from({length:64},(_,i)=>{
  const time=start+i*step;
  return {time,close_time:time+step-1,open:100+i*.1,high:101+i*.1,
   low:99+i*.1,close:100.5+i*.1,volume_base:10};
 });
 return {version:"spot-annotated-chart-v1",mode:"annotated-spot-chart-research-only",
  symbol:"BTCUSDT",interval:"15m",orders_enabled:false,independently_cross_checked:false,
  fetched_at:1793000000,last_closed_at:candles.at(-1).close_time,
  candles,levels:[{kind:"support",price:100,paper_only:false}],
  confirmed_pivots:[{side:"high",price:101,pivot_at:candles[5].close_time,
   confirmed_at:candles[7].close_time}],paper_decision:"wait"};
}
test("accepts only contiguous closed candles and confirmed pivots",()=>{
 assert.equal(validate(fixture(),"BTCUSDT","15m"),true);
 const a=fixture();a.candles[20].time+=1;
 assert.equal(validate(a,"BTCUSDT","15m"),false);
 const b=fixture();b.confirmed_pivots[0].confirmed_at=b.last_closed_at+1;
 assert.equal(validate(b,"BTCUSDT","15m"),false);
});
test("rejects fake orders, mismatched pair, and unconfirmed paper levels",()=>{
 const a=fixture();a.orders_enabled=true;assert.equal(validate(a,"BTCUSDT","15m"),false);
 assert.equal(validate(fixture(),"ETHUSDT","15m"),false);
 const b=fixture();b.levels.push({kind:"paper_stop",price:98,paper_only:true});
 assert.equal(validate(b,"BTCUSDT","15m"),false);
 const c=fixture();c.levels.push({kind:"support",price:99,paper_only:false});
 assert.equal(validate(c,"BTCUSDT","15m"),false);
});
