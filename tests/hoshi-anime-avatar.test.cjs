"use strict";
const assert=require("node:assert/strict");
const {createController,EXPRESSIONS}=require("../hoshi-anime-avatar.js");

function mock(){
  const css=new Set();
  const attributes={};
  const el={dataset:{},classList:{
    add:name=>css.add(name),remove:name=>css.delete(name),
    contains:name=>css.has(name)
  },setAttribute:(name,value)=>{attributes[name]=value}};
  const tasks=new Map();let next=0;
  const avatar=createController(el,{
    schedule:(fn,ms)=>{const id=++next;tasks.set(id,{fn,ms});return id},
    cancel:id=>tasks.delete(id),random:()=>0,reducedMotion:false
  });
  return {el,css,tasks,avatar,attributes,runOne:()=>{
    const [id,t]=tasks.entries().next().value;tasks.delete(id);t.fn();return t.ms;
  }};
}

{
  const {el,avatar}=mock();
  assert.equal(el.dataset.state,"idle");
  assert.equal(el.dataset.emotion,"caring");
  avatar.setEmotion("surprised");
  assert.equal(el.dataset.emotion,"excited");
  avatar.setEmotion("dangerous custom HTML");
  assert.equal(el.dataset.emotion,"caring");
  avatar.setEmotion("sad");
  avatar.setListening(true);
  assert.equal(el.dataset.state,"listening");
  avatar.setThinking(true);
  assert.equal(el.dataset.state,"listening","Listening must precede thinking");
  avatar.setSpeaking(true);
  assert.equal(el.dataset.state,"speaking","Speaking must take priority");
  assert.equal(el.dataset.emotion,"sad","Speech must not replace emotion");
  avatar.setSpeaking(false);
  assert.equal(el.dataset.state,"listening");
  avatar.stop();
  assert.equal(el.dataset.state,"idle");
  avatar.destroy();
}
{
  const m=mock();
  assert.equal(m.tasks.size,1,"Blink must schedule one timer");
  assert.equal(m.runOne(),2200);
  assert.equal(m.css.has("hoshi-blink"),true);
  assert.equal(m.runOne(),170);
  assert.equal(m.css.has("hoshi-blink"),false);
  assert.equal(m.tasks.size,1);
  m.avatar.setReducedMotion(true);
  assert.equal(m.tasks.size,0,"Reduced motion must cancel blink");
  assert.equal(m.el.dataset.motion,"reduced");
  m.avatar.setReducedMotion(false);
  assert.equal(m.tasks.size,1);
  m.avatar.destroy();
  assert.equal(m.tasks.size,0,"Destroy must stop timers");
}
{
  const element={dataset:{},setAttribute() {},classList:{add(){},remove(){}}};
  const pending=[];
  const avatar=createController(element,{reducedMotion:true,schedule:fn=>{pending.push(fn);return 1},cancel(){}});
  assert.equal(pending.length,0);
  avatar.setSpeaking(true);avatar.destroy();avatar.setEmotion("happy");
  assert.equal(avatar.snapshot().disposed,true);
  assert.equal(avatar.snapshot().emotion,"caring","Disposed avatars cannot change state");
}
assert.ok(Object.keys(EXPRESSIONS).length>=10);
console.log("PASS — anime expression states, blink timing, speech priority and cleanup");
