const test=require('node:test'),assert=require('node:assert/strict'),p=require('../speech-pipeline.js');
test('first meaningful phrase is shorter while preserving the complete reply',()=>{const text=('یہ ایک مکمل اردو جملہ ہے جس کا کوئی لفظ ضائع نہیں ہونا چاہیے۔ ').repeat(20).trim();const parts=p.split(text);assert.ok(parts[0].length<=70);assert.ok(parts.slice(1).every(x=>x.length<=150));assert.equal(parts.join(' '),text);});
test('only requested clip starts; cache avoids duplicate synthesis',async()=>{const calls=[];let resolve;const q=p.queue(['first','second','third'],part=>{calls.push(part);return new Promise(r=>resolve=r)});const first=q.get(0);await Promise.resolve();assert.deepEqual(calls,['first']);assert.equal(q.get(0),first);resolve('audio');assert.equal(await first,'audio');assert.deepEqual(calls,['first']);});
test('cancellation prevents queued and later requests',async()=>{let active=true,calls=0;const q=p.queue(['one','two'],()=>{calls++;return 'blob'},()=>active);const pending=q.get(0);active=false;assert.equal(await pending,null);assert.equal(await q.get(1),null);assert.equal(calls,0);});
test('audio failures resolve to a bounded text fallback',async()=>{const q=p.queue(['one'],()=>Promise.reject(Error('failed')));assert.equal(await q.get(0),null);});
test('a timed-out Urdu prefetch does not abort a different active clip',async()=>{
 const parent=new AbortController();
 const first=p.withClipTimeout(parent.signal,500,async signal=>{
  await new Promise(resolve=>setTimeout(resolve,45));
  assert.equal(signal.aborted,false);
  return 'first mp3';
 });
 const prefetch=p.withClipTimeout(parent.signal,10,signal=>new Promise((_,reject)=>{
  signal.addEventListener('abort',()=>reject(Error('prefetch timed out')),{once:true});
 }));
 await assert.rejects(prefetch,/timed out/);
 assert.equal(parent.signal.aborted,false);
 assert.equal(await first,'first mp3');
});
test('Stop Speaking cancels all outstanding segment fetches',async()=>{
 const parent=new AbortController();
 let stopped=0;
 const load=signal=>new Promise((_,reject)=>{
  signal.addEventListener('abort',()=>{stopped++;reject(Error('stopped'))},{once:true});
 });
 const a=p.withClipTimeout(parent.signal,500,load);
 const b=p.withClipTimeout(parent.signal,500,load);
 parent.abort();
 await assert.rejects(a,/cancelled/);
 await assert.rejects(b,/cancelled/);
 assert.equal(stopped,2);
});
test('an already cancelled speech session never fetches a new clip',async()=>{
 const parent=new AbortController();
 parent.abort();
 let calls=0;
 await assert.rejects(p.withClipTimeout(parent.signal,100,()=>{
  calls++;return Promise.resolve('must not load');
 }),/cancelled/);
 assert.equal(calls,0);
});

test('a non-cooperative WebView loader cannot hang the first Urdu phrase forever',async()=>{
 const parent=new AbortController();
 let signal;
 const start=Date.now();
 await assert.rejects(p.withClipTimeout(parent.signal,15,s=>{
  signal=s;
  return new Promise(()=>{});
 }),/timed out/);
 assert.equal(signal.aborted,true);
 assert.equal(parent.signal.aborted,false);
 assert.ok(Date.now()-start<1000,'deadline should settle even without loader cooperation');
});
test('Stop Speaking settles a non-cooperative loader immediately',async()=>{
 const parent=new AbortController();
 const clip=p.withClipTimeout(parent.signal,1000,()=>new Promise(()=>{}));
 parent.abort();
 await assert.rejects(clip,/cancelled/);
});
test('late success or rejection after a timeout cannot override the settled result',async()=>{
 let finish,fail;
 const success=p.withClipTimeout(null,10,()=>new Promise(resolve=>{finish=resolve}));
 const rejection=p.withClipTimeout(null,10,()=>new Promise((_,reject)=>{fail=reject}));
 await assert.rejects(success,/timed out/);
 await assert.rejects(rejection,/timed out/);
 finish('late audio');
 fail(Error('late provider error'));
 await new Promise(resolve=>setImmediate(resolve));
});
test('synchronous loader errors and invalid deadlines fail safely',async()=>{
 await assert.rejects(p.withClipTimeout(null,50,()=>{throw Error('bad loader')}),/bad loader/);
 await assert.rejects(p.withClipTimeout(null,0,()=>Promise.resolve('audio')),/Invalid speech clip timeout/);
});

test('empty and short messages do not create extra requests',()=>{assert.deepEqual(p.split(' '),[]);assert.deepEqual(p.split('جی، میں یہاں ہوں۔'),['جی، میں یہاں ہوں۔']);});

test('consumed Urdu MP3 blobs can be released without losing the next prefetched clip',async()=>{
 const calls=[];
 const q=p.queue(['first','second','third'],async part=>{
  calls.push(part);
  return {part,bytes:new Uint8Array(1024)};
 });
 const first=await q.get(0);
 assert.equal((await q.get(0)),first,'unreleased clip must share the same cached object');
 const next=q.get(1);
 q.release(0);
 assert.equal((await next).part,'second');
 assert.deepEqual(calls,['first','second']);
 q.clear();
 assert.equal(await q.get(2),null,'closed speech session cannot request more audio');
 assert.deepEqual(calls,['first','second']);
});
test('Stop Speaking closes a queue before deferred prefetch starts',async()=>{
 let calls=0;
 const q=p.queue(['next'],()=>{calls++;return 'audio'});
 const waiting=q.get(0);
 q.clear();
 assert.equal(await waiting,null);
 assert.equal(await q.get(0),null);
 assert.equal(calls,0);
});
test('invalid segment indices do not schedule audio work',async()=>{
 let calls=0;
 const q=p.queue(['one'],()=>{calls++;return 'audio'});
 for(const index of [-1,0.5,NaN,Infinity,1]){
  assert.equal(await q.get(index),null);
 }
 assert.equal(calls,0);
 q.clear();
});
