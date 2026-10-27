/* Hoshi Task 31: fixed-feed source links, safely rendered as text/anchors.
 * No arbitrary URL requests, HTML injection, automatic posts or AI claims.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.HoshiSourceResearch=api;
})(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  const HOSTS={
    world:['www.bbc.com','www.bbc.co.uk'],
    technology:['www.bbc.com','www.bbc.co.uk'],
    science:['www.bbc.com','www.bbc.co.uk'],
    space:['www.nasa.gov','science.nasa.gov']
  };
  let generation=0,controller=null;
  function parseCommand(input){
    const text=String(input||'').trim();
    if(text.length>130)return null;
    const english=text.match(/^(?:(?:latest|today's|fresh)\s+)?(world|technology|tech|science|space)\s+(?:news|updates)(?:\s+(?:about|on)\s+([\w\s-]{1,80}))?\s*[?.!]?$/i);
    if(english){
      return {topic:english[1].toLowerCase()==='tech'?'technology':english[1].toLowerCase(),
        query:(english[2]||'').trim()};
    }
    const roman=text.match(/^(duniya|dunya|technology|science|space)\s+ki\s+(?:taza\s+)?khabr(?:ein|ain)\s*[?.!]?$/i);
    if(roman){
      return {topic:/^(duniya|dunya)$/i.test(roman[1])?'world':roman[1].toLowerCase(),query:''};
    }
    return null;
  }
  function citation(url,topic){
    try{
      const value=new URL(String(url));
      if(value.protocol!=='https:'||value.username||value.password||
         value.port&&value.port!=='443'||!HOSTS[topic].includes(value.hostname))return null;
      return value.origin+value.pathname;
    }catch(_){return null}
  }
  function cancel(){
    generation++;
    if(controller){try{controller.abort()}catch(_){}}
    controller=null;
  }
  function render(container,data,topic){
    container.replaceChildren();
    container.hidden=false;
    const doc=container.ownerDocument;
    const heading=doc.createElement('h3');
    heading.textContent='Fresh source headlines · '+topic;
    container.append(heading);
    const items=Array.isArray(data.items)?data.items.slice(0,5):[];
    let shown=0;
    for(const item of items){
      if(!item||typeof item!=='object')continue;
      const href=citation(item.citation_url,topic);
      const published=Date.parse(item.published_at);
      if(!href||!Number.isFinite(published)||!String(item.title||'').trim())continue;
      const article=doc.createElement('article');
      const link=doc.createElement('a');
      link.href=href;link.target='_blank';link.rel='noopener noreferrer';
      link.textContent=String(item.title).slice(0,180);
      const note=doc.createElement('p');
      note.textContent=String(item.publisher||'Source').slice(0,40)+' · Published '+new Date(published).toISOString();
      const summary=doc.createElement('p');
      summary.textContent=String(item.summary||'').slice(0,260);
      article.append(link,note,summary);
      container.append(article);
      shown++;
    }
    if(!shown){
      const empty=doc.createElement('p');
      empty.textContent='No matching fresh headlines from this fixed source. Try another topic later.';
      container.append(empty);
    }
    const disclaimer=doc.createElement('p');
    disclaimer.textContent='These are source-reported headlines, not independently fact-checked. Open each citation to read the original.';
    container.append(disclaimer);
    return shown;
  }
  async function execute({text,backend,container,onStatus,fetchImpl}){
    const request=parseCommand(text);
    if(!request)return false;
    cancel();
    const id=generation;
    const current=typeof AbortController==='function'?new AbortController():null;
    controller=current;
    const notify=typeof onStatus==='function'?onStatus:()=>{};
    const client=fetchImpl||fetch;
    container.hidden=false;
    container.replaceChildren();
    const loading=container.ownerDocument.createElement('p');
    loading.textContent='Reading public '+request.topic+' headlines…';
    container.append(loading);
    notify('PUBLIC SOURCES · FETCHING');
    const timer=current?setTimeout(()=>current.abort(),9000):null;
    try{
      const params=new URLSearchParams({topic:request.topic,limit:'3'});
      if(request.query)params.set('q',request.query);
      const response=await client(backend+'/api/research/sources?'+params.toString(),
        {method:'GET',credentials:'omit',cache:'no-store',signal:current?current.signal:undefined});
      if(id!==generation)return true;
      if(!response.ok)throw Error('source_unavailable');
      const data=await response.json();
      if(id!==generation)return true;
      if(!data||data.topic!==request.topic||!Array.isArray(data.items))
        throw Error('invalid_source_payload');
      const count=render(container,data,request.topic);
      notify(count?'PUBLIC SOURCES · '+count+' CITED HEADLINES':'PUBLIC SOURCES · NO FRESH MATCH');
    }catch(_){
      if(id===generation){
        container.replaceChildren();
        const error=container.ownerDocument.createElement('p');
        error.textContent='Public source unavailable or timed out. No headlines were invented.';
        container.append(error);
        notify('PUBLIC SOURCES · UNAVAILABLE');
      }
    }finally{
      if(timer!==null)clearTimeout(timer);
      if(id===generation)controller=null;
    }
    return true;
  }
  return Object.freeze({parseCommand,isIntent:text=>!!parseCommand(text),execute,cancel,render,citation});
});
