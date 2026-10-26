/* HOSHI room activity engine — no framework, no camera, no screen capture.
   Only existing approved Hoshi expression art is used. Flat scene artwork
   remains flat: gestures/activity props are simulations, not a Live2D rig. */
(function (root) {
  "use strict";
  const EMOTIONS = Object.freeze([
    "neutral","happy","excited","playful","shy","affectionate","curious",
    "thinking","confused","worried","sad","crying","annoyed","angry",
    "apologetic","sleepy","caring","concerned"
  ]);
  const ACTIVITIES = Object.freeze(["idle","gaming","reels","dance","sleep"]);
  const MESSAGES = Object.freeze({
    idle:"Hoshi is relaxing in her room",
    gaming:"Gaming scene · visual simulation",
    reels:"Phone / reels scene · visual simulation",
    dance:"Dance scene · generated local melody",
    sleep:"Resting scene · visual simulation"
  });
  function validateEmotion(value) {
    return typeof value==="string" && EMOTIONS.includes(value) ? value : "neutral";
  }
  function validateActivity(value) {
    return typeof value==="string" && ACTIVITIES.includes(value) ? value : "idle";
  }
  function parseActivityCommand(raw) {
    const s=String(raw||"").toLowerCase().trim().replace(/[!?.,]/g," ").replace(/\s+/g," ");
    if(/^(?:hoshi\s+)?(?:game khelo|gaming karo|play games?|gaming mode|پی سی پر گیم کھیلو)$/.test(s))return "gaming";
    if(/^(?:hoshi\s+)?(?:reels dekho|mobile chalao|phone use karo|watch reels|reels mode|ریل دیکھو)$/.test(s))return "reels";
    if(/^(?:hoshi\s+)?(?:dance karo|naacho|nacho|music chalao|dance mode|ڈانس کرو|ناچو)$/.test(s))return "dance";
    if(/^(?:hoshi\s+)?(?:so jao|rest karo|sleep mode|آرام کرو)$/.test(s))return "sleep";
    if(/^(?:hoshi\s+)?(?:room idle|normal ho jao|dance band karo|music band karo|stop music|back to room|بس کرو)$/.test(s))return "idle";
    return null;
  }
  function create(documentRef, options) {
    const doc=documentRef,config=options||{},room=doc.getElementById("nightroom");
    if(!room)return null;
    if(room.querySelector(".room-life"))return null;
    const stage=doc.createElement("div");
    stage.className="room-life";stage.dataset.activity="idle";stage.dataset.conversation="idle";
    stage.setAttribute("aria-hidden","true");
    stage.innerHTML='<div class="life-ambient"></div><div class="life-pc"><span class="life-pc-game"><i></i><i></i><i></i></span></div><div class="life-phone"></div><div class="life-music">♫</div><div class="life-expression" data-emotion="caring"><div class="life-face"></div><div class="life-blink"></div><div class="life-mouth"></div></div><div class="life-activity-tag"></div>';
    room.insertBefore(stage,room.firstChild);
    const controls=doc.createElement("div");controls.className="room-life-controls";
    controls.innerHTML='<button type="button" class="life-toggle" aria-expanded="false" aria-label="Room activities">✦ Room</button><div class="life-menu" hidden><button type="button" data-life-activity="idle">♡ Relax</button><button type="button" data-life-activity="gaming">🎮 Gaming</button><button type="button" data-life-activity="reels">▣ Reels</button><button type="button" data-life-activity="dance">♫ Dance</button><button type="button" data-life-activity="sleep">☾ Rest</button></div>';
    room.appendChild(controls);
    const tip=doc.createElement("div");tip.className="room-life-tip";tip.hidden=true;
    tip.setAttribute("role","status");
    tip.innerHTML='<button type="button" aria-label="Dismiss Hoshi suggestion">×</button><span></span>';
    room.appendChild(tip);tip.querySelector("button").onclick=()=>{tip.hidden=true};
    const face=stage.querySelector(".life-expression"),label=stage.querySelector(".life-activity-tag"),menu=controls.querySelector(".life-menu");
    const toggle=controls.querySelector(".life-toggle");
    let activity="idle",emotion="caring",conversation="idle",audioCtx=null,melodyTimer=null,noteIndex=0,musicWanted=false;
    let suggestions=false,motion=true,lastTipAt=0,disposed=false;
    try{suggestions=localStorage.getItem("hoshiRoomSuggestions")==="true";motion=localStorage.getItem("hoshiRoomMotion")!=="false"}catch(_){}
    room.classList.toggle("life-motion-off",!motion);
    function stopMusic(){
      if(melodyTimer!==null){clearInterval(melodyTimer);melodyTimer=null}
      if(audioCtx){try{audioCtx.close()}catch(_){}audioCtx=null}
    }
    function playTone(){
      if(!audioCtx||audioCtx.state!=="running"||doc.hidden||conversation==="speaking")return;
      const notes=[392,493.88,587.33,523.25,440,392,523.25,659.25];
      const oscillator=audioCtx.createOscillator(),gain=audioCtx.createGain();
      oscillator.type="sine";oscillator.frequency.value=notes[noteIndex++%notes.length];
      gain.gain.setValueAtTime(.0001,audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(.037,audioCtx.currentTime+.025);
      gain.gain.exponentialRampToValueAtTime(.0001,audioCtx.currentTime+.26);
      oscillator.connect(gain);gain.connect(audioCtx.destination);
      oscillator.start();oscillator.stop(audioCtx.currentTime+.28);
    }
    function startMusicFromClick(){
      stopMusic();
      const Context=root.AudioContext||root.webkitAudioContext;
      if(!Context)return false;
      try{
        audioCtx=new Context();
        const response=audioCtx.resume();
        if(response&&response.catch)response.catch(()=>stopMusic());
        playTone();melodyTimer=setInterval(playTone,410);
        return true;
      }catch(_){stopMusic();return false}
    }
    function activate(requested,fromClick){
      if(disposed)return false;
      const next=validateActivity(requested);
      activity=next;stage.dataset.activity=next;
      label.textContent=MESSAGES[next];
      controls.querySelectorAll("[data-life-activity]").forEach(button=>{
        button.setAttribute("aria-pressed",String(button.dataset.lifeActivity===next));
      });
      musicWanted=next==="dance";
      stopMusic();
      if(musicWanted&&fromClick)startMusicFromClick();
      if(typeof config.onActivity==="function")config.onActivity(next);
      return true;
    }
    function setEmotion(value) {
      emotion=validateEmotion(value);
      face.dataset.emotion=emotion;
      room.dataset.lifeEmotion=emotion;
      return emotion;
    }
    function setConversation(value) {
      conversation=["idle","listening","thinking","speaking"].includes(value)?value:"idle";
      stage.dataset.conversation=conversation;
      if(conversation==="speaking"){stopMusic()}
      return conversation;
    }
    function showTip(text){
      if(!suggestions||disposed||doc.hidden)return false;
      const now=Date.now();
      if(now-lastTipAt<10*60*1000)return false;
      tip.querySelector("span").textContent=text;
      lastTipAt=now;tip.hidden=false;return true;
    }
    function onTab(tab){
      if(tab==="trading")showTip("Trading chart dekhein? Hoshi ke analysis tools sirf public market data use karte hain.");
      if(tab==="influencer")showTip("AI Influencer abhi connected nahi hai; content idea Chat mein pooch sakte ho.");
    }
    function setSuggestions(enabled){
      suggestions=!!enabled;tip.hidden=true;
      try{localStorage.setItem("hoshiRoomSuggestions",String(suggestions))}catch(_){}
      return suggestions;
    }
    function setMotion(enabled){
      motion=!!enabled;room.classList.toggle("life-motion-off",!motion);
      try{localStorage.setItem("hoshiRoomMotion",String(motion))}catch(_){}
      return motion;
    }
    function onVisibilityChange(){if(doc.hidden){stopMusic();tip.hidden=true}}
    doc.addEventListener("visibilitychange",onVisibilityChange);
    toggle.onclick=()=>{menu.hidden=!menu.hidden;toggle.setAttribute("aria-expanded",String(!menu.hidden))};
    controls.querySelectorAll("[data-life-activity]").forEach(button=>{
      button.addEventListener("click",()=>{
        activate(button.dataset.lifeActivity,true);menu.hidden=true;toggle.setAttribute("aria-expanded","false");
      });
    });
    activate("idle",false);
    function destroy(){disposed=true;stopMusic();doc.removeEventListener("visibilitychange",onVisibilityChange);stage.remove();controls.remove();tip.remove()}
    return Object.freeze({
      activate,setEmotion,setConversation,parseActivityCommand,onTab,
      setSuggestions,setMotion,destroy,
      getState:()=>({activity,emotion,conversation,suggestions,motion,musicPlaying:melodyTimer!==null}),
    });
  }
  root.HoshiRoomLife=Object.freeze({create,parseActivityCommand,validateEmotion,validateActivity,EMOTIONS,ACTIVITIES});
})(typeof window!=="undefined"?window:globalThis);
