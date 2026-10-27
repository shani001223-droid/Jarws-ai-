const test=require('node:test');
const assert=require('node:assert/strict');
const research=require('../hoshi-source-research.js');

class Element {
  constructor(tag,doc){this.tagName=tag;this.ownerDocument=doc;this.children=[];this.textContent='';this.hidden=true}
  append(...nodes){this.children.push(...nodes)}
  replaceChildren(...nodes){this.children=[...nodes]}
}
function container(){
  const doc={createElement(tag){return new Element(tag,doc)}};
  return new Element('section',doc);
}
function findAll(node,tag){
  return [...(node.tagName===tag?[node]:[]),...node.children.flatMap(x=>findAll(x,tag))];
}
const sample={topic:'world',items:[{
  title:'<img src=x onerror=alert(1)>',summary:'A reported event',
  publisher:'BBC News',published_at:'2026-10-27T00:00:00+00:00',
  citation_url:'https://www.bbc.com/news/articles/real?tracking=1'
}]};

test('bounded English/Roman Urdu news commands; no generic chat hijack',()=>{
  assert.deepEqual(research.parseCommand('latest world news'),{topic:'world',query:''});
  assert.deepEqual(research.parseCommand('tech news about AI'),{topic:'technology',query:'AI'});
  assert.deepEqual(research.parseCommand('duniya ki taza khabrein'),{topic:'world',query:''});
  assert.deepEqual(research.parseCommand('science ki khabrain'),{topic:'science',query:''});
  for(const text of ['open https://localhost','latest world news and delete data','hello',
                     'world news about '+ 'x'.repeat(81)]){
    assert.equal(research.isIntent(text),false,text);
  }
});

test('citation URLs are exact trusted HTTPS hosts with no tracking query',()=>{
  assert.equal(research.citation('https://www.bbc.com/news/real?x=1#f','world'),
               'https://www.bbc.com/news/real');
  for(const url of ['http://www.bbc.com/news','https://www.bbc.com.evil.test/a',
                    'https://www.bbc.com@127.0.0.1/private','javascript:alert(1)',
                    'https://www.nasa.gov/a']){
    assert.equal(research.citation(url,'world'),null,url);
  }
});

test('renders only safe DOM text and original citation links',()=>{
  const box=container();
  const count=research.render(box,sample,'world');
  assert.equal(count,1);
  const links=findAll(box,'a');
  assert.equal(links.length,1);
  assert.equal(links[0].textContent,'<img src=x onerror=alert(1)>');
  assert.equal(links[0].href,'https://www.bbc.com/news/articles/real');
  assert.equal(links[0].rel,'noopener noreferrer');
  assert.equal(findAll(box,'img').length,0);
  const tampered={topic:'world',items:[{...sample.items[0],citation_url:'https://127.0.0.1/admin'}]};
  assert.equal(research.render(box,tampered,'world'),0);
  assert.equal(findAll(box,'a').length,0);
});

test('fetches only fixed API path with no credentials and reports source attribution',async()=>{
  const box=container(),messages=[];
  const requests=[];
  const fake=async(url,options)=>{
    requests.push({url,options});
    return {ok:true,json:async()=>sample};
  };
  const used=await research.execute({
    text:'world news',backend:'https://jarws-ai-2.onrender.com',container:box,
    fetchImpl:fake,onStatus:s=>messages.push(s)
  });
  assert.equal(used,true);
  assert.equal(requests.length,1);
  assert.equal(requests[0].url,'https://jarws-ai-2.onrender.com/api/research/sources?topic=world&limit=3');
  assert.equal(requests[0].options.method,'GET');
  assert.equal(requests[0].options.credentials,'omit');
  assert.equal(findAll(box,'a').length,1);
  assert.match(messages.at(-1),/CITED HEADLINES/);
});

test('abort suppresses late stale responses and source errors never invent news',async()=>{
  const box=container();
  let release;
  const delayed=new Promise(resolve=>{release=resolve});
  const pending=research.execute({
    text:'world news',backend:'https://jarws-ai-2.onrender.com',container:box,
    fetchImpl:async()=>delayed
  });
  research.cancel();
  release({ok:true,json:async()=>sample});
  await pending;
  assert.equal(findAll(box,'a').length,0);
  const bad=container(),messages=[];
  await research.execute({
    text:'world news',backend:'https://jarws-ai-2.onrender.com',container:bad,
    fetchImpl:async()=>({ok:false}),onStatus:s=>messages.push(s)
  });
  assert.equal(findAll(bad,'a').length,0);
  assert.match(findAll(bad,'p')[0].textContent,/No headlines were invented/);
  assert.match(messages.at(-1),/UNAVAILABLE/);
});
