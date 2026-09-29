/* ---------- the welcome page (v0.19) ----------
   What a signed-out visitor sees on the deployed site: the pitch, blurred screenshots, and a
   thirty-second challenge in the hero. A patient in pulmonary edema gets worse on a live
   monitor, and the visitor has three buttons that genuinely move the numbers. However well
   they do, he is only better, not fixed, and the rest needs a real case.

   The demo is self-contained. It draws its own monitor and uses PATIENT for the figure,
   and touches nothing in ST, MONITOR or any case pack, so it cannot disturb a case and needs
   no case content. Its numbers are illustrative, not the CHFE case's physiology.

   ACCESS_UI decides when it shows: signed out on the site, it shows, and signing in hides it
   and leaves the case board underneath. The local build shows it only with ?landing. */
const LANDING=(function(){
  const $=id=>document.getElementById(id);
  const A=(typeof ANALYTICS==='object'&&ANALYTICS)||{track(){}};
  let shown=false, viewed=false, raf=0, t0=0, lastTick=0, handlers=null;
  const reduce=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- the demo patient ---- */
  const START={hr:118,sbp:188,dbp:104,sp:85,rr:32};
  let V, done, over, fig=null, lastSay='';
  const LINES={
    start:'"I can\'t... get my breath..."',
    worse:'"Help me... please..."',
    sit:'"That\'s... a little... better."',
    nrb:'"Still... can\'t..."',
    bipap:'(nods, breathing with the mask)',
    tired:'(his eyes are closing)'
  };
  function reset(){
    V=Object.assign({},START); done=new Set(); over=false; t0=performance.now(); lastTick=t0; tLast=null;
    const o=$('ld-over'); if(o) o.hidden=true;
    document.querySelectorAll('#ld-actions button').forEach(b=>{b.disabled=false;b.classList.remove('done');});
    say(LINES.start); paintVitals(); paintFigure();
  }
  function say(t){ if(t===lastSay) return; lastSay=t; const e=$('ld-say'); if(e) e.textContent=t; }
  function clamp(x,a,b){ return Math.max(a,Math.min(b,x)); }
  function paintVitals(){
    const set=(id,v,bad)=>{ const e=$(id); if(!e) return; e.textContent=v; e.parentElement.classList.toggle('bad',!!bad); };
    set('ld-hr',Math.round(V.hr),V.hr>100); set('ld-bp',Math.round(V.sbp)+'/'+Math.round(V.dbp),V.sbp>=160);
    set('ld-sp',Math.round(V.sp),V.sp<90); set('ld-rr',Math.round(V.rr),V.rr>24);
    const al=$('ld-alarm'); if(al) al.hidden=!(V.sp<88);
    const s=Math.floor((performance.now()-t0)/1000);
    const c=$('ld-clock'); if(c) c.textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
  }
  function figureState(){
    const bip=done.has('bipap'), nrb=done.has('nrb')&&!bip, calm=bip;
    const addons=['hospital_bed','sweating'];
    if(!calm) addons.push('agitation');
    if(bip) addons.push('bipap_mask'); else if(nrb) addons.push('nonrebreather');
    const tired=V.sp<79&&!bip;
    return {work_of_breathing: calm?'increased':'severe', respiratory_rate:V.rr, distress: calm?1:3, alertness: tired?1:0,
      eyes: tired?'closed':'open',
      expression: calm?{eyeType:'Squint',eyebrowType:'SadConcernedNatural',mouthType:'Serious'}
                      :{eyeType:'Surprised',eyebrowType:'SadConcerned',mouthType:'ScreamOpen'},
      addons: addons};
  }
  function paintFigure(){
    if(typeof PATIENT!=='object'||!PATIENT.available) return;
    try{
      if(!fig){
        const host=$('ld-patient'); if(!host) return;
        if(typeof SHARED==='object'&&SHARED.patient) PATIENT.setBases(SHARED.patient.base);
        fig=PATIENT.mount(host, PATIENT.baseFor('male',{ageGroup:'older',build:'obese'}));
      }
      fig.setState(figureState());
    }catch(e){ fig=null; }
  }
  /* Every second: untreated he drifts down toward exhaustion; each treatment sets a better
     target and the numbers walk toward it, the way a monitor settles, rather than jump. */
  function target(){
    if(done.has('bipap')) return {hr:108,sbp:176,dbp:98,sp:93,rr:25};
    let t={hr:132,sbp:196,dbp:110,sp:76,rr:38};
    if(done.has('sit')) t={hr:t.hr-4,sbp:t.sbp,dbp:t.dbp,sp:t.sp+3,rr:t.rr-3};
    if(done.has('nrb')) t={hr:t.hr-6,sbp:t.sbp-2,dbp:t.dbp,sp:t.sp+8,rr:t.rr-2};
    return t;
  }
  function tick(now){
    if(!shown) return;
    raf=requestAnimationFrame(tick);
    drawTraces(now);
    if(now-lastTick<1000||over) return;
    lastTick=now;
    const T=target(), k=done.has('bipap')?0.22:0.06;
    for(const key in T) V[key]+= (T[key]-V[key])*k + (Math.random()-.5)*(key==='sp'?0.3:0.8);
    V.sp=clamp(V.sp,70,99);
    paintVitals(); paintFigure();
    if(!done.size) say(V.sp<80?LINES.tired:(V.sp<83?LINES.worse:LINES.start));
    const secs=(now-t0)/1000;
    if(done.has('bipap')&&V.sp>=91) finish('better');
    else if(!done.has('bipap')&&secs>40&&V.sp<79) finish('tiring');
  }
  function finish(kind){
    over=true;
    const o=$('ld-over'); if(!o) return;
    if(kind==='better'){
      $('ld-overtitle').textContent='Better. Not fixed.';
      $('ld-overtext').textContent='His saturation is up. Now look at the monitor: that ST elevation is a STEMI until a 12-lead says otherwise, and BiPAP will not open an artery. What you do next decides how this goes.';
    }else{
      $('ld-overtitle').textContent="He's tiring.";
      $('ld-overtext').textContent='Look at the monitor: that ST elevation is a STEMI until proven otherwise, and oxygen will not fix it. Every minute counts. Take over the whole case.';
    }
    o.hidden=false;
    A.track('landing_demo_end',{outcome:kind, actions:[...done].join(','), seconds:Math.round((performance.now()-t0)/1000)});
  }
  function act(what){
    if(over||done.has(what)) return;
    done.add(what);
    const b=document.querySelector('#ld-actions [data-ldact="'+what+'"]'); if(b){ b.disabled=true; b.classList.add('done'); }
    if(what==='bipap'){ const n=document.querySelector('#ld-actions [data-ldact="nrb"]'); if(n) n.disabled=true; }
    say(LINES[what]); paintFigure();
    A.track('landing_demo_action',{action:what});
  }

  /* ---- the monitor traces ----
     The ECG is the simulator's own synthesiser (MONITOR.synth in monitor.js), not a
     drawing: real PR, QRS and QTc, and the QT shortens with rate the way a heart's does.
     The morphology is the ECG generator's straight upsloping ST elevation (ECG_Generator,
     src/core/st-morphology.ts) at a J-point level of 0.5 mV on lead V3's baseline complex
     (src/core/leads.ts). 0.5 mV is the generator's own anterior STEMI preset, and V3 is
     where the anterior territory weights it fully. The figures are the generator's exactly:
     ST at T onset = level + 0.6 x level (0.8 mV), a linear segment (exponent 1), and
     T = 1.1 x V3's T + 0.3 x level (0.81 mV); R and S are V3's own. All of it is the
     generator's stylisation, not a fit to data. The trace is sampled every 0.75 px, so no
     complex is lost between frames. */
  const LEVEL=0.5, V3={p:0.05, q:0, r:0.8, s:-1.2, t:0.6};
  const UP={slope:0.6, shape:1.0, tScale:1.1, tAdd:0.3};
  const SPEC={pattern:'organised', pWaves:true, prS:0.16, qrsS:0.09, qtcS:0.44,
    stMv:LEVEL, stT:LEVEL+UP.slope*LEVEL, stShape:UP.shape, tMv:UP.tScale*V3.t+UP.tAdd*LEVEL,
    amp:Object.assign({},V3)};
  const SWEEP=4;                       // seconds across the canvas
  let beats=[], nextQ=0, tLast=null, cache={};
  function complexFor(rr){
    const k=Math.round(rr*100);
    if(!cache[k]) cache[k]=(typeof MONITOR==='object'&&MONITOR.synth)?MONITOR.synth(SPEC,k/100):null;
    return cache[k];
  }
  function schedule(t){
    while(nextQ<t+1.2){ const rr=60/Math.max(40,V.hr)*(1+(Math.random()-.5)*0.02);
      beats.push({q:nextQ, rr, cx:complexFor(rr)}); nextQ+=rr; }
    beats=beats.filter(b=>b.q+1.5>t-0.2);
  }
  function ecgAt(t){
    let v=0;
    for(const b of beats){ if(!b.cx) continue; const x=t-b.q; if(x>b.cx.on&&x<b.cx.off) v+=b.cx.at(x); }
    return v;
  }
  function plethAt(t){
    let b=null; for(const x of beats){ if(x.q+0.18<=t) b=x; }
    if(!b) return 0;
    const ph=(t-b.q-0.18)/b.rr; if(ph<0||ph>1) return 0;
    return Math.max(0,Math.sin(Math.PI*Math.min(1,ph*1.8)))*(1-ph*0.45)*(V.sp/100);
  }
  function drawTraces(now){
    const t=(now-t0)/1000;
    if(tLast===null||t<tLast){ tLast=t; beats=[]; nextQ=t+0.3; }
    schedule(t);
    [['ld-ecg','#3EE08F',ecgAt,0.47,0.34],['ld-pleth','#5FC8FF',plethAt,0.88,0.72]].forEach(([id,col,fn,base,gain])=>{
      const c=$(id); if(!c) return;
      const dpr=window.devicePixelRatio||1, w=c.clientWidth, h=c.clientHeight; if(!w||!h) return;
      if(c.width!==Math.round(w*dpr)||c.height!==Math.round(h*dpr)){ c.width=Math.round(w*dpr); c.height=Math.round(h*dpr); c._y=null; }
      const ctx=c.getContext('2d'); ctx.setTransform(dpr,0,0,dpr,0,0);
      const xOf=tt=>((tt%SWEEP)+SWEEP)%SWEEP/SWEEP*w, yOf=v=>h*base-v*h*gain;
      const x0=xOf(tLast), x1=xOf(t);
      const segs= x1>=x0 ? [[x0,x1,tLast]] : [[x0,w,tLast],[0,x1,t-x1/w*SWEEP]];
      ctx.strokeStyle=col; ctx.lineWidth=1.7; ctx.lineJoin='round';
      for(const [a,bx,ta] of segs){
        /* Erase only ahead of the pen, like a monitor's sweep gap, so the stroke just
           drawn is never clipped at a frame boundary. */
        ctx.clearRect(bx+1,0,14,h); if(bx+15>w) ctx.clearRect(0,0,bx+15-w,h);
        ctx.beginPath();
        if(c._y!=null&&a!==0) ctx.moveTo(c._x,c._y); else ctx.moveTo(a,yOf(fn(ta)));
        /* Start from the last point actually drawn, and always end exactly on bx. */
        for(let x=a;;x=Math.min(bx,x+0.75)){ const tt=ta+(x-a)/w*SWEEP, y=yOf(fn(tt));
          ctx.lineTo(x,y); c._x=x; c._y=y; if(x>=bx) break; }
        ctx.stroke();
        if(bx>=w) c._y=null;
      }
    });
    tLast=t;
  }

  /* ---- the page ---- */
  function fillCases(){
    const box=$('ld-caselist'); if(!box||typeof CASES!=='object') return;
    const n=$('ld-ncases'); if(n) n.textContent=String(CASES.length);
    box.innerHTML=CASES.map((c,i)=>{
      const card=c.card||{}, p=c.patient||(c.case&&c.case.patient)||{};
      const who=[p.age,(p.sex||'').charAt(0).toUpperCase()].filter(Boolean).join(' ');
      const mins=card.runtime_seconds?Math.round(card.runtime_seconds/60)+' min':'';
      return `<button type="button" class="ld-case" data-ldcase="${i}"><div class="t">${esc(card.complaint||card.title||c.prefix)}</div>
        <div class="m">${esc([who,card.category||'',mins].filter(Boolean).join(' \u00b7 '))}</div></button>`;
    }).join('');
  }
  function bind(h){
    handlers=h;
    const root=$('landing'); if(!root||root._bound) return; root._bound=true;
    root.addEventListener('click',e=>{
      e.stopPropagation();
      const t=e.target.closest('[data-ld],[data-ldact],[data-ldcase],#ld-again,.ld-nav a,.ld-brand'); if(!t) return;
      if(t.matches('.ld-brand')){ e.preventDefault(); root.scrollTo({top:0,behavior:reduce?'auto':'smooth'}); return; }
      if(t.matches('.ld-nav a')){ e.preventDefault(); const s=$(t.getAttribute('href').slice(1)); if(s) s.scrollIntoView({behavior:reduce?'auto':'smooth'}); return; }
      if(t.id==='ld-again'){ reset(); return; }
      if(t.dataset.ldact){ act(t.dataset.ldact); return; }
      if(t.dataset.ld){ A.track(t.dataset.ld==='signup'?'signup_clicked':'login_clicked',{from:t.closest('.ld-over')?'demo':(t.closest('.ld-top')?'header':'page')}); handlers[t.dataset.ld](-1); return; }
      if(t.dataset.ldcase!==undefined){ A.track('landing_case_clicked',{case:(CASES[+t.dataset.ldcase]||{}).prefix}); handlers.signup(+t.dataset.ldcase); }
    });
  }
  /* The header shrinks once the page scrolls, and the section in view lights up in the nav. */
  function watchScroll(root){
    if(root._watch) return; root._watch=true;
    const top=$('ld-top');
    const onScroll=()=>{ if(top) top.classList.toggle('scrolled', root.scrollTop>12);
      const links=[...root.querySelectorAll('.ld-nav a[data-sec]')]; let cur='';
      for(const a of links){ const sec=$(a.dataset.sec); if(sec&&sec.getBoundingClientRect().top<window.innerHeight*0.45) cur=a.dataset.sec; }
      links.forEach(a=>a.classList.toggle('on', a.dataset.sec===cur)); };
    root.addEventListener('scroll',onScroll,{passive:true}); root._onScroll=onScroll;
  }
  function show(){
    const root=$('landing'); if(!root) return;
    watchScroll(root);
    if(!shown){ shown=true; root.classList.remove('hidden'); fillCases();
      const lg=$('ld-legal'), pl=$('pk-legal'); if(lg&&pl) lg.textContent=(typeof ACCESS==='object'&&ACCESS.legal)||'';
      reset(); cancelAnimationFrame(raf); raf=requestAnimationFrame(tick);
      if(!viewed){ viewed=true; A.track('landing_viewed'); }
      requestAnimationFrame(()=>root._onScroll&&root._onScroll()); }
  }
  function hide(){
    const root=$('landing'); if(!root) return;
    shown=false; cancelAnimationFrame(raf); root.classList.add('hidden');
  }
  return {bind, show, hide, visible:()=>shown};
})();
