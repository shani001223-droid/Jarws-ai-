/* HOSHI Task 42: same-snapshot read-only canvas and local PNG/JSON export. */
(function(root){
 'use strict';
 const steps={'15m':900000,'1h':3600000,'4h':14400000};
 const allowed=new Set(['support','resistance','paper_entry','paper_stop','paper_tp1','paper_tp2']);
 const number=x=>typeof x==='number'&&Number.isFinite(x);
 function validate(d,pair,tf){
  if(!d||d.version!=='spot-annotated-chart-v1'||d.mode!=='annotated-spot-chart-research-only'||
     d.symbol!==pair||d.interval!==tf||!steps[tf]||
     d.orders_enabled!==false||d.independently_cross_checked!==false||
     !Number.isInteger(d.fetched_at)||!Number.isInteger(d.last_closed_at)||
     !Array.isArray(d.candles)||d.candles.length<64||d.candles.length>96||
     !Array.isArray(d.levels)||d.levels.length>6||!Array.isArray(d.confirmed_pivots)||
     d.confirmed_pivots.length>12||!['wait','paper_plan_only'].includes(d.paper_decision))return false;
  const step=steps[tf];
  for(let i=0;i<d.candles.length;i++){
   const b=d.candles[i];
   if(!b||!Number.isInteger(b.time)||!Number.isInteger(b.close_time)||
      b.time<0||b.time%step!==0||b.close_time!==b.time+step-1||
      (i>0&&b.time!==d.candles[i-1].time+step)||
      !['open','high','low','close','volume_base'].every(k=>number(b[k]))||
      b.low<=0||b.volume_base<0||b.low>Math.min(b.open,b.close)||
      Math.max(b.open,b.close)>b.high)return false;
  }
  if(d.last_closed_at!==d.candles[d.candles.length-1].close_time)return false;
  const kinds=new Set();
  for(const x of d.levels){
   if(!x||!allowed.has(x.kind)||kinds.has(x.kind)||!number(x.price)||x.price<=0||
      typeof x.paper_only!=='boolean'||x.paper_only!==x.kind.startsWith('paper_')||
      (x.paper_only&&(tf!=='15m'||d.paper_decision!=='paper_plan_only')))return false;
   kinds.add(x.kind);
  }
  if(d.paper_decision==='paper_plan_only'&&tf==='15m'&&
     !['paper_entry','paper_stop','paper_tp1','paper_tp2'].every(k=>kinds.has(k)))return false;
  const start=d.candles[0].time;
  for(const p of d.confirmed_pivots){
   if(!p||!['high','low'].includes(p.side)||!number(p.price)||p.price<=0||
      !Number.isInteger(p.pivot_at)||!Number.isInteger(p.confirmed_at)||
      p.pivot_at<start||p.confirmed_at<=p.pivot_at||
      p.confirmed_at>d.last_closed_at||
      !d.candles.some(b=>b.close_time===p.pivot_at))return false;
  }
  return true;
 }
 function draw(canvas,d){
  const ctx=canvas.getContext('2d');
  if(!ctx)throw new Error('Canvas unavailable on this device.');
  const bars=d.candles,lo=Math.min(...bars.map(b=>b.low)),hi=Math.max(...bars.map(b=>b.high));
  const pad=Math.max((hi-lo)*.08,hi*.0001),bottom=385,top=65,left=52,right=750;
  const low=lo-pad,high=hi+pad,step=(right-left)/bars.length;
  const y=p=>bottom-(p-low)/(high-low)*(bottom-top);
  canvas.width=900;canvas.height=540;
  ctx.fillStyle='#081421';ctx.fillRect(0,0,900,540);
  ctx.font='14px sans-serif';ctx.fillStyle='#e8f3ff';
  ctx.fillText('HOSHI | '+d.symbol+' | '+d.interval+' | CLOSED SPOT',left,25);
  ctx.font='12px sans-serif';ctx.fillStyle='#a8bfd4';
  ctx.fillText('Paper research only - no orders or guaranteed fills',left,44);
  for(let j=0;j<5;j++){
   const yy=top+j*(bottom-top)/4;
   ctx.strokeStyle='#25394d';ctx.lineWidth=1;ctx.beginPath();
   ctx.moveTo(left,yy);ctx.lineTo(right,yy);ctx.stroke();
   ctx.fillStyle='#a8bfd4';ctx.fillText((high-(high-low)*j/4).toFixed(4),right+8,yy+4);
  }
  const vmax=Math.max(...bars.map(b=>b.volume_base));
  const xByTime=new Map();
  bars.forEach((b,i)=>{
   const x=left+(i+.5)*step,rising=b.close>=b.open;
   xByTime.set(b.close_time,x);
   ctx.strokeStyle=ctx.fillStyle=rising?'#5ad6b1':'#f58a9a';
   ctx.beginPath();ctx.moveTo(x,y(b.high));ctx.lineTo(x,y(b.low));ctx.stroke();
   ctx.fillRect(x-2,Math.min(y(b.open),y(b.close)),4,Math.max(2,Math.abs(y(b.open)-y(b.close))));
   if(vmax)ctx.fillRect(x-2,455-b.volume_base/vmax*60,4,b.volume_base/vmax*60);
  });
  const colors={support:'#48c5b6',resistance:'#e9a85d',paper_entry:'#e4dfff',
   paper_stop:'#ff718d',paper_tp1:'#b9a9ff',paper_tp2:'#898cff'};
  d.levels.forEach(level=>{
   if(level.price<low||level.price>high)return;
   const yy=y(level.price);
   ctx.strokeStyle=ctx.fillStyle=colors[level.kind];ctx.lineWidth=2;
   ctx.beginPath();ctx.moveTo(left,yy);ctx.lineTo(right,yy);ctx.stroke();
   ctx.fillText(level.kind+' '+level.price.toFixed(4),right+8,yy+14);
  });
  d.confirmed_pivots.forEach(p=>{
   const x=xByTime.get(p.pivot_at);if(x===undefined)return;
   ctx.fillStyle=p.side==='high'?'#ffd166':'#57caff';
   ctx.beginPath();ctx.arc(x,y(p.price),3,0,Math.PI*2);ctx.fill();
  });
  ctx.fillStyle='#a8bfd4';ctx.fillText('Relative base volume | UTC timestamps in JSON',left,478);
  ctx.fillText('Last closed ms: '+d.last_closed_at+' | fetched UTC s: '+d.fetched_at,left,508);
 }
 function mount({backend,document:doc=root.document}){
  const $=id=>doc.getElementById(id),run=$('tradeAnnotatedRun'),pair=$('tradePair');
  if(!run)return {reset(){}};
  const tf=$('tradeAnnotatedInterval'),canvas=$('tradeAnnotatedCanvas'),
        status=$('tradeAnnotatedStatus'),png=$('tradeAnnotatedPng'),json=$('tradeAnnotatedJson');
  let report=null,controller=null,seq=0;
  function reset(){
   seq++;if(controller)controller.abort();controller=null;report=null;
   canvas.hidden=true;png.disabled=json.disabled=true;
   run.disabled=!['BTCUSDT','ETHUSDT'].includes(pair.value);
   status.textContent=run.disabled?'Select BTC or ETH for verified closed-candle research.':
    'Ready · 15m/1h/4h · paper-only chart. No data saved automatically.';
  }
  function save(blob,name){
   const url=root.URL.createObjectURL(blob),a=doc.createElement('a');
   a.href=url;a.download=name;doc.body.append(a);a.click();a.remove();
   root.setTimeout(()=>root.URL.revokeObjectURL(url),5000);
  }
  run.onclick=async()=>{
   reset();if(run.disabled)return;
   const id=seq,symbol=pair.value,interval=tf.value;
   controller=new AbortController();const signal=controller.signal;
   run.disabled=true;status.textContent='Loading validated closed candles…';
   const timer=root.setTimeout(()=>controller.abort(),25000);
   try{
    const url=backend+'/api/trading/annotated-chart?symbol='+encodeURIComponent(symbol)+
      '&interval='+encodeURIComponent(interval)+'&output=json';
    const response=await root.fetch(url,{signal,cache:'no-store'});
    if(!response.ok)throw new Error('Chart unavailable ('+response.status+'). No export generated.');
    const data=await response.json();
    if(id!==seq)return;
    if(!validate(data,symbol,interval))throw new Error('Chart evidence invalid; export blocked.');
    draw(canvas,data);report=data;canvas.hidden=false;png.disabled=json.disabled=false;
    status.textContent='Closed-candle chart ready · '+data.paper_decision+
      ' · single Binance venue; no orders.';
   }catch(error){
    if(id===seq){report=null;canvas.hidden=true;png.disabled=json.disabled=true;
     status.textContent=error.name==='AbortError'?'Chart request timed out; no export.':
       (error.message||'Chart unavailable.');}
   }finally{
    root.clearTimeout(timer);
    if(id===seq){controller=null;run.disabled=!['BTCUSDT','ETHUSDT'].includes(pair.value);}
   }
  };
  png.onclick=()=>{
   const snapshot=report;
   if(!snapshot)return;
   canvas.toBlob(blob=>{
    if(blob)save(blob,'Hoshi_'+snapshot.symbol+'_'+snapshot.interval+'_paper_chart.png');
    else status.textContent='PNG export unavailable on this device.';
   },'image/png');
  };
  json.onclick=()=>{
   if(report)save(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),
     'Hoshi_'+report.symbol+'_'+report.interval+'_closed_candles.json');
  };
  pair.addEventListener('change',reset);tf.addEventListener('change',reset);
  reset();return {reset};
 }
 root.HoshiAnnotatedChart={validate,draw,mount};
})(typeof window!=='undefined'?window:globalThis);
