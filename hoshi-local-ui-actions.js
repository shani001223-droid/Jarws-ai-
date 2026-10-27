/* Hoshi-only, user-triggered UI actions. Never submit chat, tap outside the app, or inspect another app. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  root.HoshiLocalUiActions=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const actions=new Set(["tap_chat","tap_settings","type_draft","scroll_up","scroll_down"]);
  function valid(action,payload){
    if(!actions.has(action)||typeof payload!=="string")return false;
    if(action!=="type_draft")return payload==="";
    return payload.length>=1&&payload.length<=240&&payload.trim().length>0&&!/[\u0000-\u001f\u007f]/.test(payload);
  }
  function run(action,payload,doc){
    if(!valid(action,payload)||!doc)return false;
    const tab=name=>doc.querySelector('[data-tab="'+name+'"]');
    if(action==="tap_chat"||action==="tap_settings"){
      const button=tab(action==="tap_chat"?"chat":"settings");
      if(!button)return false;
      button.click();
      // Confirm the actual selected Hoshi tab, not merely a dispatched click.
      return button.getAttribute("aria-selected")==="true";
    }
    if(action==="type_draft"){
      const button=tab("chat"),input=doc.getElementById("commandInput");
      if(!button||!input)return false;
      button.click();
      input.value=payload; // Draft only. Never call requestSubmit(), click Send, or fetch().
      if(typeof input.dispatchEvent==="function"&&typeof Event!=="undefined")
        input.dispatchEvent(new Event("input",{bubbles:true}));
      input.focus();
      // Only compare locally; do not return, log or upload the draft text.
      return button.getAttribute("aria-selected")==="true"&&input.value===payload;
    }
    const sheet=doc.getElementById("nightSheet");
    if(!sheet||sheet.hidden)return false;
    const maximum=Math.max(0,sheet.scrollHeight-sheet.clientHeight);
    const direction=action==="scroll_down"?1:-1;
    const before=sheet.scrollTop;
    sheet.scrollTop=Math.max(0,Math.min(maximum,before+direction*240));
    // At a scroll boundary there was no change; never claim success.
    return Math.abs(sheet.scrollTop-before)>0;
  }

  // Task 24: session-only, metadata-only safety ledger. Never retain a draft,
  // screenshot, app payload, account detail, or conversation in action history.
  const historyActions=new Set([...actions,
    "screen_back","screen_home","screen_swipe_up","screen_swipe_down","screen_screenshot",
    "app_youtube","app_whatsapp","app_telegram","app_browser","app_settings","app_tradingview",
    "control"]);
  const historyOutcomes=new Set(["requested","verified","not_verified","denied",
    "timeout","cancelled","blocked","queued","accepted","paused","resumed","emergency_stop"]);
  function createSafety(maxEntries=20){
    const limit=Number.isInteger(maxEntries)?Math.max(1,Math.min(maxEntries,30)):20;
    let state="running",pending=null;
    const entries=[];
    function record(action,outcome){
      if(!historyActions.has(action)||!historyOutcomes.has(outcome))return false;
      entries.unshift(Object.freeze({action,outcome,at:Date.now()}));
      if(entries.length>limit)entries.length=limit;
      return true;
    }
    function cancel(id,reason="cancelled"){
      if(!pending||pending.id!==id||!["cancelled","timeout","denied"].includes(reason))return false;
      const action=pending.action;pending=null;record(action,reason);return true;
    }
    function begin(action,id){
      if(state!=="running"||pending||!actions.has(action)||
         !Number.isInteger(id)||id<1||id>1000000000)return false;
      pending={action,id};record(action,"requested");return true;
    }
    function finish(id,verified){
      if(!pending||pending.id!==id||typeof verified!=="boolean")return false;
      const action=pending.action;pending=null;
      record(action,verified?"verified":"not_verified");return true;
    }
    function cancelPending(){if(pending)cancel(pending.id,"cancelled");}
    function pause(){
      if(state==="halted")return false;
      if(state==="paused")return true;
      cancelPending();state="paused";record("control","paused");return true;
    }
    function resume(){
      if(state==="running")return false;
      state="running";record("control","resumed");return true;
    }
    function emergencyStop(){
      cancelPending();state="halted";record("control","emergency_stop");return true;
    }
    function snapshot(){return {state,pending:pending?{action:pending.action,id:pending.id}:null,history:entries.slice()};}
    return Object.freeze({
      begin,finish,cancel,pause,resume,emergencyStop,record,snapshot,
      blocked:()=>state!=="running",
      isCurrent:(id,action)=>state==="running"&&!!pending&&pending.id===id&&pending.action===action,
      clearHistory:()=>{entries.length=0;}
    });
  }
  return Object.freeze({valid,run,createSafety});
});