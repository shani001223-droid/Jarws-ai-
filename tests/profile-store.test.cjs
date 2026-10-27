const test=require('node:test'),assert=require('node:assert/strict'),api=require('../profile-store.js');
const packet={schema:'hoshi-private-memory-v1',entries:[{id:'m001',category:'Preferences',text:'Prefer Roman Urdu',sensitive:false},{id:'m002',category:'Health',text:'Private past symptoms',sensitive:true}]};
test('validates import and rejects duplicate entries',()=>{assert.equal(api.validate(packet).entries.length,2);assert.throws(()=>api.validate({...packet,entries:[packet.entries[0],packet.entries[0]]}));});
test('no AI sharing without explicit consent',()=>{assert.deepEqual(api.context({getItem:()=>JSON.stringify({packet,aiIds:['m001']})},'Urdu'),[]);});
test('sensitive entries are excluded even when selected',()=>{const c=api.context({getItem:()=>JSON.stringify({packet,shareWithAI:true,aiIds:['m001','m002']})},'symptoms');assert.equal(c.length,1);assert.match(c[0],/Roman Urdu/);assert.doesNotMatch(c.join(''),/symptoms/);});
test('corrupt storage fails closed',()=>assert.deepEqual(api.context({getItem:()=>'{broken'},'hi'),[]));
test('credential-like input is rejected',()=>assert.throws(()=>api.validate({...packet,entries:[{...packet.entries[0],text:'ghp_secret'}]})));
