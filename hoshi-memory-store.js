/* Hoshi opt-in, device-local conversation memory.
 * No network calls, no remote database and no credentials in exports.
 * localStorage survives normal app reloads but NOT browser data deletion.
 */
(function(root){
  "use strict";
  const MEMORY_KEY="hoshiConversationMemoryV1";
  const CONSENT_KEY="hoshiMemoryEnabled";
  const MAX_TURNS=12;
  const MAX_CHARS=500;
  function consent(storage){
    try{return storage.getItem(CONSENT_KEY)==="true"}catch(_){return false}
  }
  function safeTurns(input,isSensitive){
    if(!Array.isArray(input))return [];
    return input.filter(item=>item&&
      (item.role==="user"||item.role==="assistant")&&
      typeof item.content==="string"&&
      item.content.trim().length>0&&
      !isSensitive(item.content))
      .slice(-MAX_TURNS)
      .map(item=>({
        role:item.role,
        content:item.content.trim().slice(0,MAX_CHARS),
        at:Number.isFinite(item.at)&&item.at>=0?Math.floor(item.at):0
      }));
  }
  function read(storage,isSensitive){
    if(!consent(storage))return [];
    try{
      const value=JSON.parse(storage.getItem(MEMORY_KEY)||"[]");
      return safeTurns(value,isSensitive);
    }catch(_){return []}
  }
  function save(storage,items,isSensitive){
    if(!consent(storage))return false;
    try{storage.setItem(MEMORY_KEY,JSON.stringify(safeTurns(items,isSensitive)));return true}
    catch(_){return false}
  }
  function setConsent(storage,enabled){
    try{
      storage.setItem(CONSENT_KEY,enabled?"true":"false");
      if(!enabled)storage.removeItem(MEMORY_KEY);
      return true;
    }catch(_){return false}
  }
  function clear(storage){
    try{storage.removeItem(MEMORY_KEY);return true}catch(_){return false}
  }
  function exportJson(storage,isSensitive){
    if(!consent(storage))return null;
    return JSON.stringify({
      format:"hoshi-local-memory",
      version:1,
      exported_at:new Date().toISOString(),
      storage:"device-only",
      turns:read(storage,isSensitive)
    },null,2);
  }
  const api=Object.freeze({MEMORY_KEY,CONSENT_KEY,MAX_TURNS,consent,safeTurns,read,save,setConsent,clear,exportJson});
  root.HoshiMemoryStore=api;
  if(typeof module==="object"&&module.exports)module.exports=api;
})(typeof window!=="undefined"?window:globalThis);
