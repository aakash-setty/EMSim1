/* ============================================================
   The pupils: a magnified view of the figure's eyes, and a penlight.
   Author instruction, 19 October 2026.

   A case that authors content_keys.pupils (a guarded rule list, first match wins, resolved
   by pupilState() in engine.js) gets a hover target over the figure's eyes. Hovering it
   opens a small window with both eyes magnified. The window closes two seconds after the
   pointer leaves, unless the pointer moves into it. Inside the window the pointer is a
   penlight: over an eye, that eye is lit, and each pupil that can still respond constricts.
   A case without the key has no target and nothing here runs.

   What is modelled, and nothing more:
     - Direct and consensual response. Light in either eye reaches both, so both pupils
       respond to light in either eye unless a pupil cannot respond at all. The afferent
       side is always intact here: there is no relative afferent defect yet.
     - Five states. normal; pinpoint (small, a response too small to see well); dilated;
       dilated_fixed (large, no response in either eye); blown (one pupil large and fixed,
       the other normal and still constricting to light in either eye).
     - A short latency before the pupil moves, a faster constriction than redilation, and
       a sluggish pupil that is slower and moves less.
   The sizes and timings below are teaching values chosen by the model, not measurements.
   A case may override the resting size (size_mm) and the reaction (brisk, sluggish, none).
   For blown, affected_mm and affected_reaction override the affected eye's 8 mm and none
   (19 October 2026, author instruction, for a pupil partly back after treatment).

   This module draws its own eyes. The figure's cartoon eyes are dots and have no pupil to
   show, so the window is a separate close-up drawing, not a zoom of the figure.

   It reads ST, PT, PAUSED, ENDED, STARTED and pupilState from ui.js and engine.js at run
   time, so it must load after both. It logs nothing and scores nothing.
   ============================================================ */
