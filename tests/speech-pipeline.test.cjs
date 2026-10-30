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
 await assert.rejects(prefetch,/prefetch timed out/);
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
 await assert.rejects(a,/stopped/);
 await assert.rejects(b,/stopped/);
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

test('empty and short messages do not create extra requests',()=>{assert.deepEqual(p.split(' '),[]);assert.deepEqual(p.split('جی، میں یہاں ہوں۔'),['جی، میں یہاں ہوں۔']);});
