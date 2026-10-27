'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
require('../hoshi-speech-input.js');
const speech=globalThis.HoshiSpeechInput;

test('Urdu script and Roman Urdu are preserved for Pakistani Urdu speech',()=>{
  assert.equal(speech.resolve('  میرا نام کیا ہے؟  ').command,'میرا نام کیا ہے؟');
  assert.equal(speech.resolve('Mara nam kya hai').command,'Mara nam kya hai');
});

test('English, Roman and Urdu wake commands work in wake mode',()=>{
  const pairs=[
    ['Hey Hoshi, kal mujhe yaad dilana','kal mujhe yaad dilana'],
    ['hoshi: BTC ka chart dikhao','BTC ka chart dikhao'],
    ['Suno Hoshi mujhe pani yaad dilana','mujhe pani yaad dilana'],
    ['ہے ہوشی، میرا نام بتاؤ','میرا نام بتاؤ'],
    ['ہوشی مجھے ٹائم بتاؤ','مجھے ٹائم بتاؤ'],
    ['Hello Hooshi! kya haal hai','kya haal hai'],
  ];
  for(const [text,expected] of pairs){
    const result=speech.resolve(text,true);
    assert.equal(result.command,expected,text);
    assert.equal(result.wakeDetected,true);
    assert.equal(result.needsWake,false);
  }
});

test('Do not interpret similar non-wake names or embedded wake as microphone command',()=>{
  for(const s of ['aaj Hoshi khush hai','hey hospital mein hoon','hoshiyar bano','hello host karo']){
    const result=speech.resolve(s,true);
    assert.equal(result.needsWake,true,s);
    assert.equal(result.command,'');
  }
});

test('Silence and wake-only commands cannot submit empty cloud request',()=>{
  assert.equal(speech.resolve('  ',true).command,'');
  assert.equal(speech.resolve('Hoshi',true).command,'');
  assert.equal(speech.resolve('Hoshi',true).needsWake,false);
});

test('Recognition alternatives can recover valid Urdu-script wake command',()=>{
  const result=speech.choose(['hehost mera kaam','ہے ہوشی نیا ریمائنڈر لگاؤ','Hey Hoshi, reminder lagao'],true);
  assert.equal(result.command,'نیا ریمائنڈر لگاؤ');
  assert.equal(result.wakeDetected,true);
  assert.equal(speech.choose(['high confidence','low confidence'],false).command,'high confidence');
});

test('Unicode text is normalized without storing or translating it',()=>{
  assert.equal(speech.clean('  hey\u202E hoshi \n hello  '),'hey hoshi hello');
  assert.equal(speech.choose([],true).command,'');
  assert.equal(speech.choose([' ',null],false).command,'');
  assert.ok(speech.clean('a'.repeat(5000)).length<=4000);
});
