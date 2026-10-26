export function initCore(core, canvas) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let frame = 0;
  let last = 0;
  let size = 0;
  let phase = 0;
  const tau = Math.PI * 2;
  const isMoving = () => !document.hidden && !reduced.matches && !document.body.classList.contains('motion-off');

  function project(lat, lon, rotation, tilt) {
    const x = Math.cos(lat) * Math.cos(lon + rotation);
    const y = Math.sin(lat);
    const z = Math.cos(lat) * Math.sin(lon + rotation);
    const yy = y * Math.cos(tilt) - z * Math.sin(tilt);
    const zz = y * Math.sin(tilt) + z * Math.cos(tilt);
    const perspective = 1 + zz * .12;
    return {x:size/2 + x*size*.33*perspective,y:size/2 + yy*size*.33*perspective,z:zz};
  }
  function draw() {
    if (!size) return;
    ctx.clearRect(0,0,size,size);
    const state = core.dataset.state;
    const active = state === 'speaking' || state === 'listening';
    const tilt = -.35 + Math.sin(phase*.31)*.12;
    const r = size*.36;
    const glow = ctx.createRadialGradient(size/2,size/2,r*.16,size/2,size/2,r);
    glow.addColorStop(0,active?'rgba(124,220,255,.12)':'rgba(104,195,255,.05)');
    glow.addColorStop(.7,'rgba(48,140,207,.04)');glow.addColorStop(1,'rgba(20,100,170,0)');
    ctx.fillStyle=glow;ctx.fillRect(0,0,size,size);

    // Small streaming fragments add the holographic energy around the core.
    for(let i=0;i<110;i++) {
      const angle=i*2.39996+phase*(i%2?1:-1);
      const radius=size*(.22+(i%19)/150+.012*Math.sin(phase*3+i));
      const x=size/2+Math.cos(angle)*radius;
      const y=size/2+Math.sin(angle)*radius*.88;
      const light=.18+.38*(.5+.5*Math.sin(i*1.7+phase*2));
      ctx.strokeStyle=`rgba(174,232,255,${light})`;
      ctx.lineWidth=i%9===0?1.2:.6;
      ctx.beginPath();ctx.moveTo(x,y);
      ctx.lineTo(x-Math.sin(angle)*size*.01,y+Math.cos(angle)*size*.01);ctx.stroke();
    }

    // Eleven latitude bands and 264 nodes form a rotating perspective sphere.
    for(let row=-5;row<=5;row++) {
      const lat=row*Math.PI/13;
      ctx.beginPath();
      for(let col=0;col<=48;col++) {
        const p=project(lat,col*tau/48,phase,tilt);
        if(col===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);
      }
      ctx.strokeStyle=`rgba(113,202,255,${row===0?.23:.1})`;ctx.lineWidth=.6;ctx.stroke();
      for(let col=0;col<24;col++) {
        const p=project(lat,col*tau/24,phase,tilt);
        const front=(p.z+1)/2;
        const flicker=.6+.4*Math.sin(phase*2+row*3+col*.7);
        const alpha=(.12+front*.65)*flicker;
        ctx.fillStyle=`rgba(${Math.round(120+front*100)},${Math.round(200+front*40)},255,${alpha})`;
        ctx.beginPath();ctx.arc(p.x,p.y,.45+front*(active?1.1:.8),0,tau);ctx.fill();
      }
    }
    // Broken meridians give the core its layered circuit silhouette.
    for(let column=0;column<9;column++) {
      ctx.beginPath();
      for(let segment=0;segment<=36;segment++) {
        const p=project(-Math.PI/2+segment*Math.PI/36,column*tau/9,phase,tilt);
        if(segment===0||segment%9===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);
      }
      ctx.strokeStyle='rgba(157,224,255,.2)';ctx.lineWidth=.6;ctx.stroke();
    }
    // Three travelling arcs frame the sphere without any image assets.
    for(let arc=0;arc<3;arc++) {
      ctx.beginPath();
      ctx.ellipse(size/2,size/2,size*(.385+arc*.022),size*(.15+arc*.025),-.48+arc*.56,phase*(arc%2?-1:1)+arc*2,phase*(arc%2?-1:1)+arc*2+1.65);
      ctx.strokeStyle=arc===1?'rgba(209,246,255,.68)':'rgba(103,197,255,.32)';
      ctx.lineWidth=arc===1?1:.55;ctx.stroke();
    }
  }
  function animate(now) {
    frame=0;
    if(!isMoving())return;
    if(now-last>=1000/24) {
      const elapsed=Math.min((now-last)/1000,.1);
      phase+=elapsed*(core.dataset.state==='speaking'?.46:core.dataset.state==='listening'?.3:.13);
      last=now;draw();
    }
    frame=requestAnimationFrame(animate);
  }
  function sync() {
    cancelAnimationFrame(frame);frame=0;draw();
    if(isMoving()){last=performance.now();frame=requestAnimationFrame(animate);}
  }
  function resize() {
    size=canvas.getBoundingClientRect().width;
    const dpr=Math.min(window.devicePixelRatio||1,1.5);
    canvas.width=Math.round(size*dpr);canvas.height=Math.round(size*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);sync();
  }
  new ResizeObserver(resize).observe(canvas);
  new MutationObserver(sync).observe(core,{attributes:true,attributeFilter:['data-state']});
  new MutationObserver(sync).observe(document.body,{attributes:true,attributeFilter:['class']});
  document.addEventListener('visibilitychange',sync);
  reduced.addEventListener?.('change',sync);
  window.addEventListener('pagehide',()=>cancelAnimationFrame(frame));
  resize();
}
