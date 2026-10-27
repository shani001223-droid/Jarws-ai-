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
 function queue(parts,load,isCurrent=()=>true){
  const pending=new Map();
  return {get(index){
   if(!isCurrent()||index<0||index>=parts.length)return Promise.resolve(null);
   if(!pending.has(index))pending.set(index,Promise.resolve().then(()=>isCurrent()?load(parts[index]):null).catch(()=>null));
   return pending.get(index);
  }};
 }
 const api={split,queue};if(root)root.HoshiSpeechPipeline=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:null);
