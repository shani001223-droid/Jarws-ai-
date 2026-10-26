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
  return Object.freeze({valid,run});
});