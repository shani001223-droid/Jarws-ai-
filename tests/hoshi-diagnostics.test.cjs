'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { create } = require('../hoshi-diagnostics.js');
const ID = 'a73a7fe6-5dbe-41a3-98f8-434ce5abb008';
const response = (id=ID,status=200) => ({ status, headers: { get: () => id }, url: 'https://private.invalid/?key=URL-SECRET' });

test('records only valid generated request IDs and response status', () => {
  const sdk = create({now:()=>123});
  assert.equal(sdk.noteResponse(response(ID.toUpperCase(),503)),true);
  const report=sdk.snapshot();
  assert.deepEqual(report.last_api_response,{request_id:ID,status:503,at_ms:123});
  assert.deepEqual(report.last_failed_api_response,report.last_api_response);
  assert.equal(JSON.stringify(report).includes('URL-SECRET'),false);
});

test('keeps last failed trace while later successful response arrives', () => {
  const sdk=create(); sdk.noteResponse(response(ID,502));
  const second='00000000-0000-4000-8000-000000000002';sdk.noteResponse(response(second,200));
  assert.equal(sdk.snapshot().last_api_response.request_id,second);
  assert.equal(sdk.snapshot().last_failed_api_response.request_id,ID);
});

test('invalid IDs and malformed responses cannot inject secret/log data', () => {
  const sdk=create();
  for(const invalid of ['HEADER-SECRET\nnew log','x'.repeat(50000),'',null,'00000000-0000-0000-0000-000000000000'])assert.equal(sdk.noteResponse(response(invalid)),false);
  assert.equal(sdk.noteResponse({headers:{get(){throw new Error('SENSITIVE')}}}),false);
  assert.equal(sdk.noteResponse(null),false);
  assert.equal(sdk.snapshot().last_api_response,null);
});

test('browser errors retain allowlisted source positions, never messages or URLs', () => {
  const sdk=create({now:()=>456});
  sdk.record('uncaught_error',{filename:'https://example.test/path/index.html?token=QUERY-SECRET',lineno:18,colno:4,message:'MESSAGE-SECRET',error:{stack:'STACK-SECRET'}});
  assert.deepEqual(sdk.snapshot().events[0],{kind:'uncaught_error',script:'index.html',line:18,column:4,at_ms:456});
  assert.doesNotMatch(JSON.stringify(sdk.snapshot()),/SECRET|example\.test|token|stack|message/);
});

test('unknown sources and invalid source positions are discarded', () => {
  const sdk=create();sdk.record('uncaught_error',{filename:'https://secret/path/private.js',lineno:-1,colno:99999999999});
  const event=sdk.snapshot().events[0];assert.equal(event.script,'unknown');assert.equal(event.line,0);assert.equal(event.column,0);
  assert.doesNotMatch(JSON.stringify(event),/secret|private/);
});

test('never reads rejection reasons, error objects or message getters', () => {
  const sdk=create(); const sensitive={};
  for(const key of ['reason','message','error'])Object.defineProperty(sensitive,key,{get(){throw new Error('Must not inspect '+key)}});
  assert.equal(sdk.record('unhandled_rejection',sensitive),true);
  assert.equal(sdk.record('uncaught_error',sensitive),true);
});

test('bounds retained events while preserving aggregate counts', () => {
  const sdk=create();for(let i=0;i<10000;i++)sdk.record('request_failed',{message:'UNTRUSTED'});
  assert.equal(sdk.snapshot().events.length,10);assert.equal(sdk.snapshot().counts.request_failed,10000);
  assert.equal(sdk.record('USER-SUPPLIED-SECRET'),false);assert.equal(sdk.snapshot().counts['USER-SUPPLIED-SECRET'],undefined);
});

test('snapshots cannot mutate internal records', () => {
  const sdk=create();sdk.noteResponse(response());sdk.record('uncaught_error');const report=sdk.snapshot();
  report.events[0].script='INJECTION';report.last_api_response.request_id='INJECTION';report.counts.uncaught_error=999;
  assert.equal(sdk.snapshot().events[0].script,'unknown');assert.equal(sdk.snapshot().last_api_response.request_id,ID);assert.equal(sdk.snapshot().counts.uncaught_error,1);
});

test('clear removes only in-memory diagnostics', () => {
  const sdk=create();sdk.noteResponse(response());sdk.record('request_failed');sdk.clear();
  assert.deepEqual(sdk.snapshot(),{version:1,scope:'this_page_only',last_api_response:null,last_failed_api_response:null,counts:{},events:[]});
});

test('listeners are installed once and capture categories without uploading', () => {
  const handlers={},host={addEventListener(k,fn){assert.equal(handlers[k],undefined);handlers[k]=fn},fetch(){throw new Error('Must not upload')}};
  const sdk=create();sdk.install(host);sdk.install(host);handlers.error({filename:'index.html',lineno:1});handlers.unhandledrejection({reason:'PRIVATE'});
  assert.equal(sdk.snapshot().counts.uncaught_error,1);assert.equal(sdk.snapshot().counts.unhandled_rejection,1);assert.doesNotMatch(JSON.stringify(sdk.snapshot()),/PRIVATE/);
});

test('page instances remain isolated and cancellation is identified separately', () => {
  const one=create(),two=create();one.noteResponse(response());one.record('request_cancelled');
  assert.equal(one.snapshot().counts.request_cancelled,1);assert.equal(two.snapshot().last_api_response,null);assert.deepEqual(two.snapshot().events,[]);
});

test('compact export fits the existing Android 2000-character clipboard contract',()=>{
  const sdk=create();sdk.noteResponse(response(ID,503));
  for(const kind of ['unhandled_rejection','request_failed','request_cancelled'])for(let i=0;i<100;i++)sdk.record(kind);
  for(let i=0;i<10;i++)sdk.record('uncaught_error',{filename:'hoshi-product-ads.js',lineno:1000000,colno:1000000});
  const compact=JSON.stringify(sdk.snapshot());assert.ok(compact.length<=2000);
  assert.equal(JSON.parse(compact).events.length,10);
});
