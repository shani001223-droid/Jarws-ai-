/* Read-only research UI. Historical simulations are never shown as positions. */
(function(root){
 'use strict';
 function mount({backend,document:doc=root.document}){
  const $=id=>doc.getElementById(id),pair=$('tradePair');
  if(!$('tradeResearch'))return;
  let sequence=0,controller=null,report=null,journal=[];
  const key='hoshiPaperJournalV1',optKey='hoshiPaperJournalOptInV1';
  const supported=()=>['BTCUSDT','ETHUSDT'].includes(pair.value);
  const fmt=n=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:4}):'—';
  const stamp=n=>new Date(n).toISOString().replace('T',' ').replace('.000Z',' UTC');
  const add=(parent,tag,text)=>{const el=doc.createElement(tag);el.textContent=text;parent.append(el);return el};
  const fields=['trade_count','net_pnl','ending_equity','max_drawdown_pct','fees_paid'];
  function safeSummary(d){
   if(!d||!['BTCUSDT','ETHUSDT'].includes(d.symbol)||!['trend_pullback','breakout_retest'].includes(d.strategy)||fields.some(k=>typeof d[k]!=='number'||!Number.isFinite(d[k])))return null;
   return Object.fromEntries(['symbol','strategy',...fields].map(k=>[k,d[k]]));
  }
  function drawJournal(){
   const box=$('tradeJournal');box.replaceChildren();
   add(box,'p',journal.length?'Historical simulation summaries · not forward demo trades':'No saved simulation summaries.');
   for(const item of journal)add(box,'p',item.symbol+' · '+item.strategy+' · '+item.trade_count+' trades · net '+fmt(item.net_pnl)+' USDT');
  }
  try{
   $('tradeJournalConsent').checked=root.localStorage.getItem(optKey)==='true';
   if($('tradeJournalConsent').checked){const saved=JSON.parse(root.localStorage.getItem(key)||'[]');if(Array.isArray(saved))journal=saved.slice(-10).map(safeSummary).filter(Boolean);}
   else root.localStorage.removeItem(key);
  }catch(_){$('tradeJournalConsent').checked=false;}
  function reset(){
   sequence++;if(controller)controller.abort();controller=null;report=null;
   $('tradeResearchOutput').replaceChildren();$('tradeResearchExport').disabled=true;
   $('tradeResearchRun').disabled=$('tradeBacktestRun').disabled=!supported();
   $('tradeResearchStatus').textContent=supported()?'Ready · research uses 15m / 1h / 4h; simulation uses 15m only.':'Research supports BTC and ETH. Select one above.';
  }
  async function run(kind){
   reset();if(!supported())return;
   const id=sequence;controller=new AbortController();const active=controller;
   $('tradeResearchRun').disabled=$('tradeBacktestRun').disabled=true;
   $('tradeResearchStatus').textContent='Loading closed candles…';
   const timer=setTimeout(()=>active.abort(),25000);
   try{
    const body={symbol:pair.value,strategy:$('tradeStrategy').value};
    for(const name of kind==='backtest'?['equity','risk_pct','daily_loss_limit','fee_bps','slippage_bps']:[]){
     const input=$('paper_'+name);if(!input.checkValidity())throw new Error('Simulation settings are out of bounds.');body[name]=Number(input.value);
    }
    const response=await root.fetch(backend+(kind==='research'?'/api/trading/research?symbol='+encodeURIComponent(pair.value):'/api/trading/backtest'),{
     method:kind==='research'?'GET':'POST',headers:kind==='research'?{}:{'Content-Type':'application/json'},
     body:kind==='research'?undefined:JSON.stringify(body),signal:active.signal,cache:'no-store'
    });
    if(!response.ok)throw new Error('Research unavailable ('+response.status+'). Refresh or retry; no result generated.');
    const d=await response.json();if(id!==sequence)return;
    if(d.symbol!==pair.value||d.orders_enabled!==false)throw new Error('Invalid research response.');
    const out=$('tradeResearchOutput');out.replaceChildren();
    add(out,'p',d.symbol+' · '+d.source+' · fetched '+stamp(d.fetched_at*1000));
    if(kind==='research'){
     if(d.mode!=='research-only'||!d.timeframes||!Array.isArray(d.proposals))throw new Error('Invalid research response.');
     add(out,'strong',d.decision==='paper_candidate'?'PAPER CANDIDATE · no order':'WAIT · no confirmed paper setup');
     add(out,'p',d.reason);
     for(const tf of ['15m','1h','4h']){
      const f=d.timeframes[tf];
      if(!f||!f.indicators||!Number.isFinite(f.last_closed_at))throw new Error('Invalid timeframe response.');
      add(out,'p',tf+' · '+f.regime+' · S '+fmt(f.support)+' / R '+fmt(f.resistance)+' · EMA20 '+fmt(f.indicators.ema20)+' · EMA50 '+fmt(f.indicators.ema50)+' · RSI14 '+fmt(f.indicators.rsi14)+' · ATR14 '+fmt(f.indicators.atr14)+' · candle closed '+stamp(f.last_closed_at));
     }
     for(const p of d.proposals)add(out,'p',p.strategy+' · hypothetical long reference '+fmt(p.reference_entry)+' · stop '+fmt(p.stop)+' · target '+fmt(p.reference_target)+' · 2R before costs. Reference price is not a fill.');
     add(out,'p','S/R = previous 20 closed candles. '+d.note);
    }else{
     if(d.mode!=='historical-paper-simulation'||!safeSummary(d)||!Array.isArray(d.limitations))throw new Error('Invalid simulation response.');
     add(out,'strong','HISTORICAL SIMULATION · '+d.strategy+' · '+d.bars+' closed 15m candles');
     add(out,'p',stamp(d.start_at)+' → '+stamp(d.end_at));
     add(out,'p','Net '+fmt(d.net_pnl)+' USDT · equity '+fmt(d.initial_equity)+' → '+fmt(d.ending_equity)+' · trades '+d.trade_count+' · win rate '+fmt(d.win_rate_pct)+'%');
     add(out,'p','Drawdown '+fmt(d.max_drawdown_pct)+'% · fees '+fmt(d.fees_paid)+' USDT · expectancy '+fmt(d.expectancy)+' · profit factor '+fmt(d.profit_factor));
     add(out,'p','Simulation settings: '+d.config.risk_pct+'% risk · daily gross loss cap '+d.config.daily_loss_limit+' USDT · fee '+d.config.fee_bps+' bps / side · slippage '+d.config.slippage_bps+' bps / side.');
     for(const limitation of d.limitations)add(out,'p',limitation);
     if($('tradeJournalConsent').checked){
      const next=[...journal,safeSummary(d)].slice(-10);
      try{root.localStorage.setItem(key,JSON.stringify(next));journal=next;drawJournal();}
      catch(_){add(out,'p','Local journal could not be saved. Export this result instead.');}
     }
    }
    report=d;$('tradeResearchExport').disabled=false;
    $('tradeResearchStatus').textContent='Complete · no orders placed. Export includes data times, settings and limitations.';
   }catch(error){if(id===sequence){report=null;$('tradeResearchOutput').replaceChildren();$('tradeResearchStatus').textContent=error.name==='AbortError'?'Request timed out. Retry; no result generated.':error.message;}}
   finally{clearTimeout(timer);if(id===sequence){controller=null;$('tradeResearchRun').disabled=$('tradeBacktestRun').disabled=!supported();}}
  }
  $('tradeResearchRun').onclick=()=>run('research');$('tradeBacktestRun').onclick=()=>run('backtest');
  $('tradeResearchExport').onclick=()=>{
   if(!report)return;
   const url=root.URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
   const a=doc.createElement('a');a.href=url;a.download='Hoshi_'+report.symbol+'_'+(report.strategy||'research')+'.json';doc.body.append(a);a.click();a.remove();setTimeout(()=>root.URL.revokeObjectURL(url),1000);
  };
  $('tradeJournalConsent').onchange=()=>{
   try{
    if($('tradeJournalConsent').checked){root.localStorage.setItem(optKey,'true');}
    else{root.localStorage.removeItem(key);root.localStorage.removeItem(optKey);journal=[];drawJournal();}
   }catch(_){$('tradeJournalConsent').checked=false;$('tradeResearchStatus').textContent='Local journal unavailable: device storage blocked.';}
  };
  $('tradeJournalClear').onclick=()=>{
   try{root.localStorage.removeItem(key);journal=[];drawJournal();}
   catch(_){$('tradeResearchStatus').textContent='Could not clear local journal: device storage blocked.';}
  };
  pair.addEventListener('change',reset);
  $('tradeResearchSettings').querySelectorAll('input,select').forEach(el=>el.addEventListener('change',reset));
  drawJournal();reset();return Object.freeze({reset,run});
 }
 root.HoshiTradingResearch=Object.freeze({mount});
})(typeof window!=='undefined'?window:globalThis);