const PUPILVIEW=(function(){
  'use strict';
  const NS='http://www.w3.org/2000/svg';

  /* ---------- the model ---------- */
  const PRESET={
    normal:       {rest:4.0, reaction:'brisk'},
    pinpoint:     {rest:1.5, reaction:'sluggish'},
    dilated:      {rest:7.0, reaction:'sluggish'},
    dilated_fixed:{rest:8.0, reaction:'none'},
    blown:        {rest:4.0, reaction:'brisk'}       /* the unaffected eye */
  };
  const BLOWN={rest:8.0, reaction:'none'};           /* the affected eye */
  /* k: how far toward the smallest size a lit pupil goes. lat: seconds before it moves.
     con and dil: time constants of constriction and redilation, in seconds. */
  const KIN={
    brisk:   {k:0.55, lat:0.22, con:0.20, dil:0.90},
    sluggish:{k:0.18, lat:0.45, con:0.75, dil:1.60},
    none:    {k:0,    lat:0,    con:1,    dil:1}
  };
  const MIN_MM=1.2;
  /* The penlight is drawn 56 px square from a 120 unit box and turned to point up and left;
     its bulb sits at (31.8, 34.6) in that box. The bulb is held a little below and right of
     the pointer, which is where the beam falls, so the pen never covers the pupil it lights. */
  const PEN_PX=56, PEN_TIP={x:31.8*PEN_PX/120-16, y:34.6*PEN_PX/120-16};
  const CLOSE_MS=2000, OPEN_INTENT_MS=120;

  /* Each eye as the window draws it. 'R' is the patient's right, drawn on the viewer's left. */
  function eyesFor(v){
    const base=PRESET[v.state]||PRESET.normal;
    const rest=typeof v.size_mm==='number'?v.size_mm:base.rest;
    const reaction=v.reaction||base.reaction;
    const eye=(r,re)=>{ const kin=KIN[re]||KIN.brisk;
      return {rest:r, lit:Math.max(Math.min(MIN_MM,r), r-(r-MIN_MM)*kin.k), reaction:re, kin:kin}; };
    const one=eye(rest,reaction);
    if(v.state==='blown'){
      /* affected_mm and affected_reaction draw the affected pupil when it is not yet, or no
         longer, at its largest: a pupil partly back after treatment, say. */
      const bsize=typeof v.affected_mm==='number'?v.affected_mm
        :(typeof v.size_mm==='number'?Math.max(v.size_mm,BLOWN.rest):BLOWN.rest);
      const blown=eye(bsize,v.affected_reaction||BLOWN.reaction);
      return v.side==='left'?{R:one,L:blown}:{R:blown,L:eye(rest,reaction)};
    }
    if(v.state==='dilated_fixed') { const f=eye(rest,'none'); return {R:f,L:eye(rest,'none')}; }
    return {R:one,L:eye(rest,reaction)};
  }

  /* ---------- state ---------- */
  let hot=null, win=null, svg=null, pen=null, parts=null;
  let open=false, inWin=false, overHot=false, closeTimer=0, openTimer=0;
  let current=null, currentKey='';
  const S={R:{size:4,effLit:false,changeAt:0}, L:{size:4,effLit:false,changeAt:0}};
  let lit={R:false,L:false}, beam=null, lastT=0, raf=0;

  function available(){
    try{
      if(typeof pupilState!=='function'||!ST||!PT||!PT.svg) return null;
      if(!STARTED||ENDED||PAUSED) return null;
      const sp=document.getElementById('splash'); if(sp&&!sp.classList.contains('hidden')) return null;
      const stage=document.getElementById('patientstage');
      if(stage&&parseFloat(getComputedStyle(stage).opacity)<0.5) return null;
      const p=pupilState(ST);
      return p&&p.value?p:null;
    }catch(e){ return null; }
  }

  /* ---------- the hover target over the figure's eyes ---------- */
  function ensureHot(){
    if(hot) return hot;
    hot=document.createElement('button');
    hot.type='button'; hot.id='pv-hot'; hot.className='pv-hot'; hot.hidden=true;
    hot.setAttribute('aria-label','Look closely at the eyes');
    hot.addEventListener('pointerenter',e=>{ overHot=true; cancelClose();
      if(!open){ clearTimeout(openTimer); openTimer=setTimeout(()=>{ if(overHot) show(); },e.pointerType==='touch'?0:OPEN_INTENT_MS); } });
    hot.addEventListener('pointerleave',()=>{ overHot=false; clearTimeout(openTimer); if(open&&!inWin) scheduleClose(); });
    hot.addEventListener('click',()=>{ if(!open) show(); if(win) win.focus({preventScroll:true}); });
    document.body.appendChild(hot);
    return hot;
  }
  /* The figure's eyes in the 264 by 280 viewBox are at (106,112) and (158,112), inside the
     head rig, so mapping through the head's screen matrix follows the head as it bobs,
     tilts and shakes. */
  function eyeBox(){
    const head=PT.rig&&PT.rig.head; if(!head||!head.getScreenCTM) return null;
    const m=head.getScreenCTM(); if(!m) return null;
    const pt=PT.svg.createSVGPoint();
    const map=(x,y)=>{ pt.x=x; pt.y=y; return pt.matrixTransform(m); };
    const c=[map(84,98),map(180,98),map(84,126),map(180,126)];
    const xs=c.map(p=>p.x), ys=c.map(p=>p.y);
    return {x:Math.min.apply(null,xs), y:Math.min.apply(null,ys),
            w:Math.max.apply(null,xs)-Math.min.apply(null,xs), h:Math.max.apply(null,ys)-Math.min.apply(null,ys)};
  }
  function placeHot(p){
    ensureHot();
    const b=p?eyeBox():null;
    if(!b||b.w<8){ if(!hot.hidden){ hot.hidden=true; } return; }
    hot.hidden=false;
    hot.style.transform='translate('+Math.round(b.x)+'px,'+Math.round(b.y)+'px)';
    hot.style.width=Math.round(b.w)+'px'; hot.style.height=Math.round(b.h)+'px';
  }

  /* ---------- the window ---------- */
  function el(tag,attrs,parent){ const e=document.createElementNS(NS,tag);
    for(const k in attrs) e.setAttribute(k,attrs[k]); if(parent) parent.appendChild(e); return e; }
  const W=440, H=176, EYE_Y=96, EYE_X={R:110,L:330}, IRIS_R=33, PX_PER_MM=IRIS_R*2/11.5;

  function buildWindow(){
    win=document.createElement('div');
    win.id='pv-win'; win.className='pv-win'; win.hidden=true; win.tabIndex=-1;
    win.setAttribute('role','dialog'); win.setAttribute('aria-label','The eyes, close up');
    win.innerHTML='<div class="pv-head"><span class="pv-title">Pupils</span>'
      +'<span class="pv-lids" hidden>Lids held open</span>'
      +'<span class="pv-hint">Move the light over an eye</span></div>';
    svg=el('svg',{viewBox:'0 0 '+W+' '+H,class:'pv-svg',role:'img','aria-label':'Both eyes, magnified'});
    win.appendChild(svg);
    const defs=el('defs',{},svg);
    const u='pv';
    const rg=(id,stops,attrs)=>{ const g=el('radialGradient',Object.assign({id:id},attrs||{}),defs);
      stops.forEach(s=>el('stop',{offset:s[0],'stop-color':s[1],'stop-opacity':s[2]===undefined?1:s[2]},g)); return g; };
    rg(u+'-sclera',[[0,'#FBF8F3'],[0.7,'#F1EBE2'],[1,'#D9CBBD']],{cx:'50%',cy:'45%',r:'60%'});
    rg(u+'-glow',[[0,'#FFF8E6',0.95],[0.35,'#FFF2CC',0.55],[1,'#FFF2CC',0]]);
    rg(u+'-hole',[[0,'#000'],[0.55,'#000'],[1,'#fff']]);
    rg(u+'-skin',[[0,'#000',0],[1,'#000',0.28]],{cx:'50%',cy:'50%',r:'75%'});
    /* the beam: dark everywhere except a soft circle where the light falls */
    const mask=el('mask',{id:u+'-beam',maskUnits:'userSpaceOnUse',x:0,y:0,width:W,height:H},defs);
    el('rect',{x:0,y:0,width:W,height:H,fill:'#fff'},mask);
    const hole=el('circle',{cx:-200,cy:-200,r:70,fill:'url(#'+u+'-hole)'},mask);

    const skin=el('rect',{x:0,y:0,width:W,height:H,class:'pv-skin'},svg);
    el('rect',{x:0,y:0,width:W,height:H,fill:'url(#'+u+'-skin)'},svg);
    /* the warm spill of the penlight on the skin. Drawn under the eyes so it never washes
       out the iris and pupil it is lighting. */
    const glow=el('circle',{cx:-200,cy:-200,r:66,fill:'url(#'+u+'-glow)',class:'pv-glow'},svg);
    /* brows and the bridge of the nose, drawn soft so the eyes carry the picture */
    el('path',{d:'M'+(EYE_X.R-64)+' 30 Q'+EYE_X.R+' 8 '+(EYE_X.R+64)+' 28',class:'pv-brow'},svg);
    el('path',{d:'M'+(EYE_X.L-64)+' 28 Q'+EYE_X.L+' 8 '+(EYE_X.L+64)+' 30',class:'pv-brow'},svg);

    const eyes={};
    ['R','L'].forEach(side=>{
      const x=EYE_X[side], y=EYE_Y;
      const g=el('g',{class:'pv-eye',tabindex:0,role:'button',
        'aria-label':'Shine the light in the patient\'s '+(side==='R'?'right':'left')+' eye'},svg);
      const open='M'+(x-74)+' '+y+' Q'+x+' '+(y-64)+' '+(x+74)+' '+y+' Q'+x+' '+(y+50)+' '+(x-74)+' '+y+' Z';
      const cp=el('clipPath',{id:u+'-o'+side},defs); el('path',{d:open},cp);
      el('path',{d:'M'+(x-80)+' '+(y-6)+' Q'+x+' '+(y-76)+' '+(x+80)+' '+(y-6),class:'pv-crease'},g);
      el('path',{d:open,fill:'url(#'+u+'-sclera)'},g);
      const inner=el('g',{'clip-path':'url(#'+u+'-o'+side+')'},g);
      el('circle',{cx:x,cy:y,r:IRIS_R,class:'pv-iris'},inner);
      /* striations: thin spokes from the collarette outward */
      const spokes=el('g',{class:'pv-spokes'},inner);
      for(let i=0;i<36;i++){ const a=i*Math.PI/18+(side==='L'?0.05:0), r1=IRIS_R*0.42, r2=IRIS_R*0.95;
        el('line',{x1:x+r1*Math.cos(a),y1:y+r1*Math.sin(a),x2:x+r2*Math.cos(a),y2:y+r2*Math.sin(a)},spokes); }
      el('circle',{cx:x,cy:y,r:IRIS_R,class:'pv-limbus'},inner);
      const pupil=el('circle',{cx:x,cy:y,r:10,class:'pv-pupil'},inner);
      el('ellipse',{cx:x-11,cy:y-13,rx:6,ry:4,class:'pv-shine'},inner);
      const glint=el('circle',{cx:x,cy:y,r:2.6,class:'pv-glint',opacity:0},inner);
      /* shadow of the upper lid on the globe, and the lid margins */
      el('path',{d:'M'+(x-74)+' '+y+' Q'+x+' '+(y-64)+' '+(x+74)+' '+y+' Q'+x+' '+(y-40)+' '+(x-74)+' '+y+' Z',class:'pv-lidshade'},inner);
      el('path',{d:'M'+(x-74)+' '+y+' Q'+x+' '+(y-64)+' '+(x+74)+' '+y,class:'pv-lidline'},g);
      el('path',{d:'M'+(x-74)+' '+y+' Q'+x+' '+(y+50)+' '+(x+74)+' '+y,class:'pv-lowline'},g);
      const lash=el('g',{class:'pv-lash'},g);
      for(let i=1;i<12;i++){ const t=i/12, px=(1-t)*(1-t)*(x-74)+2*(1-t)*t*x+t*t*(x+74), py=(1-t)*(1-t)*y+2*(1-t)*t*(y-64)+t*t*y;
        const dx=(t-0.5)*10; el('line',{x1:px,y1:py,x2:px+dx*0.9,y2:py-7},lash); }
      const lab=el('text',{x:x,y:H-8,'text-anchor':'middle',class:'pv-side'},svg);
      lab.textContent=side==='R'?'Right':'Left';
      eyes[side]={g:g,pupil:pupil,glint:glint,x:x,y:y};
      g.addEventListener('focus',()=>{ lit={R:side==='R',L:side==='L'}; beam={x:x,y:y}; });
      g.addEventListener('blur',()=>{ lit={R:false,L:false}; beam=null; });
    });
    /* the dark room around the beam, and the beam itself */
    const dark=el('rect',{x:0,y:0,width:W,height:H,class:'pv-dark',mask:'url(#'+u+'-beam)'},svg);
    parts={eyes:eyes,skin:skin,hole:hole,dark:dark,glow:glow,lids:win.querySelector('.pv-lids')};

    pen=document.createElement('div'); pen.className='pv-pen'; pen.hidden=true;
    pen.innerHTML='<svg viewBox="0 0 120 120" aria-hidden="true"><g transform="rotate(-138 60 60)">'
      +'<rect x="8" y="53" width="78" height="14" rx="6" class="pv-pen-body"/>'
      +'<rect x="84" y="51" width="14" height="18" rx="3" class="pv-pen-cap"/>'
      +'<rect x="24" y="49" width="30" height="4" rx="2" class="pv-pen-clip"/>'
      +'<circle cx="98" cy="60" r="5" class="pv-pen-bulb"/></g></svg>';
    document.body.appendChild(pen);

    win.addEventListener('pointerenter',()=>{ inWin=true; cancelClose(); setPen(true); });
    win.addEventListener('pointerleave',()=>{ inWin=false; lit={R:false,L:false}; beam=null; setPen(false); if(!overHot) scheduleClose(); });
    win.addEventListener('pointermove',onMove);
    win.addEventListener('pointerdown',e=>{ if(e.pointerType==='touch'){ inWin=true; cancelClose(); onMove(e); } });
    win.addEventListener('pointerup',e=>{ if(e.pointerType==='touch'){ lit={R:false,L:false}; beam=null; scheduleClose(); } });
    win.addEventListener('keydown',e=>{ if(e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); hide(); } });
    win.addEventListener('focusout',e=>{ if(!win.contains(e.relatedTarget)&&!inWin&&!overHot) scheduleClose(); });
    document.body.appendChild(win);
  }
  function setPen(on){ if(!pen) return; pen.hidden=!on; win.classList.toggle('pv-lighting',!!on); }
  function onMove(e){
    if(!svg) return;
    const m=svg.getScreenCTM(); if(!m) return;
    const pt=svg.createSVGPoint(); pt.x=e.clientX; pt.y=e.clientY;
    const p=pt.matrixTransform(m.inverse());
    beam={x:p.x,y:p.y};
    const near=s=>{ const E=parts.eyes[s]; return Math.hypot(p.x-E.x,p.y-E.y)<=IRIS_R+8; };
    lit={R:near('R'),L:near('L')};
    /* the penlight's lit tip sits on the pointer */
    pen.style.transform='translate('+(e.clientX-PEN_TIP.x)+'px,'+(e.clientY-PEN_TIP.y)+'px)';
  }

  function place(){
    const b=hot&&!hot.hidden?hot.getBoundingClientRect():null; if(!b) return;
    const w=Math.min(W+2,window.innerWidth-16);
    win.style.width=w+'px';
    const h=win.getBoundingClientRect().height||H+34;     /* measured after the width is set */
    /* Above the eyes, so the face stays in view, unless that would run under the header;
       then below. */
    const stage=document.getElementById('patientstage');
    const top=(stage?stage.getBoundingClientRect().top:0)+8;
    let x=b.left+b.width/2-w/2, y=b.top-18-h;
    if(y<top) y=b.bottom+18;
    if(y+h>window.innerHeight-8) y=Math.max(top,window.innerHeight-8-h);
    x=Math.max(8,Math.min(x,window.innerWidth-w-8));
    win.style.transform='translate('+Math.round(x)+'px,'+Math.round(y)+'px)';
  }
  function show(){
    const p=available(); if(!p) return;
    if(!win) buildWindow();
    setModel(p,true);
    win.hidden=false; open=true; place();
    win.classList.remove('pv-in'); void win.offsetWidth; win.classList.add('pv-in');
  }
  function hide(){
    clearTimeout(closeTimer); clearTimeout(openTimer);
    if(!win) return;
    win.hidden=true; open=false; inWin=false; lit={R:false,L:false}; beam=null; setPen(false);
  }
  function scheduleClose(){ clearTimeout(closeTimer); closeTimer=setTimeout(()=>{ if(!inWin&&!overHot) hide(); },CLOSE_MS); }
  function cancelClose(){ clearTimeout(closeTimer); }

  function setModel(p,snap){
    const key=JSON.stringify(p.value)+'|'+(p.iris||'');
    if(key===currentKey&&!snap) return;
    currentKey=key; current=eyesFor(p.value);
    if(snap){ S.R.size=current.R.rest; S.L.size=current.L.rest; S.R.effLit=S.L.effLit=false; }
    if(parts){
      parts.skin.setAttribute('fill',(PT&&PT._skin)||'#D08B5B');
      svg.style.setProperty('--pv-iris',p.iris||'#5A3B22');
    }
  }

  /* ---------- the frame ---------- */
  function step(t){
    raf=requestAnimationFrame(step);
    const p=available();
    placeHot(p);
    if(!p){ if(open) hide(); return; }
    if(!open){ lastT=t; return; }
    setModel(p,false);
    const dt=Math.min(0.1,lastT?(t-lastT)/1000:0); lastT=t;
    const now=t/1000;
    const anyLit=lit.R||lit.L;               /* light in either eye reaches both */
    for(const side of ['R','L']){
      const e=current[side], s=S[side], k=e.kin;
      if(anyLit!==s.wantLit){ s.wantLit=anyLit; s.changeAt=now; }
      if(s.effLit!==s.wantLit&&now-s.changeAt>=(s.wantLit?k.lat:k.lat*0.6)) s.effLit=s.wantLit;
      const target=(s.effLit&&e.reaction!=='none')?e.lit:e.rest;
      const tau=target<s.size?k.con:k.dil;
      s.size+=(target-s.size)*(1-Math.exp(-dt/Math.max(0.05,tau)));
      const E=parts.eyes[side];
      E.pupil.setAttribute('r',(s.size/2*PX_PER_MM).toFixed(2));
      /* the corneal reflection of the penlight, on the lit eye, toward the light */
      /* Off the pupil's centre, up and toward the nose side, so the reflection never hides a
         pinpoint pupil; it drifts a little with the light. */
      if(lit[side]&&beam){ const dx=-12+Math.max(-5,Math.min(5,(beam.x-E.x)*0.15)), dy=-11+Math.max(-5,Math.min(5,(beam.y-E.y)*0.15));
        E.glint.setAttribute('cx',(E.x+dx).toFixed(1)); E.glint.setAttribute('cy',(E.y+dy).toFixed(1)); E.glint.setAttribute('opacity','1'); }
      else E.glint.setAttribute('opacity','0');
    }
    const bx=beam?beam.x:-200, by=beam?beam.y:-200;
    parts.hole.setAttribute('cx',bx); parts.hole.setAttribute('cy',by);
    parts.glow.setAttribute('cx',bx); parts.glow.setAttribute('cy',by);
    const closed=PT&&PT.state&&(PT.state.eyes==='closed'||(PT.state.alertness||0)>=2);
    if(parts.lids.hidden===!!closed) parts.lids.hidden=!closed;
  }
  function start(){ if(!raf) raf=requestAnimationFrame(step); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&open) hide(); });
  window.addEventListener('resize',()=>{ if(open) place(); });

  /* For the tests: the drawn eye model for a value, and the window's live sizes. */
  return {eyesFor:eyesFor, hide:hide, show:show, _sizes:()=>({R:S.R.size,L:S.L.size}), _lit:v=>{ if(v) lit=v; return lit; },
          isOpen:()=>open, PRESET:PRESET, KIN:KIN};
})();
