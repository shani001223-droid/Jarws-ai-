/* Hoshi task intent routing: no network and no simulated execution.
 * The backend /api/agent/route remains the authority for supported workers.
 * This client classifier only prevents unsupported tasks being mistaken for chat.
 */
(function(root){
 "use strict";
 const CREATE=/\b(?:bana\w*|make|build|create|generate|design|develop|tayyar|produce|render|likh\w*)\b/i;
 const EXPLAIN=/\b(?:kaise|how to|how do|tutorial|explain|samjhao|seekha\w*|guide|meaning|kya hai|what is)\b/i;
 const ANIME=/\b(?:anime|episodes?|animated series|cartoon series)\b/i;
 const GAME=/\b(?:games?|gameplay|playable|mobile game|apk game)\b/i;
 const TRADING=/\b(?:btc|bitcoin|eth|ethereum|crypto|trading|chart|candles?)\b/i;
 const TECHNICAL=/\b(?:analy[sz]\w*|mark\w*|support|resistance|indicator\w*|strateg\w*|entry|stop.?loss|signals?|lagao|lagado|dikhao)\b/i;
 const SCREEN=/\b(?:screen|tap|scroll|phone|mobile|browser|whatsapp|youtube|open app)\b/i;
 const MOBILE_ACTION=/\b(?:open|launch|start|tap|scroll|type|click|khol\w*|chalao)\b/i;
 const AD=/\b(?:ads?|advertisements?|posters?|promos?|creatives?)\b|اشتہار|ایڈ/i;
 const PRODUCT=/\b(?:product\w*|flora|facial|shampoo|gold|mere|mara|meri)\b/i;
 function classify(message){
   const s=String(message||"").replace(/\s+/g," ").trim();
   if(!s||EXPLAIN.test(s))return Object.freeze({mode:"chat",intent:s?"ask_explanation":"empty",ready:!!s});
   if(AD.test(s)&&PRODUCT.test(s)&&CREATE.test(s))return Object.freeze({mode:"backend_tool",intent:"create_product_ads",ready:true});
   if(ANIME.test(s)&&CREATE.test(s))return Object.freeze({mode:"backend_project",intent:"render_anime",ready:false,
     reason:"Anime project samajh aa gaya, lekin rendered episodes banane wala backend worker abhi available nahi. Main isey complete nahi keh sakti."});
   if(GAME.test(s)&&CREATE.test(s))return Object.freeze({mode:"backend_project",intent:"build_game",ready:false,
     reason:"Game project samajh aa gaya, lekin playable game build karne wala worker abhi available nahi. Main fake download nahi dungi."});
   if(TRADING.test(s)&&TECHNICAL.test(s))return Object.freeze({mode:"screen_agent",intent:"chart_analysis",ready:false,
     reason:"Chart analysis request samajh aa gayi. Live chart par auto-marking verified nahi; Trading panel mein available market data dekh sakte ho."});
   if(SCREEN.test(s)&&MOBILE_ACTION.test(s))return Object.freeze({mode:"screen_agent",intent:"device_action",ready:false,
     reason:"Screen control ke liye Android app ki explicit permission aur verified command chahiye. Ye command abhi supported nahi."});
   return Object.freeze({mode:"chat",intent:"conversation",ready:true});
 }
 root.HoshiTaskRouter=Object.freeze({classify});
})(typeof window!=="undefined"?window:globalThis);
