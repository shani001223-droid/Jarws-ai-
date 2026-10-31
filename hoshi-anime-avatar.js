/* Hoshi anime avatar V1 — visual state and bounded idle motion.
 * The current source is an 8-cell portrait expression sprite. This is NOT
 * a layered Live2D rig or phoneme-synced TTS. No camera, microphone, network,
 * storage or accessibility permissions are requested by this controller.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.HoshiAnimeAvatar=api;
})(typeof window!=="undefined"?window:undefined,function(){
  "use strict";
  const EXPRESSIONS=Object.freeze({
    neutral:"caring",caring:"caring",happy:"happy",soft_smile:"caring",
    affectionate:"affectionate",loving:"affectionate",
    listening:"caring",thinking:"thinking",surprised:"excited",
    excited:"excited",sad:"sad",crying:"sad",annoyed:"annoyed",angry:"annoyed",
    shy:"shy",playful:"playful",concerned:"concerned",curious:"thinking"
  });
  function createController(element,options){
    if(!element||!element.dataset)throw new TypeError("Avatar element required");
    const opts=options||{};
    const schedule=opts.schedule||((fn,ms)=>setTimeout(fn,ms));
    const cancel=opts.cancel||((id)=>clearTimeout(id));
    const random=opts.random||Math.random;
    let emotion="caring",listening=false,thinking=false,speaking=false;
    let timer=null,disposed=false,reduced=!!opts.reducedMotion;
    function update(){
      if(disposed)return;
      const state=speaking?"speaking":listening?"listening":thinking?"thinking":"idle";
      element.dataset.emotion=emotion;
      element.dataset.state=state;
      element.dataset.motion=reduced?"reduced":"full";
      element.setAttribute?.("aria-label","Hoshi anime avatar · "+emotion+" · "+state);
    }
    function blinkLoop(){
      if(disposed||reduced)return;
      const delay=2200+Math.floor(Math.max(0,Math.min(1,Number(random())||0))*3400);
      timer=schedule(()=>{
        timer=null;
        if(disposed||reduced)return;
        element.classList.add("hoshi-blink");
        const blinkEnd=schedule(()=>{
          if(disposed)return;
          element.classList.remove("hoshi-blink");
          timer=null;
          blinkLoop();
        },170);
        timer=blinkEnd;
      },delay);
    }
    function setEmotion(name){
      if(disposed)return;
      emotion=EXPRESSIONS[String(name||"").toLowerCase()]||"caring";
      update();
    }
    function setListening(value){listening=!!value;update()}
    function setThinking(value){thinking=!!value;update()}
    function setSpeaking(value){speaking=!!value;update()}
    function setReducedMotion(value){
      reduced=!!value;
      if(timer!==null)cancel(timer);
      timer=null;
      element.classList.remove("hoshi-blink");
      update();blinkLoop();
    }
    function stop(){listening=false;thinking=false;speaking=false;update()}
    function destroy(){disposed=true;if(timer!==null)cancel(timer);timer=null;element.classList.remove("hoshi-blink")}
    update();blinkLoop();
    return {setEmotion,setListening,setThinking,setSpeaking,setReducedMotion,stop,destroy,
      snapshot:()=>({emotion,state:element.dataset.state,reducedMotion:reduced,disposed})};
  }
  return Object.freeze({createController,EXPRESSIONS});
});
