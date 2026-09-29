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

  /* ---- the demo patient ----
     Two steps. First the visitor picks one of three airway and breathing moves. Three
     seconds later those buttons give way to a harder choice: get an ECG, or push
     metoprolol. The ECG finds the anterior STEMI and invites them to continue the case.
     Metoprolol, a beta-blocker given to a man in acute heart failure, tips him into
     cardiogenic shock: IV beta-blockers are to be avoided in STEMI with signs of heart
     failure or a risk of shock (2013 ACCF/AHA STEMI guideline, class III: harm; the COMMIT
     trial found more cardiogenic shock with early IV metoprolol). Untreated for 40 seconds,
     he tires. The numbers are illustrative, not the CHFE case's physiology. */
  const START={hr:118,sbp:188,dbp:104,sp:85,rr:32};
  const STEP1=[['sit','Sit him upright'],['nrb','Non-rebreather mask'],['bipap','Start BiPAP']];
  const STEP2=[['ecg','Get an ECG'],['meto','Push Metoprolol IV']];
  let V, done, over, step, stepTimer=0, crashAt=0, fig=null, lastSay='';
  const LINES={
    start:'"I can\'t... get my breath..."',
    worse:'"Help me... please..."',
    sit:'"That\'s... a little... better."',
    nrb:'"Still... can\'t..."',
    bipap:'(nods, breathing with the mask)',
    tired:'(his eyes are closing)',
    ecg:'12-lead: ST elevation V1 to V4. Anterior STEMI.',
    meto:'"I feel... faint..."',
    shock:'(grey, clammy, barely rousable)'
  };
  function buttons(list, ask){
    const box=$('ld-actions'); if(!box) return;
    box.classList.toggle('two', list.length===2);
    box.innerHTML=(ask?`<div class="ld-ask">${ask}</div>`:'')+list.map(([k,label])=>
      `<button type="button" data-ldact="${k}">${label}</button>`).join('');
  }
  function reset(){
    V=Object.assign({},START); done=new Set(); over=false; step=1; crashAt=0;
    clearTimeout(stepTimer); t0=performance.now(); lastTick=t0; tLast=null;
    const o=$('ld-over'); if(o) o.hidden=true;
    buttons(STEP1,'');
    say(LINES.start); paintVitals(); paintFigure();
  }
  function say(t){ if(t===lastSay) return; lastSay=t; const e=$('ld-say'); if(e){ e.textContent=t; e.classList.toggle('result', t===LINES.ecg); } }
  function clamp(x,a,b){ return Math.max(a,Math.min(b,x)); }
  function paintVitals(){
    const set=(id,v,bad)=>{ const e=$(id); if(!e) return; e.textContent=v; e.parentElement.classList.toggle('bad',!!bad); };
    set('ld-hr',Math.round(V.hr),V.hr>100||V.hr<50); set('ld-bp',Math.round(V.sbp)+'/'+Math.round(V.dbp),V.sbp>=160||V.sbp<90);
    set('ld-sp',Math.round(V.sp),V.sp<90); set('ld-rr',Math.round(V.rr),V.rr>24);
    const al=$('ld-alarm');
    if(al){ const low=V.sbp<90?'BP LOW':(V.sp<88?'SpO₂ LOW':''); al.hidden=!low; if(low) al.textContent=low; }
    const s=Math.floor((performance.now()-t0)/1000);
    const c=$('ld-clock'); if(c) c.textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
  }
  function figureState(){
    const bip=done.has('bipap'), nrb=done.has('nrb')&&!bip, shock=done.has('meto');
    const calm=bip&&!shock;
    const addons=['hospital_bed','sweating'];
    if(!calm&&!shock) addons.push('agitation');
    if(bip) addons.push('bipap_mask'); else if(nrb) addons.push('nonrebreather');
    const tired=(V.sp<79&&!bip)||(shock&&V.sbp<85);
    return {work_of_breathing: calm?'increased':'severe', respiratory_rate:V.rr, distress: calm?1:(shock?2:3), alertness: tired?2:0,
      eyes: tired?'closed':'open',
      expression: shock?{eyeType:'Squint',eyebrowType:'SadConcerned',mouthType:'Grimace'}
                : calm?{eyeType:'Squint',eyebrowType:'SadConcernedNatural',mouthType:'Serious'}
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
  /* Every second the numbers walk toward a target, the way a monitor settles, rather than
     jump. Untreated he drifts toward exhaustion; each step-one move sets a better target;
     metoprolol sets a shock target and walks there fast. */
  function target(){
    if(done.has('meto')) return {hr:104,sbp:72,dbp:40,sp:79,rr:38};
    if(done.has('bipap')) return {hr:110,sbp:178,dbp:100,sp:92,rr:26};
    let t={hr:132,sbp:196,dbp:110,sp:76,rr:38};
    if(done.has('sit')) t={hr:t.hr-4,sbp:t.sbp,dbp:t.dbp,sp:t.sp+3,rr:t.rr-3};
    if(done.has('nrb')) t={hr:t.hr-6,sbp:t.sbp-2,dbp:t.dbp,sp:t.sp+8,rr:t.rr-2};
    return t;
  }
  function tick(now){
    if(!shown) return;
    raf=requestAnimationFrame(tick);
    drawTraces(now); FX.frame(now); AMB.frame(now);
    if(now-lastTick<1000||over) return;
    lastTick=now;
    const T=target(), k=done.has('meto')?0.35:(done.has('bipap')?0.22:0.06);
    for(const key in T) V[key]+= (T[key]-V[key])*k + (Math.random()-.5)*(key==='sp'?0.3:0.8);
    V.sp=clamp(V.sp,70,99);
    paintVitals(); paintFigure();
    if(!done.size) say(V.sp<80?LINES.tired:(V.sp<83?LINES.worse:LINES.start));
    if(done.has('meto')&&V.sbp<90) say(LINES.shock);
    const secs=(now-t0)/1000;
    if(crashAt&&now>=crashAt) finish('crash');
    else if(!done.size&&secs>40&&V.sp<79) finish('tiring');
  }
  function finish(kind){
    over=true; clearTimeout(stepTimer);
    const o=$('ld-over'); if(!o) return;
    const T={
      crash:["He's crashing.", 'A beta-blocker in acute heart failure dropped his pressure into cardiogenic shock. In the full case you would have to get him back, and find what the monitor was trying to tell you.', 'Help the Patient: Sign Up Free!'],
      ecg:['Good call. Anterior STEMI.', 'ST elevation across V1 to V4. The clock on his heart muscle is running: the cath lab, the drugs and the handoff are all still to come. Continue the case.', 'Continue the Case: Sign Up Free!'],
      tiring:["He's tiring.", 'Look at the monitor: that ST elevation is a STEMI until proven otherwise, and he is running out of breath. Every minute counts. Take over the whole case.', 'Help the Patient: Sign Up Free!']
    }[kind];
    $('ld-overtitle').textContent=T[0]; $('ld-overtext').textContent=T[1];
    const cta=$('ld-overcta'); if(cta) cta.textContent=T[2];
    o.classList.toggle('good', kind==='ecg');
    o.hidden=false;
    A.track('landing_demo_end',{outcome:kind, actions:[...done].join(','), seconds:Math.round((performance.now()-t0)/1000)});
  }
  function act(what){
    if(over||done.has(what)) return;
    done.add(what);
    const b=document.querySelector('#ld-actions [data-ldact="'+what+'"]'); if(b){ b.classList.add(what==='meto'?'bad':'done'); }
    document.querySelectorAll('#ld-actions button').forEach(x=>x.disabled=true);
    say(LINES[what]); paintFigure();
    A.track('landing_demo_action',{action:what, step});
    if(step===1){
      step=2;
      stepTimer=setTimeout(()=>{ if(!over&&shown) buttons(STEP2,'What next?'); }, 3000);
    }else if(what==='ecg'){
      stepTimer=setTimeout(()=>{ if(!over) finish('ecg'); }, 2200);
    }else if(what==='meto'){
      crashAt=performance.now()+6000;
    }
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
  /* ---- lights in the distance (v0.19h) ----
     Two rotating beacons, one red and one blue, far behind the screen. No source and no beam
     is ever visible: only the diffuse light they throw, a broad soft glow that sweeps across
     the page as each beacon turns and swells while it faces the viewer, then fades as it turns
     away. When it faces the viewer the whole page also takes on a faint wash of its colour.
     Drawn at a quarter of screen resolution and stretched, which keeps it cheap and soft.
     Photosensitivity: nothing strobes. Each beacon brightens about once every two seconds,
     the change is gradual, and the wash moves white only to a pale tint, well short of the
     WCAG 2.3.1 general flash threshold. With reduced motion it draws one still frame. */
  const FX=(function(){
    const Q=4, LIGHTS=[
      {rgb:'232,44,52', per:2.2, ph:0.0, y:-0.15, k:1.0,  wash:'ld-wash-r'},
      {rgb:'44,96,236', per:2.6, ph:2.4, y:-0.05, k:0.72, wash:'ld-wash-b'}];
    let cv=null, g=null, W=0, H=0, still=false;
    function size(){
      if(!cv) return;
      const w=Math.max(40,Math.ceil(innerWidth/Q)), h=Math.max(40,Math.ceil(innerHeight/Q));
      if(w!==W||h!==H){ W=cv.width=w; H=cv.height=h; still=false; }
    }
    function glow(cx,cy,r,rgb,alpha){
      const gr=g.createRadialGradient(cx,cy,0,cx,cy,r);
      gr.addColorStop(0,'rgba('+rgb+','+alpha+')'); gr.addColorStop(0.45,'rgba('+rgb+','+(alpha*0.55)+')'); gr.addColorStop(1,'rgba('+rgb+',0)');
      g.fillStyle=gr; g.fillRect(0,0,W,H);
    }
    function frame(now){
      if(!cv){ cv=$('ld-sirens'); if(!cv||!cv.getContext) return; g=cv.getContext('2d'); addEventListener('resize',size); }
      size(); if(reduce&&still) return;
      const t=reduce?0.4:now/1000, M=Math.max(W,H);
      g.clearRect(0,0,W,H);
      for(const L of LIGHTS){
        const a=(t/L.per)*2*Math.PI+L.ph;
        const face=Math.max(0,Math.cos(a)), I=face*face*L.k;           // brightest while it faces us
        const cx=W*(0.5+0.75*Math.sin(a));                          // the lit patch sweeps across
        glow(cx, H*L.y, M*1.05, L.rgb, 0.16*I);                     // broad sweep, falling from above
        glow(W*0.5, H*0.1, M*1.3, L.rgb, 0.06*I);                   // the general glow in the room
        const w=$(L.wash); if(w) w.style.opacity=(reduce?0.12:I*0.6).toFixed(3);
      }
      still=true;
    }
    return {frame};
  })();

  /* ---- the header ambulance (v0.19h) ----
     It drives in from the right edge, slows to a stop beside the logo, turns round, and then
     drives on the spot facing right while the road runs past beneath it, as if the camera were
     following it. It drifts forward and back a little as its speed varies. It runs behind the
     nav and buttons, and is left out where the gap between the logo and the nav is too narrow
     for it (phones). With reduced motion it parks facing right and nothing moves. */
  const AMB=(function(){
    const AW=64, WR=5.6*64/72;             // drawn width and wheel radius in px
    let el=null, wrap=null, road=null, rg=null, body=null, w1=null, w2=null, lamps=null;
    let T0=0, last=0, lay=null, layAt=0, home=null, x=0, dir=-1, spin=0, s=0, prevOff=0, prevV=0, posts=[], nextPost=0;
    function layout(now){
      const top=$('ld-top'), brand=top&&top.querySelector('.ld-brand'), nav=top&&top.querySelector('.ld-nav'), auth=top&&top.querySelector('.ld-auth');
      if(!top||!brand||!auth) return null;
      const r=top.getBoundingClientRect(), b=brand.getBoundingClientRect();
      const n=(nav&&nav.offsetParent&&getComputedStyle(nav).display!=='none')?nav.getBoundingClientRect():auth.getBoundingClientRect();
      const left=b.right-r.left+8, right=n.left-r.left-10;
      return {W:r.width, left, right, fits:right-left>=AW+36};
    }
    function lights(t, face){
      const p=(t%1+1)%1, on=(a,b)=>p>=a&&p<b;
      const red=on(0,.08)||on(.16,.24), blue=on(.5,.58)||on(.66,.74);
      lamps[0].setAttribute('opacity',red?1:.35); lamps[1].setAttribute('opacity',blue?1:.35);
      lamps[2].setAttribute('opacity',red?face:0); lamps[3].setAttribute('opacity',blue?face:0);
    }
    function drawRoad(dt, v){
      if(!rg) return;
      const cw=road.width/(devicePixelRatio||1), ch=22;
      s+=v*dt;
      while(nextPost<s+cw+40){ posts.push(nextPost); nextPost+=140+Math.random()*170; }
      posts=posts.filter(p=>p-s>-20);
      rg.clearRect(0,0,cw,ch);
      rg.fillStyle='rgba(120,138,152,.55)'; rg.fillRect(0,15.2,cw,1);            // road edge
      rg.fillStyle='rgba(120,138,152,.45)';
      for(let xx=-((s%22)+22); xx<cw; xx+=22) rg.fillRect(xx,18.6,11,1.4);         // lane dashes
      rg.fillStyle='rgba(120,138,152,.35)';
      for(let xx=-((s*1.0%57)+57); xx<cw; xx+=57) rg.fillRect(xx+30,21,2,.9);     // grit on the tarmac
      for(const p of posts){ const px=p-s;                                          // roadside posts
        rg.fillStyle='rgba(120,138,152,.8)'; rg.fillRect(px,7,1.6,8.4);
        rg.fillStyle='#f0a030'; rg.fillRect(px-.2,7,2,2.2); }
    }
    function sizeRoad(L){
      const d=devicePixelRatio||1, w=Math.max(10,Math.round(L.right-L.left));
      road.style.left=L.left+'px'; road.style.width=w+'px';
      if(road.width!==w*d){ road.width=w*d; road.height=22*d; rg=road.getContext('2d'); rg.setTransform(d,0,0,d,0,0); }
    }
    function frame(now){
      if(!el){ el=$('ld-amb'); wrap=$('ld-ambwrap'); road=$('ld-road'); if(!el||!wrap||!road) return;
        body=$('ab-body'); w1=$('ab-w1'); w2=$('ab-w2'); lamps=[$('ab-r'),$('ab-b'),$('ab-rg'),$('ab-bg')]; T0=now; last=now; }
      if(!lay||now-layAt>400){ lay=layout(now); layAt=now; if(!lay) return;
        wrap.classList.toggle('off',!lay.fits); if(!lay.fits) return; sizeRoad(lay); }
      if(!lay.fits) return;
      const dt=Math.min(0.05,(now-last)/1000); last=now;
      const t=(now-T0)/1000, target=lay.left+10;
      home=home===null?target:home+(target-home)*Math.min(1,dt*4);                 // follows the logo as the header shrinks
      let v=0, off=0, lift=0, tilt=0, face=1;
      const D=Math.max(60,lay.W+20-home), TIN=Math.max(2.4,D/340+1.2), START=0.7;
      const tStop=START+TIN, tTurn=tStop+0.5, tGo=tTurn+0.8, tRun=tGo+0.35;
      if(reduce){ dir=1; x=home; lights(0.1,0.8); el.style.opacity='1'; el.style.transform='translate('+x+'px,0)'; return; }
      el.style.opacity='1';
      if(t<tStop){                                    // driving in, facing left, easing to a stop
        const p=Math.max(0,(t-START)/TIN), e=1-Math.pow(1-p,3);
        x=home+D*(1-e); dir=-1; v=D*3*Math.pow(1-p,2)/TIN;
        tilt=p>0.75?-(1-p)*6:0;                       // nose dips as it brakes
      } else if(t<tTurn){ x=home; dir=-1; }
      else if(t<tGo){                                 // turning round
        const p=(t-tTurn)/0.8; dir=-Math.cos(Math.PI*p); x=home; lift=Math.sin(Math.PI*p)*2;
      } else {
        dir=1;
        const ramp=Math.min(1,Math.max(0,(t-tRun)/1.6)), rs=ramp*ramp*(3-2*ramp);
        const u=t-tRun;
        const drift=6*Math.sin(u*0.31)+4*Math.sin(u*0.53+1.3)+2.5*Math.sin(u*1.07+0.4);
        const surge=10*Math.sin(Math.PI*Math.min(1,Math.max(0,u/2.2)));   // pulls ahead as it sets off
        off=3+surge+drift*rs;
        const vRoad=95*rs, dOff=dt>0?(off-prevOff)/dt:0; prevOff=off;
        v=vRoad+dOff; x=home+off;
        const acc=dt>0?(v-prevV)/dt:0; prevV=v; tilt=Math.max(-2.5,Math.min(2.5,-acc*0.04));
        if(vRoad>0.5) road.classList.add('on');
        drawRoad(dt,vRoad);
      }
      spin+=v*dt/WR*57.2958;
      const bob=v>5?(0.35*Math.sin(t*23)+0.2*Math.sin(t*37)):0;
      w1.setAttribute('transform','rotate('+(spin%360).toFixed(1)+' 15 29)');
      w2.setAttribute('transform','rotate('+(spin%360).toFixed(1)+' 56 29)');
      body.setAttribute('transform','translate(0 '+(bob-lift).toFixed(2)+') rotate('+tilt.toFixed(2)+' 15 29)');
      lights(t, 0.9);
      el.style.transform='translate('+x.toFixed(1)+'px,0) scaleX('+(Math.abs(dir)<0.04?0.04*Math.sign(dir||1):dir).toFixed(3)+')';
    }
    return {frame};
  })();

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
