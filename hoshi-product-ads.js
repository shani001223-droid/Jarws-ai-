/* Hoshi Product Ad Studio — real backend execution, no fake tool results.
   The same flow supports typed or spoken Hoshi commands.
   No background uploads or publishing; the user downloads the files. */
(function(root){
  "use strict";
  function isIntent(message) {
    const s=String(message||"").toLowerCase();
    return /\b(ad|ads|advert|advertisement|poster|creative|promo)\b|اشتہار|ایڈ/i.test(s)
      && /bana|banado|banao|make|create|design|generate|tayyar|ready|chahiye|دو|بناؤ/i.test(s)
      && !/\b(kaise|how to|why|tutorial|explain)\b/i.test(s);
  }
  let activeController=null, activeId=0;
  async function execute({message,backend,container,bridge,onStatus,onSuccess,onError}){
    const turn=++activeId;
    if(activeController)activeController.abort();
    const controller=new AbortController();activeController=controller;
    const timeout=setTimeout(()=>controller.abort(),28000);
    const status=typeof onStatus==="function"?onStatus:()=>{};
    const doc=container.ownerDocument;
    container.hidden=false;container.replaceChildren();
    const title=doc.createElement("h3");title.textContent="Flora · Ad Studio";container.append(title);
    const info=doc.createElement("p");info.textContent="Backend mein asli product ad PNG files ban rahi hain…";container.append(info);
    status("BACKEND · CREATING PRODUCT ADS");
    try{
      const result=await fetch(String(backend).replace(/\/$/,"")+"/api/agent/execute",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({task:"create_product_ads",message:String(message||"")}),
        signal:controller.signal,
      });
      if(root.HoshiDiagnostics)root.HoshiDiagnostics.noteResponse(result);
      const data=await result.json();
      if(turn!==activeId)return;
      if(!result.ok||!data.ok||!data.completed||!data.zip_base64){
        throw Error(typeof data.detail==="string"?data.detail:"Ad generation failed.");
      }
      if(data.zip_base64.length>8_000_000)throw Error("Ad ZIP exceeds mobile download limit.");
      info.textContent="Ready: "+data.products.map(p=>p.product).join(" + ")+".";
      if(data.preview_base64&&data.preview_base64.length<4_000_000){
        const img=doc.createElement("img");
        img.alt="Generated product ad image template (not a product photograph)";
        img.src="data:image/png;base64,"+data.preview_base64;
        container.append(img);
      }
      for(const product of data.products){
        const p=doc.createElement("p");p.className="ad-caption";
        p.textContent=product.product+" · "+product.price+"\n"+product.caption;container.append(p);
      }
      const zipText=data.zip_base64;
      const zipFile="Flora_Product_Ads.zip";
      const button=doc.createElement("button");button.type="button";
      button.textContent="⬇ Download PNG ads + captions (ZIP)";
      button.onclick=()=>{
        try{
          if(bridge&&typeof bridge.saveAdZip==="function"){
            if(bridge.saveAdZip(zipText,zipFile)){
              status("AD ZIP SAVING · CHECK ANDROID DOWNLOADS");return;
            }
          }
          const binary=atob(zipText),bytes=new Uint8Array(binary.length);
          for(let j=0;j<binary.length;j++)bytes[j]=binary.charCodeAt(j);
          const url=URL.createObjectURL(new Blob([bytes],{type:"application/zip"}));
          const a=doc.createElement("a");a.href=url;a.download=zipFile;
          doc.body.append(a);a.click();a.remove();
          setTimeout(()=>URL.revokeObjectURL(url),12000);
          status("AD DOWNLOAD REQUESTED · CHECK DOWNLOADS");
        }catch(_){status("DOWNLOAD ERROR · OPEN HOSHI WEBSITE IN CHROME")}
      };
      container.append(button);
      const note=doc.createElement("p");
      note.textContent="Feed & story PNG, captions and video storyboard included. No actual product photo or rendered video.";
      container.append(note);
      status("BACKEND AD FILES READY");
      if(typeof onSuccess==="function")onSuccess(data);
    }catch(error){
      if(turn!==activeId)return;
      info.textContent=error?.name==="AbortError"
        ?"Ad generation timed out. Dobara command do."
        :"Ad generator error: "+String(error?.message||"Unknown error");
      status("AD GENERATOR FAILED");
      if(typeof onError==="function")onError(error);
    }finally{
      clearTimeout(timeout);
      if(turn===activeId)activeController=null;
    }
  }
  root.HoshiAdStudio=Object.freeze({isIntent,execute});
})(typeof window!=="undefined"?window:globalThis);

