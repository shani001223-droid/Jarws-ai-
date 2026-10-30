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
 // Each MP3 clip has its own timeout/abort signal. A slow prefetch must not
 // cancel a different clip that is already playing. Stop Speaking still
 // propagates through the shared parent signal to every outstanding clip.
 async function withClipTimeout(parentSignal,timeoutMs,load){
  const controller=new AbortController();
  const abort=()=>controller.abort();
  if(parentSignal){
   if(parentSignal.aborted)abort();
   else parentSignal.addEventListener('abort',abort,{once:true});
  }
  const timer=setTimeout(abort,timeoutMs);
  try{
   if(controller.signal.aborted)throw new Error('Speech clip cancelled');
   return await load(controller.signal);
  }finally{
   clearTimeout(timer);
   if(parentSignal)parentSignal.removeEventListener('abort',abort);
  }
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
