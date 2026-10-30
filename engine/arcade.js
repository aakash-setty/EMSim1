/* ---------- Ambulance Run (29 October 2026) ----------
   A small arcade game on the case list, opened from the ambulance button in the bottom left
   corner. Steer an ambulance down a three lane road with the arrow keys. Things block one lane
   each. The road speeds up. Hitting anything ends the run.

   Owner request, 29 October 2026: "Create a small ambulance obstacle avoidance game ... the
   road slowly speeds up. hitting ends the game. option to replay. there is a leaderboard if
   you are in top 10 that will be shared across all accounts and you can choose what your
   name is."

   The rules (RULES, newGame, step) are plain functions with no page, so engine/arcade-tests.js
   can run them. The drawing, the window and the leaderboard come after.

   Leaderboard. In the site, scores are shared through Supabase
   (the Supabase migration 003_arcade.sql): the browser calls arcade_start when a run begins and
   arcade_finish to post a score with a name. The database refuses a score higher than the
   time since arcade_start allows (RULES.vmax points a second, with margin), keeps the best
   100 and returns the top 10 to anyone. Playing needs no account; posting needs a signed-in
   account. The local build has no backend and keeps its top 10 in this browser only.

   Nothing here names a case, a drug or a diagnosis. Not part of any case or score. */
