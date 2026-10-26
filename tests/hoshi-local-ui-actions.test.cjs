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
      return match?{click(){state.tab=match[1];}}:null;
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
  assert.equal(actions.run("scroll_up","",f.doc),true);
  assert.equal(f.sheet.scrollTop,560);
  f.sheet.hidden=true;
  assert.equal(actions.run("scroll_up","",f.doc),false);
});