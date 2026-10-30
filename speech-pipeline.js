(function(root){
 'use strict';
 function split(text){
  let remaining=String(text||'').trim();const parts=[];
  while(remaining){
   const limit=parts.length===0?70:150;
   if(remaining.length<=limit){parts.push(remaining);break;}
   const window=remaining.slice(0,limit);let cut=-1;
   for(const punctuation of ['۔','؟','!','?','،','.']){const at=window.lastIndexOf(punctuation);if(at>=20)cut=Math.max(cut,at+1);}
   if(cut<0){cut=window.lastIndexOf(' ');if(cut<1)cut=limit;}
   parts.push(remaining.slice(0,cut).trim());remaining=remaining.slice(cut).trim();
  }
  return parts;
 }
 // Clip deadlines must settle even if a WebView/network adapter ignores AbortSignal.
 // Aborting one prefetch must not abort its siblings; the shared parent still
 // cancels all child requests when the user presses Stop Speaking.
 function withClipTimeout(parentSignal,timeoutMs,load){
  if(!Number.isFinite(timeoutMs)||timeoutMs<=0)return Promise.reject(new RangeError('Invalid speech clip timeout'));
  if(typeof load!=='function')return Promise.reject(new TypeError('Speech clip loader is required'));
  const controller=new AbortController();
  return new Promise((resolve,reject)=>{
   let settled=false,timer=null;
   const cleanup=()=>{
    if(timer!==null)clearTimeout(timer);
    if(parentSignal)parentSignal.removeEventListener('abort',onParentAbort);
   };
   const settle=(callback,value)=>{
    if(settled)return;
    settled=true;cleanup();callback(value);
   };
   const cancel=reason=>{
    if(!controller.signal.aborted)controller.abort();
    settle(reject,new Error(reason));
   };
   const onParentAbort=()=>cancel('Speech clip cancelled');
   if(parentSignal){
    if(parentSignal.aborted){onParentAbort();return;}
    parentSignal.addEventListener('abort',onParentAbort,{once:true});
   }
   timer=setTimeout(()=>cancel('Speech clip timed out'),timeoutMs);
   try{
    // Both fulfillment and rejection handlers are always attached, so a late
    // loader failure after timeout cannot become an unhandled rejection.
    Promise.resolve(load(controller.signal)).then(
     value=>settle(resolve,value),error=>settle(reject,error)
    );
   }catch(error){settle(reject,error);}
  });
 }
 function queue(parts,load,isCurrent=()=>true){
  const pending=new Map();
  return {get(index){
   if(!isCurrent()||index<0||index>=parts.length)return Promise.resolve(null);
   if(!pending.has(index))pending.set(index,Promise.resolve().then(()=>isCurrent()?load(parts[index]):null).catch(()=>null));
   return pending.get(index);
  }};
 }
 const api={split,queue,withClipTimeout};if(root)root.HoshiSpeechPipeline=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:null);
