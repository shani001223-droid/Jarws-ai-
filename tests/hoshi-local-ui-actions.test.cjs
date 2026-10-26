"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const actions=require("../hoshi-local-ui-actions.js");
function fakeDom(){
  const state={tab:"settings",submitted:0,focused:false,events:0};
  const input={value:"",focus(){state.focused=true;},dispatchEvent(){state.events++;}};
  const sheet={hidden:false,scrollTop:300,scrollHeight:1200,clientHeight:400};
  const doc={
    querySelector(selector){
      const match=selector.match(/^\[data-tab="(chat|settings)"\]$/);
      return match?{click(){state.tab=match[1];},getAttribute(name){return name==="aria-selected"?String(state.tab===match[1]):null;}}:null;
    },
    getElementById(id){return id==="commandInput"?input:id==="nightSheet"?sheet:null;}
  };
  return {state,input,sheet,doc};
}
test("rejects unknown, unsafe or oversized actions",()=>{
  for(const a of ["tap_anywhere","type_password","send_message","tap","delete","open_app"]){
    assert.equal(actions.valid(a,""),false);
  }
  for(const text of [""," ","x".repeat(241),"line\nbreak","null\u0000byte"]){
    assert.equal(actions.valid("type_draft",text),false);
  }
  assert.equal(actions.valid("tap_chat","payload"),false);
  assert.equal(actions.valid("scroll_down","payload"),false);
  assert.equal(actions.valid("type_draft","Salam Hoshi"),true);
});
test("taps only Hoshi's known tabs",()=>{
  const f=fakeDom();
  assert.equal(actions.run("tap_chat","",f.doc),true);
  assert.equal(f.state.tab,"chat");
  assert.equal(actions.run("tap_settings","",f.doc),true);
  assert.equal(f.state.tab,"settings");
  assert.equal(actions.run("tap_unknown","",f.doc),false);
});
test("typing edits only local draft without submission",()=>{
  const f=fakeDom();
  assert.equal(actions.run("type_draft","Roman Urdu: chart analyze kro",f.doc),true);
  assert.equal(f.state.tab,"chat");
  assert.equal(f.input.value,"Roman Urdu: chart analyze kro");
  assert.equal(f.state.focused,true);
  assert.equal(f.state.submitted,0);
});
test("scroll clamps to the visible Hoshi sheet",()=>{
  const f=fakeDom();
  assert.equal(actions.run("scroll_down","",f.doc),true);
  assert.equal(f.sheet.scrollTop,540);
  assert.equal(actions.run("scroll_down","",f.doc),true);
  assert.equal(f.sheet.scrollTop,780);
  assert.equal(actions.run("scroll_down","",f.doc),true);
  assert.equal(f.sheet.scrollTop,800);
  assert.equal(actions.run("scroll_down","",f.doc),false,"Boundary must not report movement");
  assert.equal(actions.run("scroll_up","",f.doc),true);
  assert.equal(f.sheet.scrollTop,560);
  f.sheet.hidden=true;
  assert.equal(actions.run("scroll_up","",f.doc),false);
});
test("rejects false-success when a tab ignores a click or a draft cannot be set",()=>{
  const f=fakeDom();
  f.doc.querySelector=()=>({click(){},getAttribute(){return "false";}});
  assert.equal(actions.run("tap_chat","",f.doc),false);
  assert.equal(actions.run("type_draft","Hello",f.doc),false);
  const g=fakeDom();
  g.sheet.scrollTop=0;
  assert.equal(actions.run("scroll_up","",g.doc),false);
});


test("Task 24 safety: bounded history never records draft or arbitrary labels",()=>{
  const s=actions.createSafety(3);
  assert.equal(s.begin("type_draft",1),true);
  assert.equal(s.finish(1,true),true);
  assert.equal(s.record("custom secret password","verified"),false);
  assert.equal(s.record("app_whatsapp","accepted"),true);
  assert.equal(s.record("screen_back","queued"),true);
  const h=s.snapshot().history;
  assert.equal(h.length,3);
  assert.deepEqual(h.map(x=>x.action),["screen_back","app_whatsapp","type_draft"]);
  assert.equal(JSON.stringify(h).includes("password"),false);
  h.pop();
  assert.equal(s.snapshot().history.length,3,"History is a copy");
});
test("Task 24 safety: pause cancels pending and blocks actions until explicit resume",()=>{
  const s=actions.createSafety();
  assert.equal(s.begin("tap_chat",12),true);
  assert.equal(s.pause(),true);
  assert.equal(s.blocked(),true);
  assert.equal(s.isCurrent(12,"tap_chat"),false);
  assert.equal(s.finish(12,true),false,"Late result cannot count as verified");
  assert.equal(s.begin("scroll_up",13),false);
  assert.equal(s.resume(),true);
  assert.equal(s.begin("scroll_up",13),true);
  assert.equal(s.finish(13,false),true);
  assert.equal(s.snapshot().history[0].outcome,"not_verified");
});
test("Task 24 safety: emergency stop stays latched until explicit resume",()=>{
  const s=actions.createSafety();
  assert.equal(s.begin("type_draft",77),true);
  assert.equal(s.emergencyStop(),true);
  assert.equal(s.snapshot().state,"halted");
  assert.equal(s.isCurrent(77,"type_draft"),false);
  assert.equal(s.finish(77,true),false);
  assert.equal(s.begin("tap_chat",78),false);
  assert.equal(s.pause(),false);
  assert.equal(s.resume(),true);
  assert.equal(s.begin("tap_chat",78),true);
  assert.equal(s.cancel(77,"timeout"),false);
  assert.equal(s.cancel(78,"timeout"),true);
  assert.equal(s.snapshot().history.some(x=>x.outcome==="emergency_stop"),true);
  s.clearHistory();
  assert.deepEqual(s.snapshot().history,[]);
  assert.equal(s.snapshot().state,"running");
});
test("Task 24 safety: unknown actions, request IDs and outcomes fail closed",()=>{
  const s=actions.createSafety();
  for(const id of [-1,0,1.5,1000000001,"2"]){
    assert.equal(s.begin("tap_chat",id),false);
  }
  assert.equal(s.begin("send_message",1),false);
  assert.equal(s.record("control","payload"),false);
  assert.equal(s.begin("tap_chat",1),true);
  assert.equal(s.begin("tap_settings",2),false);
  assert.equal(s.finish(2,true),false);
  assert.equal(s.finish(1,"true"),false);
  assert.equal(s.finish(1,true),true);
});
