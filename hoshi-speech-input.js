/* Hoshi voice recognition postprocessor: Hindi/Urdu script is never translated
   or sent to a new provider. Handles recognizer alternatives & Urdu wake word.
   No extra network traffic, audio storage, or phone permissions. */
(function(root){
  'use strict';
  const wake=/^(?:(?:hey|hay|hi|hello|ok|okay|suno|oye|ہے|ہی|اے|اوکے)\s*[,،:!؟.]*\s*)?(?:hoshi|hooshi|hoshee|hushi|ہوشی|هوشي)(?=$|[\s,،:!؟.\-])/iu;
  function clean(value){
    return String(value||'').normalize('NFKC')
      .replace(/[\u0000-\u001F\u007F\u202A-\u202E\u2066-\u2069]/g,' ')
      .replace(/\s+/g,' ').trim().slice(0,4000);
  }
  function resolve(value,requireWake=false){
    const text=clean(value);
    if(!text)return {heard:'',command:'',wakeDetected:false,needsWake:!!requireWake};
    const match=text.match(wake);
    const wakeDetected=!!match;
    if(!requireWake)return {heard:text,command:text,wakeDetected,needsWake:false};
    if(!wakeDetected)return {heard:text,command:'',wakeDetected:false,needsWake:true};
    const command=text.slice(match[0].length).replace(/^[\s,،:!؟.\-]+/u,'').trim();
    return {heard:text,command,wakeDetected:true,needsWake:false};
  }
  function choose(alternatives,requireWake=false){
    const values=Array.isArray(alternatives)?alternatives.slice(0,5):[alternatives];
    const candidates=values.map(v=>resolve(v,requireWake)).filter(v=>v.heard);
    if(requireWake)return candidates.find(v=>v.wakeDetected&&v.command)
      || candidates.find(v=>v.wakeDetected) || candidates[0]
      || resolve('',true);
    return candidates[0]||resolve('',false);
  }
  root.HoshiSpeechInput=Object.freeze({clean,resolve,choose});
})(typeof window!=='undefined'?window:globalThis);