const ARCADE = (function(){
  /* ================= the rules ================= */
  const RULES = {
    lanes: 3,           // lanes, numbered 0 (left) to 2 (owner, 30 October 2026: was 4)
    laneW: 4.0,         // m, so the road stays about as wide as it was
    v0: 46,             // m/s at the start (about 103 mph). Owner: 28, then 42, then 46 on 30 October ("harder")
    accel: 0.55,        // m/s gained each second (was 0.45)
    vmax: 76,           // m/s cap (about 170 mph; was 72). Points are meters, so at most 76 a second.
                        // The database allows 80 (003_arcade.sql); arcade-tests.js checks it
    laneRate: 6.5,      // lanes a second while changing lane
    playerZ: 8,         // m from the camera to the back of the ambulance
    carLen: 4.6,        // m
    hitHalf: 0.6,       // lanes: centers closer than this touch
    spawnZ: 125,        // m: rows appear this far ahead
    firstRowZ: 70       // m: the first row
  };
  const KINDS = [
    {id:'gurney',  len:2.1, label:'a runaway stretcher'},
    {id:'cones',   len:0.8, label:'the traffic cones'},
    {id:'pothole', len:2.2, label:'a pothole'},
    {id:'sofa',    len:1.0, label:'a sofa that fell off a truck'},
    {id:'ducks',   len:0.8, label:'the ducks. They had right of way'},
    {id:'scooter', len:1.8, label:'a parked pizza scooter'},
    {id:'cart',    len:1.0, label:'a shopping cart'},
    {id:'barrier', len:0.5, label:'a road barrier'},
    {id:'flamingo',len:1.2, label:'an inflatable flamingo'},
    {id:'gator',   len:1.2, label:'an alligator'},
    {id:'mattress',len:2.0, label:'a mattress'},
    {id:'hotdog',  len:1.6, label:'a hot dog cart'}
  ];
  const MAXLEN = Math.max(...KINDS.map(k=>k.len));
  const clamp=(v,a,b)=>v<a?a:v>b?b:v;
  /* A small seeded generator, so tests repeat. */
  function rng(seed){ let a=(seed>>>0)||1; return ()=>{ a=(a+0x6D2B79F5)>>>0; let t=a; t=Math.imul(t^t>>>15,t|1); t^=t+Math.imul(t^t>>>7,t|61); return ((t^t>>>14)>>>0)/4294967296; }; }
  const speedAt = t => Math.min(RULES.vmax, RULES.v0 + RULES.accel*t);
  /* Meters between rows: 50 at the start, closing by 0.18 m a second to 30 at about 111 s
     (30 October 2026, harder; was 54 and 0.16)
     (owner, 29 October 2026: close more slowly, start with more coming). */
  const rowGap = t => Math.max(30, 50 - 0.18*t);

  function newGame(seed){
    const g={t:0, v:RULES.v0, dist:0, x:1, target:1, obs:[], rowZ:RULES.firstRowZ, path:1,
      rand:rng(seed==null?(Math.random()*2**32):seed), over:false, hit:null, rows:0, marks:[]};
    spawnRow(g, RULES.firstRowZ);
    return g;
  }
  /* How many lanes the player can move between two rows that pass dt seconds apart. A row is
     beside the ambulance for (row length + ambulance length) / v, and the ambulance must be
     fully in a lane then. 0.1 s is left for reaction. */
  function reachFor(gap, v){
    const free = gap/v - (MAXLEN+RULES.carLen)/v - 0.1;
    return Math.max(0, Math.floor(free*RULES.laneRate));
  }
  /* A row blocks one to three lanes. One lane, `path`, is always open, and it never moves
     further from the last row's open lane than the player can steer in the time between. */
  function spawnRow(g, z){
    const t=g.t, r=g.rand, L=RULES.lanes;
    const gap=g.lastGap||rowGap(t), reach=Math.min(L-1, reachFor(gap, speedAt(t+ (z-RULES.playerZ)/speedAt(t))));
    if(g.rows>0) g.path=clamp(g.path+Math.round((r()*2-1)*reach), 0, L-1);
    /* Lanes blocked per row: 1.15 on average at the start, rising to 1.8 at 120 s and no more,
       the same obstacles a second as on four lanes (owner, 30 October 2026). With three lanes
       a row blocks one or two, so two-lane rows carry it: 15% at the start, 50% at 90 s, 80%
       from 120 s. */
    /* 30 October 2026, harder: 25% at the start (was 15%), 85% from 120 s (was 80%). */
    const p2=0.25+0.30*clamp(t/90,0,1)+0.30*clamp((t-40)/80,0,1);
    const u=r(), n = Math.min(RULES.lanes-1, u<p2 ? 2 : 1);
    const open=[...Array(L).keys()].filter(i=>i!==g.path);
    for(let k=0;k<n;k++){
      const j=Math.floor(r()*open.length), lane=open.splice(j,1)[0];
      const kind=KINDS[Math.floor(r()*KINDS.length)];
      g.obs.push({lane, z, kind:kind.id, len:kind.len, seed:Math.floor(r()*1000)});
    }
    g.marks.push({z, path:g.path});
    g.rows++;
  }
  /* One frame. input: {left, right} presses since the last frame (counts). */
  function step(g, dt, input){
    if(g.over) return g;
    dt=clamp(dt,0,0.1);
    if(input){
      if(input.left)  g.target=clamp(g.target-input.left, 0, RULES.lanes-1);
      if(input.right) g.target=clamp(g.target+input.right, 0, RULES.lanes-1);
    }
    g.t+=dt; g.v=speedAt(g.t);
    const d=g.v*dt; g.dist+=d;
    const dx=g.target-g.x, mv=RULES.laneRate*dt;
    g.x = Math.abs(dx)<=mv ? g.target : g.x+Math.sign(dx)*mv;
    for(const o of g.obs) o.z-=d;
    for(const m of g.marks) m.z-=d;
    g.rowZ-=d;
    while(g.rowZ < RULES.spawnZ){
      const gap=rowGap(g.t)*(0.88+0.24*g.rand()); g.lastGap=gap;
      g.rowZ+=gap; spawnRow(g, g.rowZ);
    }
    g.obs=g.obs.filter(o=>o.z+o.len > -2);
    g.marks=g.marks.filter(m=>m.z+MAXLEN > -2);
    const back=RULES.playerZ, front=RULES.playerZ+RULES.carLen;
    for(const o of g.obs){
      if(o.z < front && o.z+o.len > back && Math.abs(g.x-o.lane) < RULES.hitHalf){ g.over=true; g.hit=o; break; }
    }
    return g;
  }
  const scoreOf = g => Math.floor(g.dist);
  const rules = {RULES, KINDS, newGame, step, speedAt, rowGap, reachFor, scoreOf, rng};

  /* In node (the tests) there is no page: stop here. */
  if(typeof document==='undefined') return {rules};

  /* ================= the page ================= */
  const CFG=(typeof ACCESS==='object'&&ACCESS)||{mode:'local'};
  const SITE=CFG.mode==='site';
  const A=(typeof ANALYTICS==='object'&&ANALYTICS)||{track(){}};
  const $=id=>document.getElementById(id);
  const esc=t=>String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const NAME_KEY='emsim.arcadeName', LOCAL_KEY='emsim.arcadeTop', SOUND_KEY='emsim.arcadeSound';
  const NAME_RE=/^[A-Za-z0-9 ._!?'-]{1,16}$/;
  const store={get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } },
               set(k,v){ try{ localStorage.setItem(k,v); }catch(e){} }};
  const fmt=n=>Number(n||0).toLocaleString('en-US');

  let client=null, session=null;
  let open=false, lastFocus=null, raf=0, lastT=0;
  let g=null, mode='title';            // title | play | paused | over
  let press={left:0,right:0};
  let runId=null, runReady=null;       // the server's id for this run, when signed in
  let top=[], topState='idle', topErr='';
  let posted=false, postMsg='', postBusy=false, best=0;
  let banner='', bannerT=0, nextLine=6;
  let sound=store.get(SOUND_KEY)==='1';

  /* ---- leaderboard ---- */
  const signedIn=()=>!!(session&&session.user);
  function localTop(){ try{ const a=JSON.parse(store.get(LOCAL_KEY)||'[]'); return Array.isArray(a)?a:[]; }catch(e){ return []; } }
  async function loadTop(){
    topState='loading'; topErr=''; paintBoard();
    try{
      if(SITE){
        if(!client) throw new Error('none');
        const {data,error}=await client.rpc('arcade_top'); if(error) throw error;
        top=(data||[]).map(r=>({name:r.name, score:r.score, mine:!!r.mine}));
      } else top=localTop();
      topState='ready';
    }catch(e){ topState='error'; topErr='The leaderboard could not be loaded.'; }
    paintBoard(); paintHud();
  }
  const cutoff=()=> top.length<10 ? 0 : top[9].score;
  const qualifies=s=> s>0 && (top.length<10 || s>top[9].score);
  function beginRun(){
    runId=null; runReady=null;
    if(!SITE||!client||!signedIn()) return;
    runReady=client.rpc('arcade_start').then(({data,error})=>{ if(!error) runId=data; return runId; }).catch(()=>null);
  }
  async function postScore(name){
    const s=scoreOf(g);
    name=String(name||'').trim().replace(/\s+/g,' ');
    if(!NAME_RE.test(name)){ postMsg='Use 1 to 16 letters, numbers, spaces or . _ ! ? \' -'; paintOver(); return; }
    name=name.toUpperCase(); store.set(NAME_KEY,name);
    postBusy=true; postMsg=''; paintOver();
    try{
      if(SITE){
        if(runReady) await runReady;
        if(!runId) throw Object.assign(new Error('norun'),{msg:'This run was not registered, so it cannot be posted. Sign in before you start a run.'});
        const {data,error}=await client.rpc('arcade_finish',{p_run:runId, p_score:s, p_name:name});
        if(error) throw Object.assign(error,{msg: /not possible/i.test(error.message||'')?'The server could not confirm that score.':'The score could not be posted. Try again.'});
        top=(data||[]).map(r=>({name:r.name, score:r.score, mine:!!r.mine}));
        runId=null;
      } else {
        const a=localTop(); a.push({name, score:s, mine:true});
        a.sort((x,y)=>y.score-x.score); top=a.slice(0,10); store.set(LOCAL_KEY, JSON.stringify(top));
      }
      posted=true; postMsg='Posted.';
      A.track('arcade_score_posted',{score:s});
    }catch(e){ postMsg=(e&&e.msg)||'The score could not be posted. Try again.'; }
    postBusy=false; paintOver(); paintBoard();
    const go=$('ar-go'); if(posted&&go) go.focus();
  }

  /* ---- sound: a two-tone siren and a crash, off until turned on ---- */
  let ac=null, sirenOsc=null, sirenGain=null, sirenLfo=null;
  function audio(){ if(ac) return ac; try{ ac=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ ac=null; } return ac; }
  function sirenOn(){
    if(!sound||sirenOsc) return; const c=audio(); if(!c) return;
    if(c.state==='suspended') c.resume();
    sirenOsc=c.createOscillator(); sirenGain=c.createGain(); sirenLfo=c.createOscillator(); const lg=c.createGain();
    sirenOsc.type='triangle'; sirenOsc.frequency.value=760; sirenLfo.type='square'; sirenLfo.frequency.value=1.4; lg.gain.value=170;
    sirenLfo.connect(lg); lg.connect(sirenOsc.frequency); sirenGain.gain.value=0.025;
    sirenOsc.connect(sirenGain); sirenGain.connect(c.destination); sirenOsc.start(); sirenLfo.start();
  }
  function sirenOff(){ try{ sirenOsc&&sirenOsc.stop(); sirenLfo&&sirenLfo.stop(); }catch(e){} sirenOsc=sirenLfo=sirenGain=null; }
  function crashSound(){
    if(!sound) return; const c=audio(); if(!c) return;
    const n=c.sampleRate*0.5, b=c.createBuffer(1,n,c.sampleRate), d=b.getChannelData(0);
    for(let i=0;i<n;i++) d[i]=(Math.random()*2-1)*Math.pow(1-i/n,2.2);
    const s=c.createBufferSource(), gn=c.createGain(); gn.gain.value=0.22; s.buffer=b; s.connect(gn); gn.connect(c.destination); s.start();
  }
  function blip(){
    if(!sound) return; const c=audio(); if(!c) return;
    const o=c.createOscillator(), gn=c.createGain(); o.type='square'; o.frequency.value=520;
    gn.gain.setValueAtTime(0.03,c.currentTime); gn.gain.exponentialRampToValueAtTime(0.0001,c.currentTime+0.06);
    o.connect(gn); gn.connect(c.destination); o.start(); o.stop(c.currentTime+0.07);
  }

  /* ================= drawing =================
     The road is drawn at 320 by 240 and scaled up with square pixels. A ground point z meters
     ahead is on screen line HY + K/z, and one meter there is F/z pixels wide. */
  const W=320, H=240, HY=84, F=160, K=1092, CX=W/2;
  const sy=z=>HY+K/z, sc=z=>F/z;
  const laneX=(lane,z)=>CX+((lane-(RULES.lanes-1)/2)*RULES.laneW)*sc(z);
  let cv=null, ctx=null, stars=null, sky=null, skyCv=null;
  /* Speed (29 October 2026, measured in Chromium with the processor slowed six times): the
     blurred backdrop behind the window cost the most, then the page under it repainting. The
     window's backdrop is solid and the page under it is hidden while it is open (shell.html).
     In the game itself the sky is drawn once, the ground is written straight into pixels, and
     the score and banner touch the page only when their text changes. */
  const C={road:'#5d6470', road2:'#575e69', line:'#f4f4ee', edge:'#f2c12e', grass:'#2f8a3a', grass2:'#2a7d34',
    rumbleA:'#d33a2c', rumbleB:'#f4f4ee', shoulder:'#8a8f96'};
  function px(x,y,w,h,c){ ctx.fillStyle=c; ctx.fillRect(Math.round(x),Math.round(y),Math.max(1,Math.round(w)),Math.max(1,Math.round(h))); }
  /* A box in meters, from the bottom center of a thing at screen (cx, yb), s pixels a meter. */
  function bx(cx,yb,s,x0,y0,w,h,c){ px(cx+x0*s, yb-(y0+h)*s, w*s, h*s, c); }
  function ell(cx,cy,rx,ry,c){ ctx.fillStyle=c; ctx.beginPath(); ctx.ellipse(Math.round(cx),Math.round(cy),Math.max(1,rx),Math.max(1,ry),0,0,Math.PI*2); ctx.fill(); }

  function makeSky(){
    const r=rng(7); stars=[...Array(46)].map(()=>[Math.floor(r()*W), Math.floor(r()*(HY-26)), r()<0.2?2:1]);
    /* The skyline: a coastal city at the far end of the road. */
    sky=[]; let x=-4;
    while(x<W){ const w=6+Math.floor(r()*14), h=6+Math.floor(r()*(Math.abs(x-CX)<70?34:16)); sky.push([x,w,h, r()]); x+=w+(r()<0.3?3:0); }
  }
  /* The sky in two layers drawn once: behind the clouds (gradient, moon) and in front of them
     (the skyline and the palms). Each frame adds only the twinkling stars and three clouds. */
  function bakeSky(){
    const mk=()=>{ const c=document.createElement('canvas'); c.width=W; c.height=HY; return c; };
    const back=mk(), front=mk(), keep=ctx;
    ctx=back.getContext('2d');
    const gr=ctx.createLinearGradient(0,0,0,HY); gr.addColorStop(0,'#0b1840'); gr.addColorStop(1,'#26407a');
    ctx.fillStyle=gr; ctx.fillRect(0,0,W,HY);
    ell(222,40,9,9,'#f3efd6'); ell(218,38,2,2,'#dcd6b8'); ell(226,43,1.5,1.5,'#dcd6b8');
    ctx=front.getContext('2d');
    for(const [x,w,h,u] of sky){
      px(x, HY-h, w, h, u<0.5?'#1a2a4f':'#22355e');
      for(let yy=HY-h+2; yy<HY-1; yy+=3) for(let xx=x+1; xx<x+w-1; xx+=3)
        if(((xx*7+yy*13)%11)<4) px(xx,yy,1,1,'#f2d27a');
    }
    for(const x0 of [22,58,276,300]){ px(x0,HY-14,1,14,'#2b2a22'); ell(x0-3,HY-15,4,1.5,'#1d4d2a'); ell(x0+4,HY-15,4,1.5,'#1d4d2a'); }
    ctx=keep; skyCv={back, front};
  }
  function drawSky(t){
    if(!skyCv) bakeSky();
    ctx.drawImage(skyCv.back,0,0);
    for(const s of stars) px(s[0],s[1],s[2],s[2], (Math.floor(t*2+s[0])%7===0)?'#9fb4e8':'#e8eeff');
    /* Clouds drift right. */
    for(let i=0;i<3;i++){
      const cx=((i*121+t*4)%(W+60))-30, cy=16+i*13;
      ell(cx,cy,12,4,'#e9eef8'); ell(cx-8,cy+1,7,3,'#e9eef8'); ell(cx+9,cy+1,8,3,'#cfd8ea');
    }
    ctx.drawImage(skyCv.front,0,0);
  }
  /* The ground, written straight into a pixel buffer one screen line at a time, then put on
     the canvas in one call. Same shapes and rounding as px(). */
  let gImg=null, g32=null, G=null;
  function rgba(hex){ const n=parseInt(hex.slice(1),16); return (255<<24|(n&255)<<16|((n>>8)&255)<<8|(n>>16))>>>0; }
  function drawGround(dist){
    if(!gImg){ gImg=ctx.createImageData(W,H-HY); g32=new Uint32Array(gImg.data.buffer); G={}; for(const k in C) G[k]=rgba(C[k]); }
    const half=RULES.lanes*RULES.laneW/2;
    const run=(row,x,w,c)=>{ const a=Math.max(0,Math.round(x)), b=Math.min(W,Math.round(x)+Math.max(1,Math.round(w))); if(b>a) g32.fill(c,row+a,row+b); };
    for(let y=HY; y<H; y++){
      const row=(y-HY)*W, z=K/(y+0.5-HY), wz=z+dist, s=sc(z);
      const band=Math.floor(wz/7)%2===0;
      g32.fill(band?G.grass:G.grass2, row, row+W);
      const L=CX-half*s, R=CX+half*s, rum=Math.max(1,0.55*s);
      run(row,L-rum-0.9*s,0.9*s,G.shoulder); run(row,R+rum,0.9*s,G.shoulder);
      run(row,L-rum,rum, band?G.rumbleA:G.rumbleB); run(row,R,rum, band?G.rumbleA:G.rumbleB);
      run(row,L,R-L, band?G.road:G.road2);
      const lw=Math.max(1,0.16*s);
      run(row,L+0.12*s,lw,G.edge); run(row,R-0.12*s-lw,lw,G.edge);
      if((wz%12)<5.5) for(let i=1;i<RULES.lanes;i++){ const x=CX+(i*RULES.laneW-half)*s; run(row,x-lw/2,lw,G.line); }
    }
    ctx.putImageData(gImg,0,HY);
  }
  /* Roadside trees and palms, at fixed places along the road. */
  function drawRoadside(dist){
    const half=RULES.lanes*RULES.laneW/2, list=[];
    const step=16, first=Math.floor((dist+3)/step)+1;
    for(let k=first+9; k>=first; k--){
      const wz=k*step, z=wz-dist; if(z<9) continue;
      for(const side of [-1,1]){
        const h=(k*2654435761>>>0)%100, off=half+3.4+(h%4)*1.1;
        list.push({z, x:CX+side*off*sc(z), kind:(h+(side>0?37:0))%3===0?'palm':'tree', h});
      }
    }
    for(const o of list) drawTree(o.x, sy(o.z), sc(o.z), o.kind, o.h);
  }
  function drawTree(x,yb,s,kind,h){
    if(kind==='palm'){
      bx(x,yb,s,-0.2,0,0.4,5.2,'#6b4a2b'); bx(x,yb,s,-0.2,1.2,0.4,0.15,'#5a3d22'); bx(x,yb,s,-0.2,2.8,0.4,0.15,'#5a3d22');
      const cy=yb-5.4*s; ell(x-1.4*s,cy,1.8*s,0.45*s,'#2f8f3f'); ell(x+1.4*s,cy,1.8*s,0.45*s,'#2a7f38');
      ell(x-0.9*s,cy+0.6*s,1.4*s,0.4*s,'#257434'); ell(x+0.9*s,cy+0.6*s,1.4*s,0.4*s,'#2f8f3f'); ell(x,cy-0.2*s,0.6*s,0.5*s,'#3aa14c');
    } else {
      bx(x,yb,s,-0.3,0,0.6,1.6,'#6b4a2b');
      const cy=yb-3.3*s, r=2*s;
      ell(x,cy,r*1.05,r,'#2e7d3a'); ell(x-0.6*s,cy-0.5*s,r*0.6,r*0.55,'#3a9a48');
      if(s>3) for(let i=0;i<6;i++){ const a=(h+i*53)%360*Math.PI/180; px(x+Math.cos(a)*r*0.6, cy+Math.sin(a)*r*0.6, Math.max(1,0.3*s), Math.max(1,0.3*s), '#e0462f'); }
    }
  }

  /* ---- the obstacles, each drawn in meters from its bottom center ---- */
  const DRAW={
    gurney(x,y,s){ // a stretcher rolled across the lane
      bx(x,y,s,-1.0,0,0.08,0.5,'#9aa3ad'); bx(x,y,s,0.92,0,0.08,0.5,'#9aa3ad'); bx(x,y,s,-0.4,0,0.08,0.5,'#9aa3ad'); bx(x,y,s,0.32,0,0.08,0.5,'#9aa3ad');
      for(const w of [-1.05,-0.45,0.27,0.87]) bx(x,y,s,w,0,0.18,0.14,'#20242a');
      bx(x,y,s,-1.1,0.5,2.2,0.12,'#c8cfd6'); bx(x,y,s,-1.05,0.62,2.1,0.22,'#f6f7f9'); bx(x,y,s,-0.2,0.62,1.25,0.24,'#3d7fd1');
      bx(x,y,s,-1.0,0.84,0.45,0.16,'#ffffff'); bx(x,y,s,1.0,0.5,0.08,0.7,'#9aa3ad');
    },
    cones(x,y,s){ for(const c of [-0.75,0,0.75]){ bx(x,y,s,c-0.28,0,0.56,0.08,'#e2591f'); bx(x,y,s,c-0.2,0.08,0.4,0.25,'#ff7a2a'); bx(x,y,s,c-0.16,0.33,0.32,0.12,'#f6f6f2'); bx(x,y,s,c-0.11,0.45,0.22,0.25,'#ff7a2a'); } },
    pothole(x,y,s){ ell(x,y-0.15*s,1.05*s,0.22*s,'#2b2f35'); ell(x+0.1*s,y-0.18*s,0.7*s,0.13*s,'#3a5a78'); px(x-0.2*s,y-0.22*s,0.3*s,1,'#9cc4e8');
      bx(x,y,s,0.95,0,0.06,0.9,'#c9ced4'); bx(x,y,s,0.75,0.9,0.46,0.4,'#f2c12e'); bx(x,y,s,0.95,1.0,0.06,0.2,'#20242a'); },
    sofa(x,y,s){ bx(x,y,s,-1.1,0,2.2,0.12,'#3a2440'); bx(x,y,s,-1.1,0.12,2.2,0.38,'#7b4a93'); bx(x,y,s,-0.95,0.5,1.9,0.42,'#8d58a6');
      bx(x,y,s,-1.15,0.12,0.25,0.62,'#6c3f81'); bx(x,y,s,0.9,0.12,0.25,0.62,'#6c3f81'); bx(x,y,s,-0.02,0.5,0.04,0.42,'#6c3f81');
      bx(x,y,s,-0.6,0.62,0.35,0.3,'#e9c46a'); },
    ducks(x,y,s){ const d=(dx,k,c)=>{ bx(x,y,s,dx-0.2*k,0,0.4*k,0.26*k,c); bx(x,y,s,dx+0.08*k,0.24*k,0.18*k,0.18*k,c); bx(x,y,s,dx+0.24*k,0.29*k,0.1*k,0.05*k,'#f08a1c'); px(x+(dx+0.15*k)*s,y-0.36*k*s,1,1,'#111'); };
      d(-0.75,1.4,'#f4f4ee'); d(-0.05,0.9,'#f7d23b'); d(0.45,0.9,'#f7d23b'); d(0.9,0.9,'#f7d23b'); },
    scooter(x,y,s){ bx(x,y,s,-0.1,0,0.2,0.4,'#20242a'); bx(x,y,s,-0.34,0.32,0.68,0.5,'#d33a2c'); bx(x,y,s,-0.36,0.82,0.72,0.52,'#f4f1e6');
      bx(x,y,s,-0.3,0.95,0.6,0.08,'#d33a2c'); bx(x,y,s,-0.3,1.1,0.6,0.08,'#2f8a3a'); bx(x,y,s,-0.1,0.38,0.2,0.1,'#ffb3a8'); bx(x,y,s,-0.55,1.32,1.1,0.06,'#20242a'); },
    cart(x,y,s){ for(const w of [-0.42,0.32]) bx(x,y,s,w,0,0.1,0.12,'#20242a');
      bx(x,y,s,-0.45,0.12,0.9,0.06,'#b8c0c8'); bx(x,y,s,-0.5,0.4,1.0,0.6,'#a5aeb7');
      for(let i=0;i<5;i++) bx(x,y,s,-0.48+i*0.22,0.42,0.05,0.56,'#6d7781'); bx(x,y,s,-0.5,0.66,1.0,0.04,'#6d7781');
      bx(x,y,s,-0.58,1.0,1.16,0.08,'#d33a2c'); },
    barrier(x,y,s){ bx(x,y,s,-1.1,0,0.1,0.7,'#d9dde2'); bx(x,y,s,1.0,0,0.1,0.7,'#d9dde2');
      for(let i=0;i<8;i++) bx(x,y,s,-1.2+i*0.3,0.55,0.3,0.4,i%2?'#f4f4ee':'#f07a1c');
      bx(x,y,s,-1.15,1.0,0.22,0.16,(Math.floor(performance.now()/350)%2)?'#ffe14d':'#8a7a2a'); },
    flamingo(x,y,s){ ell(x,y-0.35*s,0.9*s,0.35*s,'#ff7fb0'); ell(x,y-0.35*s,0.45*s,0.14*s,'#3a5a78');
      bx(x,y,s,0.35,0.55,0.22,1.0,'#ff7fb0'); ell(x+0.55*s,y-1.6*s,0.3*s,0.2*s,'#ff7fb0'); bx(x,y,s,0.78,1.48,0.2,0.1,'#20242a'); px(x+0.55*s,y-1.66*s,1,1,'#111'); },
    gator(x,y,s){ bx(x,y,s,-1.2,0,2.2,0.32,'#3f7a2f'); bx(x,y,s,0.9,0,0.45,0.2,'#3f7a2f'); bx(x,y,s,-1.5,0,0.4,0.14,'#36692a');
      for(let i=0;i<6;i++) bx(x,y,s,-1.0+i*0.32,0.32,0.14,0.08,'#2d5a22'); bx(x,y,s,0.7,0.32,0.14,0.12,'#e8e070'); px(x+0.74*s,y-0.42*s,1,1,'#111');
      for(let i=0;i<4;i++) bx(x,y,s,0.95+i*0.1,0.16,0.05,0.05,'#f4f4ee'); bx(x,y,s,-0.8,0,0.18,0.1,'#2d5a22'); bx(x,y,s,0.4,0,0.18,0.1,'#2d5a22'); },
    mattress(x,y,s){ bx(x,y,s,-1.05,0,2.1,0.38,'#eef1f6'); for(let i=0;i<7;i++) bx(x,y,s,-1.0+i*0.3,0.04,0.1,0.3,'#9db8dd'); bx(x,y,s,-1.05,0.36,2.1,0.05,'#c9d2df'); },
    hotdog(x,y,s){ for(const w of [-0.6,0.45]) bx(x,y,s,w,0,0.16,0.2,'#20242a');
      bx(x,y,s,-0.75,0.2,1.5,0.75,'#e9e3cf'); bx(x,y,s,-0.75,0.5,1.5,0.14,'#d33a2c'); bx(x,y,s,-0.05,0.95,0.08,1.0,'#9aa3ad');
      for(let i=0;i<6;i++) bx(x,y,s,-0.9+i*0.3,1.95,0.3,0.2,i%2?'#f2c12e':'#d33a2c'); bx(x,y,s,-0.6,2.15,1.2,0.1,'#d33a2c');
      bx(x,y,s,-0.5,0.7,0.5,0.12,'#c8732e'); }
  };
  /* The ambulance from behind: box body, a red stripe, rear doors, a light bar. */
  function drawAmbulance(x,yb,s,t,crashed){
    ell(x,yb-0.05*s,1.15*s,0.18*s,'rgba(0,0,0,.35)');
    bx(x,yb,s,-0.95,0,0.32,0.3,'#16191d'); bx(x,yb,s,0.63,0,0.32,0.3,'#16191d');
    bx(x,yb,s,-1.0,0.2,2.0,1.95,'#f7f8fa'); bx(x,yb,s,-1.0,0.2,2.0,0.22,'#c9ced6');
    bx(x,yb,s,-1.0,0.78,2.0,0.2,'#d33a2c'); bx(x,yb,s,-0.02,0.42,0.04,1.6,'#aeb5bf');
    bx(x,yb,s,-0.82,1.38,0.62,0.48,'#2c4766'); bx(x,yb,s,0.2,1.38,0.62,0.48,'#2c4766');
    bx(x,yb,s,-0.75,1.7,0.2,0.1,'#58789c'); bx(x,yb,s,0.27,1.7,0.2,0.1,'#58789c');
    bx(x,yb,s,-0.96,0.5,0.18,0.24,'#ff4a3d'); bx(x,yb,s,0.78,0.5,0.18,0.24,'#ff4a3d');
    bx(x,yb,s,-0.36,1.02,0.72,0.3,'#2f6fd1'); bx(x,yb,s,-0.06,1.06,0.12,0.22,'#f7f8fa'); bx(x,yb,s,-0.2,1.12,0.4,0.1,'#f7f8fa');
    const on=Math.floor(t*4)%2===0;
    bx(x,yb,s,-0.9,2.15,0.8,0.22, on?'#ff3b2f':'#6a1a16'); bx(x,yb,s,0.1,2.15,0.8,0.22, on?'#2a3f6a':'#3b8bff');
    bx(x,yb,s,-0.1,2.15,0.2,0.22,'#e8e8e8');
    if(!crashed){ ctx.fillStyle=on?'rgba(255,60,50,.22)':'rgba(60,140,255,.22)'; ctx.beginPath(); ctx.ellipse(x+(on?-0.5:0.5)*s,yb-2.26*s,0.75*s,0.3*s,0,0,6.3); ctx.fill(); }
  }
  /* ---- after a crash (29 October 2026, owner request) ----
     The crash plays out under the score panel, in one of four scenes, never the same twice in
     a row: 1 the crew gets out and puts out the fire, 2 the crew runs around, pulls out the
     stretcher, one rides and the other pushes them off the screen, 3 an alien beams the
     ambulance away, 4 the burning ambulance falls into a sinkhole. Each lasts about seven
     seconds and then holds. Drawn in meters at the ambulance's depth, like everything else. */
  const SCENES=['crew','stretcher','alien','sinkhole'];
  let crash=null, lastScene=-1;
  function startCrash(){
    let k=Math.floor(Math.random()*SCENES.length); if(k===lastScene) k=(k+1)%SCENES.length;
    lastScene=k; crash={t:0, scene:SCENES[k]};
  }
  const hz=i=>{ const x=Math.sin(i*127.1+311.7)*43758.5453; return x-Math.floor(x); };
  const lerp=(a,b,f)=>a+(b-a)*clamp(f,0,1);
  const ease=f=>{ f=clamp(f,0,1); return f*f*(3-2*f); };
  /* A crew member: navy uniform with a yellow stripe. pose: stand, walk, run, cheer, lie, push. */
  function person(x,yb,s,ph,pose,skin,flip){
    const d=flip?-1:1;
    if(pose==='lie'){
      bx(x,yb,s,-0.85,0.05,0.62,0.24,'#1d3557'); bx(x,yb,s,-0.25,0.05,0.5,0.26,'#1d3557'); bx(x,yb,s,-0.25,0.14,0.5,0.05,'#f2c12e');
      ell(x+0.42*s,yb-0.2*s,0.14*s,0.13*s,skin); bx(x,yb,s,0.3,0.24,0.22,0.06,'#20242a');
      bx(x,yb,s,-0.15,0.3,0.1,0.35+0.08*Math.sin(ph*9),'#1d3557'); return;   // one arm up, waving
    }
    const step=(pose==='walk'||pose==='run'||pose==='push')?Math.sin(ph*(pose==='run'?16:9)):0;
    const lean=pose==='push'?0.18*d:(pose==='run'?0.08*d:0);
    const hop=pose==='cheer'?Math.abs(Math.sin(ph*7))*0.22:(pose==='run'?Math.abs(step)*0.06:0);
    const b=yb-hop*s;
    bx(x,b,s,-0.2+lean*0.3,0,0.17,0.82+0.1*step,'#16233b'); bx(x,b,s,0.03+lean*0.3,0,0.17,0.82-0.1*step,'#16233b');
    bx(x,b,s,-0.24+lean,0.8,0.48,0.62,'#1d3557'); bx(x,b,s,-0.24+lean,1.06,0.48,0.07,'#f2c12e');
    ell(x+(lean)*s,b-1.58*s,0.15*s,0.16*s,skin); bx(x,b,s,-0.14+lean,1.64,0.28,0.08,'#20242a');
    if(pose==='cheer'||pose==='run'){
      const w=pose==='run'?0.15*Math.sin(ph*18):0;
      bx(x,b,s,-0.36+lean,1.32+w,0.11,0.48,'#1d3557'); bx(x,b,s,0.25+lean,1.32-w,0.11,0.48,'#1d3557');
    } else if(pose==='push'){
      bx(x,b,s,lean+0.18*d-(d<0?0.42:0),1.12,0.42,0.1,'#1d3557');
    } else {
      bx(x,b,s,-0.35+lean,0.86-0.05*step,0.11,0.5,'#1d3557'); bx(x,b,s,0.24+lean,0.86+0.05*step,0.11,0.5,'#1d3557');
    }
  }
  /* Flames on the ambulance, level 0 to 1. */
  function fire(x,yb,s,lv,t){
    if(lv<=0.02) return;
    for(let i=0;i<14;i++){
      const u=hz(i), fl=(t*2.6+u)%1, fx=x+(u-0.5)*1.7*s, fy=yb-(2.25+fl*1.6*lv)*s;
      const r=(0.45-fl*0.32)*s*lv*(0.7+0.6*hz(i+40));
      ell(fx,fy,r,r*1.3, fl<0.35?'#fff3b0':fl<0.7?'#ffb52e':'#ff5a1f');
    }
  }
  function smoke(x,yb,s,amt,t){
    if(amt<=0.02) return;
    for(let i=0;i<8;i++){
      const u=hz(i+9), f=(t*0.35+u)%1, r=(0.3+f*0.9)*s*amt;
      ctx.globalAlpha=0.55*(1-f)*amt; ell(x+(u-0.5)*1.2*s+f*0.8*s, yb-(2.4+f*4)*s, r, r*0.8, '#6f7680');
    }
    ctx.globalAlpha=1;
  }
  function boom(x,y,s,f){
    if(f>=1) return; const k=1-f;
    for(let i=0;i<10;i++){ const a=i*0.63, r=(i%2?1.1:1.8)*s*(0.6+f); ell(x+Math.cos(a)*r*0.8, y+Math.sin(a)*r*0.5, 0.5*s*k+1, 0.35*s*k+1, i%2?'#ffd23b':'#ff7a2a'); }
    ell(x,y,0.8*s*k+1,0.6*s*k+1,'#fff3b0');
  }
  function stretcher(x,yb,s){
    for(const w of [-0.75,0.6]) bx(x,yb,s,w,0,0.16,0.14,'#20242a');
    bx(x,yb,s,-0.7,0.1,0.06,0.42,'#9aa3ad'); bx(x,yb,s,0.62,0.1,0.06,0.42,'#9aa3ad');
    bx(x,yb,s,-0.9,0.5,1.8,0.1,'#c8cfd6'); bx(x,yb,s,-0.88,0.58,1.76,0.14,'#f6f7f9');
  }
  /* The ambulance with its rear doors open: the box goes dark inside. */
  function doorsOpen(x,yb,s,f){
    if(f<=0) return;
    const w=0.8*ease(f);
    bx(x,yb,s,-0.82,0.42,1.64,1.6,'#2a2f36'); bx(x,yb,s,-0.7,0.42,1.4,0.18,'#4b525c');
    bx(x,yb,s,-1.0-w,0.42,w,1.6,'#e9ecf0'); bx(x,yb,s,1.0,0.42,w,1.6,'#e9ecf0');
    bx(x,yb,s,-1.0-w,0.95,w,0.16,'#d33a2c'); bx(x,yb,s,1.0,0.95,w,0.16,'#d33a2c');
  }
  function drawCrash(ax,yb,s,t){
    const c=crash||{t:9,scene:'crew'}, ct=c.t, SK=['#c98e6b','#8d5a3b'];
    const amb=(yOff,scale)=>drawAmbulance(ax, yb+(yOff||0), s*(scale||1), t, true);
    if(c.scene==='crew'){
      amb(); doorsOpen(ax,yb,s,(ct-0.9)/0.4);
      const out=ease((ct-1.2)/0.9);
      const lv=ct<0.3?ct/0.3:1-ease((ct-2.4)/2.6);
      fire(ax,yb,s,lv,ct); smoke(ax,yb,s,ct>2.4?Math.min(1,(ct-2.4)/1.5)*(1-ease((ct-7)/3)):0,ct);
      if(ct>1.2){
        const pa=ax+lerp(-0.2,-1.9,out)*s, pb=ax+lerp(0.2,1.9,out)*s, moving=out<1;
        const cheer=ct>5.4;
        person(pa,yb+0.4*s,s,ct,cheer?'cheer':moving?'walk':'stand',SK[0],false);
        person(pb,yb+0.4*s,s,ct+0.3,cheer?'cheer':moving?'walk':'stand',SK[1],true);
        /* The extinguisher and its spray, from the right-hand crew member. */
        bx(pb,yb+0.4*s,s,-0.42,0.85,0.16,0.42,'#d33a2c'); bx(pb,yb+0.4*s,s,-0.38,1.27,0.08,0.08,'#20242a');
        if(ct>2.2&&ct<5.2) for(let i=0;i<16;i++){
          const f=(ct*3+hz(i))%1, sx=pb-0.45*s, sy0=yb+0.4*s-1.2*s;
          const tx=ax+0.2*s+(hz(i+3)-0.5)*1.2*s, ty=yb-(2.4+hz(i+5)*0.8)*s;
          ctx.globalAlpha=0.8*(1-f*0.6); ell(lerp(sx,tx,f), lerp(sy0,ty,f), (0.12+f*0.3)*s, (0.1+f*0.22)*s, '#f2f5fa'); }
        ctx.globalAlpha=1;
      }
      boom(ax,yb-1.6*s,s,ct/0.7);
    }
    else if(c.scene==='stretcher'){
      const lv=ct<0.3?ct/0.3:1;
      amb(); doorsOpen(ax,yb,s,(ct-0.9)/0.4); fire(ax,yb,s,lv,ct); smoke(ax,yb,s,Math.min(1,ct/3),ct);
      const fy=yb+0.45*s;
      /* 1.2 to 3.6: they run around in a panic. 3.6 to 4.4: the stretcher comes out.
         4.4 to 4.9: one jumps on. Then the other pushes them off to the right. */
      let sxp=null, riderOn=false;
      if(ct>=3.6) sxp=ax+lerp(0,1.4,ease((ct-3.6)/0.8))*s;
      if(ct>=4.9){ const ft=ct-4.9; sxp=ax+1.4*s+(1.2*ft*ft+0.6*ft)*s; }
      if(sxp!=null) stretcher(sxp,fy,s);
      if(ct>1.2&&ct<3.6){
        const k=(ct-1.2);
        const pa=ax+Math.sin(k*3.1)*2.1*s, pb=ax+Math.sin(k*3.1+Math.PI)*2.1*s;
        person(pa,fy,s,ct,'run',SK[0],Math.cos(k*3.1)<0); person(pb,fy,s,ct+0.4,'run',SK[1],Math.cos(k*3.1+Math.PI)<0);
      } else if(ct>=3.6){
        /* The rider: waits, jumps in an arc, lies down. */
        if(ct<4.4) person(ax-1.6*s,fy,s,ct,'stand',SK[0],false);
        else if(ct<4.9){ const f=(ct-4.4)/0.5; person(lerp(ax-1.6*s,sxp,f), fy-Math.sin(f*Math.PI)*1.4*s, s, ct,'cheer',SK[0],false); }
        else riderOn=true;
        if(riderOn) person(sxp,fy-0.72*s,s,ct,'lie',SK[0],false);
        /* The pusher stands behind the foot end. */
        const px0=sxp!=null?sxp-1.25*s:ax-0.2*s;
        person(px0,fy,s,ct,ct>=4.9?'push':'walk',SK[1],false);
      }
      boom(ax,yb-1.6*s,s,ct/0.7);
    }
    else if(c.scene==='alien'){
      const ufoY=lerp(-30, yb-6.2*s, ease((ct-0.8)/1.2)) + (ct>4.4? -ease((ct-4.4)/0.6)*260:0);
      const ufoX=ax + (ct>4.4? ease((ct-4.4)/0.6)*220:0) + Math.sin(ct*2.2)*0.2*s;
      const beam=ct>2.0&&ct<4.5;
      const lift=ease((ct-2.4)/2.0), sc2=1-0.75*lift;
      if(beam){ ctx.globalAlpha=0.28+0.08*Math.sin(ct*20); ctx.fillStyle='#8dff7a'; ctx.beginPath();
        ctx.moveTo(ufoX-0.6*s,ufoY+0.3*s); ctx.lineTo(ufoX+0.6*s,ufoY+0.3*s); ctx.lineTo(ax+1.7*s,yb+0.2*s); ctx.lineTo(ax-1.7*s,yb+0.2*s); ctx.closePath(); ctx.fill(); ctx.globalAlpha=1; }
      if(ct<4.4){
        const yy=lerp(yb, ufoY+1.4*s, lift);
        if(beam&&Math.floor(ct*14)%3===0) ctx.globalAlpha=0.6;
        drawAmbulance(ax, yy, s*sc2, t, true); ctx.globalAlpha=1;
        fire(ax,yy,s*sc2,(ct<0.3?ct/0.3:1)*(1-ease((ct-2.0)/0.6)),ct);
      } else { ell(ax,yb-0.08*s,1.1*s,0.22*s,'rgba(20,22,26,.55)'); }
      /* The saucer. */
      ell(ufoX,ufoY,1.7*s,0.42*s,'#9aa6b4'); ell(ufoX,ufoY-0.3*s,0.75*s,0.48*s,'#7fd4ff'); ell(ufoX-0.15*s,ufoY-0.45*s,0.22*s,0.14*s,'#d6f3ff');
      ell(ufoX,ufoY-0.2*s,0.28*s,0.24*s,'#5fd35a'); px(ufoX-0.1*s,ufoY-0.3*s,1,1,'#111'); px(ufoX+0.08*s,ufoY-0.3*s,1,1,'#111');
      for(let i=0;i<5;i++) ell(ufoX+(i-2)*0.65*s, ufoY+0.08*s, 0.12*s, 0.08*s, Math.floor(ct*6+i)%2?'#ffe14d':'#ff5a5a');
      boom(ax,yb-1.6*s,s,ct/0.7);
    }
    else { // sinkhole
      const hw=lerp(0.2,1.65,ease((ct-1.5)/0.6))*s, hh=hw*0.32, hy=yb-0.05*s;
      if(ct>0.8){ ctx.strokeStyle='#2b2f35'; ctx.lineWidth=1; ctx.beginPath();
        for(let i=0;i<7;i++){ const a=i*0.9+0.3, r=(1.2+hz(i)*1.2)*s*ease((ct-0.8)/0.7); ctx.moveTo(ax,hy); ctx.lineTo(ax+Math.cos(a)*r, hy+Math.sin(a)*r*0.3); }
        ctx.stroke(); }
      if(ct>1.5) ell(ax,hy,hw,hh,'#121417');
      if(ct>1.5) ell(ax,hy+hh*0.25,hw*0.86,hh*0.7,'#06070a');
      const drop=ct<2.2?0:Math.pow(clamp((ct-2.2)/1.3,0,1),1.8)*3.4*s;
      if(drop<3.3*s){
        ctx.save(); if(ct>1.5){ ctx.beginPath(); ctx.rect(0,0,W,hy+hh*0.3); ctx.clip(); }
        drawAmbulance(ax, yb+drop, s, t, true); fire(ax,yb+drop,s,ct<0.3?ct/0.3:1,ct);
        ctx.restore();
      }
      if(ct>3.4){ const g2=0.4+0.3*Math.sin(ct*9); ctx.globalAlpha=g2; ell(ax,hy+hh*0.2,hw*0.5,hh*0.4,'#ff7a2a'); ctx.globalAlpha=1;
        smoke(ax,yb+1.6*s,s,Math.min(1,(ct-3.4)/1.2),ct); }
      boom(ax,yb-1.6*s,s,ct/0.7);
    }
  }
  function draw(){
    if(!ctx) return;
    const t=g?g.t:performance.now()/1000, dist=g?g.dist:performance.now()/1000*18;
    ctx.imageSmoothingEnabled=false;
    drawSky(performance.now()/1000);
    drawGround(dist);
    drawRoadside(dist);
    const things=g?g.obs.filter(o=>o.z>K/(H-HY)-1&&o.z<RULES.spawnZ+5).slice():[];
    things.sort((a,b)=>b.z-a.z);
    const pz=RULES.playerZ;
    let drew=false;
    const drawP=()=>{ if(!g) return; const s=sc(pz); const x=CX+((g.x-(RULES.lanes-1)/2)*RULES.laneW)*s;
      if(g.over) drawCrash(x, sy(pz), s, performance.now()/1000); else drawAmbulance(x, sy(pz), s, t, false); drew=true; };
    for(const o of things){
      if(!drew && o.z<pz) drawP();
      /* Drawn a third larger than life so they read at a distance. Hits go by lane, not by size. */
      const fn=DRAW[o.kind]; if(fn) fn(laneX(o.lane,o.z), sy(o.z), sc(o.z)*(o.kind==='ducks'?1.7:1.35));
    }
    if(!drew) drawP();
  }

  /* ================= the window ================= */
  const AMB_ICON='<svg viewBox="0 0 32 24" aria-hidden="true" shape-rendering="crispEdges">'+
    '<rect x="1" y="5" width="19" height="13" fill="#f7f8fa" stroke="#16242e" stroke-width="1.2"/>'+
    '<path d="M20 9h6l4 5v4H20z" fill="#f7f8fa" stroke="#16242e" stroke-width="1.2"/>'+
    '<rect x="21.5" y="10.4" width="4" height="3.4" fill="#2c4766"/>'+
    '<rect x="1" y="12" width="29" height="2.2" fill="#d33a2c"/>'+
    '<rect x="8" y="7" width="5" height="1.6" fill="#2f6fd1"/><rect x="9.7" y="5.3" width="1.6" height="5" fill="#2f6fd1"/>'+
    '<rect x="6" y="2.2" width="3.4" height="2.6" fill="#ff3b2f" class="ar-l1"/><rect x="11" y="2.2" width="3.4" height="2.6" fill="#3b8bff" class="ar-l2"/>'+
    '<circle cx="7" cy="19.5" r="2.6" fill="#16242e"/><circle cx="24.5" cy="19.5" r="2.6" fill="#16242e"/>'+
    '<circle cx="7" cy="19.5" r="1" fill="#c9ced6"/><circle cx="24.5" cy="19.5" r="1" fill="#c9ced6"/></svg>';

  function paintFloat(){
    const f=$('ar-float'); if(!f) return;
    f.hidden=false;
    f.innerHTML=`<button class="ar-box" type="button" id="ar-open" aria-haspopup="dialog" aria-label="Ambulance Run, a small arcade game">${AMB_ICON}</button>`;
    $('ar-open').onclick=show;
  }
  function windowHTML(){
    return `<div class="ms-back" data-arclose="1"></div>
      <div class="ms-card ar-card" role="dialog" aria-modal="true" aria-labelledby="ar-h">
        <button class="db-x ms-x" type="button" data-arclose="1" aria-label="Close"><svg viewBox="0 0 24 24" class="ic" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
        <div class="ar-in">
          <div class="ar-head"><h2 id="ar-h">Ambulance Run</h2>
            <button class="ar-snd" type="button" id="ar-snd" aria-pressed="${sound}">${sound?'Sound on':'Sound off'}</button></div>
          <div class="ar-grid">
            <div class="ar-stage" id="ar-stage">
              <canvas id="ar-cv" width="${W}" height="${H}" role="img" aria-label="The road ahead, seen from behind the ambulance"></canvas>
              <div class="ar-hud" id="ar-hud" aria-hidden="true"></div>
              <div class="ar-banner" id="ar-banner" aria-hidden="true"></div>
              <div class="ar-over" id="ar-over"></div>
              <div class="ar-touch" aria-hidden="true"><button type="button" data-tap="left" tabindex="-1">◀</button><button type="button" data-tap="right" tabindex="-1">▶</button></div>
            </div>
            <aside class="ar-board" aria-labelledby="ar-bh"><h3 id="ar-bh">Top 10</h3><ol id="ar-list"></ol><p class="ar-fine" id="ar-bfine"></p></aside>
          </div>
          <p class="ar-keys">Left and right arrow keys change lanes. Space starts and replays. P pauses. Esc closes. On a touch screen, tap either side of the road.</p>
          <p class="ar-live" id="ar-live" role="status" aria-live="polite"></p>
        </div>
      </div>`;
  }
  function paintBoard(){
    const l=$('ar-list'); if(!l) return;
    const f=$('ar-bfine');
    if(topState==='loading'&&!top.length){ l.innerHTML='<li class="ar-empty">Loading…</li>'; }
    else if(topState==='error'&&!top.length){ l.innerHTML=`<li class="ar-empty">${esc(topErr)}</li>`; }
    else if(!top.length){ l.innerHTML='<li class="ar-empty">No scores yet. Be the first.</li>'; }
    else l.innerHTML=top.map((r,i)=>`<li class="${r.mine?'mine':''}"><span class="ar-rk">${i+1}</span><span class="ar-nm">${esc(r.name)}</span><span class="ar-sc">${fmt(r.score)}</span></li>`).join('');
    if(f) f.textContent = SITE ? 'Shared by everyone who plays. Names are public.' : 'This build keeps scores in this browser only.';
  }
  let hudEls=null, hudLast=['','',''], bannerLast=null;
  function paintHud(){
    const h=$('ar-hud'); if(!h) return;
    if(!hudEls||!h.contains(hudEls[0])){
      h.innerHTML=`<div class="ar-cell"><b>Top 10 at</b><span></span></div>
        <div class="ar-cell ar-mid"><b>mph</b><span></span></div>
        <div class="ar-cell"><b>Score</b><span></span></div>`;
      hudEls=[...h.querySelectorAll('span')]; hudLast=['','',''];
    }
    const s=g?scoreOf(g):0, mph=g?Math.round(g.v*2.237):0;
    const txt=[top.length<10?'any score':fmt(cutoff()+1), String(mph), fmt(s)];
    for(let i=0;i<3;i++) if(txt[i]!==hudLast[i]){ hudEls[i].textContent=txt[i]; hudLast[i]=txt[i]; }
  }
  function paintBanner(){
    if(banner===bannerLast) return;
    const b=$('ar-banner'); if(!b) return;
    bannerLast=banner; b.textContent=banner; b.classList.toggle('on',!!banner);
  }
  function paintOver(){
    const o=$('ar-over'); if(!o) return;
    if(mode==='play'){ o.hidden=true; o.innerHTML=''; return; }
    o.hidden=false; o.classList.toggle('crash', mode==='over');
    if(mode==='title'){
      o.innerHTML=`<div class="ar-panel"><p class="ar-big">Ambulance Run</p>
        <p>Clear the road. Steer around whatever is in your lane. It gets faster.</p>
        <button class="ar-go" type="button" id="ar-go">Start</button></div>`;
    } else if(mode==='paused'){
      o.innerHTML=`<div class="ar-panel"><p class="ar-big">Paused</p><button class="ar-go" type="button" id="ar-go">Resume</button></div>`;
    } else {
      const s=scoreOf(g), q=qualifies(s)&&!posted;
      const what=g.hit?(KINDS.find(k=>k.id===g.hit.kind)||{}).label:'';
      let form='';
      if(q && (!SITE || signedIn())){
        const nm=(store.get(NAME_KEY)||'').toUpperCase();
        form=`<form class="ar-form" id="ar-form"><label for="ar-name">You made the top 10. Your name on the board:</label>
          <div class="ar-row"><input id="ar-name" maxlength="16" autocomplete="nickname" spellcheck="false" value="${esc(nm)}" ${postBusy?'disabled':''}>
          <button type="submit" class="ar-post" ${postBusy?'disabled':''}>${postBusy?'Posting…':'Post'}</button></div></form>`;
      } else if(q && SITE){
        form=`<p class="ar-note">That is a top 10 score. Sign in to post scores.</p>`;
      }
      o.innerHTML=`<div class="ar-panel ar-crashp"><p class="ar-big">Crash</p>
        <p>You hit ${esc(what||'something')}. Score <b class="ar-sc2">${fmt(s)}</b>${best&&s<best?`<span class="ar-bst">Best this visit ${fmt(best)}</span>`:''}</p>
        ${form}<p class="ar-msg">${esc(postMsg)}</p>
        <button class="ar-go" type="button" id="ar-go">Play again</button></div>`;
      const fm=$('ar-form');
      if(fm){ fm.onsubmit=e=>{ e.preventDefault(); postScore($('ar-name').value); }; }
    }
    const go=$('ar-go'); if(go) go.onclick=()=>{ if(mode==='paused') resume(); else startGame(); };
  }
  function bindWindow(){
    const m=$('ar-modal');
    m.querySelectorAll('[data-arclose]').forEach(b=>b.onclick=hide);
    $('ar-snd').onclick=()=>{ sound=!sound; store.set(SOUND_KEY,sound?'1':'0'); const b=$('ar-snd'); b.setAttribute('aria-pressed',sound); b.textContent=sound?'Sound on':'Sound off'; if(sound&&mode==='play') sirenOn(); else sirenOff(); };
    m.querySelectorAll('[data-tap]').forEach(b=>{
      b.addEventListener('pointerdown',e=>{ e.preventDefault(); if(mode==='play'){ press[b.dataset.tap]++; blip(); } else if(mode!=='over') startOrResume(); });
    });
    cv=$('ar-cv'); ctx=cv.getContext('2d');
    /* Tapping the left or right half of the road steers too. */
    cv.addEventListener('pointerdown',e=>{ if(mode!=='play') return; const r=cv.getBoundingClientRect(); press[(e.clientX-r.left)<r.width/2?'left':'right']++; blip(); });
  }
  function show(){
    if(open) return;
    lastFocus=document.activeElement; open=true;
    const m=$('ar-modal'); m.hidden=false; m.innerHTML=windowHTML(); hudEls=null; bannerLast=null; gImg=null; bindWindow();
    document.body.classList.add('ar-on');
    if(!stars) makeSky();
    g=null; mode='title'; posted=false; postMsg='';
    paintOver(); paintHud(); paintBoard(); loadTop();
    A.track('arcade_opened');
    lastT=performance.now(); raf=requestAnimationFrame(loop);
    const go=$('ar-go'); if(go) go.focus();
  }
  function hide(){
    if(!open) return;
    if(mode==='play') pause();
    open=false; cancelAnimationFrame(raf); sirenOff();
    const m=$('ar-modal'); m.hidden=true; m.innerHTML=''; cv=ctx=null;
    document.body.classList.remove('ar-on');
    if(lastFocus&&lastFocus.focus) try{ lastFocus.focus(); }catch(e){}
  }
  const LINES=['Dispatch: clear the road','Ducks have right of way','Watch for gators','Loose stretcher reported','Faster now','Stay in your lane','Code 3 traffic'];
  function startGame(){
    g=newGame(); mode='play'; posted=false; postMsg=''; postBusy=false; press={left:0,right:0};
    banner='Go'; bannerT=1.2; nextLine=7; paintBanner();
    beginRun(); paintOver(); paintHud(); sirenOn();
    $('ar-live').textContent='Run started.';
    const st=$('ar-stage'); if(st) st.focus();
  }
  function pause(){ if(mode!=='play') return; mode='paused'; sirenOff(); paintOver(); const go=$('ar-go'); if(go) go.focus(); }
  function resume(){ if(mode!=='paused') return; mode='play'; lastT=performance.now(); paintOver(); sirenOn(); }
  function startOrResume(){ if(mode==='paused') resume(); else startGame(); }
  function gameOver(){
    mode='over'; sirenOff(); crashSound(); startCrash();
    const s=scoreOf(g); best=Math.max(best,s);
    A.track('arcade_game_over',{score:s, seconds:Math.round(g.t)});
    paintOver(); paintHud();
    $('ar-live').textContent=`Crash. Score ${fmt(s)}.`+(qualifies(s)?' That is a top 10 score.':'');
    const n=$('ar-name'); if(n){ n.focus(); n.select(); } else { const go=$('ar-go'); if(go) go.focus(); }
  }
  function loop(now){
    if(!open) return;
    const dt=Math.min(0.05,(now-lastT)/1000); lastT=now;
    if(mode==='play'&&g){
      const before=Math.floor(g.v*2.237/20);
      step(g, dt, press); press={left:0,right:0};
      if(Math.floor(g.v*2.237/20)>before && g.v<RULES.vmax){ banner='Faster'; bannerT=1.4; }
      nextLine-=dt; if(nextLine<=0){ banner=LINES[Math.floor(Math.random()*LINES.length)]; bannerT=2.4; nextLine=9+Math.random()*6; }
      if(bannerT>0){ bannerT-=dt; if(bannerT<=0) banner=''; }
      paintBanner();
      if(g.over){ banner=''; paintBanner(); gameOver(); }
      else if(Math.floor(now/120)!==Math.floor((now-dt*1000)/120)) paintHud();
    }
    if(mode==='over'&&crash) crash.t+=dt;
    draw();
    raf=requestAnimationFrame(loop);
  }
  function keydown(e){
    if(!open) return;
    const typing=e.target&&e.target.id==='ar-name';
    if(e.key==='Escape'){ e.preventDefault(); hide(); return; }
    if(typing) return;
    if(e.key==='ArrowLeft'||e.key==='a'||e.key==='A'){ e.preventDefault(); if(mode==='play'){ press.left++; blip(); } return; }
    if(e.key==='ArrowRight'||e.key==='d'||e.key==='D'){ e.preventDefault(); if(mode==='play'){ press.right++; blip(); } return; }
    if(e.key==='ArrowUp'||e.key==='ArrowDown'){ e.preventDefault(); return; }
    if(e.key===' '||e.key==='Enter'){
      if(e.target&&e.target.tagName==='BUTTON'&&e.target.id!=='ar-go'&&e.key==='Enter') return;
      e.preventDefault(); if(mode==='title'||mode==='over'||mode==='paused') startOrResume(); return;
    }
    if(e.key==='p'||e.key==='P'){ e.preventDefault(); if(mode==='play') pause(); else if(mode==='paused') resume(); }
  }

  function init(){
    if(!$('ar-float')) return;
    paintFloat();
    document.addEventListener('keydown', keydown);
    document.addEventListener('visibilitychange',()=>{ if(document.hidden) pause(); });
    window.addEventListener('blur',()=>pause());
  }
  /* access.js hands over the Supabase client and each session change. */
  function setClient(c){ client=c; }
  function onSession(s){ session=s||null; if(open&&mode!=='play') paintOver(); }
  return {init, setClient, onSession, show, hide, rules, _state:()=>({mode, g, top, runId, crash}),
    /* For tests and screenshots: replay a crash scene from its start. */
    _scene:(n,t)=>{ if(crash&&SCENES.includes(n)){ crash.scene=n; crash.t=t||0; } }};
})();
