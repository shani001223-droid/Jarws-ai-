(function(root){
  'use strict';
  const KEY='hoshiPrivateProfileV1';
  function validate(input){
    if(!input||input.schema!=='hoshi-private-memory-v1'||!Array.isArray(input.entries)||input.entries.length>150)throw new Error('Invalid Hoshi memory file');
    const ids=new Set();
    const entries=input.entries.map(item=>{
      if(!item||typeof item.id!=='string'||!/^m\d{3}$/.test(item.id)||ids.has(item.id)||typeof item.text!=='string'||item.text.length>3000||typeof item.category!=='string'||item.category.length>100||typeof item.sensitive!=='boolean')throw new Error('Invalid memory entry');
      if(/(?:sk-proj-|sk_live_|ghp_|github_pat_|AIza|\b\d{8,12}:[A-Za-z0-9_-]{30,})/.test(item.text))throw new Error('Remove credentials before importing');
      ids.add(item.id);
      return {id:item.id,text:item.text,category:item.category,sensitive:item.sensitive,status:String(item.status||'remembered').slice(0,150)};
    });
    return {schema:input.schema,exported_at:String(input.exported_at||'').slice(0,30),entries};
  }
  function context(storage,message){
    try{
      const stored=JSON.parse(storage.getItem(KEY)||'null');
      if(!stored||stored.shareWithAI!==true||!Array.isArray(stored.aiIds))return [];
      const packet=validate(stored.packet);
      const words=String(message||'').toLowerCase().split(/\W+/).filter(w=>w.length>3);
      return packet.entries.filter(e=>!e.sensitive&&stored.aiIds.includes(e.id)).map(e=>({e,score:words.filter(w=>e.text.toLowerCase().includes(w)).length})).sort((a,b)=>b.score-a.score).slice(0,4).map(({e})=>'user: Remembered profile ('+e.status+'): '+e.text.slice(0,420));
    }catch(_){return []}
  }
  const api={KEY,validate,context};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.HoshiProfile=api;
})(typeof window!=='undefined'?window:null);
