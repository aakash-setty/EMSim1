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
    V=Object.assign({},START); done=new Set(); over=false; t0=performance.now(); lastTick=t0;
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
      $('ld-overtext').textContent='His saturation is up, but his blood pressure is still high and his lungs are still full of fluid. What you do next decides how this goes.';
    }else{
      $('ld-overtitle').textContent="He's tiring.";
      $('ld-overtext').textContent='Every minute on this monitor counts, and he needs more than oxygen. Take over the whole case: history, exam, orders and treatment.';
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

  /* ---- the monitor traces ---- */
  let ecgX=0, plX=0, lastDraw=0, beatPhase=0;
  function ecgAt(ph){ // one beat, phase 0..1
    const g=(m,w,a)=>a*Math.exp(-Math.pow((ph-m)/w,2));
    return g(.16,.03,.12)+g(.30,.008,-.14)+g(.33,.012,1)+g(.36,.01,-.25)+g(.58,.05,.28);
  }
  function drawTraces(now){
    const dt=lastDraw?Math.min(64,now-lastDraw):16; lastDraw=now;
    const beats=V.hr/60*dt/1000; beatPhase=(beatPhase+beats)%1;
    [['ld-ecg','#3EE08F',()=>ecgAt(beatPhase),x=>ecgX=x,()=>ecgX],
     ['ld-pleth','#5FC8FF',()=>{const p=(beatPhase+.85)%1; return Math.max(0,Math.sin(Math.PI*Math.min(1,p*1.6)))*(1-p*.4)*(V.sp/100);},x=>plX=x,()=>plX]]
    .forEach(([id,col,fn,setX,getX])=>{
      const c=$(id); if(!c) return;
      const w=c.clientWidth|0, h=c.height; if(!w) return;
      if(c.width!==w){ c.width=w; setX(0); }
      const ctx=c.getContext('2d'), speed=w/4*dt/1000;
      let x=getX(); const nx=x+speed;
      ctx.clearRect(x,0,speed+14,h);
      ctx.strokeStyle=col; ctx.lineWidth=1.8; ctx.beginPath();
      const y=h*0.72-fn()*h*0.6;
      ctx.moveTo(x,c._y==null?y:c._y); ctx.lineTo(nx,y); ctx.stroke(); c._y=y;
      setX(nx>=w?0:nx); if(nx>=w) c._y=null;
    });
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
