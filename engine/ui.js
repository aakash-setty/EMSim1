/* ============================================================
   UI. Everything below renders derived state; nothing stores it.
   ============================================================ */
/* v0.26: a case opens on Stabilization, the top tab. */
let LOG=[], SEQ=0, T0=Date.now(), ST=null, TAB='stabilization', ENDED=false;
/* v0.9: `diagnoses` is an ordered list and its first entry is the primary. The
   singular is filled in at submit for readers written before the list existed. */
let PENDING_HANDOFF={disposition:null,diagnoses:[]};
let LASTNURSE=-1, LASTPHASE=null, ASKTEXT='', DXTEXT='', RUNID=0;
/* Filter text and the pending order basket are per tab, so switching tabs and
   coming back leaves both exactly as they were. */
const FILTERS={}, BASKET={};
/* Expanded state for collapsible groups, per tab, so leaving and returning to a tab
   leaves the accordion exactly as it was. */
const EXPANDED={};
/* v0.26. The chosen sub-tab of a group drawn as sub-tabs (PROTO.subgroupTabs), keyed
   tab|group. Unset means the first subgroup in subgroupOrder. */
const SUBTAB={};
/* Subgroups listed in PROTO.subgroupCollapsed that the learner has opened, keyed
   tab|group|subgroup. Closed unless listed here. */
const SUBOPEN=new Set();
/* Seeded once per tab from SHARED.defaultExpanded, then left alone. A learner who
   collapses a group that opened by default keeps it collapsed for the rest of the run,
   because the set exists from the first call and is never re-seeded. */
const expandedOf = t => (EXPANDED[t]=EXPANDED[t]
  || new Set(((PROTO&&PROTO.defaultExpanded)||{})[t]||[]));
/* The mode a run starts in comes from the catalog rather than from a literal here,
   so there is one place that decides it and the splash cannot disagree with it. */
let MODE=SHARED.difficulty.default, STARTED=false;
/* ---------- panel state ----------
   Two booleans describe the whole layout. The tab rail is fixed and never
   participates: it is on screen in every state, which is what makes closing
   the workspace panel a safe thing to do to the learner.

     LEFT_OPEN   workspace panel out from behind the rail
     RIGHT_WIDE  record panel at 70% of the viewport, workspace closed

   They are written onto <body> as data attributes and the transitions live in
   CSS, so nothing here measures or animates anything by hand. */
let LEFT_OPEN=true, RIGHT_WIDE=false;
const ICON_EXPAND='<path d="M15 4h5v5M20 4l-7 7M9 20H4v-5M4 20l7-7"/>';
const ICON_SHRINK='<path d="M20 9h-5V4M15 9l6-6M4 15h5v5M9 15l-6 6"/>';
function setPanels(leftOpen,rightWide){
  LEFT_OPEN=!!leftOpen; RIGHT_WIDE=!!rightWide;
  document.body.dataset.left  = LEFT_OPEN ? 'open' : 'closed';
  document.body.dataset.right = RIGHT_WIDE ? 'wide' : 'dock';
  const b=el('rp-toggle');
  if(b){
    const lbl=RIGHT_WIDE?'Minimize the chart':'Expand the chart';
    b.title=lbl; b.setAttribute('aria-label',lbl);
    b.setAttribute('aria-expanded',RIGHT_WIDE?'true':'false');
    const ic=el('rp-icon'); if(ic) ic.innerHTML=RIGHT_WIDE?ICON_SHRINK:ICON_EXPAND;
  }
  /* The scroller changes with the state, so the next feed render has to
     re-follow the newest entry rather than leaving the reader at the top of a
     panel they just expanded to read the bottom of. */
  FEED_N=-1;
  if(ST) renderMonitor();
}
/* Expanding is a reading gesture, so it takes the whole width it can get and
   the workspace goes away. Minimising is a return to work, so the workspace
   comes back on Patient rather than on whichever tab was open twenty minutes
   ago: after reading the chart the next question is almost always about the
   patient, not about the tab that happened to be showing. */
function expandRecord(){ if(!RIGHT_WIDE) setPanels(false,true); }
function minimiseRecord(){
  if(!RIGHT_WIDE) return;
  TAB='history'; setPanels(true,false); render();
}
const DM = () => PROTO.difficulty.modes[MODE].prompt_multiplier;
/* The debrief's Sources button opens and closes the reference list under its note. */
document.addEventListener('click',e=>{
  const b=e.target.closest&&e.target.closest('.srcbtn'); if(!b) return;
  const refs=b.closest('details') && b.closest('details').querySelector('.refs'); if(!refs) return;
  refs.hidden=!refs.hidden; b.setAttribute('aria-expanded',refs.hidden?'false':'true');
});
/* 28 October 2026: the box keeps what was typed and matching trims it. Storing the trimmed
   text re-rendered the box without a trailing space, so a second word could not be typed. */
const filterOf = t => (FILTERS[t]||'').trim();
const basketOf = t => (BASKET[t]=BASKET[t]||new Set());
/* A group can show on two tabs (PROTO.groupAlsoOn), so one action can be picked from either.
   It is one pick wherever it was made: shown as picked on both, ordered once. */
const pickedAnywhere = id => (PROTO.orderableTabs||[]).some(t=>basketOf(t).has(id));
/* v0.26c, author instruction: Submit Order on any tab sends everything selected on every
   ordering tab. Each pick is numbered so the whole order goes out in the order it was
   picked, across tabs, exactly as it would have one tab at a time. */
let PICKSEQ={}, PICKN=0;
function allPicked(){
  const out=[];
  const seen=new Set();
  for(const t of PROTO.orderableTabs) for(const id of basketOf(t)) if(!seen.has(id)){ seen.add(id); out.push({id,t}); }
  return out.sort((a,b)=>(PICKSEQ[a.id]||0)-(PICKSEQ[b.id]||0));
}
function clearAllBaskets(){ for(const t of PROTO.orderableTabs) basketOf(t).clear(); PICKSEQ={}; }

/* Label lookups the handoff and debrief need. Plain functions rather than properties
   hung on PROTO, because PROTO is rebound whenever a case is selected and anything
   attached to it would be lost. */
const dxLabel   = id => (SHARED.diagnoses.find(d=>d.id===id)||{}).label
                     || (id?id.replace(/^dx_/,'').replace(/_/g,' '):'not recorded');
const dispLabel = id => (PROTO.dispLabels||{})[id] || (id?id.replace(/_/g,' '):'not recorded');

/* The case clock, with time the resident was not looking at it removed. PAUSED_MS is
   what has already been given back and the second term is the pause in progress, so the
   clock freezes rather than jumping when it resumes. A resident who answers a page is not
   charged for it, and the deterioration deadlines in a case are claims about how long a
   patient tolerates something rather than about how long a browser tab was open. */
let PAUSED=false, PAUSED_AT=0, PAUSED_MS=0;
const elapsedMs = ()=> (PAUSED?PAUSED_AT:Date.now()) - T0 - PAUSED_MS;
const now = ()=> ENDED ? ST.now : (STARTED ? Math.max(0,elapsedMs())/1000 : 0);
/* v0.18f. Analytics: a no-op outside the deployed site (see analytics.js). */
const AN=(typeof ANALYTICS==='object'&&ANALYTICS)||{track(){},count(){},takeCounts(){return {};}};
function log(e){
  /* v0.26. A composite (catalog `performs`) is never logged itself. Each act it names is
     logged in its place, at the same instant and in order, so the fold, the tags and the
     debrief see exactly what pressing the three buttons would have produced. Every route
     in comes through here: a button, a submitted order and the microphone. */
  const a=e&&e.actionId&&ACT[e.actionId];
  if(a&&a.performs&&a.performs.length&&!e.kind){
    for(const id of a.performs) if(ACT[id]) log(Object.assign({},e,{actionId:id}));
    return;
  }
  e.seq=SEQ++; e.t=now(); LOG.push(e); refold();
  PROGRESS.touch();
}
function refold(){ ST=fold(LOG,now(),DM()); }

const esc = s => String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const mmss = s => { s=Math.max(0,Math.floor(s)); return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0'); };
const el = id => document.getElementById(id);

/* ---------- vitals ramp ----------
   The engine changes phase in one step, so before this the monitor jumped: a
   heart rate could go 119 to 92 between two frames. Nothing in a body does
   that, and an instantaneous jump also hides the thing the learner is meant to
   watch for, which is a trend. The numbers now travel to the new phase's
   values over five seconds.

   THIS IS DISPLAY ONLY. It does not touch ST, the fold, or any authored value.
   A study still reports the authored vitals for the moment it was ordered, a
   transition still fires the instant its condition is met, and the debrief is
   unaffected. If this code were deleted the medicine would be identical.

   The ramp starts from what is currently on screen rather than from the
   previous phase's authored numbers, so a second transition landing mid-ramp
   continues smoothly from where the display actually was.

   v0.7: the target is ST.vitals, the phase baseline with any active vital effect
   already applied, so an effect starting or lapsing travels exactly as a phase change
   does. The re-arm test is the target itself rather than the phase id, because an
   effect changes the numbers without changing the phase. */
const RAMP_MS=5000;
const RAMP_KEYS=['heart_rate','systolic_bp','diastolic_bp','oxygen_saturation',
                 'respiratory_rate','temperature_c'];
let RAMP_FROM=null, RAMP_T0=0, RAMP_KEY=null, RAMP_SHOWN=null;
function resetRamp(){ RAMP_FROM=null; RAMP_T0=0; RAMP_KEY=null; RAMP_SHOWN=null; }
function targetVitals(){
  if(!ST||!PHASE) return null;
  if(ST.vitals) return ST.vitals;
  const p=PHASE[ST.phase];
  return p?p.vitals:null;
}
function rampedVitals(){
  const target=targetVitals();
  if(!target) return target;
  const key=ST.phase+'|'+RAMP_KEYS.map(k=>target[k]).join(',');
  if(RAMP_KEY!==key){
    /* First paint of a case shows the arrival vitals outright: there is nothing
       to travel from, and a five second climb from nowhere would be a lie. */
    RAMP_FROM = (RAMP_KEY===null||!RAMP_SHOWN) ? target : RAMP_SHOWN;
    RAMP_T0 = Date.now();
    RAMP_KEY = key;
  }
  /* The case is over, so show where it ended rather than freezing part way. */
  if(ENDED){ RAMP_SHOWN=target; return target; }
  const k=Math.min(1,Math.max(0,(Date.now()-RAMP_T0)/RAMP_MS));
  const e=k*k*(3-2*k);                      /* smoothstep: no jerk at either end */
  const out={};
  for(const key in target) out[key]=target[key];
  for(const key of RAMP_KEYS){
    const a=RAMP_FROM[key], b=target[key];
    if(typeof a!=='number'||typeof b!=='number') continue;
    const val=a+(b-a)*e;
    out[key] = key==='temperature_c' ? Math.round(val*10)/10 : Math.round(val);
  }
  RAMP_SHOWN=out;
  return out;
}

/* ---------- monitor (section 6, 8.4) ---------- */
/* Cosmetic variance so the monitor does not look frozen. It reads the wall clock rather
   than the case clock, which is right while a case is running and wrong while it is
   paused: numbers wobbling behind a Paused overlay say the case is still going. */
function jitter(v,amp){ return PAUSED ? v
  : v + Math.round((Math.sin(Date.now()/1300+v)+Math.sin(Date.now()/770+v*2))/2*amp); }
/* Normal ranges for the monitor's bold or plain numbers, inclusive (28 October 2026). */
const VITAL_NORMAL={hr:[60,100], sbp:[90,139], dbp:[60,89], spo2:[94,100], rr:[12,20], temp:[36.0,37.9]};
function renderMonitor(){
  const p=PHASE[ST.phase];
  const v=rampedVitals()||targetVitals()||{};
  const halted = ST.halted||ST.complete||ST.earlyExit;
  const j = halted ? (x=>x) : jitter;
  /* Nothing is on the screen until the patient is on a monitor. The numbers exist in
     the fold from the first second; what the resident is missing is the equipment that
     would show them to them, which is a decision they have to make rather than a
     starting condition they are given. Every cell reads as an unauthored one does,
     because "no monitor" and "no numbers" look the same to a reader and the dash is
     already the interface's word for both. */
  const on = !!ST.monitoring;
  /* A case still being authored has null vitals. Show a dash rather than crashing:
     the picker offers skeletons on purpose, and a skeleton that white-screens is
     worse than one that reads as obviously unfinished. */
  const num=(x,amp)=>(on&&typeof x==='number')?j(x,amp||0):'\u2013';
  const cells=[
    ['HR',   num(v.heart_rate,2),                            '/minute','hr'],
    ['BP',   (on&&typeof v.systolic_bp==='number'&&typeof v.diastolic_bp==='number')
               ? v.systolic_bp+'/'+v.diastolic_bp : '\u2013',  'mmHg','bp'],
    ['SpO\u2082', num(v.oxygen_saturation,1),                 '%','spo2'],
    ['RR',   num(v.respiratory_rate,1),                      '/minute','rr'],
    ['T',    (on&&typeof v.temperature_c==='number')?v.temperature_c.toFixed(1):'\u2013','\u00B0C','temp']
  ];
  /* The header carries the full monitor at every panel state and no panel ever covers it,
     so the expanded record used to show a second copy of the same five numbers on the same
     screen. Removed in v0.17o on the author's instruction. */
  /* A number outside its normal range is bold and one inside it is not (author instruction,
     28 October 2026), judged on the number the monitor shows. The ranges are adult teaching
     thresholds held here for every case, not clinical claims about any one patient. */
  const outside=k=>{
    if(!on) return false;
    const n=parseFloat(cells.find(c=>c[3]===k)[1]);
    if(k==='bp'){ const s=+v.systolic_bp, d=+v.diastolic_bp; return s<VITAL_NORMAL.sbp[0]||s>VITAL_NORMAL.sbp[1]||d<VITAL_NORMAL.dbp[0]||d>VITAL_NORMAL.dbp[1]; }
    const r=VITAL_NORMAL[k]; return !!r&&!isNaN(n)&&(n<r[0]||n>r[1]);
  };
  el('monitor').innerHTML = cells.map(c=>
    `<div class="vit"><div class="vitlab">${c[0]}</div>
     <div class="vitval v-${c[3]}${outside(c[3])?' vabn':''}">${c[1]}</div><div class="vitunit">${c[2]}</div></div>`).join('')
    + `<div class="clockbox"><div class="vitlab">elapsed</div>
       <div class="clock">${mmss(ST.now)}</div>
       <div class="phasechip">${esc(PROTO.phaseShort[ST.phase]||ST.phase)}</div></div>`;
  if(LASTPHASE!==null && LASTPHASE!==ST.phase) el('monitor').animate?.([{opacity:.35},{opacity:1}],{duration:420});
  LASTPHASE=ST.phase;
  /* The trace is live: the monitor module draws it, one lead, at paper speed, from the
     same beat clock the audio sounds. Off means a dark screen, which is the same nothing
     the vital cells show. sync() starts or stops the clock; frame() draws one frame. */
  MONITOR.frame(on);
  MONITOR.sync();
  renderSound();
  AUDIO.sync();
}
/* Enabled only inside a case, exactly as the microphone is: there is nothing to search
   on the case list or on the card. */
function renderSearchBtn(){
  const b=el('searchbtn'); if(!b) return;
  const active=inCase();
  b.disabled=!active;
  if(!active&&SEARCH_OPEN) closeSearch();
  /* The other direction. The microphone's own button is handled inside voice.js, which
     knows nothing about this panel, so the exclusion is checked here rather than wired
     through it. */
  if(SEARCH_OPEN&&VOICE.isOpen&&VOICE.isOpen()) closeSearch();
}
function renderSound(){
  const b=el('soundbtn'); if(!b) return;
  /* Four states, not three. Sound can be on and the room still be silent, because the
     heartbeat is the monitor's and there is no monitor yet. Saying "Sound on" over
     silence reads as a fault, so the button says which of the two is missing. */
  b.textContent = AUDIO.running
    ? (ST&&ST.monitoring ? 'Sound on' : 'Sound on, no monitor')
    : (AUDIO.enabled ? 'Sound starting\u2026' : 'Sound off');
  b.setAttribute('aria-pressed', AUDIO.enabled?'true':'false');
  b.title = 'Click to turn sound '+(AUDIO.enabled?'off':'on')+'. Audio context: '+AUDIO.state;

}

/* ---------- the patient in the room ----------
   Mounted once per bound case, then told the visible state every frame. setState is a
   string compare when nothing has changed, so calling it from the frame loop costs nothing.
   The respiratory rate is the one on the monitor, ramp included, so the chest and the number
   never disagree; it is read from what the monitor last showed rather than by calling
   rampedVitals again, which would re-arm the ramp. The figure is there whether or not the
   monitor is on: a resident can see a patient breathe without a monitor. Paused means
   still, for the reason the monitor's jitter stops: movement behind a Paused overlay says
   the case is still going. */
let PT=null, PT_CASE=null;
/* What the figure looks like and what it is doing, computed once for the room and once
   for the splash from the same two functions, so the patient on the card before Begin
   and the patient in the room after it are the same patient in the same state. */
function figureAppearance(){
  /* The standard man or woman by patient.sex, from SHARED.patient.base. A case may author
     patient.avatar to differ from the base, key by key; none does yet. The appearance is
     fixed for the whole case: states never touch hair, clothes or colours. The age group
     is drawn from patient.age, which every case has; avatar.ageGroup may overrule it. */
  PATIENT.setBases((SHARED.patient||{}).base);
  const p=CASE.patient||{};
  const av=Object.assign({ageGroup:PATIENT.ageGroupFor(p.age)},p.avatar||{});
  return PATIENT.baseFor(p.sex,av);
}
function figureState(st,shown){
  const v=Object.assign({},patientVisual(st).value);
  if(shown&&typeof shown.respiratory_rate==='number') v.respiratory_rate=shown.respiratory_rate;
  /* The resting face is drawn from the distress level the phase already authors, the same
     way the chest is drawn from the rate: passed in here, never authored a second time. */
  const ap=(PHASE[st.phase]||{}).appearance||{};
  if(typeof ap.distress_level==='number') v.distress=ap.distress_level;
  if(typeof ap.alertness_level==='number') v.alertness=ap.alertness_level;
  /* Every patient is on a stretcher. SHARED.patient.always lists add-ons drawn for every
     case whatever its rules say, so no case has to author the furniture. ?bed=0 on the
     address takes the bed away and ?bed=flat draws its unshaded first stage, for comparison. */
  const always=((SHARED.patient||{}).always||[]).filter(a=>a!=='hospital_bed'||BED_SWITCH!=='off')
    .map(a=>(a==='hospital_bed'&&BED_SWITCH==='flat')?'hospital_bed_flat':a);
  if(always.length) v.addons=(v.addons||[]).concat(always.filter(a=>(v.addons||[]).indexOf(a)<0));
  return v;
}
const BED_SWITCH=(function(){ try{ const m=/[?&]bed=(\w+)/.exec(location.search); return !m?'on':m[1]==='0'?'off':m[1]==='flat'?'flat':'on'; }catch(e){ return 'on'; } })();
function renderPatient(){
  const host=el('patientfig');
  if(!host||typeof PATIENT==='undefined'||!PATIENT.available||!ST) return;
  /* The frame loop never stops once a case has begun, so leaving for the case list or sitting
     on the next case's splash would otherwise remount the last patient behind it on the next
     frame and animate them unseen. Found by the v0.17f check. */
  if(wlVisible()||!el('splash').classList.contains('hidden')){ clearPatient(); return; }
  if(!PT||PT_CASE!==CASE){
    if(PT) PT.destroy();
    PT=PATIENT.mount(host,figureAppearance()); PT_CASE=CASE;
  }
  PT.setState(figureState(ST,RAMP_SHOWN||targetVitals()||{}));
  PATIENT.setPaused(PAUSED||ENDED);
}
function clearPatient(){ if(PT){ PT.destroy(); PT=null; PT_CASE=null; } }

/* ---------- the patient on the splash ----------
   The same figure, on the card before Begin, in the arrival state: phase one's vitals,
   distress and add-ons, on the stretcher, breathing at the arrival rate. It is mounted
   when the splash is drawn and destroyed when the case begins or the resident goes back
   to the list, so at most one figure exists at a time and the room's figure is never
   animating unseen behind the card. A build without the figure art collapses the card
   back to one column rather than leaving an empty stage beside it. */
let SP=null;
function renderSplashPatient(){
  const host=el('sp-patient'), wrap=el('splashwrap'); if(!host||!wrap) return;
  clearSplashPatient();
  const ok=typeof PATIENT!=='undefined'&&PATIENT.available&&!!ST;
  wrap.classList.toggle('nofig',!ok);
  if(!ok) return;
  SP=PATIENT.mount(host,figureAppearance());
  SP.setState(figureState(ST,targetVitals()||{}));
  /* The module's pause flag is global and the last case may have left it set. */
  PATIENT.setPaused(false);
  /* The art is drawn past its 264 by 280 box on purpose: in the room the stretcher runs
     on behind the frosted panes. On the card there are no panes, so the box is refitted
     to what is actually drawn, measured rather than assumed, and the rails stop short of
     the text. A few units of margin cover the breath's scale. */
  const svg=host.querySelector('svg');
  if(svg&&svg.getBBox){
    try{
      /* The stretcher is an add-on, and add-ons are drawn on the first frame rather than
         at mount, so the measurement has to come after them or it measures a patient
         with no bed and clips the rails off. */
      if(SP._dirty&&SP.reconcile) SP.reconcile();
      /* Width from what is drawn, so the rails are in. Height stops at the art's own
         bottom edge, y=280, where the gown ends: the stretcher runs on below it, and a
         torso shown with mattress under it read as a torso floating on a bed rather
         than a patient cropped at the frame, which is what the room does too. */
      const bb=svg.getBBox(), m=6, bottom=280;
      svg.setAttribute('viewBox',`${(bb.x-m).toFixed(1)} ${(bb.y-m).toFixed(1)} ${(bb.width+2*m).toFixed(1)} ${(bottom-bb.y+m).toFixed(1)}`);
      svg.style.overflow='hidden'; svg.style.marginBottom='0';
    }catch(e){}
  }
}
function clearSplashPatient(){
  if(SP){ SP.destroy(); SP=null; }
  const h=el('sp-patient'); if(h) h.innerHTML='';
}

/* ---------- nurse ---------- */
/* When the nurse says something, her picture grows for ten seconds and then settles
   back. A new line restarts the ten seconds. Transform only, so it is smooth and moves
   nothing around it. Author instruction, 11 October 2026. */
let NURSE_BIG_T=0;
function nurseSpeaking(){
  const f=document.querySelector('.nurse'); if(!f) return;
  f.classList.add('speaking');
  clearTimeout(NURSE_BIG_T);
  NURSE_BIG_T=setTimeout(()=>f.classList.remove('speaking'),10000);
}
function renderNurse(){
  const n=ST.nurse[ST.nurse.length-1];
  const line=el('nurseline');
  if(!n){ line.textContent=PROTO.nurseIdle; el('nursemeta').textContent=''; return; }
  if(ST.nurse.length!==LASTNURSE){
    line.classList.remove('fresh'); void line.offsetWidth; line.classList.add('fresh');
    /* Every nurse utterance makes a sound, because a line nobody noticed is a line
       nobody read. A prompt keeps the trill it has always had, which is deliberately
       unlike anything else; everything else gets a short soft cue that says only that
       she spoke. Two sounds on one line would be worse than none, so they are exclusive.
       Skipped for the very first line, as the trill always was. */
    if(LASTNURSE>=0){ if(n.kind==='prompt') AUDIO.trill(); else AUDIO.cue(); }
    LASTNURSE=ST.nurse.length;
    nurseSpeaking();
  }
  line.textContent=n.text;
  const lab={prompt:'prompt',blocked:'blocked action',result:'result',halt:'halt',
             alert:'note',deterioration:'change',narration:''}[n.kind]||'';
  el('nursemeta').textContent = mmss(n.t) + (lab?'  '+lab:'');
}

/* ---------- rail ---------- */
function renderRail(){
  const p=ST.pending;
  el('pendlist').innerHTML = p.length ? p.map(o=>{
    const left=Math.max(0,o.dueT-ST.now), tot=Math.max(0.1,o.dueT-o.orderT);
    return `<div class="pendrow"><span>${esc(dispName(o.id))}</span><span class="cd">${left.toFixed(1)}s</span></div>
            <div class="bar"><i style="width:${Math.min(100,(1-left/tot)*100).toFixed(0)}%"></i></div>`;
  }).join('') : '<div class="emptyline">Nothing pending.</div>';
  renderFeed();
}

/* ---------- running chart ----------
   Everything the case has produced, in the order it arrived: results as they come back,
   exam findings, consultant replies, what the patient said, and every action performed
   or blocked. It is always on screen, because a finding read on one tab is gone the
   moment the resident moves to another and the whole point of a chart is that it is not.

   Results enter the feed at the moment they RESULT, not when they were ordered, so the
   order here is the order the resident actually learned things. */
/* ---------- the running chart ----------
   NEWEST FIRST. The chart is read while the case is running, to answer "what just
   happened", and the answer to that is at one end of the list. Oldest-first put it at
   the far end of a scroller that grows all case, and in the expanded multi-column layout
   it put the newest entry at the bottom of the LAST column, which is the hardest place
   on the panel to find. Reversed, the thing a resident is looking for is at the top of
   the first column and the panel needs no scrolling at all to answer that question.

   Ties are broken by push order, reversed with everything else, so several things landing
   in the same second still read newest-first rather than in an arbitrary order. */
function feedItems(){
  const out=[];
  const add=o=>{ o.seq=out.length; out.push(o); };
  /* A blocked attempt carries the reason the nurse gave. It used to be a bare "Blocked:
     X" row, with the reason only in the header line that scrolls away and in the debrief
     at the end. The reason is the teaching. */
  const blockMsg={};
  for(const b of ST.blocked) blockMsg[b.t+'|'+b.id]=b.message;
  for(const x of ST.timeline){
    if(x.type==='blocked'){
      add({t:x.t,kind:'blocked',name:x.label,body:blockMsg[x.t+'|'+x.id]||''}); continue;
    }
    /* Observational entries are already represented by the readout they produced, and
       the interview and review entries would just duplicate it. */
    if(x.type==='observational') continue;
    if(x.type==='end') continue;
    /* A study appears twice: once when it is sent, once when it results. Same name on
       both reads as a duplicate, so the order is labelled as an order. */
    /* A consultation is charted once, by the readout that carries the consultant's
       answer, below. The order line above it said the same name again. Kept only when
       the consult was harmful, so the harm marker is not lost. */
    if(catOf(x.id)==='consultant'&&x.tag!=='harmful') continue;
    const isStudy=catOf(x.id)==='investigation';
    add({t:x.t,kind:x.tag==='harmful'?'harm':(isStudy?'order':'action'),
         name:isStudy?('Ordered: '+x.label):x.label});
  }
  for(const r of ST.readouts){
    if(r.kind==='exam')    add({t:r.t,kind:'exam',name:r.title,payload:r.body});
    if(r.kind==='consult') add({t:r.t,kind:'consult',name:r.title,body:r.body});
    /* The patient's answers are not chart entries (13 October 2026, author instruction).
       The chart is the record of what was ordered, found and said by the nurse. The
       conversation lives on the History tab, which keeps every answer and shows which
       questions did not land. Until this date a matched answer was a chart row and an
       unmatched one was not. */
  }
  /* What the nurse said, but not everything she said.

     Her line is the only thing in the interface that is overwritten rather than added to:
     the header holds one utterance and the next one replaces it. A resident working a tab
     loses every prompt they did not happen to be looking at, which is the one kind of
     information in this product that had nowhere to be read back. So it goes in the
     chart.

     Four of her six kinds are left out, and each for its own reason. `narration` echoes an
     action that is already a row ("Insert IV" then "Okay: insert iv."). `result` echoes a
     result that is already a row, with its payload. `blocked` is folded into the blocked
     row above, where it reads as the reason rather than as a second entry. And `halt` is
     said at the instant the case ends, which is the instant finish() hides this whole
     panel, so a halt row would be written into something nobody can look at; its reason
     is on the halt card and in the debrief, which is where a resident reads it.

     Two kinds are left, and neither has anywhere else to be read:

       prompt         she asked for something. Nowhere else at all
       deterioration  the one place a nurse line may describe a trajectory, and it
                      narrates a change the resident may not have been watching for
       alert          something the case wanted said about an act that was just
                      performed. It has to be findable again, because a line like "these
                      agents take a bit of time to work" is useless once it has scrolled
                      off the nurse's line and the resident is deciding whether to redose */
  const NURSE_IN_CHART={prompt:1,deterioration:1,alert:1};
  for(const n of ST.nurse){
    if(!NURSE_IN_CHART[n.kind]) continue;
    add({t:n.t,kind:n.kind==='prompt'?'nurse':'nursealert',name:'Nurse',body:n.text});
  }
  /* A lab is one entry, at its newest result, with every draw so far as a column (author
     instruction, 28 October 2026), the way Labs Only shows them. Each repeat moves the entry
     to the top of the chart with the new column on the left. Everything else that results
     is one entry per result, as before. */
  Object.keys(ST.orders).forEach(id=>{
    const done=ST.orders[id].filter(o=>o.value!==null);   /* pending ones live in the rail */
    if(!done.length) return;
    if(isLabId(id)){
      const last=done.reduce((a,b)=>b.dueT>a.dueT?b:a);
      add({t:last.dueT,kind:'lab',name:dispName(id),id,
           payload:{series:id,abnormal:!!(last.value&&last.value.abnormal)}});
      return;
    }
    done.forEach(o=>add({t:o.dueT,kind:catOf(id)==='investigation'?'lab':'imaging',
         name:dispName(id),payload:o.value,id}));
  });
  out.sort((a,b)=>b.t-a.t||b.seq-a.seq);
  return out;
}

/* ---------- results that are a picture ----------
   A twelve-lead tracing is not prose and a case may author it as the image itself, with no
   report text at all: the reading is the skill, and a payload that hands the resident "QRS
   132 ms" beside the tracing has done the reading for them. DIPH authors three that way.
   Since 13 October 2026 every case's twelve-lead is a tracing, its read kept as the comment
   the debrief prints under it, and its caption at most the machine measurements.

   The media map is per case and lives on PROTO, keyed by the file stem, so a case that
   ships no images costs nothing here and a payload naming a missing one degrades to a line
   of text rather than to a broken image icon. The validator catches that case before it
   ever ships; this is the runtime half of the same guarantee. */
/* Only an inline raster image is ever used as a src: every picture in a pack is one, and
   anything else in that slot is refused rather than written into the page. */
const IMG_DATA=/^data:image\/(png|jpeg|webp|gif);base64,[A-Za-z0-9+\/=]+$/;
function imageSrc(id){ const s=(PROTO.media||{})[id]; return typeof s==='string'&&IMG_DATA.test(s)?s:null; }

function imageThumb(v){
  const src=imageSrc(v.image);
  const cap=v.caption||'Image';
  /* 19 October 2026. A payload that names a series opens the CT viewer; its still is the
     thumbnail. A series missing from the build falls back to the still. */
  const ser=v.series&&PROTO.series&&PROTO.series[v.series]?v.series:'';
  if(!src) return `<div class="fb">${esc(cap)} (image ${esc(v.image||'?')} is not in this build)</div>`;
  /* A button rather than a div, so it is reachable by keyboard and announces itself. The
     data attributes are read by the delegated click handler; the src is inlined because
     every image in the build is already a data URI. */
  return `<button type="button" class="imgthumb" data-img="${esc(v.image)}"
            data-cap="${esc(cap)}" data-series="${esc(ser)}" title="${esc(cap)} - click to open">
            <img src="${src}" alt="${esc(cap)}" loading="lazy">
          </button><p class="imgcap">${esc(cap)}. Click to open.</p>`;
}

/* One lab's draws side by side, newest on the left, each column headed by the time it was
   drawn. Rows keep the chart's alternating shading; the range column shows when the record
   is expanded, as elsewhere in the chart. */
function labSeries(id){
  const draws=ST.orders[id].filter(o=>o.value!==null).slice().sort((a,b)=>b.orderT-a.orderT||b.dueT-a.dueT);
  const rows=[], by={};
  let text=false;
  draws.forEach((o,ci)=>{
    const v=o.value, comps=(v&&typeof v==='object'&&Array.isArray(v.components))?v.components:null;
    const put=(key,label,unit,ref,val,abn)=>{
      let r=by[key]; if(!r){ r=by[key]={label,unit:unit||'',ref:ref||'',cells:{}}; rows.push(r); }
      if(!r.cells[ci]) r.cells[ci]={val,abn};
    };
    if(comps&&comps.length) for(const c of comps) put('c:'+c.label,c.label,c.unit,c.reference_range,c.value,!!c.abnormal);
    else { text=true; put('t','Result','','',(v&&typeof v==='object')?(v.report||v.findings||v.value||''):String(v==null?'':v),!!(v&&v.abnormal)); }
  });
  const N=draws.length;
  let h='<table class="labser"><thead><tr><th class="lb"></th>'
    +draws.map(o=>`<th class="v" title="Drawn ${mmss(o.orderT)}, resulted ${mmss(o.dueT)}">${mmss(o.orderT)}</th>`).join('')
    +'<th class="rf"></th></tr></thead><tbody>';
  for(const r of rows){
    h+=`<tr><td class="lb">${esc(r.label)}${r.unit?' <span class="u">'+esc(r.unit)+'</span>':''}</td>`;
    for(let i=0;i<N;i++){ const c=r.cells[i];
      h+=c?`<td class="v${c.abn?' abn':''}${text?' tx':''}">${esc(c.val)}</td>`:'<td class="v"></td>'; }
    h+=`<td class="rf">${esc(r.ref)}</td></tr>`;
  }
  return h+'</tbody></table>';
}

function feedPayload(v){
  if(v&&typeof v==='object'&&v.series) return labSeries(v.series);
  if(!v||typeof v!=='object') return v?`<div class="fb">${esc(v)}</div>`:'';
  if(v.kind==='image') return imageThumb(v);
  /* The reference range is the third cell. It is hidden while the record is docked,
     where 360 pixels holds a label and a number and nothing else, and shown when the
     record is expanded, which is the reading gesture. */
  if(v.components&&v.components.length)
    return '<table>'+v.components.map(c=>
      `<tr><td class="lb">${esc(c.label)}</td>
           <td class="vl${c.abnormal?' abn':''}">${esc(c.value)}</td><td class="un">${esc(c.unit||'')}</td>
           <td class="rf">${esc(c.reference_range||'')}</td></tr>`
    ).join('')+'</table>';
  const txt=v.report||v.findings||v.value||'';
  return txt?`<div class="fb${v.abnormal?' abn':''}">${esc(txt)}</div>`:'';
}

/* ---------- chart filters (author instruction, 11 October 2026) ----------
   Labs Only and Nurse Only, one at a time. Labs Only replaces the running list with one
   table of every lab result. Nurse Only keeps the running list and shows what the nurse
   said: her prompts, her alerts and the reasons she gave when an order could not go
   ahead. Exam Only (author instruction, 23 October 2026) keeps the running list and shows
   the examination findings. Image/ECG Only (author instruction, 23 October 2026) keeps the
   running list and shows the imaging and twelve-lead results. The filter changes what is
   shown and nothing else: feedItems(), the search and the decision to open the record all
   read the whole chart. */
let CHART_FILTER=null;                     // null, 'labs', 'exam', 'imaging' or 'nurse'
const NURSE_KINDS={nurse:1,nursealert:1,blocked:1};
const EXAM_KINDS={exam:1};
/* A lab is an investigation drawn from a specimen. Imaging and the ECG are investigations
   too and are not labs. The last two tests catch a case-only lab with no catalog entry. */
function isLabId(id){
  const a=ACT[id]||{};
  return catOf(id)==='investigation' && (!!a.specimen || a.group==='Lab Work' || /^labs_/.test(id));
}
/* Imaging and the ECG: the catalog's Imaging group, the twelve-lead, and a case-only study
   named like one. Bedside tests that are neither (a Doppler, a peak flow) are left out. */
function isImagingId(id){
  const a=ACT[id]||{};
  return catOf(id)==='investigation' && !isLabId(id)
    && (a.group==='Imaging' || /(^|_)(ecg|ekg)(_|$)/.test(id) || /^(echo_|cxr|ct_|pocus|ultrasound_|xr_|mri_)/.test(id));
}
function chartFilterHTML(){
  const b=(k,label)=>{
    const on=CHART_FILTER===k, off=!!CHART_FILTER&&!on;
    return `<button type="button" class="cfbtn${on?' on':''}" data-cfilter="${k}" aria-pressed="${on}"`
      +`${off?' disabled':''} title="${on?'Show the whole chart':'Show '+label.toLowerCase()}">`
      +`${label}${on?'<span class="cfx" aria-hidden="true">\u00d7</span>':''}</button>`;
  };
  return b('labs','Labs Only')+b('imaging','Image/ECG Only')+b('exam','Exam Only')+b('nurse','Nurse Only');
}
/* One table of every lab result that is back. Pending ones are in the Pending box above.

   Columns are draws. Studies sent within two seconds of each other went off together (one
   Submit Order sends the whole basket) and share a column, headed by when they were drawn.
   A study sent twice is two columns, because a column never holds the same study twice.
   Newest on the left. Each cell's tooltip gives the drawn and resulted times.

   Rows are grouped by study, the study with the most recent draw first. A panel is a name
   row with a row per component under it, in the order of its latest result. A study with
   a single number is one row under the component's own label. A result that is words
   (a smear, a qualitative test) is one row with the words in the cell. */
function labTable(){
  const draws=[];
  Object.keys(ST.orders).forEach(id=>{
    if(!isLabId(id)) return;
    ST.orders[id].forEach(o=>{ if(o.value!==null) draws.push({id,orderT:o.orderT,dueT:o.dueT,v:o.value}); });
  });
  if(!draws.length) return {n:0,html:'<div class="emptyline">No lab results yet.</div>'};
  draws.sort((a,b)=>a.orderT-b.orderT||a.dueT-b.dueT);
  const cols=[];
  for(const d of draws){
    let c=cols.find(c=>d.orderT-c.t<=2&&!c.ids.has(d.id));
    if(!c){ c={t:d.orderT,ids:new Set()}; cols.push(c); }
    c.ids.add(d.id); d.col=c;
  }
  cols.reverse(); cols.forEach((c,i)=>{ c.i=i; });
  const P={}, panels=[];
  for(let k=draws.length-1;k>=0;k--){             // newest first, so its row order wins
    const d=draws[k], v=d.v;
    let p=P[d.id];
    if(!p){ p=P[d.id]={id:d.id,last:d.orderT,rows:[],by:{},text:false}; panels.push(p); }
    const comps=(v&&typeof v==='object'&&Array.isArray(v.components))?v.components:null;
    const put=(key,label,unit,ref,val,abn)=>{
      let r=p.by[key];
      if(!r){ r=p.by[key]={label,unit:unit||'',ref:ref||'',cells:{}}; p.rows.push(r); }
      if(!r.cells[d.col.i]) r.cells[d.col.i]={val,abn,d};
    };
    if(comps&&comps.length){
      for(const c of comps) put('c:'+c.label,c.label,c.unit,c.reference_range,c.value,!!c.abnormal);
    } else {
      p.text=true;
      const txt=(v&&typeof v==='object')?(v.report||v.findings||v.value||v.caption||''):String(v==null?'':v);
      put('t',dispName(d.id),'','',txt,!!(v&&v.abnormal));
    }
  }
  panels.sort((a,b)=>b.last-a.last);
  const N=cols.length, tip=d=>'Drawn '+mmss(d.orderT)+', resulted '+mmss(d.dueT);
  const row=(p,r,cls)=>{
    let h=`<tr class="${cls}"><td class="lb">${esc(r.label)}${r.unit?' <span class="u">'+esc(r.unit)+'</span>':''}</td>`;
    for(let i=0;i<N;i++){
      const c=r.cells[i];
      h+=c?`<td class="v${c.abn?' abn':''}${p.text?' tx':''}" title="${esc(tip(c.d))}">${esc(c.val)}</td>`:'<td class="v"></td>';
    }
    return h+`<td class="rf">${esc(r.ref)}</td></tr>`;
  };
  let h='<div class="labwrap"><table class="labt"><thead><tr><th class="lb">Drawn</th>'
    +cols.map(c=>`<th>${mmss(c.t)}</th>`).join('')+'<th class="rf">Range</th></tr></thead><tbody>';
  for(const p of panels){
    if(p.rows.length===1){ h+=row(p,p.rows[0],'lg one'); continue; }
    h+=`<tr class="lg"><td class="lb">${esc(dispName(p.id))}</td>${'<td></td>'.repeat(N)}<td class="rf"></td></tr>`;
    for(const r of p.rows) h+=row(p,r,'lc');
  }
  return {n:draws.length,html:h+'</tbody></table></div>'};
}

let FEED_N=-1, FEED_HTML='', CF_HTML='';
function renderFeed(){
  const all=feedItems();
  const cf=chartFilterHTML();
  if(cf!==CF_HTML){ CF_HTML=cf; el('chartfilters').innerHTML=cf; }
  let items=all, html, n;
  if(CHART_FILTER==='labs'){ const L=labTable(); html=L.html; n=L.n; }
  else {
    if(CHART_FILTER==='nurse') items=all.filter(i=>NURSE_KINDS[i.kind]);
    if(CHART_FILTER==='exam') items=all.filter(i=>EXAM_KINDS[i.kind]);
    if(CHART_FILTER==='imaging') items=all.filter(i=>i.id&&i.payload!==undefined&&isImagingId(i.id));
    n=items.length;
  }
  el('feedcount').textContent = n ? n : '';
  if(html===undefined) html = items.length ? items.map(i=>
    `<div class="fitem k-${i.kind}${(i.payload&&i.payload.abnormal)?' abnormal':''}">
       <div class="fh"><span class="ft">${mmss(i.t)}</span><span class="fn">${esc(i.name)}</span></div>
       ${i.payload!==undefined?feedPayload(i.payload):(i.body?`<div class="fb">${esc(i.body)}</div>`:'')}
     </div>`).join('')
    : (CHART_FILTER==='nurse'?'<div class="emptyline">Nothing from the nurse yet.</div>'
      :CHART_FILTER==='exam'?'<div class="emptyline">No examination yet.</div>'
      :CHART_FILTER==='imaging'?'<div class="emptyline">No imaging or ECG results yet.</div>'
                             :'<div class="emptyline">Nothing yet.</div>');
  /* Written only when it differs. This runs from the frame loop, and assigning the same
     markup sixty times a second replaced every node in the chart between one mouse
     button going down and coming up, which is why a thumbnail in the record could be
     seen and never clicked. Nothing in the chart carries a live number, so the string
     is the state. */
  if(html!==FEED_HTML){ FEED_HTML=html; el('feed').innerHTML=html; }
  /* The record stays tucked away until the first thing enters it: an order pending or
     an entry in the chart. The CSS takes its docked width to zero while it is empty, and
     the workspace and the patient widen into the space. */
  const hasRecord = all.length>0 || !!(ST && ST.pending && ST.pending.length);
  const rec = hasRecord ? 'has' : 'empty';
  if(document.body.dataset.record!==rec) document.body.dataset.record=rec;
  /* Follow the newest entry only when something has actually been added, so a reader
     scrolled down through earlier results is not yanked back every tick. The newest
     entry is now at the TOP, so following it means scrolling to zero rather than to the
     full height. */
  const feedKey=(CHART_FILTER||'all')+':'+n;
  if(feedKey!==FEED_N){
    FEED_N=feedKey;
    /* Which element actually scrolls depends on the panel state: docked, the
       feed scrolls inside its box; expanded, the feed is a multi-column block
       of natural height and the panel body around it is the scroller. */
    const f = RIGHT_WIDE ? document.querySelector('.rp-body') : el('feed');
    if(f) f.scrollTop=0;
  }
}

/* ---------- tab rail ----------
   A fixed vertical rail at the left edge rather than a horizontal strip. It is
   the one element that is on screen in every layout state, so the eight
   destinations stay reachable whether the workspace is open, closed, or hidden
   behind an expanded chart. Icons carry the recognition; the label under each
   one carries the meaning, and the labels are the catalog's own words rather
   than abbreviations. */
const TABICON={
  patient:'<circle cx="12" cy="8" r="3.2"/><path d="M5 20c0-3.6 3.1-5.6 7-5.6s7 2 7 5.6"/>',
  history:'<path d="M20 15a2 2 0 0 1-2 2H8l-4 3V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z"/>',
  exam:'<path d="M6 3v6a4 4 0 0 0 8 0V3"/><path d="M4.5 3h3M12.5 3h3"/>'
      +'<path d="M10 13v1.5A5.5 5.5 0 0 0 15.5 20 3.5 3.5 0 0 0 19 16.5V14"/>'
      +'<circle cx="19" cy="11.6" r="2.2"/>',
  stabilization:'<path d="M3 12h4l2.5-7 4 14L16 12h5"/>',
  investigations:'<path d="M9.5 3h5M10.6 3v5.6L5.3 18.1A2 2 0 0 0 7 21h10a2 2 0 0 0 1.7-2.9L13.4 8.6V3"/>'
      +'<path d="M7.6 15.5h8.8"/>',
  interventions:'<rect x="3.2" y="9" width="17.6" height="6" rx="3" transform="rotate(-45 12 12)"/>'
      +'<path d="M8.8 8.8l6.4 6.4"/>',
  consultations:'<path d="M21 16.9v2.5a1.5 1.5 0 0 1-1.6 1.5A17.6 17.6 0 0 1 3 4.6 1.5 1.5 0 0 1 4.5 3h2.5'
      +'a1.5 1.5 0 0 1 1.5 1.3c.1 1 .3 1.9.6 2.8a1.5 1.5 0 0 1-.3 1.6L7.6 10a14 14 0 0 0 6.4 6.4l1.3-1.2'
      +'a1.5 1.5 0 0 1 1.6-.3c.9.3 1.8.5 2.8.6a1.5 1.5 0 0 1 1.3 1.5z"/>',
  handoff:'<path d="M9.5 4.5H7A1.8 1.8 0 0 0 5.2 6.3v12.9A1.8 1.8 0 0 0 7 21h10a1.8 1.8 0 0 0 1.8-1.8V6.3'
      +'A1.8 1.8 0 0 0 17 4.5h-2.5"/><rect x="9.2" y="2.6" width="5.6" height="3.6" rx="1.1"/>'
      +'<path d="M9.3 13.4l2 2 3.6-3.8"/>'
};
/* The Patient tab is gone. It carried the full authored background: past medical
   history, every home medication, the whole EMS narrative. That is a chart a
   resident would not have on arrival, and handing it over at the start replaced
   the work of taking a history with the work of reading one.

   The case file still carries all of it, because the debrief, the review packet
   and the authoring process all need it. The learner now gets what a resident
   actually gets: two sentences of handover, on the History tab, and everything
   else has to be asked for.

   Filtering here rather than only in the build keeps an older build working: a
   shared payload that still lists the tab will not produce a dead button. */
const HIDDEN_TABS=new Set(['patient']);
const tabList=()=>PROTO.tabOrder.filter(id=>!HIDDEN_TABS.has(id));
function renderTabs(){
  el('tabbar').innerHTML=tabList().map(id=>{
    let badge='';
    if(id==='investigations'&&ST.pending.length) badge=`<span class="badge">${ST.pending.length}</span>`;
    const lab=esc(PROTO.tabLabel[id]);
    return `<button class="tabbtn" role="tab" aria-selected="${id===TAB&&LEFT_OPEN}" data-tab="${esc(id)}"
      title="${lab}"><svg viewBox="0 0 24 24" aria-hidden="true">${TABICON[id]||TABICON.patient}</svg>
      <span class="lb">${lab}</span>${badge}</button>`;
  }).join('');
}

/* ---------- result payload rendering: abnormal components in red ----------
   A lab result carries the number, the unit and the interval, and nothing else while
   the case runs. The authored `comment` under a panel is an interpretation ("worsening
   respiratory acidosis: he is tiring"), and an interpretation handed to the resident
   with the number is the simulator doing the reading for them. It is kept, and the
   debrief prints every one of them under "Your results, read" once the answers are
   revealed. Reports (imaging, ECG) are unchanged: their text is the result. */
function renderPayload(v){
  if(v===null||v===undefined) return '<div class="body">No result is defined for this study.</div>';
  if(typeof v==='string') return `<div class="body">${esc(v)}</div>`;
  if(v.kind==='image') return imageThumb(v);
  if(v.kind==='report'){
    return `<div class="body${v.abnormal?' abn-report':''}">${esc(v.report)}</div>`;
  }
  const rows=(v.components||[]).map(c=>
    `<tr class="${c.abnormal?'abn':''}">
       <td class="lab">${esc(c.label)}</td>
       <td class="val">${esc(c.value)}${c.unit?' '+esc(c.unit):''}</td>
       <td class="ref">${esc(c.reference_range||'')}</td>
     </tr>`).join('');
  /* `verify` is a note to the reviewing physician and lives in the case file and the
     review packet. It used to print under the result as "Needs verification", which told
     the resident to distrust the number they had just been given. */
  return `<table class="labtbl">${rows}</table>`;
}

/* ---------- action buttons ---------- */
function actionsFor(tab){
  const f=filterOf(tab), out={};
  const hits=f?filterHits(f):null;
  const also=(PROTO.groupAlsoOn||{})[tab]||[];
  for(const id in ACT){
    const a=ACT[id];
    if(a.hidden||a.menu_hidden) continue;
    if(isStopOrder(id)) continue;                  /* a stop order is the cross on its drip's button */
    const mine=a.groups||[a.group];
    const gs=a.tab===tab?mine.slice():[];
    for(const x of also){
      /* [tab, group]: the whole group, under its own name. {from:[tab, group, subgroup], into}:
         one subgroup of it, inside another group, where it keeps its subgroup heading. */
      if(Array.isArray(x)){ const [t,g]=x; if(a.tab===t&&mine.includes(g)&&!gs.includes(g)) gs.push(g); }
      else if(x&&x.from&&a.tab===x.from[0]&&mine.includes(x.from[1])&&(!x.from[2]||a.subgroup===x.from[2])
              &&!gs.includes(x.into)) gs.push(x.into);
    }
    if(!gs.length) continue;
    if(hits&&!hits.has(id)) continue;
    for(const g of gs) (out[g]=out[g]||[]).push(id);
  }
  /* A group in PROTO.buttonOrder lists its buttons in that order, by catalog id (author
     instruction, 13 October 2026: the exams head to toe). Anything it does not name
     follows, alphabetically, as every other group does. */
  Object.keys(out).forEach(g=>{
    const ord=(PROTO.buttonOrder||{})[g]||[];
    const rank=id=>{ const i=ord.indexOf(catIdOf(id)); return i<0?500:i; };
    out[g].sort((x,y)=>rank(x)-rank(y)||ACT[x].name.localeCompare(ACT[y].name));
  });
  return out;
}
/* The tab filter matches as the global search does (author instruction, 14 October 2026):
   every word has to start or sit inside the name, the group or the id, in any order, and
   the microphone's table adds the brand names, slang, abbreviations and misspellings no
   display name carries. The tab's
   own name is left out of the text, or "lab" would match everything on Labs/Imaging. */
function filterHits(text){
  const q=searchNorm(text).split(' ').filter(Boolean);
  if(!q.length) return null;
  const out=new Set();
  for(const id in ACT){
    const a=ACT[id];
    if(a.hidden||a.menu_hidden) continue;
    const groups=(a.groups||[a.group]).filter(Boolean);
    const side=groups.join(' ')+' '+groups.map(groupLabel).join(' ')+' '+id.replace(/_/g,' ');
    if(searchScore(q,a.name,side)>=0) out.add(id);
  }
  /* Then the microphone's table. Its exact parses are added always. Its close guesses
     (a misspelling: "metroprolol", "troponn") are added only when nothing matched exactly.
     The global search leaves the guesses out because a press there places the order; here
     they only narrow the buttons, and the resident still chooses one. */
  if(typeof VOICE!=='undefined'&&VOICE.parse){
    const parses=VOICE.parse(text), guesses=[];
    for(const r of parses){
      const ids=r.kind==='ok'?[r.id]:(r.kind==='ambiguous'?r.ids:[]);
      for(const id of ids) if(ACT[id]){ if(r.uncertain) guesses.push(id); else out.add(id); }
    }
    if(!out.size) guesses.forEach(id=>out.add(id));
  }
  return out;
}
/* A drug group reads with "Meds" after its system, smaller and greyer (author instruction,
   14 October 2026): "Meds - Cardiac" is shown "Cardiac Meds". The group's name itself, which
   the catalog and the cases use, is unchanged. */
const GROUP_SHORT={'Vasoactive Agents':'Vasoactive'}, GROUP_NO_MEDS={'Antibiotics':1};
function groupLabel(g){
  const m=/^Meds - (.+)$/.exec(String(g||''));
  if(!m) return String(g||'');
  const n=GROUP_SHORT[m[1]]||m[1];
  return GROUP_NO_MEDS[m[1]]?n:n+' Meds';
}
function groupLabelHTML(g){
  const m=/^Meds - (.+)$/.exec(String(g||''));
  if(!m) return esc(g);
  const n=esc(GROUP_SHORT[m[1]]||m[1]);
  return GROUP_NO_MEDS[m[1]]?n:`${n} <span class="gmeds">Meds</span>`;
}
/* Group icons on the Actions tab (author instruction, 14 October 2026). The same tiles as
   the exam buttons. Where a group belongs to a body system it takes that exam's colours
   (cardiac and vasoactive the heart's rose, respiratory the lungs' aqua, and so on); the
   rest have colours of their own. Keyed by tab, then group. Display only. */
const GROUP_ICON={interventions:{
  'Fluids':{bg:'#D6EAF3',fg:'#3F88A6',d:'<path d="M12 3.5s-5.5 6.2-5.5 10.2a5.5 5.5 0 0 0 11 0C17.5 9.7 12 3.5 12 3.5z"/><path d="M9.6 14.2a2.6 2.6 0 0 0 2.4 2.4"/>'},
  'Meds - Resuscitation':{bg:'#F7DAD3',fg:'#B65F4B',d:'<path d="M13.5 3 6 13.5h5.5L10.5 21 18 10.5h-5.5z"/>'},
  'Meds - Intubation':{bg:'#E7E0F3',fg:'#7D6AAE',d:'<path d="M8 3.5v9a6 6 0 0 0 6 6h5"/><path d="M5.5 3.5h5"/><rect x="14.5" y="15.8" width="3.2" height="5.4" rx="1.4"/>'},
  'Meds - Cardiac':{bg:'#F5DCE1',fg:'#B05D70',d:'<path d="M12 20s-7.5-4.6-7.5-10A4.2 4.2 0 0 1 12 7.6 4.2 4.2 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/><path d="M7.5 12.5h2.3l1.2-2 2 4 1.2-2h2.3"/>'},
  'Meds - Vasoactive Agents':{bg:'#F5DCE1',fg:'#B05D70',d:'<path d="M4 16a8 8 0 0 1 16 0"/><path d="M12 16l3.6-4.4"/><circle cx="12" cy="16" r="1.2"/><path d="M4 19.5h16"/>'},
  'Meds - Respiratory':{bg:'#D5ECEE',fg:'#3F8C95',d:'<path d="M12 3.5v8M12 9.5l-2.6 2M12 9.5l2.6 2"/><path d="M9.2 7.5C6.4 7.5 4 11.6 4 16c0 2.2 1.1 3.5 2.9 3.5 1.8 0 2.8-1.1 2.8-3V9"/><path d="M14.8 7.5c2.8 0 5.2 4.1 5.2 8.5 0 2.2-1.1 3.5-2.9 3.5-1.8 0-2.8-1.1-2.8-3V9"/>'},
  'Meds - Gastrointestinal':{bg:'#F8E3D4',fg:'#B5774B',d:'<path d="M7.2 3.5c0 4.2-2.2 6.2-2.2 10.2 0 3.9 3.1 6.8 7 6.8s7-2.9 7-6.8c0-4-2.2-6-2.2-10.2"/><circle cx="12" cy="13" r="1.1"/><path d="M7.5 8.5c1.4.7 2.9 1 4.5 1s3.1-.3 4.5-1"/>'},
  'Meds - OB/GYN':{bg:'#F1DDEC',fg:'#9A5F8C',d:'<circle cx="12" cy="9" r="5"/><path d="M12 14v7M9 18h6"/>'},
  'Meds - Allergy':{bg:'#F5EECF',fg:'#9C8634',d:'<circle cx="12" cy="12" r="2.2"/><path d="M12 3.5v4M12 16.5v4M3.5 12h4M16.5 12h4M6 6l2.8 2.8M15.2 15.2 18 18M18 6l-2.8 2.8M8.8 15.2 6 18"/>'},
  'Meds - Sedation/Analgesia':{bg:'#D8EEDF',fg:'#4B8E62',d:'<path d="M18.5 14.5A7.5 7.5 0 0 1 9.5 5.5a7.5 7.5 0 1 0 9 9z"/><path d="M16 4.5h3l-3 3.5h3"/>'},
  'Meds - Psych':{bg:'#DCE3F6',fg:'#5F72AE',d:'<path d="M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v8A1.5 1.5 0 0 1 19 16.5h-8.5L6 20v-3.5H5A1.5 1.5 0 0 1 3.5 15V7A1.5 1.5 0 0 1 5 5.5z"/><path d="M9 11.5c.8 1.2 1.8 1.8 3 1.8s2.2-.6 3-1.8"/><path d="M9 9h.01M15 9h.01"/>'},
  'Meds - Antibiotics':{bg:'#E9EBD2',fg:'#7D8442',d:'<rect x="5" y="8" width="14" height="8" rx="4"/><path d="M8.5 11.2h.01M12 12.8h.01M15.5 11.2h.01"/><path d="M5.5 8.5 3.5 6.5M18.5 8.5l2-2M5.5 15.5l-2 2M18.5 15.5l2 2"/>'},
  'Meds - Tox':{bg:'#E9E2DC',fg:'#85705F',d:'<path d="M9.5 3.5h5M10.5 3.5v5L6 17.5a2 2 0 0 0 1.8 3h8.4a2 2 0 0 0 1.8-3l-4.5-9v-5"/><path d="M8 14h8"/>'},
  'Meds - Miscellaneous':{bg:'#E7E8EA',fg:'#6F7780',d:'<rect x="3.8" y="8.5" width="16.4" height="7" rx="3.5" transform="rotate(-35 12 12)"/><path d="M9.9 9 14.1 15"/>'},
  'Blood Bank':{bg:'#F2D7DC',fg:'#A2495C',d:'<path d="M12 3.5s-5.5 6.2-5.5 10.2a5.5 5.5 0 0 0 11 0C17.5 9.7 12 3.5 12 3.5z"/><path d="M12 10.5v6M9 13.5h6"/>'},
  'Procedures':{bg:'#DFE4EA',fg:'#5E6F83',d:'<path d="M4 20 15.5 8.5"/><path d="M15.5 8.5l2-2a2.1 2.1 0 0 1 3 3l-2 2-3-3z"/><path d="M7 17l-1.5-1.5M9.5 14.5 8 13"/>'},
}};
function groupIconHTML(tab,g){
  const ic=(GROUP_ICON[tab]||{})[g];
  return ic?`<span class="abic gic" style="--icbg:${ic.bg};--icfg:${ic.fg}" aria-hidden="true"><svg viewBox="0 0 24 24">${ic.d}</svg></span>`:'';
}

/* ---------- drips are stopped from their own button (author instruction, 14 October 2026) ----------
   A catalog "Stop X" entry names the drip it stops (`stops`). Those entries leave the
   menus, and a running drip's button carries a red cross that gives the stop order at once,
   so it reaches the record as the drip stopping, exactly as the old button did. Voice and
   the global search still know the stop orders by name. DRIP_STOP maps each drip, as this
   pack names it (through its bindings), to its stop order. */
let DRIP_STOP_FOR=null, DRIP_STOP={}, STOP_IDS=new Set();
function dripStops(){
  if(DRIP_STOP_FOR===PACK) return DRIP_STOP;
  DRIP_STOP={}; STOP_IDS=new Set(); DRIP_STOP_FOR=PACK;
  const eff=c=>((PACK&&PACK.bindings)||{})[c]||c, base=SHARED.actionsBase||{};
  for(const cid in base){
    const d=base[cid].stops; if(!d) continue;
    const de=eff(d), se=eff(cid);
    if(ACT[de]&&ACT[se]){ if(!DRIP_STOP[de]) DRIP_STOP[de]=se; STOP_IDS.add(se); }
  }
  return DRIP_STOP;
}
const isStopOrder=id=>{ dripStops(); return STOP_IDS.has(id); };
/* Running: given, and not stopped since. Read off the run's timeline, the same events the
   record shows, so the cross and the record cannot disagree. */
function dripRunning(id){
  const stop=dripStops()[id]; if(!stop||!ST) return false;
  let on=false;
  for(const x of ST.timeline){
    if(x.type==='blocked') continue;
    if(x.id===id) on=true; else if(x.id===stop) on=false;
  }
  return on;
}
/* The catalog id behind a button. A pack may bind a catalog entry to a case action with
   another id, so the order and the icons, which name catalog ids, look through it. */
function catIdOf(id){
  const b=(PACK&&PACK.bindings)||{};
  for(const c in b) if(b[c]===id) return c;
  return id;
}
function groupNames(tab,groups){
  const fixed=(PROTO.groupOrder||{})[tab]||[];
  const rank=g=>{
    if(g==='Not in the catalog') return 999;
    const i=fixed.indexOf(g);
    return i<0 ? 500 : i;
  };
  return Object.keys(groups).sort((a,b)=>rank(a)-rank(b)||a.localeCompare(b));
}
/* Buttons carry the name and nothing else. Prerequisites and turnaround times used to
   be printed underneath; they are system detail the resident does not read off a menu,
   and a blocked attempt teaches the prerequisite better than a label does. */
/* On the buttons only, a leading "Consult" or "Perform" is dropped (author instruction,
   11 October 2026): the tab already says what the button does. The full name stays
   everywhere else: the record, the nurse, the debrief, search and voice. */
function buttonLabel(n){
  const t=String(n||'').replace(/^(consult|perform)\s+/i,'');
  return t ? t.charAt(0).toUpperCase()+t.slice(1) : String(n||'');
}
/* Exam button icons (author instruction, 13 October 2026). 24-unit line drawings on a muted
   pastel tile, one colour pair per exam. Display only. Keyed by catalog id. */
const BUTTON_ICON={
  exam_neck:{bg:'#E7E0F3',fg:'#7D6AAE',d:'<circle cx="12" cy="6.8" r="3.9"/><path d="M10.1 10.4v3.6M13.9 10.4v3.6"/><path d="M4.5 20.5c.8-3.6 3.8-5.6 7.5-5.6s6.7 2 7.5 5.6"/>'},
  exam_heent:{bg:'#D9E8F5',fg:'#4F7FA8',d:'<path d="M2.5 12s3.6-6 9.5-6 9.5 6 9.5 6-3.6 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.8"/>'},
  exam_card:{bg:'#F5DCE1',fg:'#B05D70',d:'<path d="M12 20s-7.5-4.6-7.5-10A4.2 4.2 0 0 1 12 7.6 4.2 4.2 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/><path d="M7.5 12.5h2.3l1.2-2 2 4 1.2-2h2.3"/>'},
  exam_pulm:{bg:'#D5ECEE',fg:'#3F8C95',d:'<path d="M12 3.5v8M12 9.5l-2.6 2M12 9.5l2.6 2"/><path d="M9.2 7.5C6.4 7.5 4 11.6 4 16c0 2.2 1.1 3.5 2.9 3.5 1.8 0 2.8-1.1 2.8-3V9"/><path d="M14.8 7.5c2.8 0 5.2 4.1 5.2 8.5 0 2.2-1.1 3.5-2.9 3.5-1.8 0-2.8-1.1-2.8-3V9"/>'},
  exam_abd:{bg:'#F8E3D4',fg:'#B5774B',d:'<path d="M7.2 3.5c0 4.2-2.2 6.2-2.2 10.2 0 3.9 3.1 6.8 7 6.8s7-2.9 7-6.8c0-4-2.2-6-2.2-10.2"/><circle cx="12" cy="13" r="1.1"/><path d="M7.5 8.5c1.4.7 2.9 1 4.5 1s3.1-.3 4.5-1"/>'},
  exam_back:{bg:'#EFE7D2',fg:'#958046',d:'<rect x="8.5" y="2.8" width="7" height="3.6" rx="1.3"/><rect x="8.5" y="8" width="7" height="3.6" rx="1.3"/><rect x="8.5" y="13.2" width="7" height="3.6" rx="1.3"/><path d="M10 18.4l2 2.8 2-2.8"/>'},
  exam_gu:{bg:'#F1DDEC',fg:'#9A5F8C',d:'<path d="M14.5 4c-4.3 0-8 3.4-8 8s3.7 8 8 8c1.9 0 3-1.1 3-2.8 0-1.9-1.9-2.6-1.9-5.2s1.9-3.3 1.9-5.2C17.5 5.1 16.4 4 14.5 4z"/><path d="M12 12h-3"/>'},
  exam_msk:{bg:'#E2EAD7',fg:'#6A8650',d:'<path d="M8.2 15.8l7.6-7.6"/><circle cx="15.6" cy="5.6" r="2.2" style="fill:var(--icbg)"/><circle cx="18.4" cy="8.4" r="2.2" style="fill:var(--icbg)"/><circle cx="5.6" cy="15.6" r="2.2" style="fill:var(--icbg)"/><circle cx="8.4" cy="18.4" r="2.2" style="fill:var(--icbg)"/><path d="M14.2 7.4l2.4 2.4M7.4 14.2l2.4 2.4" style="stroke:var(--icbg);stroke-width:2.6"/>'},
  exam_skin:{bg:'#F5EECF',fg:'#9C8634',d:'<rect x="4" y="4" width="16" height="16" rx="4.5"/><circle cx="9" cy="9.5" r="1.1"/><circle cx="14.5" cy="8.5" r=".9"/><circle cx="13" cy="14" r="1.4"/><circle cx="8.5" cy="15" r=".8"/><circle cx="16.5" cy="15.5" r=".8"/>'},
  exam_neuro:{bg:'#D8EEDF',fg:'#4B8E62',d:'<path d="M11.5 5.2C10.7 3.6 7.6 3.5 6.8 5.9 4.4 6.1 3.6 9 5 10.5c-1.6 1.6-.8 4.6 1.6 4.9.3 2.5 3.3 3.3 4.9 1.7V5.2z"/><path d="M12.5 5.2c.8-1.6 3.9-1.7 4.7.7 2.4.2 3.2 3.1 1.8 4.6 1.6 1.6.8 4.6-1.6 4.9-.3 2.5-3.3 3.3-4.9 1.7V5.2z"/><path d="M12 17.5v3"/>'},
  exam_psych:{bg:'#DCE3F6',fg:'#5F72AE',d:'<path d="M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v8A1.5 1.5 0 0 1 19 16.5h-8.5L6 20v-3.5H5A1.5 1.5 0 0 1 3.5 15V7A1.5 1.5 0 0 1 5 5.5z"/><path d="M9 11.5c.8 1.2 1.8 1.8 3 1.8s2.2-.6 3-1.8"/><path d="M9 9h.01M15 9h.01"/>'},
};
function actionButton(id,tab,grp){
  const a=ACT[id];
  const orders=ST.orders[id]||[];
  const last=orders[orders.length-1];
  let cls='ab';
  if(IS_STUDY(id)){
    if(last&&last.value===null) cls+=' pend';
    else if(last) cls+=' hasres';
  } else if(a.performs){
    if(a.performs.every(p=>ST.taken.has(p))) cls+=' done';
  } else if(ST.taken.has(id)) cls+=' done';
  if(a.orphan) cls+=' orphan';
  if(a.specimen) cls+=' spec-'+a.specimen;
  if(tab&&pickedAnywhere(id)) cls+=' picked';
  /* v0.26b. A button in one of PROTO.immediateGroups acts on the click, like an exam. */
  const now=!!(grp&&((PROTO.immediateGroups||{})[tab]||[]).includes(grp));
  const ic=BUTTON_ICON[catIdOf(id)];
  if(ic) cls+=' hasic';
  const label=ic?`<span class="abic" style="--icbg:${ic.bg};--icfg:${ic.fg}" aria-hidden="true"><svg viewBox="0 0 24 24">${ic.d}</svg></span><span>${esc(buttonLabel(a.name))}</span>`
               :esc(buttonLabel(a.name));
  /* The red cross, on a drip that is running: it stops the drip at once. */
  const stopId=dripStops()[id];
  const dripName=String(a.name).split(',')[0].trim().toLowerCase();   /* "Nitroglycerin infusion, start 50 ..." */
  const cancel=stopId&&dripRunning(id)
    ? `<span class="abstop" role="button" data-stop="${esc(stopId)}" data-tip="Cancel ${esc(dripName)}" aria-label="Cancel ${esc(dripName)}">\u00D7</span>`:'';
  if(cancel) cls+=' hasstop';
  return `<button class="${cls}" data-act="${esc(id)}" data-tabof="${esc(tab||'')}"${now?' data-now="1"':''}>${label}${cancel}</button>`;
}
/* v0.26. One group's buttons. Entries with no subgroup come first as a plain grid. The
   rest are split by subgroup, in PROTO.subgroupOrder, and drawn either as headings inside
   the folder or, for a group in PROTO.subgroupTabs, as sub-tabs with one showing at a
   time. While a filter is set every matching subgroup shows under its heading, because a
   search result hidden behind a sub-tab is not a result. */
function groupBody(tab,g,ids,filtering){
  const grid=list=>`<div class="grid">${list.map(id=>actionButton(id,tab,g)).join('')}</div>`;
  const plain=ids.filter(id=>!ACT[id].subgroup);
  const by={};
  for(const id of ids){ const s=ACT[id].subgroup; if(s) (by[s]=by[s]||[]).push(id); }
  const order=((PROTO.subgroupOrder||{})[g]||[]);
  const rank=s=>{ const i=order.indexOf(s); return i<0?500:i; };
  const subs=Object.keys(by).sort((a,b)=>rank(a)-rank(b)||a.localeCompare(b));
  let html=plain.length?grid(plain):'';
  if(!subs.length) return html;
  const asTabs=(PROTO.subgroupTabs||[]).includes(g)&&!filtering;
  if(asTabs){
    const key=tab+'|'+g;
    const cur=subs.includes(SUBTAB[key])?SUBTAB[key]:subs[0];
    html+=`<div class="subtabs" role="tablist" aria-label="${esc(g)}">${subs.map(s=>
      `<button class="subtab" role="tab" data-subtab="${esc(s)}" data-subgroup="${esc(g)}" data-tabof="${esc(tab)}"
        aria-selected="${s===cur}">${esc(s)}<span class="n">${by[s].length}</span></button>`).join('')}</div>`;
    html+=grid(by[cur]);
  } else {
    const sw=PROTO.subgroupSwatch||{};
    const folds=(PROTO.subgroupCollapsed||{})[g]||[];
    for(const s of subs){
      const chip=sw[s]?`<span class="swatch" style="background:${esc(sw[s])}"></span>`:'';
      if(folds.includes(s)){
        const key=tab+'|'+g+'|'+s, open=filtering||SUBOPEN.has(key);
        html+=`<button class="subhead subfold" type="button" data-subfold="${esc(key)}" aria-expanded="${open}">${chip}${esc(s)}
          <span class="n">${by[s].length}</span><svg class="dbfold-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>`;
        if(open) html+=grid(by[s]);
      } else {
        /* A subgroup may keep its less-used entries in a closed drop-down of its own, after
           the rest (PROTO.subgroupExtra; the green top's "Additional tests"). */
        const ex=(PROTO.subgroupExtra||{})[s];
        const extra=ex?by[s].filter(id=>ex.ids.includes(catIdOf(id))):[];
        html+=`<div class="subhead">${chip}${esc(s)}</div>`+grid(extra.length?by[s].filter(id=>!extra.includes(id)):by[s]);
        if(extra.length){
          const key=tab+'|'+g+'|'+s+'|'+ex.label, open=filtering||SUBOPEN.has(key);
          html+=`<button class="subhead subfold subextra" type="button" data-subfold="${esc(key)}" aria-expanded="${open}">${esc(ex.label)}
            <span class="n">${extra.length}</span><svg class="dbfold-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>`;
          if(open) html+=grid(extra);
        }
      }
    }
  }
  return html;
}
function renderActionTab(tab,intro){
  const groups=actionsFor(tab);
  const names=groupNames(tab,groups);
  const collapsible=(PROTO.collapsibleTabs||[]).includes(tab);
  const open=expandedOf(tab);
  /* A filter forces every surviving group open for as long as it is set. Typing a
     filter and being shown nine collapsed headers is not a search result.

     This used to be done by adding the matched groups to the expanded set AFTER the
     markup had been built, which had two faults: the effect landed one render late, so
     a filter set in a single stroke showed collapsed headers until something else
     repainted the tab, and the set kept every group that had ever matched a filter, so
     clearing the box left the accordion open on groups the learner had never touched.
     Forcing it here instead leaves the learner's own accordion state alone: clear the
     filter and the tab is exactly as they left it. */
  const forced=collapsible&&!!filterOf(tab);
  let html='';
  for(const g of names){
    const picked=groups[g].filter(id=>pickedAnywhere(id)).length;
    if(collapsible){
      const isOpen=forced||open.has(g);
      html+=`<button class="grouphdr" data-group="${esc(g)}" data-tabof="${tab}"
        aria-expanded="${isOpen}"><span class="chev">${isOpen?'\u25BC':'\u25B6'}</span>
        ${groupIconHTML(tab,g)}<span>${groupLabelHTML(g)}</span>
        ${picked?`<span class="picks">${picked} selected</span>`:''}
        <span class="n">${groups[g].length}</span></button>`;
      if(!isOpen) continue;
      html+='<div class="groupbody">';
    } else {
      html+=`<h3>${esc(g)}</h3>`;
    }
    if(g==='Not in the catalog')
      html+=`<div class="note" style="border-left-color:var(--harm)">${esc(PROTO.orphanNote)}</div>`;
    html+=groupBody(tab,g,groups[g],forced);
    if(collapsible) html+='</div>';
  }
  if(!names.length) html='<p class="sub">Nothing matches that filter.</p>';
  const orderable=PROTO.orderableTabs.includes(tab);
  const basket=[...basketOf(tab)], everything=allPicked();
  const elsewhere=PROTO.orderableTabs.filter(t=>t!==tab&&basketOf(t).size)
    .map(t=>esc(PROTO.tabLabel[t])+': '+[...basketOf(t)].map(id=>esc(dispName(id))).join(', ')).join('. ');
  return `<div class="panel"><h2>${esc(PROTO.tabLabel[tab])}</h2>
    <p class="sub">${intro}</p>
    <div class="toolbar">
      <span class="searchwrap">
        <input type="text" id="filterbox" class="filter" placeholder="Filter this tab"
          value="${esc(FILTERS[tab]||'')}" data-tabof="${tab}">
        ${filterOf(tab)?`<button class="clearfilter" id="clearfilter" data-tabof="${tab}"
          title="Clear the filter" aria-label="Clear the filter">\u00D7</button>`:''}
      </span>
      ${orderable?`<button class="btn" id="submitorder" data-tabof="${tab}" ${everything.length?'':'disabled'}>
          Submit Order${everything.length?' ('+everything.length+')':''}</button>
        <button class="btn ghost" id="clearorder" data-tabof="${tab}" ${everything.length?'':'disabled'}>${elsewhere?'Clear all':'Clear'}</button>`:''}
    </div>
    ${orderable?`<div class="basket${everything.length?'':' empty'}">${everything.length
        ? (basket.length?'Selected, not yet sent: '+basket.map(id=>esc(dispName(id))).join(', ')+'.':'Nothing selected on this tab.')
          +(elsewhere?' Also selected on '+elsewhere+'.':'')
        : 'Nothing selected. Click items to add them, then Submit Order.'}</div>`:''}
    ${html}</div>`;
}

/* Put one orderable tab back to its opening state: no filter, every group collapsed, and
   scrolled to the top. The scroll matters as much as the other two, because the panel
   keeps its offset across a re-render and a tab that has just become five headers tall
   would otherwise be scrolled past its own contents.

   The accordion is emptied rather than re-seeded from `defaultExpanded`. That seed exists
   so a resident meets Stabilization's first three acts without hunting for them on the
   opening screen, which is a question about the start of a case rather than about the
   start of a search, and by the time an order has been submitted it has been answered. */
function resetTabView(tab){
  if(!tab) return;
  FILTERS[tab]='';
  expandedOf(tab).clear();
}
/* Separate from the state above, and called after the repaint rather than before it. The
   scroll container outlives the tab's markup, so an offset set while the long filtered
   list is still on screen is clamped against that list's height and not against the short
   one that replaces it. */
function scrollTabTop(){
  const box=el('tabpanel'), sc=box&&box.closest('.lp-scroll');
  if(sc) sc.scrollTop=0;
}

function renderTab(){
  const box=el('tabpanel');
  const R={
    history:tabHistory, handoff:tabHandoff,
    exam:()=>generalStatusPanel()
             +renderActionTab('exam','Repeat any maneuver; it returns the current state.')
             +readoutPanel('exam','Findings'),
    /* Results are read in the record on the right and nowhere else. They used to be
       repeated under the order grid here, which put the same table on both sides of the
       room and left a resident unsure which one the case meant. */
    investigations:()=>renderActionTab('investigations',
      'A result reflects the patient at the moment it was ordered, not when it arrives. Results appear in the record.'),
    stabilization:()=>renderActionTab('stabilization','Access, airway, oxygen and monitoring.')
             +compositeFindingsPanel('stabilization')+blockPanel(),
    interventions:()=>renderActionTab('interventions','')+blockPanel(),
    consultations:()=>renderActionTab('consultations','')
             +readoutPanel('consult','Conversations')
  };
  const active=document.activeElement, keepId=active&&active.id, keepPos=active&&active.selectionStart;
  { const th=el('imsgthread'); if(th) THREAD_TOP=th.scrollTop; }
  box.innerHTML=(R[TAB]||tabHistory)();
  /* The thread follows the newest message when one arrives, and otherwise keeps the
     place a reader scrolled back to. */
  { const th=el('imsgthread');
    if(th){
      const n=ST.readouts.filter(r=>r.kind==='speech').length;
      th.scrollTop = (n!==THREAD_N) ? th.scrollHeight : THREAD_TOP;
      THREAD_N=n;
    } }
  if(keepId==='filterbox'||keepId==='dxbox'||keepId==='askbox'){
    const back=el(keepId);
    if(back){ back.focus(); try{ back.setSelectionRange(keepPos,keepPos); }catch(e){} }
  } else if(TAB==='history'&&!DEVNOTES.typing()){   /* never take the caret out of a note */
    const inp=el('askbox');
    if(inp&&document.activeElement!==inp){ inp.focus(); inp.setSelectionRange(inp.value.length,inp.value.length); }
  }
}

/* The general status line sits above the manoeuvres, is not clickable, and cannot be
   omitted by the learner. It is the one exam finding that is always visible. */
function generalStatusPanel(){
  const g=generalStatus(ST);
  const v=g.value||{};
  return `<div class="panel gs"><h2>General appearance</h2>
    <div class="gsline${v.abnormal?' abn':''}">${esc(v.findings||'')}</div>
  </div>`;
}

function readoutPanel(kind,title){
  const outs=ST.readouts.filter(r=>r.kind===kind).slice(-8).reverse().map(r=>
    kind==='consult'
      ? `<div class="speech"><div class="who">${esc(r.title)}, ${mmss(r.t)}</div>${esc(r.body)}</div>`
      : `<div class="read"><h4>${esc(r.title)}</h4>
         <div class="body${(r.body&&r.body.abnormal)?' abn-report':''}">${esc(
            r.body&&r.body.findings!==undefined?r.body.findings:r.body)}</div>
         <div class="meta">${mmss(r.t)}</div></div>`
  ).join('');
  return outs?`<div class="panel"><h3>${title}</h3>${outs}</div>`:'';
}
/* v0.26. Findings from a composite exam placed on an ordering tab (the airway, breathing
   and circulation exam on Stabilization), shown under that tab the way the Exam tab shows
   its own. They also go to the record like any exam. */
function compositeFindingsPanel(tab){
  const keys=new Set();
  for(const id in ACT){ const a=ACT[id]; if(a.tab===tab&&a.performs) a.performs.forEach(p=>keys.add(p)); }
  if(!keys.size) return '';
  const outs=ST.readouts.filter(r=>r.kind==='exam'&&keys.has(r.key)).slice(-6).reverse().map(r=>
    `<div class="read"><h4>${esc(r.title)}</h4>
       <div class="body${(r.body&&r.body.abnormal)?' abn-report':''}">${esc(
          r.body&&r.body.findings!==undefined?r.body.findings:r.body)}</div>
       <div class="meta">${mmss(r.t)}</div></div>`).join('');
  return outs?`<div class="panel"><h3>Findings</h3>${outs}</div>`:'';
}
function blockPanel(){
  const blk=ST.blocked.slice(-3).reverse().map(b=>
    `<div class="blockmsg"><b>${esc(dispName(b.id))} did not happen.</b><br>${esc(b.message)}
     <div class="meta">${b.source==='catalog_default'?'catalog default prerequisite':'case prerequisite'}</div></div>`).join('');
  return blk?`<div class="panel"><h3>Recent blocks</h3>${blk}</div>`:'';
}

/* ---------- arrival ----------
   Two authored facts, and both are deliberately small.

   WHERE. metadata.arrival.location is one of resuscitation_bay, trauma_bay or
   patient_room. It sets one line on the splash screen and nothing else. It
   tells the learner what kind of room they have walked into, which is real
   information a clinician has before they have any history at all.

   WHO HANDED OVER. metadata.arrival.mode is ems or triage. It only chooses the
   heading above the two-sentence handover, but the difference is worth
   authoring: a paramedic handover and a triage nurse note carry different
   things, and a resident should read them differently.

   The legacy readers below exist because cases authored before this change
   carry a free-text arrival.mode from an older vocabulary ("Ambulance",
   "Walk-in") and no location at all. Rather than break them, the mode is
   normalised and the location is recovered from the arrival line if it names a
   room. A case that says nothing gets no location line rather than a guess. */
const ARRIVAL_ROOM={resuscitation_bay:'Resuscitation Bay',trauma_bay:'Trauma Bay',
                    patient_room:'Patient Room'};
function arrivalRoom(){
  const ar=(CASE.metadata||{}).arrival||{};
  const key=String(ar.location||'').toLowerCase().replace(/[^a-z]+/g,'_');
  if(ARRIVAL_ROOM[key]) return ARRIVAL_ROOM[key];
  const hay=String(ar.line||'').toLowerCase();          /* legacy cases */
  if(hay.includes('resus')) return ARRIVAL_ROOM.resuscitation_bay;
  if(hay.includes('trauma')) return ARRIVAL_ROOM.trauma_bay;
  if(hay.includes('room'))  return ARRIVAL_ROOM.patient_room;
  return null;
}
function arrivalMode(){
  const raw=String(((CASE.metadata||{}).arrival||{}).mode||'').toLowerCase();
  if(/triage|walk|ambulatory/.test(raw)) return 'triage';
  return 'ems';                                          /* including legacy "Ambulance" */
}
function arrivalHandover(){
  const p=CASE.patient||{};
  /* Authored short form first. The long ems_handover_text is retained in the
     case file for the review packet and is deliberately not shown. */
  const short=p.arrival_handover||p.triage_handover;
  if(short) return String(short);
  const line=((CASE.metadata||{}).arrival||{}).line;     /* legacy fallback */
  return line?String(line):'';
}

/* A one-line statement of how the patient is understanding questions right now.
   It is here rather than in the header because this is the only screen where it
   changes what the learner should expect, and because a learner who asks
   "orthopnoea?" and gets a shrug deserves to know whether the patient denied it
   or the system did not follow. The wording avoids "AI" and "model": what the
   learner needs to know is how well they can expect to be understood. */
function semChip(){
  const S={
    idle:      ['basic',            'matching on wording alone'],
    loading:   ['basic',            'improving in the background, this takes a moment on first use'],
    ready:     ['enhanced',         'phrasing and abbreviations are understood'],
    unavailable:['basic',           'the enhanced matcher could not load, so wording alone is used']
  }[SEM.state]||['basic',''];
  return `<div class="semchip s-${SEM.state}">
    <span class="dot" aria-hidden="true"></span>
    <b>Question matching: ${S[0]}</b><span>${esc(S[1])}</span></div>`;
}

/* The interview as a phone message thread (author instruction, 11 October 2026): the
   learner's questions on the right in blue, the answers on the left, oldest at the top
   and newest at the bottom, the box to type in underneath. A case-clock time is shown
   above the first message and wherever more than a minute has passed. The answer's
   outer quotation marks are dropped, because a bubble already says who is speaking. */
function bubbleText(s){
  const t=String(s==null?'':s).trim();
  const m=t.match(/^(['\u2018\u201C"])([\s\S]*)(['\u2019\u201D"])$/);
  return m?m[2].trim():t;
}
function historyThread(){
  const rs=ST.readouts.filter(r=>r.kind==='speech');
  if(!rs.length) return `<div class="imsg-empty">Your conversation with the patient appears here.</div>`;
  let html='', lastT=-1e9;
  rs.forEach((r,i)=>{
    /* Only a message that has just arrived slides in. The tab is rebuilt on other
       changes too, and replaying the animation on the whole thread would flicker. */
    const fresh=(i===rs.length-1&&rs.length>THREAD_N)?' fresh':'';
    if(r.t-lastT>=60) html+=`<div class="imsg-time">${mmss(r.t)}</div>`;
    lastT=r.t;
    html+=`<div class="imsg-row me${fresh}"><div class="imsg me">${esc(r.title)}</div></div>`;
    html+=`<div class="imsg-row them${fresh}"><div class="imsg them${r.matched?'':' unmatched'}">${esc(bubbleText(r.body))}</div></div>`;
  });
  return html;
}
/* ---------- speaking a question to the patient (author instruction, 11 October 2026) ----------
   Optional. The microphone beside the question box dictates one question with the
   browser's own speech recognition. What is heard shows in the box as it is heard, and
   when the speaker stops, the question is asked exactly as if it had been typed and sent.
   Pressing the microphone again while it listens stops it and sends what was heard. It is
   separate from voice orders and never runs alongside them. Browsers without speech
   recognition do not show the button. */
const ASKMIC=(function(){
  const SR=(typeof window!=='undefined')?(window.SpeechRecognition||window.webkitSpeechRecognition||null):null;
  let rec=null, ON=false, ARMED=false, FINAL='', INTERIM='', MSG='';
  function setText(){
    ASKTEXT=(FINAL+' '+INTERIM).replace(/\s+/g,' ').trim();
    const b=el('askbox'); if(b) b.value=ASKTEXT;
  }
  function paint(){
    const m=el('askmic');
    if(m){ m.classList.toggle('on',ON); m.setAttribute('aria-pressed',ON?'true':'false');
           m.title=ON?'Listening. Press to stop and ask.':'Ask by voice'; }
    const n=el('askmicmsg'); if(n){ n.textContent=MSG; n.hidden=!MSG; }
  }
  function start(){
    if(!SR||ON||ENDED) return;
    if(typeof VOICE!=='undefined'&&VOICE.listening&&VOICE.listening()){
      MSG='Voice orders are listening. Stop them first, then ask.'; paint(); return; }
    FINAL=''; INTERIM=''; MSG=''; ON=true; ARMED=true;
    rec=new SR();
    rec.continuous=false; rec.interimResults=true; rec.maxAlternatives=1;
    rec.lang=(navigator.language&&/^en/i.test(navigator.language))?navigator.language:'en-US';
    rec.onaudiostart=()=>{ ARMED=false; };
    rec.onresult=e=>{
      let interim='';
      for(let i=e.resultIndex;i<e.results.length;i++){
        const r=e.results[i];
        if(r.isFinal) FINAL+=r[0].transcript+' '; else interim+=r[0].transcript+' ';
      }
      INTERIM=interim; setText();
    };
    rec.onerror=e=>{
      const k=e&&e.error;
      if(k==='not-allowed'||k==='service-not-allowed') MSG='The browser blocked the microphone. Allow it for this page, or type the question.';
      else if(k==='network') MSG='The browser could not reach its speech service. Type the question.';
      else if(k==='audio-capture') MSG='No microphone was found. Type the question.';
      else if(k==='no-speech') MSG='Nothing was heard. Press the microphone and ask again.';
    };
    rec.onend=()=>{
      const heard=(FINAL+' '+INTERIM).replace(/\s+/g,' ').trim();
      ON=false; ARMED=false; rec=null; FINAL=''; INTERIM='';
      paint();
      if(heard&&!ENDED){ MSG=''; paint(); ask(heard); }
    };
    try{ rec.start(); }
    catch(err){ ON=false; ARMED=false; rec=null; MSG='The microphone could not be started. Type the question.'; }
    paint();
  }
  function stop(){ if(ON&&rec){ try{ rec.stop(); }catch(err){} } }
  /* Leaving, restarting or pausing a case: nothing heard is asked. */
  function abort(){
    if(!rec){ ON=false; ARMED=false; return; }
    const r=rec; r.onresult=r.onend=r.onerror=r.onaudiostart=null;
    try{ r.abort(); }catch(err){}
    rec=null; ON=false; ARMED=false; FINAL=''; INTERIM=''; paint();
  }
  return {supported:()=>!!SR, listening:()=>ON, arming:()=>ARMED, msg:()=>MSG,
          toggle:()=>{ ON?stop():start(); }, abort, paint};
})();
let THREAD_N=-1, THREAD_TOP=0;
function tabHistory(){
  const p=CASE.patient||{};
  /* Age, sex and weight stay on screen. They are not history to be taken: they
     are on the wristband, and weight-based dosing is unanswerable without the
     last of them. */
  const demo=[p.age?p.age+' year old':'', p.sex||'', p.weight_kg?p.weight_kg+' kg':'']
             .filter(Boolean).join(', ');
  const hand=arrivalHandover();
  const who=arrivalMode()==='triage'?'Handover from the triage nurse':'Handover from the paramedics';
  return `<div class="panel"><h2>History</h2>
    ${demo?`<p class="sub">${esc(demo)}</p>`:''}
    ${hand?`<div class="handover"><div class="who">${who}</div>${esc(hand)}</div>`:''}
    <!-- The transcript heading below is "What you were told" rather than "What he told
         you". It said "he" until v0.11, which was wrong in the two packs whose patient is
         a woman, and tokenising it would have been the obvious fix and the wrong one: a
         case may author a collateral historian, and DIPH does, so the person answering is
         not always the patient and their sex is not patient.sex. Neutral phrasing is
         correct for every case and needs no substitution. "Ask the patient" above it still
         assumes the patient answers, which is a case-level question rather than a string:
         see DIPH's review packet, section 3. -->
    <h3>Ask the patient</h3>
    <div class="imsg-glass">
      <div class="imsg-thread" id="imsgthread" aria-live="polite">${historyThread()}</div>
      <div class="imsg-compose">
        ${ASKMIC.supported()?`<button class="imsg-mic${ASKMIC.listening()?' on':''}" id="askmic" type="button"
          aria-pressed="${ASKMIC.listening()}" title="${ASKMIC.listening()?'Listening. Press to stop and ask.':'Ask by voice'}" aria-label="Ask by voice">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/></svg></button>`:''}
        <input type="text" id="askbox" placeholder="${ASKMIC.listening()?'Listening…':'Ask the patient something'}" autocomplete="off" value="${esc(ASKTEXT)}">
        <button class="imsg-send" id="askbtn" title="Ask" aria-label="Ask">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/></svg></button>
      </div>
    </div>
    <div class="askmicmsg" id="askmicmsg"${ASKMIC.msg()?'':' hidden'}>${esc(ASKMIC.msg())}</div>
    ${semChip()}
</div>`;
}

/* Line icons for the disposition tiles. Chosen from words in the disposition id, which a
   case authors, so the engine names no case and a new id falls back to the hospital. */
const DISP_ICON={
  home:'<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
  clock:'<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>',
  talk:'<path d="M4 5h16v11H9l-5 4z"/><path d="M8 10h8M8 13h5"/>',
  bed:'<path d="M3 6v13M3 15h18v4M21 15v-3a3 3 0 0 0-3-3h-8v6"/><circle cx="6.5" cy="11.5" r="2"/>',
  ecg:'<path d="M2 12h4l2-5 3 10 3-8 2 3h6"/>',
  monitor:'<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M5.5 10h3l1.5-3 2 6 1.5-3h5"/><path d="M9 20h6M12 16v4"/>',
  heart:'<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/><path d="M15 3c2 1 2.5 3 1.5 5"/>',
  scalpel:'<path d="M4 20l9-9"/><path d="M13 11l6-6c1 2 0 5-3 7l-2 1z"/>',
  transfer:'<rect x="2" y="8" width="12" height="9" rx="1"/><path d="M14 11h4l3 3v3h-7"/><circle cx="6" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/><path d="M7 12.5h4M9 10.5v4"/>',
  hospital:'<path d="M4 21V5h16v16"/><path d="M2 21h20M12 8v6M9 11h6"/>'
};
function dispIcon(id){
  const s=String(id||'').toLowerCase();
  const k=/home|discharge/.test(s)?'home'
    :/observ/.test(s)?'clock'
    :/psych/.test(s)?'talk'
    :/cath/.test(s)?'heart'
    :/operat|surg|theatre/.test(s)?'scalpel'
    :/transfer/.test(s)?'transfer'
    :/icu|ccu|intensive|critical/.test(s)?'monitor'
    :/step|hdu|intermediate/.test(s)?'ecg'
    :/floor|ward|medical/.test(s)?'bed'
    :'hospital';
  return `<svg class="dispicon" viewBox="0 0 24 24" aria-hidden="true">${DISP_ICON[k]}</svg>`;
}

function tabHandoff(){
  const h=CASE.handoff;
  const disp=[{id:h.correct_disposition.id,label:h.correct_disposition.label}]
    .concat(h.alternative_dispositions.map(d=>({id:d.id,label:d.label})))
    .sort((a,b)=>PROTO.dispOrder.indexOf(a.id)-PROTO.dispOrder.indexOf(b.id));
  const dxs=PENDING_HANDOFF.diagnoses;
  const pend=ST.pending.length;
  /* Results are on the chart the moment they return, so there is no unread state to
     warn about. What can still be missed is a study that never came back. */
  return `<div class="panel"><h2>Handoff</h2>
    <p class="sub">Submitting and confirming ends the case and generates the debrief.
    The diagnosis list is the full catalog, ${PROTO.diagnoses.length} entries.</p>
    <h3>Disposition</h3>
    <div class="dispgrid${disp.length>6?' g4':''}">
    ${disp.map(d=>`<button class="opt disptile" data-disp="${esc(d.id)}" aria-pressed="${PENDING_HANDOFF.disposition===d.id}">${dispIcon(d.id)}<span>${esc(d.label)}</span></button>`).join('')}
    </div>
    <h3>Diagnoses</h3>
    <p class="sub">Name everything you are handing over. The first entry is your primary
    diagnosis; add as many others as apply to this patient.</p>
    ${dxs.length?`<ol class="dxlist">${dxs.map((id,i)=>`<li class="dxrow${i?'':' primary'}">
        <span class="dxrank">${i?i+1:'Primary'}</span>
        <span class="dxname">${esc(dxLabel(id))}</span>
        ${i?`<button class="dxbtn" data-dxup="${esc(id)}" title="Make this the primary diagnosis" aria-label="Make ${esc(dxLabel(id))} the primary diagnosis">Make primary</button>`:''}
        <button class="dxbtn" data-dxrm="${esc(id)}" title="Remove" aria-label="Remove ${esc(dxLabel(id))}">\u00D7</button>
      </li>`).join('')}</ol>`:''}
    <input type="text" id="dxbox" placeholder="${dxs.length?'Add another diagnosis':'Search '+PROTO.diagnoses.length+' diagnoses'}" autocomplete="off"
      value="${esc(DXTEXT)}">
    <div id="dxhits"></div>
    <h3>Confirm</h3>
    ${pend?`<div class="note"><b>Before you confirm.</b> ${pend} study still pending.</div>`:''}
    <button class="btn" id="submitho" ${(!PENDING_HANDOFF.disposition||!dxs.length)?'disabled':''}>Hand over and end the case</button>
    <button class="btn ghost" id="earlyexit" style="margin-left:8px">End early without handing over</button>
    </div>`;
}

/* ---------- interview matching (section 8.6) ---------- */
const STOP=new Set(('a an the is are was were do does did you your yours he him his i me my of to in on at it '
 +'any have has had can could would will about for with what when how why where which that this and or but '
 +'tell please sir mr been being get got some there their they').split(' '));
function norm(s){ return s.toLowerCase().replace(/[^a-z0-9\s]/g,' ').split(/\s+/).filter(w=>w&&!STOP.has(w)); }

/* ============================================================
   CLINICAL LEXICON

   Section 10.4 requires the PATIENT to speak in lay language, and the variant
   banks were written in the same register. Residents do not type in that
   register. Measured on the CHFE bank, 31 of 40 common clinical terms and
   abbreviations appear in none of the 340 variants, so "PND?", "orthopnea?",
   "PMH?" and "NKDA?" scored exactly zero against every topic and fell through
   to the out-of-scope fallback. That is a vocabulary gap, not a scoring
   problem, and no threshold fixes it.

   Each key is a clinical term or abbreviation. Each value is the lay words the
   banks are actually written in, chosen by reading the vocabulary of the
   existing topics rather than guessed, so an expansion lands on words that are
   really there.

   THIS IS CLINICAL CONTENT AND NEEDS A PHYSICIAN'S REVIEW, on the same footing
   as the action catalog. A wrong entry here produces a confident wrong answer,
   which section 8.6 names as the failure mode invisible to the learner. Two
   rules kept the list conservative:

     - No key shorter than two letters that could be a typo of something else.
       "PE" is omitted for that reason, and because it is a diagnosis rather
       than a question.
     - Nothing that would put a diagnosis in the patient's mouth. "chf" maps to
       the words for asking about known history, not to an answer.

   It lives here rather than in the catalog because it is case-independent and
   because engine/matcher_eval.mjs extracts this whole region from the build and
   tests it. When a second case pack exists, move it beside the action catalog
   and load it through SHARED, and update the marker comments in the harness.
   ============================================================ */
const LEXICON={
  /* breathing */
  'pnd':'wake night gasping breath', 'paroxysmal nocturnal dyspnoea':'wake night gasping breath',
  'paroxysmal nocturnal dyspnea':'wake night gasping breath',
  'orthopnea':'lie flat pillows sleep lying down prop', 'orthopnoea':'lie flat pillows sleep lying down prop',
  'dyspnea':'breathless breathing breath short', 'dyspnoea':'breathless breathing breath short',
  'sob':'breathless short breath', 'soboe':'breathless walk stairs exercise',
  'doe':'breathless walk stairs exercise tolerance', 'exertional':'walk stairs exercise tolerance',
  'exertion':'walk stairs exercise tolerance',
  'haemoptysis':'coughed up blood', 'hemoptysis':'coughed up blood',
  'productive':'phlegm sputum coughing up', 'purulent':'phlegm colour sputum',
  'expectorate':'coughing up phlegm', 'expectorating':'coughing up phlegm',
  'osa':'snore breathing sleep night apnoea', 'sleep apnoea':'snore breathing sleep night apnoea',
  'sleep apnea':'snore breathing sleep night apnoea',
  'copd':'chest breathing medical problems history',

  /* circulation */
  'oedema':'swelling swollen legs ankles feet', 'edema':'swelling swollen legs ankles feet',
  'pedal oedema':'swelling swollen ankles feet legs', 'pedal edema':'swelling swollen ankles feet legs',
  'peripheral oedema':'swelling swollen ankles feet legs', 'peripheral edema':'swelling swollen ankles feet legs',
  'syncope':'passed out fainted collapsed blackouts', 'presyncope':'dizzy lightheaded nearly passed out',
  'pleuritic':'chest pain breathing', 'diaphoresis':'sweating sweats',
  'diaphoretic':'sweating sweats', 'claudication':'pain legs walk',
  'dvt':'leg swollen calf pain clot', 'vte':'clot leg travel immobility',
  'htn':'blood pressure', 'ihd':'heart attack', 'cad':'heart attack',
  'mi':'heart attack', 'nstemi':'heart attack', 'stemi':'heart attack',
  'chf':'heart problems medical history', 'ccf':'heart problems medical history',
  'hfref':'heart problems medical history',

  /* abdomen and renal */
  'emesis':'vomiting sick', 'haematemesis':'vomiting blood', 'hematemesis':'vomiting blood',
  'anorexia':'appetite eat eating', 'ascites':'bloated belly swelling abdomen distended',
  'oliguria':'passing urine less output', 'anuria':'passing urine output',
  'polyuria':'passing urine often more', 'nocturia':'urine night toilet passing',
  'ckd':'kidney medical problems',

  /* history taking, the sections residents name by abbreviation */
  /* general shorthand, added Sep 2026 after the first measured run. `hx` on its own
     had become a rare token in the expanded banks ("Hx of afib?") and was pulling every
     "<thing> hx" question toward whichever topic happened to hold it. */
  'hx':'history', 'sx':'symptoms', 'dx':'diagnosis diagnosed told', 'rx':'medication tablets prescribed',
  'abx':'antibiotics', 'cp':'chest pain', 'uop':'urine passing water', 'loc':'passed out consciousness blackout',
  'lmp':'last period', 'n v':'sick vomiting nausea', 'nv':'sick vomiting nausea', 'po':'eat drink',
  'tob':'smoke smoking cigarettes', 'afib':'heart racing irregular fibrillation', 'af':'heart racing irregular fibrillation',
  'dm':'diabetes', 'bp':'blood pressure', 'uti':'burning pass urine infection', 'sti':'sexually active partners infection',
  'std':'sexually active partners infection', 'gu':'urine burning discharge', 'ros':'symptoms',
  'pmh':'medical problems history conditions diagnosed', 'pmhx':'medical problems history conditions diagnosed',
  'psh':'operations surgery procedures', 'pshx':'operations surgery procedures',
  'fhx':'family history parents siblings', 'shx':'smoke drink alcohol tobacco',
  'meds':'medications tablets medicines', 'medication':'medications tablets medicines',
  'compliance':'taking medications missed tablets doses prescribed',
  'adherence':'taking medications missed tablets doses prescribed',
  'concordance':'taking medications missed tablets doses prescribed',
  'nkda':'allergies allergic drug', 'allergy':'allergies allergic',
  'npo':'last eat drink food', 'nbm':'last eat drink food',
  'etoh':'alcohol drink', 'ivdu':'drugs recreational street use',
  'pwid':'drugs recreational street use', 'pack years':'cigarettes smoke day many',
  'pack year':'cigarettes smoke day many',
  'adls':'normally manage walk stairs shopping', 'functional status':'normally manage walk stairs shopping',

  /* infection and exposure */
  'sick contacts':'anyone ill sick unwell around', 'uri':'cold sore throat runny nose flu',
  'urti':'cold sore throat runny nose flu', 'lrti':'chest infection cough',
  'pyrexia':'fever temperature', 'pyrexial':'fever temperature', 'febrile':'fever temperature',
  'rigors':'chills shivering shakes',

  /* drugs the resident will name where the patient would not */
  'water pill':'water tablet diuretic medications', 'water tablet':'water tablet diuretic medications',
  'diuretic':'water tablet medications', 'furosemide':'water tablet diuretic medications',
  'frusemide':'water tablet diuretic medications', 'lasix':'water tablet diuretic medications',
  'sodium':'salt salty diet', 'dietary sodium':'salt salty diet eating'
};
/* Multi-word keys are matched on the raw string before tokenising, longest
   first so "pedal oedema" is not eaten by "oedema". */
const LEX_PHRASES=Object.keys(LEXICON).filter(k=>k.indexOf(' ')>=0)
                        .sort((a,b)=>b.length-a.length);

/* ---------- typo repair ----------
   Optimal string alignment distance, which counts a transposition as one edit,
   so "takign" reaches "taking" and "strat" reaches "start". Plain Levenshtein
   charges two for those and would miss both.

   Repair is applied PER TOKEN against the bank's own vocabulary, never sentence
   against sentence. That distinction is the whole design. A first attempt at
   this scored whole questions against whole variants by character trigram; it
   lifted typo handling from 25 to 75 percent and took out-of-scope rejection
   from 60 percent to zero, because any two English sentences share plenty of
   trigrams. Repairing single words cannot invent that similarity: an unrelated
   word has no near neighbour in the vocabulary, so it stays unknown and keeps
   costing the query weight, which is what makes an unrelated question score
   low in the first place. */
function osaDistance(a,b,max){
  const n=a.length,m=b.length;
  if(Math.abs(n-m)>max) return max+1;
  let prev2=null,prev=new Array(m+1),cur=new Array(m+1);
  for(let j=0;j<=m;j++) prev[j]=j;
  for(let i=1;i<=n;i++){
    cur[0]=i; let rowMin=i;
    for(let j=1;j<=m;j++){
      const cost=a.charCodeAt(i-1)===b.charCodeAt(j-1)?0:1;
      let v=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+cost);
      if(i>1&&j>1&&a.charCodeAt(i-1)===b.charCodeAt(j-2)&&a.charCodeAt(i-2)===b.charCodeAt(j-1))
        v=Math.min(v,prev2[j-2]+cost);
      cur[j]=v; if(v<rowMin) rowMin=v;
    }
    if(rowMin>max) return max+1;                 /* whole row already too far */
    prev2=prev; prev=cur; cur=new Array(m+1);
  }
  return prev[m];
}
/* Two limits, both chosen by measurement rather than argument.

   FIVE LETTERS, NOT SIX. Six was measurably safer: it turned "shall i call your
   family" from a wrong answer into a fallthrough. It also turned "when did this
   strat" from a correct answer into a fallthrough. The deciding argument is not
   a metric but the teaching situation: this simulator is the learner's only
   source of history, so a fallthrough costs them information they cannot get
   anywhere else, while a visibly odd answer at least sits in the transcript
   next to the question they typed. Generosity wins at five.

   ONE EDIT, NEVER TWO. This one is not a trade. Allowing two edits on longer
   words repaired no additional real typo in the eval set and added one
   misroute, so it is strictly worse. Every typo worth catching is one edit away
   once transpositions count as one, which is why the distance is optimal string
   alignment and not Levenshtein: plain Levenshtein charges two for a swap and
   would miss "takign" and "strat". */
function repairWord(w){
  if(w.length<5) return null;
  if(REPAIR_CACHE.has(w)) return REPAIR_CACHE.get(w);
  const max=1;
  let best=null,bd=max+1;
  const scan=cand=>{
    if(cand.length<4||Math.abs(cand.length-w.length)>max) return;
    const d=osaDistance(w,cand,max);
    /* Ties broken lexicographically so the same typo always repairs the same
       way. A matcher that depends on object iteration order is not reproducible
       and the debrief claims to report what the learner actually did. */
    if(d<bd||(d===bd&&best!==null&&cand<best)){ bd=d; best=cand; }
  };
  VOCAB.forEach(scan);
  for(const k in LEXICON) if(k.indexOf(' ')<0) scan(k);
  const out=bd<=max?best:null;
  REPAIR_CACHE.set(w,out);
  return out;
}

/* ---------- query normalisation ----------
   Applied to the learner's question only, never to the authored variants: the
   bank defines the vocabulary and the IDF weights, and rewriting it would move
   the ground the query is measured against.

   A token is rewritten only where the bank does not already contain it. That
   ordering matters. "palpitations" and "haemoptysis" ARE in the bank, so they
   are left exactly as they are and every match that works today keeps working;
   expansion is strictly a fallback for words the bank has never heard of. */
function normQuery(q){
  let s=' '+String(q==null?'':q).toLowerCase().replace(/[^a-z0-9\s]/g,' ')
        .replace(/\s+/g,' ')+' ';
  const phrases=[];
  for(const p of LEX_PHRASES){
    if(s.indexOf(' '+p+' ')>=0){ s=s.split(' '+p+' ').join(' '); phrases.push(LEXICON[p]); }
  }
  const out=[];
  for(const w of s.split(/\s+/)){
    if(!w||STOP.has(w)) continue;
    if(VOCAB.has(w)){ out.push(w); continue; }            // the bank knows this word
    if(LEXICON[w]){ norm(LEXICON[w]).forEach(x=>out.push(x)); continue; }
    const r=repairWord(w);
    if(r===null){ out.push(w); continue; }                // unknown: keep, it costs weight
    if(LEXICON[r]) norm(LEXICON[r]).forEach(x=>out.push(x));
    else out.push(r);
  }
  for(const p of phrases) norm(p).forEach(x=>out.push(x));
  return Array.from(new Set(out));
}

let DF={}, NTOP=0, RARE={}, VOCAB=new Set(), REPAIR_CACHE=new Map();
/* Rebuilt whenever a case is selected: the weights describe one case's variant bank. */
/* ---------- the out-of-scope bank ----------
   A case may carry `interview.out_of_scope_bank`: questions it has no authored answer
   to. They are matched exactly like a topic, under this reserved id, and a question
   that lands closest to them is answered by the fallback rather than by the nearest
   real topic. Measured before this existed: nineteen of thirty unrelated questions on
   AFRVR were answered with a confident wrong topic, because "nothing relevant" had no
   neighbourhood of its own and every question is closest to something. */
const OOS_TOPIC='__out_of_scope__';
function matchTopics(){
  const bank=(CASE.interview&&CASE.interview.out_of_scope_bank)||[];
  const ts=CASE.interview.topics.slice();
  if(bank.length) ts.push({topic:OOS_TOPIC,canonical:bank[0],variants:bank.slice(1)});
  return ts;
}
/* What the embedding model is given to embed: the topics, the out-of-scope bank, and
   every authored fact's own phrasings under a `topic#fact` key. The fact rows never
   compete for a topic (the fusion skips keys with a hash); they exist so a follow-up
   can be scored against the last topic's facts by the same model. */
function semanticRows(){
  const rows=matchTopics();
  for(const t of CASE.interview.topics)
    for(const f of (t.facts||[]))
      if(f.asks&&f.asks.length) rows.push({topic:t.topic+'#'+f.id,canonical:f.asks[0],variants:f.asks.slice(1)});
  return rows;
}
function buildMatcher(){
  const TS=matchTopics();
  DF={}; RARE={}; NTOP=TS.length;
  VOCAB=new Set(); REPAIR_CACHE=new Map();
  for(const t of TS){
    const seen=new Set();
    for(const c of [t.canonical].concat(t.variants||[])) norm(c).forEach(w=>seen.add(w));
    seen.forEach(w=>DF[w]=(DF[w]||0)+1);
  }
  for(const t of TS){
    const seen=new Set();
    for(const c of [t.canonical].concat(t.variants||[])) norm(c).forEach(w=>seen.add(w));
    seen.forEach(w=>{ if((DF[w]||0)<=2) (RARE[w]=RARE[w]||new Set()).add(t.topic); });
  }
  VOCAB=new Set(Object.keys(DF));
}
const idf=w=>Math.log((NTOP+1)/((DF[w]||0)+0.5));
function wdice(a,b){
  const A=new Set(a),B=new Set(b); if(!A.size||!B.size) return 0;
  let inter=0,tot=0;
  new Set([...A,...B]).forEach(w=>{ const g=idf(w); tot+=g; if(A.has(w)&&B.has(w)) inter+=g; });
  return tot ? (2*inter)/(tot+inter) : 0;
}
/* Words the learner actually typed that the bank holds verbatim: the only words the
   rare-word override below is allowed to act on. A word that reached the query through
   a typo repair or a lexicon expansion is a guess, and a guess must not outrank a
   measured match. */
function typedBankWords(q){
  const out=new Set();
  for(const w of norm(q)) if(VOCAB.has(w)) out.add(w);
  return out;
}
/* Every topic's best lexical score for a question, the out-of-scope bank included.
   This is what the fusion below combines with the embedding model's per-topic scores;
   matchTopic() is the same ranking reduced to one answer, for use before the model
   has loaded. */
function rankTopics(q){
  const qt=normQuery(q), scores={};
  for(const t of matchTopics()){
    let b=0;
    for(const c of [t.canonical].concat(t.variants||[])){ const s=wdice(qt,norm(c)); if(s>b) b=s; }
    scores[t.topic]=b;
  }
  return {qt,scores};
}
function matchTopic(q){
  const {qt,scores}=rankTopics(q);
  let best=null,bs=0;
  for(const k in scores) if(scores[k]>bs){ bs=scores[k]; best=k; }
  /* A rare word the learner typed pulls the match toward its topic, but only when that
     topic is a genuine contender. The measured failure this guards against: "pmh?"
     expanded to "diagnosed", which was rare and belonged to sleep apnoea, and a 0.67
     match on past medical history was handed to a topic scoring 0.19. */
  const typed=typedBankWords(q);
  for(const w of qt){
    if(!typed.has(w)||!RARE[w]||RARE[w].has(best)) continue;
    let alt=null,as=0; RARE[w].forEach(t=>{ if(scores[t]>as){ as=scores[t]; alt=t; } });
    if(alt&&as>=PROTO.matchThreshold&&as>=0.8*bs){ best=alt; bs=as; break; }
  }
  if(bs<PROTO.matchThreshold) return {topic:null,score:bs};
  if(best===OOS_TOPIC) return {topic:null,score:bs,oos:true};
  return {topic:best,score:bs};
}

/* ---------- fusion of the lexical and semantic matchers ----------
   Until the embedding model has loaded, and permanently if it never does, the
   lexical matcher above answers alone. Once the model is ready the two are
   combined PER TOPIC:

       combined[t] = WEIGHT * cosine[t] + (1 - WEIGHT) * lexical[t]

   and the best combined score wins if it clears THRESHOLD. The out-of-scope bank
   is a topic in both rankings, so "nothing relevant" competes on equal terms and
   a question that lands closest to it gets the fallback.

   This replaced a threshold ladder (semantic wins above ACCEPT, agreement counts
   above AGREE, otherwise lexical). Measured against the ladder on the held-out
   sets after the banks were expanded, the ladder was handing correct lexical
   answers to near-tie semantic guesses: "when did the shortness of breath begin"
   scored 0.80 on both onset and character_of_dyspnea for the model, the lexical
   matcher had onset at 0.78, and the ladder took the model's coin toss. A sum
   lets the second matcher break the tie, which is the only thing a second
   matcher is for.

   WEIGHT and THRESHOLD were chosen on the packs' TUNING sets, which are phrasings
   withheld from the banks by catalog/expand_interview_variants.py, never on the
   held-out sets that are quoted. engine/matcher_eval.mjs --sweep reproduces the
   choice. The harness may override them through FUSE_OVERRIDE, which exists only
   so a sweep can run against the shipped code rather than a copy of it.

   Every result records which matcher produced it. The model may finish loading
   part way through a case, so two identical questions in one session can be
   routed differently, and a debrief that claims to report what the learner did
   should be able to say which. Nothing already in the log is ever re-matched. */
const FUSE={weight:0.6, threshold:0.45, soloCosine:0.62, soloMargin:0.08, soloLexical:0.55, lexicalUncontested:0.55};
function fuseParams(){ return (typeof FUSE_OVERRIDE!=='undefined'&&FUSE_OVERRIDE)?FUSE_OVERRIDE:FUSE; }
async function matchOne(q){
  const lex=matchTopic(q);
  const out=(topic,score,matcher)=>({topic,score,matcher,lexTopic:lex.topic});
  if(!SEM.ready()) return out(lex.topic,lex.score,'lexical');
  let sem=null;
  try{ sem=await SEM.best(q); }catch(e){ sem=null; }
  if(!sem||!sem.scores) return out(lex.topic,lex.score,'lexical');
  const F=fuseParams(), lx=rankTopics(q).scores;
  let best=null,bs=-1;
  for(const t in lx){
    const c=F.weight*(sem.scores[t]===undefined?0:sem.scores[t])+(1-F.weight)*lx[t];
    if(c>bs){ bs=c; best=t; }
  }
  /* A question the bank shares no words with scores zero lexically and cannot reach
     THRESHOLD on the model's half alone unless the cosine is very high. Where the
     model is both confident and unambiguous, its answer stands on its own: "Temp at
     home?" is fever at 0.69 with the runner-up at 0.39, and no token overlap is
     needed to believe it. Both figures were chosen on the tuning sets. */
  if(bs<F.threshold && sem.score>=F.soloCosine && sem.margin>=F.soloMargin && sem.topic!==null){
    best=sem.topic; bs=sem.score;
  }
  /* And the mirror image. The model has never seen "NKDA?" or "PMH?" and scores
     nothing above 0.35 for them, while the lexicon takes the lexical matcher straight to
     allergies at 0.78. Where the lexical matcher is confident and the model has no
     confident opinion of its own, the lexical answer stands. Without this the expanded
     fusion was WORSE than the lexical matcher alone on clinical shorthand, which is the
     register the whole lexicon exists for. */
  if(bs<F.threshold && lex.topic!==null && lex.score>=F.soloLexical && sem.score<F.lexicalUncontested){
    best=lex.topic; bs=lex.score;
  }
  if(bs<F.threshold||best===null) return out(null,bs,'fused');
  if(best===OOS_TOPIC) return out(null,bs,'fused-out-of-scope');
  /* Two real topics within a hair of each other, both over the line: the matcher
     does not know, and guessing is the failure the learner cannot see. It asks. */
  const D=PROTO.interviewDefaults||{};
  let second=null,ss=-1;
  for(const t in lx){
    if(t===best||t===OOS_TOPIC) continue;
    const c=F.weight*(sem.scores[t]===undefined?0:sem.scores[t])+(1-F.weight)*lx[t];
    if(c>ss){ ss=c; second=t; }
  }
  if(second&&ss>=F.threshold&&(bs-ss)<(D.clarifyMargin||0)) return {...out(null,bs,'fused-clarify'),clarify:[best,second]};
  const r=out(best,bs,'fused');
  if(bs<(D.echoBelow||0)) r.uncertain=true;
  return r;
}

/* ---------- follow-ups: the last topic is the context (design 10.7) ----------
   "And how bad?" after "tell me about the pain" is about the pain. A short question
   is first tried as a continuation of whatever the patient last spoke about: either
   "anything else?" (the topic's untold facts) or one of the topic's authored facts,
   scored the same way topics are. Only if neither fits does it go to the full matcher,
   and even then a weak global match yields to a good fact match. */
function lastSpokenTopic(){
  if(typeof ST==='undefined'||!ST||!ST.readouts) return null;
  for(let i=ST.readouts.length-1;i>=0;i--){
    const r=ST.readouts[i];
    if(r.kind==='speech'&&r.matched) return r.matched;
  }
  return null;
}
function isMorePhrase(q){
  const D=PROTO.interviewDefaults||{};
  const n=norm(q).join(' ');
  const raw=String(q).toLowerCase().replace(/[^a-z\s]/g,' ').replace(/\s+/g,' ').trim();
  return (D.morePhrasings||[]).some(p=>raw===p||n===p||raw===p+' then');
}
async function matchFact(q,topicId,sem){
  const T=CASE.interview.topics.find(x=>x.topic===topicId);
  if(!T||!T.facts||!T.facts.length) return null;
  const F=fuseParams(), qt=normQuery(q);
  let best=null,bs=-1;
  for(const f of T.facts){
    let lx=0;
    for(const a of (f.asks||[])){ const v=wdice(qt,norm(a)); if(v>lx) lx=v; }
    const sv=sem&&sem.scores?sem.scores[topicId+'#'+f.id]:undefined;
    const c=sem?F.weight*(sv===undefined?0:sv)+(1-F.weight)*lx:lx;
    if(c>bs){ bs=c; best=f.id; }
  }
  return best&&bs>=F.threshold?{fact:best,score:bs}:null;
}


/* ---------- compound questions ----------
   "Any chest pain or palpitations?" is two questions. Until now the matcher
   answered one of them and dropped the other with no signal, so a learner could
   walk away believing they had asked about both and recorded a pertinent
   negative they were never actually given.

   Splitting is also the largest remaining source of ADDITIONAL answers, which
   matters here more than it would elsewhere: this simulator is the learner's
   only source of history, so an answer withheld is not recoverable from any
   other part of the case.

   Not every "or" joins two questions. Plenty of single-intent questions contain
   one, including authored variants like "Is it tightness or is it not getting
   air in?" and "Has it come and gone or been constant?". Splitting those
   naively produced a spurious second answer on 7 of the 340 authored variants.

   The gate: the question as a whole is matched first, and a clause earns its
   own answer only if it matches at least as convincingly as the whole question
   did. A fragment of a single-intent question never does, because the whole
   sentence is the better match for it. That took the spurious extras from 7 to
   1 while keeping every genuine second answer, so it costs no generosity at
   all. Measured identical anywhere from 0.7 to 1.0; the low end is used because
   nothing here argues for being strict. */
const CLAUSE_TOLERANCE=0.7;
const CLAUSE_SPLIT=/\s+(?:and|or|also|plus)\s+|\s*[,;]+\s*|\s+&\s+/i;
function splitClauses(q){
  const parts=String(q==null?'':q).split(CLAUSE_SPLIT).map(s=>s.trim()).filter(s=>s.length>2);
  return parts.length>1?parts:[];
}

/* Returns one entry per topic the question asked about, in the order the
   learner wrote them. Capped at three: past that it stops reading as a
   conversation and starts reading as a data dump. */
async function matchQuestion(q){
  const D=PROTO.interviewDefaults||{};
  const last=lastSpokenTopic();
  const words=norm(q).length;
  if(last&&isMorePhrase(q)) return [{topic:last,score:1,matcher:'follow-up',more:true,q}];
  const parts=splitClauses(q);
  if(!parts.length){
    const only=await matchOne(q);
    /* A short question that is weak or unmatched globally, or that lands on the topic
       just spoken about, is tried against that topic's facts. */
    if(last&&words<=(D.followUpMaxWords||6)&&(only.topic===null||only.uncertain||only.topic===last)){
      let sem=null;
      if(SEM.ready()){ try{ sem=await SEM.best(q); }catch(e){ sem=null; } }
      const f=await matchFact(q,last,sem);
      /* A fact wins over a weak or absent global match outright. Over a confident
         match on the same topic it has to score higher, or "When did it start?" asked
         a second time would be handed to the "how did it start" fact instead of being
         the repeat it is. */
      const confidentSame=only.topic===last&&!only.uncertain;
      if(f&&(!confidentSame||f.score>only.score)) return [{topic:last,score:f.score,matcher:'follow-up',fact:f.fact,q}];
    }
    return [{...only,q}];
  }
  /* The whole question is the baseline reading, and the bar each clause has to
     clear to earn an answer of its own. */
  const whole=await matchOne(q);
  const bar=(whole.topic?whole.score:0)*CLAUSE_TOLERANCE;
  const hits=[], seen=new Set();
  for(const p of parts){
    const r=await matchOne(p);
    if(!r.topic||r.score<bar||seen.has(r.topic)) continue;
    seen.add(r.topic); hits.push({...r,q:p});
  }
  /* If the split changed the meaning, the question as a whole may reach a topic
     no clause did. Ask it too rather than lose the reading. */
  if(whole.topic && !seen.has(whole.topic)){ seen.add(whole.topic); hits.push({...whole,q}); }
  if(hits.length) return hits.slice(0,3);
  return [{...whole,q}];
}

/* Bind both matchers to the selected case. Kept out of buildMatcher deliberately:
   engine/matcher_eval.mjs extracts the region above verbatim from the build and
   runs it, per section 8.6, so that region has to stay free of anything the
   lexical matcher does not need. */
function bindCase(){
  buildMatcher();
  /* The voice order index is built per case, because a catalog id resolves to whatever
     the bound case calls it, and an orphan action exists only in its case. */
  VOICE.build(VOICE_DATA);
  /* Not awaited. The case must be playable the instant it is chosen, and a
     first model load can take tens of seconds. */
  try{ SEM.init(CASE.case_id, semanticRows()); }catch(e){}
}
/* Repaint the History tab when the matcher changes state, so the line under the
   question box stops saying "improving" once it has. Nothing else depends on it. */
SEM.onChange(()=>{ if(!ENDED && TAB==='history') renderTab(); });

/* ---------- events ---------- */
/* A stray text selection (23 October 2026, author report). Most of what a learner presses is
   a button, and the browser does not clear a selection when a button is pressed. The places
   that would clear it are controls themselves (the room closes the panels, the docked record
   expands), and the record and monitor are rewritten many times a second, so a selection made
   by accident stayed for the rest of the case. Any press now clears an existing selection
   first. The press's own default still runs after this, so a new drag still selects text,
   Shift and a press still extends a selection, and text inside a field is left alone. Escape
   clears it as well. */
function clearStraySelection(e){
  const sel=window.getSelection&&window.getSelection();
  if(!sel||sel.isCollapsed||e.shiftKey) return;
  const t=e.target;
  if(t&&t.closest&&t.closest('input,textarea,[contenteditable="true"]')) return;
  sel.removeAllRanges();
}
document.addEventListener('mousedown',clearStraySelection,true);
document.addEventListener('keydown',e=>{
  if(e.key!=='Escape') return;
  const sel=window.getSelection&&window.getSelection();
  if(sel&&!sel.isCollapsed) sel.removeAllRanges();
},true);
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-tab],[data-act],[data-ask],[data-disp],[data-dx],[data-dxrm],[data-dxup],'
    +'#askbtn,#submitho,#earlyexit,#restart,#revealanswers,#soundbtn,#submitorder,#clearorder,#clearfilter,'
    +'[data-group],[data-mode],[data-case],#beginbtn,#backtopicker,#pickanother,#homebtn,'
    +'#rp-toggle,#lp-collapse,#railmenu,#searchbtn,#searchclose,[data-sgo],[data-schart],[data-subtab],#askmic,[data-subfold],[data-cfilter],[data-stop]');
  if(t&&t.id==='soundbtn'){ AUDIO.toggle(); renderSound(); return; }
  AUDIO.unlock();
  /* Panel controls run before the ENDED guard and before the null check: the
     record panel is a click target in its own right, and the toggle sits
     inside it, so the toggle has to be tested first or every expand would be
     followed immediately by the panel's own handler. */
  if(t&&t.id==='rp-toggle'){ RIGHT_WIDE?minimiseRecord():expandRecord(); return; }
  /* A chart filter changes what the record shows and does not expand it. A greyed-out one
     does nothing: the filter that is on has to be turned off first. */
  if(t&&t.dataset.cfilter!==undefined){
    if(!t.disabled){ CHART_FILTER=CHART_FILTER===t.dataset.cfilter?null:t.dataset.cfilter; renderFeed(); }
    return;
  }
  if(t&&t.id==='lp-collapse'){ setPanels(false,RIGHT_WIDE); renderTabs(); return; }
  /* Leaving by the rail button asks the same question the browser's back button asks, and
     takes the same route out, so there is one way to end a case early and one guard on it. */
  if(t&&t.id==='railmenu'){ askLeave('menu'); return; }
  if(t&&t.id==='searchbtn'){ SEARCH_OPEN?closeSearch():openSearch(); return; }
  if(t&&t.id==='searchclose'){ closeSearch(); return; }
  if(t&&t.dataset.sgo!==undefined){ searchPick(t.dataset.sgo); return; }
  if(t&&t.dataset.schart!==undefined){ CHART_FILTER=null; closeSearch(); expandRecord(); return; }
  /* Anything else inside the search panel stops here. It covers the record panel, which is
     a click target in its own right, and a click on the panel's own background must not
     expand the chart underneath it. After the panel's controls, never before them. */
  if(e.target.closest&&e.target.closest('#searchpanel')) return;
  /* A thumbnail is excepted: the click means "show me the picture", and the image
     handler below takes it. Expanding the record as well left the reader, on closing
     the picture, in a layout they had not asked for. */
  if(!RIGHT_WIDE && !ENDED && e.target.closest('#rightpanel') && !e.target.closest('.imgthumb')){
    expandRecord(); renderTabs(); return;
  }
  /* A click on the room behind the panels closes both of them: the workspace slides
     back behind the rail and the record returns to its dock, leaving the seven tab
     names and the docked record. It is the same gesture from every state, so a learner
     never has to know which panel is open to clear the screen. Until v0.16 it minimised
     the record and reopened the workspace on History, which meant clicking the room
     to get rid of one panel produced another. Anything that is itself a control (the
     rail, the header, an overlay, either panel) keeps its own behaviour. */
  if(STARTED && !ENDED && !e.target.closest(
       '#rightpanel,#tabbar,#leftpanel,header,#endview,#pauseview,#leaveview,#picker,#splash,#imgview,button,a,input')){
    if(LEFT_OPEN||RIGHT_WIDE){ setPanels(false,false); renderTabs(); }
    return;
  }
  if(!t) return;
  if(t.dataset.tab){
    TAB=t.dataset.tab;
    /* Choosing a section is a request to work in it, so the workspace opens and
       an expanded chart steps back to its dock. */
    setPanels(true,false);
    render(); return;
  }
  if(ENDED&&!t.id) return;
  /* The red cross on a running drip's button: the stop order, given at once rather than put
     in the basket. It sits inside the drip's button and is matched first, so the click never
     reaches the drip itself. */
  if(t.dataset.stop){ log({actionId:t.dataset.stop}); render(); return; }
  if(t.dataset.act){
    const id=t.dataset.act, tabof=t.dataset.tabof;
    if(id.indexOf('interview_topic_')===0){
      const tid=id.slice(16);
      const tp=CASE.interview.topics.find(x=>x.topic===tid);
      ask(tp?tp.canonical:tid.replace(/_/g,' ')); return;
    }
    /* A composite exam is an examination, not an order, so it is performed at once
       wherever its button sits, exactly as the Exam tab's buttons are. */
    if(ACT[id]&&ACT[id].performs){ log({actionId:id}); render(); return; }
    /* v0.26b. The top Stabilization folder orders on the click, with no Submit Order. */
    if(t.dataset.now){ log({actionId:id}); render(); return; }
    /* On an orderable tab a click selects; nothing is sent until Submit Order. */
    if(tabof&&PROTO.orderableTabs.includes(tabof)){
      const bag=basketOf(tabof);
      if(pickedAnywhere(id)){ PROTO.orderableTabs.forEach(x=>basketOf(x).delete(id)); delete PICKSEQ[id]; }
      else { bag.add(id); PICKSEQ[id]=++PICKN; }
      renderTab(); return;
    }
    log({actionId:id}); render(); return;
  }
  if(t.dataset.case){ chooseCase(Number(t.dataset.case)); return; }
  if(t.id==='backtopicker'){ backToPicker(); return; }
  if(t.dataset.mode){ MODE=t.dataset.mode; renderSplash(); return; }
  if(t.id==='beginbtn'){ begin(); return; }
  if(t.dataset.subfold){
    const k=t.dataset.subfold; SUBOPEN.has(k)?SUBOPEN.delete(k):SUBOPEN.add(k);
    renderTab(); return;
  }
  if(t.dataset.subtab){
    SUBTAB[t.dataset.tabof+'|'+t.dataset.subgroup]=t.dataset.subtab;
    renderTab(); return;
  }
  if(t.dataset.group){
    const set=expandedOf(t.dataset.tabof);
    set.has(t.dataset.group)?set.delete(t.dataset.group):set.add(t.dataset.group);
    renderTab(); return;
  }
  if(t.id==='clearfilter'){
    FILTERS[t.dataset.tabof]='';
    renderTab();
    const box=el('filterbox'); if(box) box.focus();
    return;
  }
  if(t.id==='clearorder'){ clearAllBaskets(); renderTab(); return; }
  if(t.id==='submitorder'){
    const tabof=t.dataset.tabof;
    /* Submit everything selected on every ordering tab, in the order it was picked. Each
       is a separate log entry at the same instant, so the fold applies them in sequence and
       prerequisites, transitions and harmful tags all evaluate exactly as they would one at
       a time. */
    const picks=allPicked();
    for(const p of picks) log({actionId:p.id});
    const tabsUsed=[...new Set(picks.map(p=>p.t))];
    clearAllBaskets();
    tabsUsed.forEach(x=>{ if(x!==tabof) resetTabView(x); });
    /* A submitted order is the end of one search, so the tab goes back to where that
       search started rather than staying where it ended. The filter text and the opened
       group are both scaffolding for finding the thing that has now been ordered, and
       leaving them in place means the next order begins from three-quarters of the way
       down a filtered list showing the drug the resident has already given.

       Deliberately not the same as `restart`'s reset: the basket is cleared here because
       it was just submitted, and the other tabs' baskets and open groups are untouched.
       Their filter text is cleared too, see below. */
    resetTabView(tabof);
    /* v0.9, author instruction: a submitted order clears the search box on every tab,
       not only the one it was submitted from. The earlier design kept a filter typed
       on Investigations alive across an order sent from Interventions; in use that
       read as the box refusing to clear. */
    Object.keys(FILTERS).forEach(k=>{ FILTERS[k]=''; });
    render(); scrollTabTop(); return;
  }
  if(t.dataset.ask){ ask(t.dataset.ask); return; }
  if(t.id==='askmic'){ ASKMIC.toggle(); return; }
  if(t.id==='askbtn'){ const b=el('askbox'); if(b&&b.value.trim()) ask(b.value.trim()); return; }
  if(t.dataset.disp){ PENDING_HANDOFF.disposition=t.dataset.disp; render(); return; }
  if(t.dataset.dx){
    if(!PENDING_HANDOFF.diagnoses.includes(t.dataset.dx)) PENDING_HANDOFF.diagnoses.push(t.dataset.dx);
    DXTEXT=''; render(); return;
  }
  if(t.dataset.dxrm){
    PENDING_HANDOFF.diagnoses=PENDING_HANDOFF.diagnoses.filter(d=>d!==t.dataset.dxrm); render(); return;
  }
  if(t.dataset.dxup){
    PENDING_HANDOFF.diagnoses=[t.dataset.dxup].concat(PENDING_HANDOFF.diagnoses.filter(d=>d!==t.dataset.dxup));
    render(); return;
  }
  if(t.id==='submitho'){
    /* v0.21. A disposition the case intercepts is logged as the action the case names and
       the run carries on (engine handoffIntercept). The choice is cleared so the same
       button cannot be pressed twice by reflex, and the diagnoses are kept. */
    const alt=handoffIntercept(ST,PENDING_HANDOFF.disposition);
    if(alt){
      log({actionId:alt});
      PENDING_HANDOFF.disposition=null;
      TAB='stabilization';
      render(); return;
    }
    const list=PENDING_HANDOFF.diagnoses.slice();
    log({actionId:'handoff_submit',payload:{disposition:PENDING_HANDOFF.disposition,
         diagnosis:list[0]||null,diagnoses:list}});
    finish(); return;
  }
  if(t.id==='earlyexit'){ log({actionId:'early_exit',kind:'early_exit'}); finish(); return; }
  /* Replay starts the case again at once. Revealing the answers asks first, offering one
     more try (author instruction, 14 October 2026; until then the question guarded Replay). */
  if(t.id==='restart'){ restart(); return; }
  if(t.id==='revealanswers'){ askReplay(); return; }
  if(t.id==='pickanother'){ toPickerFromDebrief(); return; }
  if(t.id==='homebtn'){ toPickerFromDebrief(); return; }
});
document.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&e.target.id==='askbox'&&e.target.value.trim()) ask(e.target.value.trim());
});
document.addEventListener('input',e=>{
  if(e.target.id==='askbox'){ ASKTEXT=e.target.value; return; }
  if(e.target.id==='filterbox'){
    FILTERS[e.target.dataset.tabof||TAB]=e.target.value.toLowerCase();
    renderTab(); return;
  }
  if(e.target.id==='dxbox'){
    DXTEXT=e.target.value;
    const q=e.target.value.toLowerCase().trim();
    const hits=q.length<2?[]:PROTO.diagnoses.filter(d=>
      !PENDING_HANDOFF.diagnoses.includes(d.id)&&
      (d.label.toLowerCase().includes(q)||d.syn.some(s=>s.toLowerCase().includes(q)))).slice(0,10);
    el('dxhits').innerHTML=hits.length?`<div class="hits">${hits.map(d=>
      `<button class="hit" data-dx="${esc(d.id)}">${esc(d.label)}${d.syn.length?`<span class="syn">${esc(d.syn.join(', '))}</span>`:''}</button>`).join('')}</div>`:'';
  }
});
/* Asking is asynchronous now, because embedding the question takes a few tens
   of milliseconds once the model is loaded. The box is cleared first so the
   interaction still feels immediate, and ASKING blocks a second submission
   while the first is in flight, which is otherwise easy to trigger by hitting
   Enter twice. */
let ASKING=false;
async function ask(q){
  if(ASKING||ENDED) return;
  ASKING=true;
  const run=RUNID;
  ASKTEXT=''; const b=el('askbox'); if(b) b.value='';
  let ms;
  try{ ms=await matchQuestion(q); }
  catch(e){ const l=matchTopic(q); ms=[{topic:l.topic,score:l.score,matcher:'lexical',q}]; }
  finally{ ASKING=false; }
  if(run!==RUNID||ENDED) return;      // the case ended or restarted while the matcher ran
  /* One log entry per topic asked about. They share an instant, exactly as a
     submitted order basket does, so the fold applies them in sequence and each
     answer is produced by the authored rules for its own topic. */
  for(const m of ms)
    log({actionId:null,kind:'interview',topic:m.topic,q:m.q,score:m.score,matcher:m.matcher,
         fact:m.fact||null,more:!!m.more,clarify:m.clarify||null,uncertain:!!m.uncertain});
  render();
}

/* ---------- loop ---------- */
let lastFold=0;
function tick(){
  if(!ENDED&&!PAUSED){
    const t=Date.now();
    if(t-lastFold>100){ lastFold=t; refold(); } else { ST.now=now(); }
    if(ST.halted){ finish(); return; }
    /* A terminal phase reached by the clock ends the run, but not at the instant it is
       reached. The nurse's line and the monitor dropping to the terminal numbers are the
       moment the case is teaching; cutting to a debrief on the same frame throws that
       away. The wait is fixed and short, and nothing the resident does during it can
       change the ending, since the phase has no exits. */
    if(ST.failed && ST.now >= ST.failed.t + GRACE_S){ finish(); return; }
    if(reflectDue()) openReflect();
  }
  renderMonitor(); renderNurse(); renderRail(); renderPatient(); renderSearchBtn();
  /* One loop at a time, and none once the case is over. Until v0.18a every Begin started a
     further loop and none ever stopped, so each replay added a full render per frame. */
  RAF=ENDED?0:requestAnimationFrame(tick);
}
let RAF=0;
function startLoop(){ if(RAF) cancelAnimationFrame(RAF); RAF=requestAnimationFrame(tick); }
function render(){
  refold();
  if(ST.halted&&!ENDED){ finish(); return; }
  renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor(); renderPatient(); renderSearchBtn();
  VOICE.paint();
}
/* Rebuild the tab only when something the tab shows has actually changed. A nurse
   line or a prompt does not change the action grid, and rebuilding it can swallow a
   click the user has already started. */
const tabFingerprint=()=>ST?ST.resulted.size+':'+ST.pending.length+':'+ST.blocked.length
                            +':'+ST.readouts.length+':'+ST.phase:'';
setInterval(()=>{
  if(ENDED||!CASE) return;             // the deployed build can sit on the case list with nothing bound
  const before=tabFingerprint();
  refold();
  if(tabFingerprint()!==before){ renderTabs(); renderTab(); }
  autoOpenImages();
},300);

/* ---------- ending ---------- */
const GRACE_S = (SHARED.ending&&SHARED.ending.terminalGraceSeconds) || 5;

/* The debrief now opens twice. The first screen answers the only question a resident
   asks the instant a case ends: did I do the things that had to be done. It carries the
   verdict, the critical actions that were completed, and two ways out. Everything else,
   the missed actions, the teaching notes, the domain table, the handoff verdict, is the
   answer key, and a resident who wants to replay the case before reading it should not
   have to scroll past it to reach the replay button. `Reveal Case Answers` opens the
   full debrief in place.

   REVEALED is not persisted across a replay: restart() clears it through finish() being
   called again, and a new run should start from the gate. */
let REVEALED=false;

/* Which of the three endings this was, in the order that matters clinically. A run that
   walked into a terminal phase is a failure whatever else was completed, because the
   patient arrested; a run that completed every critical action and did not arrest is the
   only one that gets the affirmative. */
function endingKind(){
  /* A harmful action is grouped with the clock's ending rather than scored against the
     critical actions. A resident who completed every critical action and then gave
     something that stopped the case has not had a clean run, and a first screen reading
     "All Critical Actions Achieved!" over a halt reason would be the interface
     congratulating him on the way to the morgue. Both endings put their own reason
     directly under the title. */
  if(ST.failed||ST.halted) return 'failed';
  return [...ST.expected].every(id=>ST.satisfied.has(id)) ? 'all' : 'missed';
}
const GATE_TITLE={failed:'Case Failed',
                  all:'All Critical Actions Achieved!',
                  missed:'Critical Actions Missed'};

/* The debrief's first screen: a dial from 0 to 100 percent, filled by the share of the
   case's critical actions completed, with the count in the centre ("6/8"). Nothing is
   drawn for a case that expects no critical action. Author instruction, 11 October 2026. */
function dialSVG(f,big,small,label,aria,cls){
  f=Math.max(0,Math.min(1,f)); const r=52, c=2*Math.PI*r;
  return `<figure class="dialwrap"><div class="critdial${cls?' '+cls:''}" role="img" aria-label="${esc(aria)}">
    <svg viewBox="0 0 128 128" aria-hidden="true">
      <circle class="track" cx="64" cy="64" r="${r}"/>
      <circle class="fill" cx="64" cy="64" r="${r}" stroke-dasharray="${(f*c).toFixed(2)} ${c.toFixed(2)}"
        transform="rotate(-90 64 64)"/>
    </svg>
    <div class="critdial-n">${big}${small?`<span>${small}</span>`:''}</div></div>
    <figcaption>${esc(label)}</figcaption></figure>`;
}
function critDial(n,total){
  if(!total) return '';
  const f=n/total;
  return dialSVG(f, n+'/'+total, Math.round(f*100)+'%', 'Critical actions',
    n+' of '+total+' critical actions completed, '+Math.round(f*100)+' percent');
}
/* The second dial: overall score (engine overallScore). A run that was halted or ended in
   a terminal phase is not scored, so its dial is empty and says so. */
function overallDial(){
  const o=overallScore(ST);
  if(!o.scored) return dialSVG(0,'n/a','not scored','Overall score','Overall score: not scored, the case ended early','muted');
  return dialSVG(o.pct/100, o.pct+'%', '', 'Overall score', 'Overall score '+o.pct+' percent', 'overall');
}
function gateHTML(){
  const kind=endingKind();
  const done=[...ST.expected].filter(id=>ST.satisfied.has(id));
  const dispExp=id=>((ACT[id]||{}).expectation_label)||dispName(id);
  /* Names only. No pill, no expander, no teaching note: a note attached to a completed
     action is still an answer, and this screen is deliberately not the answer key. */
  return `<div class="dbf">
    <div class="dbsec gate">
      <div class="gatecols">
      <div class="gateleft">
      <h2 class="gatetitle ${kind==='all'?'g-ok':'g-bad'}">${esc(GATE_TITLE[kind])}</h2>
      ${ST.failed&&ST.failed.reason?`<p class="sub">${esc(ST.failed.reason)}</p>`:''}
      ${ST.halted&&ST.halted.reason?`<p class="sub">${esc(ST.halted.reason)}</p>`:''}
      <div class="gatedialrow">
        ${critDial(done.length,ST.expected.size)}
        ${overallDial()}
        <button class="btn bigreplay" id="restart">Replay this case</button>
      </div>
      </div>
      <div class="gateright">
      <h3 class="gatesub">Critical actions you completed</h3>
      ${(()=>{
        /* Author instruction, 15 October 2026: a checked box per critical action done, then
           an empty box per one missed. The missed ones are counted, not named: their text is
           the same blurred nonsense every time, because this screen is not the answer key.
           Screen readers hear "Critical action not completed" instead of the nonsense. */
        const missed=Math.max(0,ST.expected.size-done.length);
        if(!done.length&&!missed) return `<p class="sub">This case has no critical actions.</p>`;
        const on=`<span class="gbox on" aria-hidden="true"><svg viewBox="0 0 26 26"><rect x="2" y="6" width="18" height="18" rx="4.5"/><path d="M6.5 14.5l4.4 4.6L23.5 3.5"/></svg></span>`;
        const off=`<span class="gbox" aria-hidden="true"><svg viewBox="0 0 26 26"><rect x="2" y="6" width="18" height="18" rx="4.5"/></svg></span>`;
        return `<div class="gatelist">${done.map(id=>
            `<div class="gitem">${on}<span>${esc(dispExp(id))}</span></div>`).join('')}${
          Array.from({length:missed},()=>
            `<div class="gitem gmiss">${off}<span class="gblur" aria-hidden="true">Vorelt quandish ambrel tosk nemura</span><span class="gsr">Critical action not completed</span></div>`).join('')}</div>`;
      })()}
      </div>
      </div>
      <div class="gatebtns">
        <button class="btn ghost" id="revealanswers">Reveal Case Answers</button>
        ${CASES.length>1?'<button class="btn ghost" id="pickanother">Choose a different case</button>':''}
      </div>
    </div>
  </div>`;
}

/* A debrief section that starts closed and opens on its down arrow. Native <details>, so
   it works from the keyboard with no script. `sub` draws it at subsection size. */
function dbFold(title,inner,sub){
  return `<details class="dbfold${sub?' sub':''}"><summary><span class="dbfold-t">${esc(title)}</span>
    <svg class="dbfold-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>
    <div class="dbfold-body">${inner}</div></details>`;
}
/* Case discussion, the left column of the debrief (author instruction, 14 October 2026).
   A textbook-style chapter on the case: learning goals, the physiology, figures. It is
   authored per case in cases/<P>/<P>-discussion.html and carried on the pack, so a locked
   pack carries its own. Reviewer markers in square brackets are stripped as everywhere else.
   A case without one shows the heading and a line saying so. */
function discussionHTML(){
  const body=learnerText(PACK.discussion||'');
  return `<aside class="dbsec cdisc" aria-labelledby="cdisch"><h2 id="cdisch">Case discussion</h2>
    ${body?`<div class="cdbody">${body}</div>`:'<p class="sub cdnone">Not written yet for this case.</p>'}</aside>`;
}
function revealAnswers(){
  REVEALED=true; AN.track('debrief_revealed',{case:PACK.prefix});
  const v=el('endview');
  /* Two columns: the case discussion on the left, the run's own debrief on the right. */
  v.innerHTML='<div class="endwrap two"><div class="dbcols">'+discussionHTML()
    +'<div class="dbmain">'+(ST.halted?haltCard():'')+(ST.failed?failCard():'')+debriefHTML()+'</div></div></div>';
  v.scrollTop=0;
}

/* The clock's equivalent of haltCard. A harmful action names itself; a terminal phase
   reached by the clock has no action to name, so the phase's own timeout_reason is the
   whole explanation and it is authored for exactly this. A terminal phase reached by an
   instantaneous transition does have an action to name, and the action's own debrief note
   names it; the phase's timeout_reason then has to be true of both routes, which is a
   constraint on the case rather than on this card. */
/* v0.18a. A terminal phase reached by an instantaneous transition was caused by an action
   taken at that moment. It is named on the card and in its own debrief section, and it is
   left out of the list of actions that "did not stop the case", which it did. The action
   is the one at that second whose id or flag the transition's guard names, or failing that
   the last one taken at that second. */
function failCause(){
  if(!ST||!ST.failed||ST.failed.byClock) return null;
  const at=ST.timeline.filter(x=>x.type==='state-changing'&&x.t===ST.failed.t);
  if(!at.length) return null;
  const seq=ST.phaseSeq, from=seq.length>1?seq[seq.length-2].id:null;
  const tr=from&&PHASE[from]?(PHASE[from].transitions||[])
    .find(t=>t.to===ST.failed.phase&&t.after_seconds===undefined):null;
  const hay=' '+String((tr&&tr.when)||'').replace(/[()]/g,' ')+' ';
  const named=at.filter(x=>hay.includes(' '+x.id+' ')
    ||((ACT[x.id]||{}).flags_set||[]).some(f=>hay.includes(' '+f+' ')));
  return (named.length?named[named.length-1]:at[at.length-1]).id;
}
function failCard(){
  const cause=failCause();
  return `<div class="halt"><h2>The case ended here</h2>
    <p><b>${esc(PHASE[ST.failed.phase].label||ST.failed.phase)}</b> at ${mmss(ST.failed.t)}${cause?`, straight after <b>${esc(dispName(cause))}</b>`:''}.</p>
    ${ST.failed.reason?`<p>${esc(ST.failed.reason)}</p>`:''}
    <p style="color:var(--ink2);font-size:13.5px">Nothing you did before this is lost.
    It is all below.</p></div>`;
}

function finish(){
  /* The room goes quiet with the case. A debrief is reading rather than resuscitating,
     and ambience still humming under it is the interface not noticing the case is over.
     setScene('idle') stops the heartbeat and the room together. */
  refold(); ENDED=true; RUNID++; AUDIO.setScene('idle'); MONITOR.setScene('idle');
  VOICE.reset(); ASKMIC.abort();
  /* Neither overlay belongs over a debrief. The case is over, so there is nothing to
     resume and nothing left to lose by leaving. */
  el('pauseview').classList.add('hidden'); closeLeave(); PAUSED=false;
  el('playview').classList.add('hidden');
  /* Saved progress (28 October 2026): the run becomes a score summary in the learner's
     history and its saved log is emptied. Labels, percentages and counts only, the same
     rows the debrief's Summary shows. Nothing here names an action. */
  try{
    const ov=overallScore(ST);
    PROGRESS.finish({mode:MODE, sim_seconds:ST.now||0, outcome:endingKind(), ended_by:endedBy(),
      score_pct:ov.scored?ov.pct:null,
      summary:{v:1, scored:!!ov.scored, critical:{done:ov.critical.done,total:ov.critical.total},
               rows:summaryScores(ST).map(r=>({id:r.id,label:r.label,pct:r.pct,detail:r.detail||''}))}});
  }catch(err){}
  const v=el('endview'); v.classList.remove('hidden');
  REVEALED=false;
  v.innerHTML='<div class="endwrap">'+gateHTML()+'</div>';
  /* Counts and kinds only. No orders, answers, diagnoses or notes leave the page. */
  try{
    const c=AN.takeCounts(), kinds={};
    LOG.forEach(e=>{ const k=e.kind||(e.actionId?'action':'other'); kinds[k]=(kinds[k]||0)+1; });
    AN.track('case_finished',{case:PACK.prefix, mode:MODE, outcome:endingKind(),
      ended_by: endedBy(),
      sim_seconds: Math.round(ST.now||0),
      critical_done:[...ST.expected].filter(id=>ST.satisfied.has(id)).length, critical_total:ST.expected.size,
      actions:kinds.action||0, interview_questions:kinds.interview||0, exams:kinds.exam||0,
      voice_orders:c.voice_orders||0, search_opens:c.search_opens||0});
  }catch(err){}
  v.scrollTop=0;
}
function endedBy(){
  return ST.halted?'harmful_action':(ST.failed?(ST.failed.byClock?'clock':'action'):(ST.earlyExit?'early_exit':'completed'));
}
function restart(){
  /* A run left unfinished stays saved to be resumed. This only stops saving into it. */
  PROGRESS.detach();
  LOG=[];SEQ=0;ENDED=false;STARTED=false;TAB='stabilization';LASTNURSE=-1;LASTPHASE=null;
  RUNID++; ASKTEXT=''; DXTEXT='';
  VOICE.reset(); ASKMIC.abort();
  closeImage(); IMG_SEEN=new Set(); IMG_QUEUE=[];
  resetRamp();
  Object.keys(FILTERS).forEach(k=>delete FILTERS[k]);
  REFLECT_DONE=false; REFLECT_NOTE=''; REFLECT_NOTE2=''; REFLECT_OPEN=false;
  el('reflectview').classList.add('hidden');
  SEARCH_Q=''; SEARCH_DONE=''; closeSearch();
  Object.keys(BASKET).forEach(k=>delete BASKET[k]); PICKSEQ={}; PICKN=0;
  Object.keys(EXPANDED).forEach(k=>delete EXPANDED[k]);
  Object.keys(SUBTAB).forEach(k=>delete SUBTAB[k]); SUBOPEN.clear();
  PENDING_HANDOFF={disposition:null,diagnoses:[]};
  PAUSED=false; PAUSED_MS=0; PAUSED_AT=0;
  el('pauseview').classList.add('hidden'); closeLeave();
  AUDIO.setScene('idle'); MONITOR.setScene('idle'); MONITOR.reset();
  el('endview').classList.add('hidden'); el('playview').classList.remove('hidden');
  el('splash').classList.remove('hidden');
  setPanels(true,false);
  renderSplash(); refold(); renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor();
  PROGRESS.onSplash(PACK.prefix);
}
function toPickerFromDebrief(){ restart(); backToPicker(); }
function haltCard(){
  return `<div class="halt"><h2>The case stopped here</h2>
    <p><b>${esc(dispName(ST.halted.id))}</b> at ${mmss(ST.halted.t)}.</p>
    <p>${esc(ST.halted.reason)}</p>
    <p style="color:var(--ink2);font-size:13.5px">Everything you did before this is in the debrief below.
    Read it, then replay.</p></div>`;
}

/* ---------- debrief (section 11) ---------- */
/* v0.18a. Verification markers such as "[UNVERIFIED, confirm before release]" are notes to
   the reviewing physician. They stay in the case file and the review packet and are removed
   from anything the learner reads, wherever in the text they sit. */
function learnerText(s){
  return String(s||'').replace(/\s*\[(?:UNVERIFIED|PubMed|VERIFY|MODEL OUTPUT)[^\]]*\]/g,'').trim();
}
/* v0.18a. The note written at the reflection pause, printed beside the case's diagnosis so
   the learner can compare what they thought at the time with what it was. Nothing is
   printed when the box was left empty. */
function reflectHTML(){
  /* Two boxes since the pause card was split: the differential, then what to check or
     give. Each prints only when it was filled in. */
  const one=(title,s)=>{
    const n=String(s||'').trim();
    if(!n) return '';
    return `<div class="item"><div class="hd"><span class="nm">${esc(title)} at ${mmss(REFLECT_AT)}</span>
      <span class="pill p-neu">your note</span></div>
      <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0;white-space:pre-wrap">${esc(n)}</div></div>`;
  };
  return one('Your differential',REFLECT_NOTE)+one('What you planned to check or give',REFLECT_NOTE2);
}
function dxAnswerHTML(){
  return `<div class="item"><div class="hd"><span class="nm">${esc('The case\'s diagnosis: '+dxLabel(PROTO.correctDxId))}</span>
      <span class="pill p-neu">answer</span></div>
      ${PROTO.correctDxExplanation?`<div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(PROTO.correctDxExplanation)}</div>`:''}</div>`;
}
function debriefHTML(){
  const done=[],omit=[];
  /* `satisfied`, so a critical action performed through a coverage group is not
     reported as missed. The action grid still reads `taken`, so only the button that
     was actually pressed is drawn as used. */
  ST.expected.forEach(id=>{ (ST.satisfied.has(id)?done:omit).push(id); });
  /* Recommended actions, done and not. The ones nobody needs telling about are left
     out: a line and a monitor are the first two acts of any resuscitation, and a
     debrief that lists them beside a nitrate infusion has made them look like a
     finding. Taken through a coverage group counts, as it does for critical actions. */
  const OBVIOUS=id=>{ const a=ACT[id]||{}; return a.reveals_vitals||a.catalog_id==='insert_iv'||a.catalog_id==='attach_monitor'; };
  const recDone=[...ST.recommendedTaken].filter(id=>!OBVIOUS(id));
  const recMissed=[...ST.recommendedExpected].filter(id=>!ST.recommendedTaken.has(id)&&!ST.satisfied.has(id)&&!OBVIOUS(id));
  const cause=failCause();
  const dis=[...ST.discouragedTaken].filter(id=>id!==cause);
  const traps=ST.timeline.filter(x=>x.tag==='neutral'&&PROTO.traps.includes(x.id));
  const stillPending=ST.pending.map(p=>p.id);
  const noteOf=id=>learnerText((ACT[id]||{}).debrief_note);
  /* References carry a verification marker in the case file, for example
     "[PubMed record checked]" or "[UNVERIFIED, confirm before release]". That is a note
     to the reviewing physician, not to the learner, and it stays in the case file and the
     review packet rather than being printed in the debrief. */
  const refsOf=id=>((ACT[id]||{}).references||[])
    .map(r=>learnerText(r.replace(/\s*\[[^\]]*\]\s*$/,''))).filter(Boolean);
  /* The teaching note is the most valuable thing in the debrief and also the longest.
     Printed in full for every action it becomes a wall of text that gets skimmed, so each
     one sits behind its own expander and the list of what was done and missed stays
     readable at a glance. Native <details> rather than a scripted toggle, so the open
     state survives re-render and needs no click handling. */
  const dispExp=id=>((ACT[id]||{}).expectation_label)||dispName(id);
  const item=(id,pill,pillcls,label)=>{
    const note=noteOf(id), refs=refsOf(id);
    const head=`<span class="nm">${esc(label||dispName(id))}</span><span class="pill ${pillcls}">${pill}</span>
      ${ST.prompted.has(id)?'<span class="pill p-warn">prompted</span>':''}`;
    if(!note&&!refs.length) return `<div class="item"><div class="hd">${head}</div></div>`;
    /* Sources sit behind a small button at the end of the note and drop down under it
       (author instruction, 28 October 2026), so the note reads as prose first. */
    const srcBtn=refs.length?`<button type="button" class="srcbtn" aria-expanded="false">Sources</button>`:'';
    return `<div class="item"><details class="teach">
      <summary class="hd">${head}<span class="expand">Why</span></summary>
      ${note?`<div class="note" style="background:none;border:0;padding:0;margin:8px 0 0">${esc(note)} ${srcBtn}</div>`
            :(srcBtn?`<div class="note" style="background:none;border:0;padding:0;margin:8px 0 0">${srcBtn}</div>`:'')}
      ${refs.length?`<div class="refs" hidden>${refs.map(esc).join('<br>')}</div>`:''}
    </details></div>`;
  };

  /* v0.9: seven categories, scored in the engine (summaryScores) from what the case
     authored. The old clinical-domain table is gone on the author's instruction. */
  const scoreRows=summaryScores(ST).map(r=>{
    const cls=r.pct===null?'':(r.pct<50?'low':(r.pct<80?'mid':''));
    return `<tr><td>${esc(r.label)}</td>
      <td class="n">${r.pct===null?'<span class="pill p-neu">n/a</span>'
        :`${r.pct}%<span class="bar ${cls}"><i style="width:${r.pct}%"></i></span>`}</td>
      <td class="n">${r.max?r.points+' / '+r.max:''}</td>
      <td class="d">${esc(r.detail)}${r.halted?' <span class="pill p-harm">halted here</span>':''}</td></tr>`;
  }).join('');

  let ho='';
  if(ST.handoff){
    const h=CASE.handoff, dId=ST.handoff.disposition;
    const dOK=dId===h.correct_disposition.id;
    const dAlt=h.alternative_dispositions.find(a=>a.id===dId);
    const dExp=dOK?h.correct_disposition.explanation:(dAlt?dAlt.explanation:'');
    const dV=dOK?['correct','p-ok']:(dAlt&&dAlt.verdict==='acceptable_with_qualification'?['defensible','p-warn']:['incorrect','p-harm']);
    /* v0.9: every diagnosis the resident listed gets its own verdict, the primary on
       its own terms and the rest as things also true of the patient or not. The
       case's own diagnosis is printed at the end whenever it was not named, so the
       answer is on the page. */
    const dx=scoreDiagnoses(ST);
    const PILL={primary_correct:['correct','p-ok'],primary_defensible:['defensible','p-warn'],
                primary_incorrect:['incorrect','p-harm'],main_not_primary:['the main diagnosis, not listed first','p-warn'],
                appropriate:['appropriate','p-ok'],also_true:['also true','p-ok'],defensible:['defensible','p-warn'],unsupported:['not supported','p-harm']};
    const dxItem=(label,pill,why)=>`<div class="item"><div class="hd"><span class="nm">${esc(label)}</span>
        <span class="pill ${pill[1]}">${esc(pill[0])}</span></div>
        ${why?`<div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(why)}</div>`:''}</div>`;
    const named=dx.rows.some(r=>r.verdict==='primary_correct'||r.verdict==='main_not_primary');
    ho=`<div class="dbsec"><h2>Handoff</h2>
      ${reflectHTML()}
      <div class="item"><div class="hd"><span class="nm">Disposition: ${esc(dispLabel(dId))}</span>
        <span class="pill ${dV[1]}">${dV[0]}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(dExp)}</div></div>
      <h3>Diagnoses you handed over</h3>
      ${dx.rows.map((r,i)=>dxItem((i?'':'Primary: ')+dxLabel(r.id),PILL[r.verdict]||['','p-neu'],r.why)).join('')}
      ${dx.missed.length?dbFold('Also true of this patient, and not named',
        dx.missed.map(m=>dxItem(dxLabel(m.id),['not named','p-warn'],m.why)).join(''),true):''}
      ${dx.optional.length?dbFold('Also true of this patient, not scored',
        dx.optional.map(m=>dxItem(dxLabel(m.id),['not scored','p-neu'],m.why)).join(''),true):''}
      ${named?'':dxItem('The case\'s diagnosis: '+dxLabel(PROTO.correctDxId),['answer','p-neu'],PROTO.correctDxExplanation)}
      </div>`;
  } else if(ST.earlyExit){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>You ended the case early, so this debrief is marked incomplete.</p>${reflectHTML()}${reflectHTML()?dxAnswerHTML():''}</div>`;
  } else if(ST.halted){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>The case halted before a handoff.</p>${reflectHTML()}${reflectHTML()?dxAnswerHTML():''}</div>`;
  } else if(ST.failed){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>The case ended before a handoff.</p>${reflectHTML()}${reflectHTML()?dxAnswerHTML():''}</div>`;
  }

  const defaults=[...ST.defaultsServed];

  /* v0.9: the interpretations. While the case ran, a lab panel showed its numbers and
     nothing else; the authored reading under each one is printed here, once, with the
     numbers it belongs to. Reports (imaging, ECG) are their own text and are not
     repeated. */
  const read=[];
  Object.keys(ST.orders).forEach(id=>ST.orders[id].forEach(o=>{
    const v=o.value;
    if(v&&typeof v==='object'&&v.kind!=='report'&&v.comment) read.push({id,o});
  }));
  read.sort((a,b)=>a.o.dueT-b.o.dueT);

  /* v0.18a. What happened, in order: every action and every change in the patient at its
     time on the case clock. The description and analysis phases of a debrief start from a
     shared account of events, and until this existed the running chart disappeared with
     the play view and the notes on timed transitions were never shown. */
  const TAGPILL={critical:['critical','p-crit'],recommended:['recommended','p-ok'],
                 discouraged:['discouraged','p-warn'],harmful:['harmful','p-harm'],neutral:['neutral','p-neu']};
  const when=t=>`<span class="tlt">${mmss(t)}</span>`;
  const rows=[];
  ST.timeline.forEach((x,k)=>{
    if(x.type==='state-changing'){
      const tp=TAGPILL[x.tag]||['','p-neu'];
      rows.push({t:x.t,k,html:`<div class="item"><div class="hd">${when(x.t)}<span class="nm">${esc(x.label)}</span>
        <span class="pill ${tp[1]}">${tp[0]}</span>${ST.prompted.has(x.id)?'<span class="pill p-warn">prompted</span>':''}</div></div>`});
    } else if(x.type==='blocked'){
      rows.push({t:x.t,k,html:`<div class="item"><div class="hd">${when(x.t)}<span class="nm">${esc(x.label)}</span>
        <span class="pill p-warn">did not happen</span></div></div>`});
    } else if(x.type==='end'){
      rows.push({t:x.t,k,html:`<div class="item"><div class="hd">${when(x.t)}<span class="nm">${esc(x.label)}</span></div></div>`});
    } else {
      const asked=String(x.id).startsWith('interview:');
      rows.push({t:x.t,k,html:`<div class="item"><div class="hd">${when(x.t)}<span class="nm" style="font-weight:400">${esc(asked?'Asked: '+x.label:x.label)}</span></div></div>`});
    }
  });
  ST.phaseSeq.forEach((ph,i)=>{
    if(!PHASE[ph.id]) return;
    const tf=i?ST.timeFires.find(f=>f.to===ph.id&&f.t===ph.t):null;
    const note=tf?learnerText(tf.note):'';
    const label=(i?'The patient: ':'On arrival: ')+(PHASE[ph.id].label||ph.id);
    const head=`${when(ph.t)}<span class="nm">${esc(label)}</span>`;
    /* A change of state lands after the action that caused it in the same second. */
    rows.push({t:ph.t,k:i?1e6+i:-1,html:note
      ?`<div class="item"><details class="teach"><summary class="hd">${head}<span class="expand">Why</span></summary>
         <div class="note" style="background:none;border:0;padding:0;margin:8px 0 0">${esc(note)}</div></details></div>`
      :`<div class="item"><div class="hd">${head}</div></div>`});
  });
  rows.sort((a,b)=>a.t-b.t||a.k-b.k);
  /* Removed from the debrief on author instruction (11 October 2026). Still built, so the
     rows above stay available if it is brought back. */
  const timeline=`<div class="dbsec"><h2>What happened, in order</h2>
    <p class="sub">Every action you took and every change in the patient, at its time on the case clock.
    Where the patient changed on a clock, open the line to read why.</p>
    ${rows.map(r=>r.html).join('')}</div>`;

  /* v0.18a. Three take-home points directly under the critical actions, where they are
     read, and the rest at the end. */
  const points=(CASE.debrief_configuration.cross_cutting_teaching_points||[])
    .map(p=>learnerText(typeof p==='string'?p:p.point||'')).filter(Boolean);
  const pointItem=p=>`<div class="item"><div class="note" style="background:none;border:0;padding:0;margin:0">${esc(p)}</div></div>`;

  /* v0.18a. A run that ended in an arrest or a harmful action is not scored. A percentage
     for the parts of that run points review at the wrong thing; the table stays available
     behind an expander for anyone reviewing the run. */
  const endLabel=ST.failed?(PHASE[ST.failed.phase].label||ST.failed.phase):'';
  const notScored=ST.halted?'Not scored: a harmful action ended the case.'
    :(ST.failed?'Not scored: the case ended in '+endLabel.charAt(0).toLowerCase()+endLabel.slice(1)+'.':'');
  /* Author instruction, 11 October 2026: the summary is one closed drop-down per
     category, and inside each, one closed drop-down per thing not done. History lists the
     key questions not asked, with what the patient would have said. Physical and the four
     ordering tabs list the actions not taken, with the case's teaching note. Handoff lists
     what the handover got wrong or left out. */
  const missedOf=r=>{
    const miss=r.missed||[];
    if(r.id==='history'){
      const topics=(CASE.interview&&CASE.interview.topics)||[];
      return miss.map(tid=>{
        const tp=topics.find(x=>x.topic===tid)||{};
        const rules=Array.isArray(tp.answer)?tp.answer:[];
        const base=rules.length?(rules.find(x=>!x.when)||rules[rules.length-1]).value:'';
        const label=tp.canonical||String(tid).replace(/_/g,' ');
        const ans=bubbleText(learnerText(base||''));
        return ans?`<div class="item"><details class="teach"><summary class="hd"><span class="nm">${esc(label)}</span>
            <span class="pill p-warn">not asked</span><span class="expand">Answer</span></summary>
            <div class="note" style="background:none;border:0;padding:0;margin:8px 0 0">${esc(ans)}</div></details></div>`
          :`<div class="item"><div class="hd"><span class="nm">${esc(label)}</span><span class="pill p-warn">not asked</span></div></div>`;
      }).join('');
    }
    if(r.id==='handoff') return handoffMisses();
    return miss.map(id=>item(id,'not done',
      (ST.expected.has(id)?'p-harm':'p-warn'),dispExp(id))).join('');
  };
  const handoffMisses=()=>{
    if(!ST.handoff) return '';
    const H=CASE.handoff, dId=ST.handoff.disposition, out=[];
    const fold=(label,pill,pillcls,body)=>body
      ?`<div class="item"><details class="teach"><summary class="hd"><span class="nm">${esc(label)}</span>
          <span class="pill ${pillcls}">${esc(pill)}</span><span class="expand">Why</span></summary>
          <div class="note" style="background:none;border:0;padding:0;margin:8px 0 0">${esc(learnerText(body))}</div></details></div>`
      :`<div class="item"><div class="hd"><span class="nm">${esc(label)}</span><span class="pill ${pillcls}">${esc(pill)}</span></div></div>`;
    if(dId!==H.correct_disposition.id)
      out.push(fold('Disposition: '+H.correct_disposition.label,'not chosen','p-harm',H.correct_disposition.explanation));
    const dx=scoreDiagnoses(ST);
    const named=dx.rows.some(x=>x.verdict==='primary_correct'||x.verdict==='main_not_primary');
    if(!named) out.push(fold('Diagnosis: '+dxLabel(PROTO.correctDxId),'not named','p-harm',PROTO.correctDxExplanation));
    dx.missed.forEach(m=>out.push(fold('Diagnosis: '+dxLabel(m.id),'not named','p-warn',m.why)));
    return out.join('');
  };
  const scoreTable=`<div class="catlist">${summaryScores(ST).map(r=>{
    const cls=r.pct===null?'':(r.pct<50?'low':(r.pct<80?'mid':''));
    const inner=missedOf(r);
    return `<details class="catfold"><summary>
      <span class="cat-l">${esc(r.label)}</span>
      <span class="cat-s">${r.pct===null?'<span class="pill p-neu">n/a</span>'
        :`${r.pct}%<span class="bar ${cls}"><i style="width:${r.pct}%"></i></span>`}</span>
      <span class="cat-p">${r.max?r.points+' / '+r.max:''}</span>
      <svg class="dbfold-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
      <span class="cat-d">${esc(r.detail)}${r.halted?' <span class="pill p-harm">halted here</span>':''}</span>
      </summary>
      <div class="cat-body">${inner||'<p class="sub" style="margin:0">Nothing missed here.</p>'}</div></details>`;
  }).join('')}</div>`;

  /* Critical actions lead. They are what the case is about, and a resident reading top
     to bottom should meet the medicine before the scoreboard. */
  return `<div class="dbf">
    ${ST.halted?`<div class="dbsec"><h2>Harmful action</h2>${item(ST.halted.id,'harmful','p-harm')}</div>`:''}
    ${cause?`<div class="dbsec"><h2>The action that ended the case</h2>${item(cause,'ended the case','p-harm')}</div>`:''}

    <div class="dbsec"><h2 class="crith">Critical actions</h2>
      <h3 class="misshd">Completed</h3>
      ${done.length?done.map(id=>item(id,'done','p-crit',dispExp(id))).join(''):'<p class="sub">None of this case\'s critical actions were completed.</p>'}
      <h3 class="misshd">Missed critical actions</h3>
      ${omit.length?omit.map(id=>item(id,'not done','p-harm',dispExp(id))).join(''):'<p class="sub">None. Every critical action was completed.</p>'}
      ${[...ST.fuOutstanding].length?'<h3 class="misshd">Follow-up obligations left open</h3>'+[...ST.fuOutstanding].map(fid=>
        `<div class="item"><div class="hd"><span class="nm">${esc(fid.replace(/_/g,' '))}</span>
        <span class="pill p-harm">not done</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(FU[fid].debrief_note)}</div></div>`).join(''):''}
      <div class="gatebtns"><button class="btn" id="restart">Replay this case</button>
      ${CASES.length>1?'<button class="btn ghost" id="pickanother">Choose a different case</button>':''}</div></div>

    <!-- Author instruction, 15 October 2026: above the Summary, headed "Critical Errors", no
         explanatory paragraph. Shown only when there is something in it. -->
    ${dis.length?`<div class="dbsec"><h2>Critical Errors</h2>
      ${dis.map(id=>item(id,'discouraged','p-warn')).join('')}</div>`:''}

    <div class="dbsec"><h2>Summary</h2>
      <p class="sub">${ST.halted?'Halted':(ST.failed?(ST.failed.byClock?'Ended by the clock':'Ended by an action'):(ST.earlyExit?'Ended early, incomplete':'Completed'))} at ${mmss(ST.now)},
      in ${esc(PROTO.difficulty.modes[MODE].label.toLowerCase())} mode${DM()===1&&MODE!==PROTO.difficulty.default?`, so the nurse prompted at the deadlines the case authored rather than waiting past them`:''}.
      Points direct review; they do not rank you. Critical actions count two, recommended
      actions one, a discouraged action costs one, and a harmful action zeroes its tab.</p>
      ${notScored?`<p><b>${esc(notScored)}</b> Start with what ended it, above.</p>
        <details class="teach"><summary class="hd"><span class="nm" style="font-weight:400">Show the category scores anyway</span><span class="expand">Show</span></summary>${scoreTable}</details>`
        :scoreTable}</div>

    ${points.length?`<div class="dbsec">${dbFold('Points to carry out of this case',
      points.slice(0,3).map(pointItem).join(''))}</div>`:''}

    <!-- "Other actions worth doing" removed on author instruction, 11 October 2026.
         Missed recommended actions are still listed under each category in the Summary. -->

    <!-- The discouraged actions moved above the Summary as "Critical Errors" (15 October 2026). -->

    ${traps.length?`<div class="dbsec"><h2>Things that looked reasonable and were not</h2>
      ${traps.map(x=>item(x.id,'no benefit here','p-neu')).join('')}
      </div>`:''}

    ${ho}

    ${read.length?`<div class="dbsec">${dbFold('Your results, read',`
      <p class="sub">While the case ran you saw the numbers and the tracings and nothing else.
      This is the case's own reading of each panel and tracing you ordered, in the order they
      came back.</p>
      ${read.map(r=>`<div class="item"><div class="hd"><span class="nm">${esc(dispName(r.id))}</span>
        <span class="pill p-neu">${mmss(r.o.dueT)}</span></div>
        ${renderPayload(r.o.value)}
        <div class="note" style="background:none;border:0;padding:0;margin:6px 0 0">${esc(r.o.value.comment)}</div></div>`).join('')}`)}</div>`:''}

    ${defaults.length?`<div class="dbsec"><h2>Answered by a default, not by the case</h2>
      <p class="sub">These returned the catalog's normal result or the global response because this case
      authors nothing for them. A normal default is not a neutral default: if an author forgets a study
      that matters, the learner is shown normal and taught the wrong thing.</p>
      <p>${defaults.map(d=>esc(dispName(d))).join(', ')}.</p></div>`:''}

    ${stillPending.length?`<div class="dbsec"><h2>Results you did not read</h2>
      ${stillPending.length?`<p>Still pending when the case ended: ${stillPending.map(i=>esc(dispName(i))).join(', ')}.</p>`:''}
      <p class="sub">Handing over with a result you never looked at is a real handover failure.</p></div>`:''}

    ${points.length>3?`<div class="dbsec">${dbFold('More points from this case',
      points.slice(3).map(pointItem).join(''))}</div>`:''}

    ${DEVNOTES.debriefHTML()}
  </div>`;
}

/* ---------- case picker ---------- */
/* ---------- welcome screen ----------
   Replaces the old card picker. Derived entirely from CASES, so adding a case stays a
   data change. Two optional card fields drive it, `complaint` and `category`; both
   degrade, so a pack that predates them still lists. Age and sex come from
   case.patient, which every pack already has. */
let WL_FILTER='all', WL_SEL=-1, WL_ROWS=[], WL_BOUND=false;
const WL_SHORT={male:'M',female:'F'};
const WL_LABEL={male:'Male patient',female:'Female patient'};

function wlModel(){
  return CASES.map((c,i)=>{
    /* A locked stub in the deployed build has no case yet, only its card and the patient's
       age and sex (engine/access.js). */
    const k=c.card||{}, p=(c.case&&c.case.patient)||c.patient||{};
    /* "medical student, intern, junior resident" is a range and reads better as one */
    const lvs=(Array.isArray(k.target_level)?k.target_level:[k.target_level||''])
      .filter(Boolean).map(x=>String(x).replace(/_/g,' '));
    const lv=lvs.length>2 ? lvs[0]+' to '+lvs[lvs.length-1] : lvs.join(' and ');
    return {i, prefix:c.prefix, num:k.number||null,
      complaint:k.complaint||k.title||c.prefix,
      age:p.age, sex:(p.sex||'').toLowerCase(),
      category:k.category||'Cases',
      level:lv.charAt(0).toUpperCase()+lv.slice(1),
      mins:k.runtime_seconds?Math.round(k.runtime_seconds/60):null,
      unreviewed:k.unreviewed!==false,
      locked:!!c.locked,
      broken:c.locked?(c.buildNoteCount||0):(c.buildNotes||[]).length};
  });
}
function wlCats(m){ const o=[]; for(const c of m) if(!o.includes(c.category)) o.push(c.category); return o.sort(); }

function wlChips(m){
  const box=el('wl-chips'), cats=wlCats(m);
  /* one category is not a filter, it is noise */
  if(cats.length<2){ box.style.display='none'; return; }
  box.style.display='';
  box.innerHTML=[['all','All cases']].concat(cats.map(c=>[c,c]))
    .map(([k,l])=>`<button class="wl-chip" type="button" data-wlchip="${esc(k)}" aria-pressed="${WL_FILTER===k}">${esc(l)}</button>`)
    .join('');
}

function renderPicker(){
  const m=wlModel();
  const q=(el('wl-q')?el('wl-q').value:'').trim().toLowerCase();
  wlChips(m);
  /* "case 3" or "#3" finds that case by its number. A bare 3 stays a word search, so an age
     still finds what it found before. */
  const qn=q.match(/^(?:case\s*|#)(\d{1,4})$/);
  const hits=m.filter(c=>{
    if(WL_FILTER!=='all'&&c.category!==WL_FILTER) return false;
    if(qn) return c.num===Number(qn[1]);
    if(!q) return true;
    const hay=[c.complaint,c.category,c.level,String(c.age),WL_SHORT[c.sex]||'',c.sex,c.prefix]
      .join(' ').toLowerCase();
    return q.split(/\s+/).every(t=>hay.includes(t));
  });
  /* In case-number order within each group (28 October 2026). */
  hits.sort((a,b)=>(a.num||1e9)-(b.num||1e9));
  el('wl-count').textContent=hits.length;
  WL_ROWS=hits;

  if(!hits.length){
    el('pk-list').innerHTML='<div class="wl-empty"><b>No case matches that.</b>'+
      'Try a body system, an age, or clear the search to see everything.</div>';
    WL_SEL=-1; return;
  }
  const groups=[...new Set(hits.map(c=>c.category))].sort();
  const grouped=groups.length>1;
  let html='';
  for(const g of groups){
    if(grouped) html+=`<div class="wl-group">${esc(g)}</div>`;
    for(const c of hits.filter(x=>x.category===g)){
      const face=WL_SHORT[c.sex]?`<i class="${c.sex}"></i>`:'';
      const prog=PROGRESS.rowBadge(c.prefix);
      const aria=[(c.num?'Case '+c.num+'. ':'')+c.complaint,
                  (WL_LABEL[c.sex]||'Patient')+', '+(c.age!==undefined?c.age+' years old':'age not recorded'),
                  c.category,c.level,c.mins?'about '+c.mins+' minutes':'',
                  c.unreviewed?'Unsigned draft.':'Reviewed.',
                  c.locked&&!ACCESS_UI.signedIn()?'Sign in to open.':'',
                  c.broken?'Incomplete: '+c.broken+' build problems, this case will not run correctly.':'',
                  prog.aria
                 ].filter(Boolean).join('. ');
      html+=`<button class="wl-case${ACCESS_UI.loadingIndex()===c.i?' loading':''}" type="button" role="option" data-case="${c.i}"
        data-row="${WL_ROWS.indexOf(c)}" aria-label="${esc(aria)}">
        <span class="wl-face">${face}</span>
        <span class="wl-body">
          <span class="wl-ttl">${c.num?`<span class="wl-no">Case ${c.num}</span>`:''}${esc(c.complaint)}</span>
          <span class="wl-meta">
            <span class="ag">${c.age!==undefined?esc(String(c.age)):'\u2013'} ${esc(WL_SHORT[c.sex]||'\u2013')}</span>
            <span class="lv">${c.broken?'<span style="color:var(--harm)">will not run correctly</span>':esc(c.level)}</span>
            <span class="rt">${c.mins?c.mins+' min':''}</span>
          </span>${prog.html}
        </span>
        ${c.locked&&!ACCESS_UI.signedIn()?`<svg class="wl-lock" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2"/></svg>`:''}
        <span class="wl-state${c.unreviewed?'':' ok'}" title="${c.unreviewed?'Unsigned draft':'Reviewed'}"></span>
      </button>`;
    }
  }
  el('pk-list').innerHTML=html;
  wlPaint();
  el('pk-warn').textContent = CASES.length===1
    ? '' : 'Each case is independent. Nothing carries over between them.';
  wlBind();
}
function wlPaint(){
  document.querySelectorAll('.wl-case').forEach(b=>{
    const on=Number(b.dataset.row)===WL_SEL;
    b.classList.toggle('sel',on); b.setAttribute('aria-selected',String(on));
  });
}
function wlOpen(){ if(WL_SEL>=0&&WL_ROWS[WL_SEL]) chooseCase(WL_ROWS[WL_SEL].i); }
/* v0.19. The welcome page covers the list when shown, so keys meant for the list stay off. */
function wlVisible(){ return !el('picker').classList.contains('hidden') && !(typeof LANDING==='object'&&LANDING.visible()); }
function wlBind(){
  if(WL_BOUND) return; WL_BOUND=true;
  el('wl-q').addEventListener('input',()=>{ WL_SEL=-1; renderPicker(); });
  /* Rows carry data-case, so opening a case still goes through the document-level
     delegation and chooseCase(). This listener only handles the chrome. */
  el('picker').addEventListener('click',e=>{
    const chip=e.target.closest('[data-wlchip]');
    if(chip){ WL_FILTER=chip.dataset.wlchip; WL_SEL=-1; renderPicker(); return; }
    const kb=e.target.closest('#wl-menubtn');
    if(kb){ e.stopPropagation();
      const on=!el('wl-menu').classList.contains('open');
      el('wl-menu').classList.toggle('open',on); kb.setAttribute('aria-expanded',String(on)); return; }
    const nav=e.target.closest('[data-nav]');
    if(nav){ e.preventDefault(); el('wl-menu').classList.remove('open');
      el('wl-menubtn').setAttribute('aria-expanded','false');
      document.dispatchEvent(new CustomEvent('navigate',{detail:{to:nav.dataset.nav}})); return; }
    const row=e.target.closest('.wl-case');
    if(row){ WL_SEL=Number(row.dataset.row); wlPaint(); }
    el('wl-menu').classList.remove('open');
    el('wl-menubtn').setAttribute('aria-expanded','false');
  });
  /* Scoped to the welcome screen so none of these keys reach a running case. */
  document.addEventListener('keydown',e=>{
    if(!wlVisible()) return;
    if(ACCESS_UI.modalOpen()) return;   // typing a password must not search or open a case
    if(CHARGE.isOpen()) return;         // a case is downloading behind the charging screen
    const q=el('wl-q');
    if(e.key==='/'&&document.activeElement!==q){ e.preventDefault(); q.focus(); q.select(); return; }
    if(e.key==='Escape'){
      if(el('wl-menu').classList.contains('open')){
        el('wl-menu').classList.remove('open');
        el('wl-menubtn').setAttribute('aria-expanded','false'); return; }
      if(q.value){ q.value=''; renderPicker(); } return; }
    if(!WL_ROWS.length) return;
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){
      e.preventDefault();
      WL_SEL=e.key==='ArrowDown'?Math.min(WL_ROWS.length-1,WL_SEL+1):Math.max(0,WL_SEL-1);
      wlPaint();
      const r=document.querySelector('.wl-case[data-row="'+WL_SEL+'"]');
      if(r) r.scrollIntoView({block:'nearest'});
      return; }
    if(e.key==='Enter'){
      /* Enter from the search box opens the first result, but only when nothing is
         selected. Arrowing down then pressing Enter must open what is highlighted. */
      if(WL_SEL<0&&document.activeElement===q&&WL_ROWS.length){ WL_SEL=0; wlPaint(); }
      wlOpen(); }
  });
}
/* ---------- the charging defibrillator (author instruction, 11 October 2026) ----------
   Shown by access.js while a locked case downloads, which can take tens of seconds. The
   download reports no progress, so the bar is a waiting indicator, not a measurement: it
   climbs quickly and then slows, never passing 92 percent until the case is actually in
   hand, and then fills. The shock button to the right is disabled until then. Pressing it
   flashes and fades the overlay away, uncovering the case's arrival screen, which
   chooseCase has already drawn underneath. Cancel, or Escape while charging, closes the
   overlay and leaves the learner on the case list; a download still in flight is kept for
   later and does not open the case. */
const CHARGE=(function(){
  /* The bar's fill is a CSS animation on a transform (shell.html, .chg-barfill), so it
     runs on the compositor and keeps moving while the main thread is busy with the
     download. The joule count reads the bar's current scale each frame rather than
     keeping a clock of its own, so the two cannot drift apart, and is only rewritten
     when the whole number changes. */
  const JOULES=200;
  let open=false, ready=false, raf=0, onCancel=null, lastJ=-1, janim=null;
  const $=id=>document.getElementById(id);
  /* The count is a column of every value, moved by a transform, so it keeps counting on the
     compositor while the download holds the main thread (11 October 2026: rewriting the text
     each frame froze with it). ty(n) puts value n in the window. */
  const ty=n=>'translateY('+(-n/(JOULES+1)*100)+'%)';
  /* One keyframe per joule, at the moment the bar reaches it. The bar is CSS
     cubic-bezier(.12,.62,.32,1) over 45 s to 92 percent (shell.html, chgfill), so the
     keyframe for n sits where that curve reaches n/184, and each holds until the next. */
  const KF=(function(){
    const x1=.12,y1=.62,x2=.32,y2=1,S=[];
    for(let i=0;i<=4000;i++){ const u=i/4000,a=1-u;
      S.push([3*a*a*u*x1+3*a*u*u*x2+u*u*u, 3*a*a*u*y1+3*a*u*u*y2+u*u*u]); }
    const top=Math.round(.92*JOULES), out=[]; let k=0;
    for(let n=0;n<=top;n++){
      const p=n/top; while(k<S.length-1&&S[k][1]<p) k++;
      out.push({offset:n?Math.min(1,S[k][0]):0,transform:ty(n),easing:'step-end'});
    }
    if(out[out.length-1].offset<1) out.push({offset:1,transform:ty(top)});
    return out;
  })();
  function jcol(){
    const c=$('chg-jcol'); if(!c) return null;
    if(!c.childElementCount){ let h=''; for(let n=0;n<=JOULES;n++) h+='<div>'+n+' J</div>'; c.innerHTML=h; }
    return c;
  }
  function scaleNow(){
    const b=$('chg-bar'); if(!b) return 0;
    const m=getComputedStyle(b).transform;
    if(!m||m==='none') return 0;
    const v=m.match(/matrix\(([^,]+)/); return v?Math.max(0,Math.min(1,parseFloat(v[1]))):0;
  }
  function paintJ(f){
    const n=Math.round(Math.max(0,Math.min(1,f))*JOULES);
    if(n===lastJ) return; lastJ=n;
    const c=jcol(); if(c) c.style.transform=ty(n);
  }
  function setStatus(s){ const n=$('chargestatus'); if(n) n.textContent=s; }
  function start(title,cancel){
    const v=$('chargeview'); if(!v) return;
    open=true; ready=false; lastJ=-1; onCancel=cancel||null;
    const bar=$('chg-bar');
    if(bar){ bar.style.transition='none'; bar.style.transform=''; }
    v.classList.remove('hidden','ready','shocked','leaving','charging');
    void v.offsetWidth;                    // restart the fill from zero on a second open
    v.classList.add('charging');
    document.body.classList.add('chg-cover');
    $('chargetitle').textContent=title||'';
    $('chg-state').textContent='CHARGING';
    $('chg-btnlab').textContent='CHARGING';
    { const tp=$('chargetop'); if(tp) tp.textContent='Charging'; }
    $('chg-led').setAttribute('fill','#3a3f45');
    const b=$('chargedeliver'); b.disabled=true;
    setStatus('Charging. Opening the case.');
    cancelAnimationFrame(raf);
    if(janim){ janim.cancel(); janim=null; }
    paintJ(0);
    const jc=jcol(), reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
    if(jc&&reduce) paintJ(.6);
    else if(jc&&jc.animate) janim=jc.animate(KF,{duration:45000,fill:'forwards'});
    const c=$('chargecancel'); if(c) c.focus();
  }
  /* The case is bound and its arrival screen is drawn underneath. The bar finishes its
     fill over half a second, then the shock button arms and takes the focus. */
  function done(){
    if(!open) return;
    ready=true; cancelAnimationFrame(raf);
    const f0=scaleNow(); if(janim){ janim.cancel(); janim=null; } lastJ=-1; paintJ(f0);
    /* Freeze the bar where the animation has it, then let a transition finish the fill. */
    const v=$('chargeview'), bar=$('chg-bar'), from=scaleNow(), s0=performance.now();
    if(bar){
      bar.style.transition='none'; bar.style.transform='scaleX('+from+')';
      v.classList.remove('charging'); void bar.offsetWidth;
      bar.style.transition='transform .5s cubic-bezier(.2,.7,.3,1)'; bar.style.transform='scaleX(1)';
    }
    const fill=now=>{
      if(!open) return;
      const k=Math.min(1,(now-s0)/500);
      paintJ(from+(1-from)*(1-Math.pow(1-k,3)));
      if(k<1){ raf=requestAnimationFrame(fill); return; }
      v.classList.add('ready');
      $('chg-state').textContent='CHARGED';
      $('chg-btnlab').textContent='CHARGED';
      { const tp=$('chargetop'); if(tp) tp.textContent='Charged'; }
      $('chg-led').setAttribute('fill','#38e07b');
      const b=$('chargedeliver'); b.disabled=false; b.focus();
      setStatus('Charged. Press the button to enter the case.');
    };
    raf=requestAnimationFrame(fill);
  }
  function hide(){
    open=false; ready=false; cancelAnimationFrame(raf);
    if(janim){ janim.cancel(); janim=null; }
    const v=$('chargeview'); if(v){ v.classList.add('hidden'); v.classList.remove('charging'); }
    document.body.classList.remove('chg-cover');
  }
  function deliver(){
    if(!open||!ready) return;
    const v=$('chargeview'); open=false;
    document.body.classList.remove('chg-cover');
    v.classList.add('shocked','leaving');
    const reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
    setTimeout(()=>{ v.classList.add('hidden'); v.classList.remove('shocked','leaving','ready');
      const bb=el('beginbtn'); if(bb) bb.focus(); }, reduce?0:380);
  }
  function cancel(){
    if(!open||ready) return;
    const cb=onCancel; hide(); if(cb) cb();
  }
  function bind(){
    const d=$('chargedeliver'), c=$('chargecancel');
    if(d) d.addEventListener('click',e=>{ e.stopPropagation(); deliver(); });
    if(c) c.addEventListener('click',e=>{ e.stopPropagation(); cancel(); });
    document.addEventListener('keydown',e=>{
      if(!open) return;
      if(e.key==='Escape'){ e.preventDefault(); e.stopImmediatePropagation(); cancel(); }
    },true);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',bind); else bind();
  return {start, done, fail:hide, isOpen:()=>open||!!(document.getElementById('chargeview')&&!document.getElementById('chargeview').classList.contains('hidden'))};
})();
function chooseCase(i){
  /* A locked stub is fetched first; access.js calls back here once the pack is in place. */
  if(ACCESS_UI.isLocked(i)){ ACCESS_UI.open(i); return; }
  selectCase(i);
  bindCase();
  CHART_FILTER=null;
  MODE=SHARED.difficulty.default;
  AN.track('case_opened',{case:PACK.prefix});
  /* Fold the chosen case at t=0 before anything reads ST. Until v0.17 ST still held the
     previously bound case here, so the first five seconds of a run ramped from the
     numbers of whichever case had been bound before it, and the splash figure would
     have drawn that patient's state too. The ramp is reset for the same reason. */
  refold(); resetRamp();
  el('picker').classList.add('hidden');
  el('splash').classList.remove('hidden');
  renderSplash();
  PROGRESS.onSplash(PACK.prefix);
}
function backToPicker(){
  VOICE.reset(); ASKMIC.abort();
  if(typeof NINTRO==='object') NINTRO.cancel();
  clearPatient(); clearSplashPatient();
  AUDIO.setScene('idle'); MONITOR.setScene('idle'); MONITOR.reset();
  el('splash').classList.add('hidden');
  el('picker').classList.remove('hidden');
  WL_SEL=-1;                          // returning must not land on a stale highlight
  renderPicker();
  const q=el('wl-q'); if(q) q.blur();
}

/* ---------- splash ---------- */
function renderSplash(){
  const m=CASE.metadata, p=CASE.patient, cs=m.care_setting||{}, ar=m.arrival||{};
  /* The care setting label is no longer shown on the splash. */
  el('sp-title').textContent=m.working_title||'';
  { const no=el('sp-no'), n=(PACK.card||{}).number||m.case_number;
    if(no){ no.textContent=n?'Case '+n:''; no.hidden=!n; } }
  el('sp-cc').textContent=m.chief_complaint_patient_voice
    ? '\u201C'+m.chief_complaint_patient_voice+'\u201D' : '';
  /* Section 3.2 used to print the arrival line and the full EMS narrative here.
     Both are gone from the splash: the narrative is most of the case, and a
     learner who reads it before pressing Begin has been handed the history
     instead of taking it. What is left is the room they are walking into. */
  const room=arrivalRoom();
  const arr=el('sp-arrival');
  arr.textContent = room ? 'Patient brought to the '+room : '';
  arr.classList.toggle('hidden', !room);
  renderSplashVitals();
  renderSplashPatient();
  /* The mode the case starts in is drawn first and as a box; every other mode follows
     it as a line of text. Which is which is read from `difficulty.default` rather than
     from a mode's name, so the card cannot end up recommending one mode while the
     interface starts in another. */
  const D=PROTO.difficulty;
  const order=Object.keys(D.modes).sort((a,b)=>(a===D.default?0:1)-(b===D.default?0:1));
  el('sp-modes').innerHTML=order.map(k=>{
    const md=D.modes[k], plain=k!==D.default;
    /* The default mode is a name and nothing else (v0.17l, on the author's instruction): the
       paragraph under it was the longest thing on the card and said what the debrief says
       better. Its description stays in SHARED and is the button's tooltip and its name for
       a screen reader. Every other mode keeps its one line, because that line is the only
       reason to choose it. */
    return plain
      ? `<button class="mode plain" role="radio" data-mode="${esc(k)}" aria-checked="${MODE===k}">
      <b>${esc(md.label)}</b><span>${esc(md.description)}</span></button>`
      : `<button class="mode" role="radio" data-mode="${esc(k)}" aria-checked="${MODE===k}"
      title="${esc(md.description)}" aria-label="${esc(md.label+'. '+md.description)}"><i class="modedot" aria-hidden="true"></i><b>${esc(md.label)}</b></button>`;
  }).join('');

}
/* The arrival vitals, on the card, before Begin.

   This is a handover artifact, not the monitor, and the distinction is the whole reason
   it is safe to show. A crew hands over the numbers they measured; that is what the two
   sentences above it are. What the resident still does not have is the CURRENT number
   and the trend, which is what a monitor is for and what attaching one buys them. So
   these are static, carry no jitter, and are drawn on a pale panel rather than in the
   monitor's dark.

   There is deliberately no caption explaining that they are not live. "Vitals on
   arrival" is past tense and the empty monitor a second later says the rest; a resident
   who needs to be told in a sentence that a number from before they walked in is not a
   live reading has been handed the lesson instead of learning it.

   Read from the first authored phase rather than from ST, so the card shows the same
   numbers whichever case is selected and shows them before the clock has started. A
   half-authored case with null vitals hides the section rather than printing dashes:
   the picker offers skeletons on purpose and an empty panel teaches nothing. */
/* Adult resting ranges for the arrival card. Every current case is an adult (18 to 68).
   A pediatric case would need age-based ranges before this is used for it.
   HR 60 to 100, systolic 90 to 139 and diastolic under 90, SpO2 94 or more, RR 12 to 20,
   temperature 36.0 to 37.9. */
function splashVitalAbnormal(v){
  const n=x=>typeof x==='number';
  return {
    hr:   n(v.heart_rate) && (v.heart_rate<60 || v.heart_rate>100),
    bp:   (n(v.systolic_bp) && (v.systolic_bp<90 || v.systolic_bp>=140)) || (n(v.diastolic_bp) && v.diastolic_bp>=90),
    spo2: n(v.oxygen_saturation) && v.oxygen_saturation<94,
    rr:   n(v.respiratory_rate) && (v.respiratory_rate<12 || v.respiratory_rate>20),
    t:    n(v.temperature_c) && (v.temperature_c<36 || v.temperature_c>=38)
  };
}
function renderSplashVitals(){
  const sec=el('sp-vitalsec'), box=el('sp-vitals');
  if(!sec||!box) return;
  const v=(CASE&&CASE.phases&&CASE.phases[0])?CASE.phases[0].vitals:null;
  const num=x=>typeof x==='number';
  if(!v||!num(v.heart_rate)){ sec.classList.add('hidden'); box.innerHTML=''; return; }
  sec.classList.remove('hidden');
  /* v0.18g. Values outside the adult resting range are red, as on a triage sheet. */
  const ab=splashVitalAbnormal(v);
  const cells=[
    ['HR', num(v.heart_rate)?String(v.heart_rate):'\u2013', '/minute', ab.hr],
    ['BP', (num(v.systolic_bp)&&num(v.diastolic_bp))?v.systolic_bp+'/'+v.diastolic_bp:'\u2013','mmHg', ab.bp],
    ['SpO\u2082', num(v.oxygen_saturation)?String(v.oxygen_saturation):'\u2013','%', ab.spo2],
    ['RR', num(v.respiratory_rate)?String(v.respiratory_rate):'\u2013','/minute', ab.rr],
    ['T',  num(v.temperature_c)?v.temperature_c.toFixed(1):'\u2013','\u00B0C', ab.t]
  ];
  box.innerHTML=cells.map(c=>`<div class="spvitcell${c[3]?' abn':''}"><div class="spvitlab">${c[0]}</div>
    <div class="spvitval">${esc(c[1])}</div>
    <div class="spvitunit">${c[2]}</div></div>`).join('');
}

function begin(){
  AN.takeCounts(); AN.track('case_started',{case:PACK.prefix, mode:MODE});
  STARTED=true; T0=Date.now(); PAUSED=false; PAUSED_MS=0; PAUSED_AT=0;
  /* Saved progress: a new run. One already in progress on this case is discarded (Start over). */
  PROGRESS.start(PACK.prefix, MODE);
  /* A history entry to pop, so the back button has something to catch. It can throw on a
     file:// URL in some browsers, and a simulator that will not start because the history
     API refused would be a poor trade for a guard. */
  try{ history.pushState({emsim:1},''); }catch(err){}
  clearSplashPatient();
  el('splash').classList.add('hidden');
  AUDIO.unlock();
  /* The room starts here rather than on the splash. A case that has been chosen and not
     started is not a case anybody is in. */
  AUDIO.setScene('case'); MONITOR.setScene('case');
  render();
  VOICE.paint();
  startLoop();
  THEME.fitRail();
  NINTRO.play();
}

/* ---------- saved progress (28 October 2026) ----------
   What engine/progress.js stores for a run in progress, and how it is put back. The log,
   the case clock and the mode are the run: fold() rebuilds the rest. The tab, the handoff
   being drafted and the six-minute pause are screen state a resumed learner would notice
   losing. Order baskets, filters and search text are not kept. */
function runSnapshot(){
  return {v:1, t:Math.round(now()*1000)/1000, mode:MODE, tab:TAB,
    log:LOG,
    handoff:{disposition:PENDING_HANDOFF.disposition||null,
             diagnoses:Array.isArray(PENDING_HANDOFF.diagnoses)?PENDING_HANDOFF.diagnoses.slice():[]},
    /* An open pause is saved as not yet shown, so it opens again rather than losing a note
       that was half written. */
    reflect:{done:REFLECT_DONE&&!REFLECT_OPEN, note:REFLECT_NOTE, note2:REFLECT_NOTE2}};
}
/* Called from the splash of the case the run belongs to (chooseCase has bound it). The run
   opens paused at the saved case time, with no nurse card, and the clock starts again only
   when the learner presses play, as after any other pause. */
function resumeRun(s){
  VOICE.reset(); ASKMIC.abort(); RUNID++;
  const D=SHARED.difficulty||{};
  if(s.mode&&D.modes&&D.modes[s.mode]) MODE=s.mode;
  LOG=s.log.map(e=>Object.assign({},e));
  SEQ=LOG.reduce((m,e)=>Math.max(m,(Number(e.seq)||0)+1),0);
  const t=Math.max(0,Number(s.t)||0);
  AN.takeCounts();
  STARTED=true; ENDED=false; CLOCK_HELD=false;
  T0=Date.now()-t*1000; PAUSED_MS=0; PAUSED=true; PAUSED_AT=Date.now();
  if(s.tab&&tabList().includes(s.tab)) TAB=s.tab;
  if(s.handoff&&typeof s.handoff==='object')
    PENDING_HANDOFF={disposition:s.handoff.disposition||null,
                     diagnoses:Array.isArray(s.handoff.diagnoses)?s.handoff.diagnoses.slice():[]};
  const r=s.reflect||{};
  REFLECT_DONE=!!r.done; REFLECT_NOTE=String(r.note||''); REFLECT_NOTE2=String(r.note2||'');
  try{ history.pushState({emsim:1},''); }catch(err){}
  clearSplashPatient();
  el('splash').classList.add('hidden');
  resetRamp(); refold();
  /* Results already on the chart were seen before the break and do not open again. */
  Object.keys(ST.orders).forEach(id=>ST.orders[id].forEach(rec=>{
    const v=rec.value; if(v&&typeof v==='object'&&v.kind==='image') IMG_SEEN.add(id+'@'+rec.dueT);
  }));
  LASTNURSE=-1; LASTPHASE=null;      /* the nurse's latest line is shown, without its chime */
  AUDIO.unlock(); AUDIO.setScene('idle'); MONITOR.setScene('idle');
  render(); VOICE.paint(); startLoop(); THEME.fitRail();
  if(ENDED) return;                  /* render() ended a run that a harmful action had halted */
  /* A run whose handover or early exit was saved, but whose ending was not (the network
     failed at the debrief), ends now: those two end the case from the click, not the fold. */
  if(LOG.some(e=>e.actionId==='handoff_submit'||e.kind==='early_exit')){ PAUSED=false; finish(); return; }
  el('pausemsg').innerHTML='Resumed at '+esc(mmss(t))+' of case time.<br><span>The case clock is stopped. '+
    'It starts again when you press play.</span>';
  el('pauseview').classList.remove('hidden');
  el('resumebtn').focus();
}

/* ---------- the nurse's opening card (author instruction, 13 October 2026) ----------
   See .nintro in shell.html. Three seconds of card, then the drawer closes (0.65 s), then
   the portrait flies to the header's portrait (0.75 s) and the header one takes over. The
   flight measures the header portrait at that moment, so it lands wherever the layout put
   it. The case clock is held for the whole of it and released at the end. */
const NINTRO=(function(){
  const HOLD=3000, DRAWER=650, FLY=750;
  let node=null, timers=[], phase='', held=false;
  const later=(f,ms)=>{ timers.push(setTimeout(f,ms)); };
  function clear(){ timers.forEach(clearTimeout); timers=[]; }
  function finish(){
    clear(); phase='done';
    if(node){ node.remove(); node=null; }
    document.body.classList.remove('nintro-on');
    if(held){ held=false; releaseClock(); }
  }
  function fly(){
    if(!node||phase==='fly'||phase==='done') return;
    clear(); phase='fly';
    node.classList.add('closing');
    const reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
    later(()=>{
      if(!node) return;
      const face=node.querySelector('.nintro-face'), dest=document.querySelector('.nurse .nurseface');
      if(face&&dest&&!reduce){
        const a=face.getBoundingClientRect(), b=dest.getBoundingClientRect();
        const k=b.width/a.width;
        node.classList.add('flying');
        face.style.transform=`translate(${b.left-a.left}px,${b.top-a.top}px) scale(${k})`;
        face.style.borderWidth='1px';
      }
      node.classList.add('away');
      later(finish, reduce?0:FLY);
    }, reduce?0:DRAWER);
  }
  function play(){
    if(node) finish();
    const line=(el('nurseline')||{}).textContent||PROTO.nurseIdle||'';
    const src=(document.querySelector('.nurse .nurseface')||{}).src||'';
    node=document.createElement('div');
    node.className='nintro'; node.setAttribute('role','status'); node.setAttribute('aria-live','polite');
    node.innerHTML=`<div class="nintro-card">
        <img class="nintro-face" src="${esc(src)}" alt="" draggable="false">
        <div class="nintro-clip"><div class="nintro-drawer"><div class="nintro-says">
          <div class="nintro-lab">Nurse</div><div class="nintro-line">${esc(line)}</div>
        </div></div></div></div>`;
    node.addEventListener('click',e=>{ e.stopPropagation(); fly(); });
    document.body.appendChild(node);
    document.body.classList.add('nintro-on');
    phase='hold';
    if(!PAUSED){ holdClock(); held=CLOCK_HELD; }
    later(fly,HOLD);
  }
  /* Any key skips to the flight, and is not passed on: the first keystroke of a case
     should not also type into whatever has the focus behind the card. */
  document.addEventListener('keydown',e=>{
    if(!node||phase!=='hold') return;
    e.preventDefault(); e.stopPropagation(); fly();
  },true);
  return {play, active:()=>!!node, cancel:finish};
})();

/* The header is fixed and its height varies with the nurse line, so every
   panel top and the debrief scroller are offset from a measured value rather
   than a guessed one. */
const hdr=document.querySelector('.stick');
const setHdr=()=>{
  const h=hdr.offsetHeight+'px';
  document.documentElement.style.setProperty('--top',h);
  document.documentElement.style.setProperty('--hdr',h);
};
if(window.ResizeObserver) new ResizeObserver(setHdr).observe(hdr);
window.addEventListener('resize',setHdr); setHdr();

/* ---------- pause, and leaving ----------
   Two situations where the simulator has to stop being a thing that runs on its own.

   The window losing focus is the easy one. The case clock is wall-clock time and the
   deadlines in a case are claims about a patient, so charging a resident for the minutes
   they spent in another window would make those claims false. It pauses on either signal
   the browser gives, because they cover different things: visibilitychange catches a
   hidden tab and a minimised window, and blur catches a window that is still on screen
   with the focus somewhere else.

   It never resumes on its own. Coming back to a case that has been running without you
   is worse than coming back to one that waited, so resuming is a deliberate click. */
const inCase = ()=> STARTED && !ENDED;

function pauseSim(){
  if(PAUSED||!inCase()) return;
  /* The microphone permission prompt can take the window's focus. A case that pauses
     itself the moment someone tries to speak to it would be a poor first impression of
     the feature, so the blur that the prompt causes is not a pause. A hidden tab still
     is: visibilitychange does not come through here with the flag set. */
  if((VOICE.arming()||ASKMIC.arming())&&!document.hidden) return;
  /* A paused case is not listening. What was heard so far is kept in the list. */
  VOICE.pause(); ASKMIC.abort();
  PAUSED=true; PAUSED_AT=Date.now();
  AUDIO.setScene('idle'); MONITOR.setScene('idle');
  el('pausemsg').innerHTML=PAUSE_MSG;
  el('pauseview').classList.remove('hidden');
  PROGRESS.flush();
}
const PAUSE_MSG=el('pausemsg').innerHTML;
function resumeSim(){
  if(!PAUSED) return;
  const away=Date.now()-PAUSED_AT;
  PAUSED_MS+=away;
  /* A vitals ramp in flight resumes where it was rather than arriving while nobody was
     watching. It is measured from the wall clock, so it needs the same offset. */
  RAMP_T0+=away;
  PAUSED=false;
  el('pauseview').classList.add('hidden');
  AUDIO.unlock(); AUDIO.setScene('case'); MONITOR.setScene('case');
  render();
}
document.addEventListener('visibilitychange',()=>{ if(document.hidden) pauseSim(); });
window.addEventListener('blur',pauseSim);
el('resumebtn').addEventListener('click',resumeSim);

/* Leaving. A refresh or a back throws the run away, and the run is the only copy: there
   is no server and nothing is stored, which is the whole architecture rather than an
   oversight.

   WHAT THIS CAN AND CANNOT COVER, because the difference is not a design choice.
   Keyboard refresh and the back button are interceptable and get the dialog below. A
   click on the browser's own reload control is not: the only hook is beforeunload, whose
   wording no browser has let a page choose for over a decade. So that path gets the
   native dialog, and the two look different because the platform makes them different. */
/* ---------- the six-minute pause ----------
   Once per case, at SHARED.reflect.atSeconds of case time, wherever the case has got to.
   It holds the clock, it has no way out but Continue, and the note it takes is the
   resident's own: nothing reads it, nothing scores it and it never reaches the log. It is
   kept for the run so that reopening the case mid-session does not lose what was written,
   and restart() clears it with everything else.

   It does not fire over the debrief, over a case the resident has already paused, or over
   the leave dialog, because in each of those the case is already stopped and a second
   modal on top of the first is two dialogs arguing. Whichever is up, the check waits. */
const REFLECT=(SHARED.reflect||{});
const REFLECT_AT=(typeof REFLECT.atSeconds==='number')?REFLECT.atSeconds:360;
let REFLECT_DONE=false, REFLECT_NOTE='', REFLECT_NOTE2='', REFLECT_OPEN=false;
function reflectDue(){
  return !REFLECT_DONE && !REFLECT_OPEN && inCase() && !PAUSED && ST && ST.now>=REFLECT_AT
         && el('leaveview').classList.contains('hidden');
}
function openReflect(){
  REFLECT_DONE=true; REFLECT_OPEN=true;
  holdClock();
  el('reflecttitle').textContent=REFLECT.title||'Pause: consider your differential diagnosis.';
  el('reflectbody').textContent=REFLECT.body||'';
  el('reflectbody').hidden=!REFLECT.body;
  const box=el('reflectnote');
  box.placeholder=REFLECT.placeholder||'Your differential diagnosis (optional)';
  box.value=REFLECT_NOTE;
  const box2=el('reflectnote2');
  if(box2){ box2.placeholder=REFLECT.placeholder2||'What you need to check or give (optional)';
            box2.value=REFLECT_NOTE2; }
  el('reflectview').classList.remove('hidden');
  /* The button, not the box: the prompt is a question to think about, and a cursor already
     blinking in a text field reads as one that has to be answered in writing. */
  el('reflectok').focus();
}
function closeReflect(){
  if(!REFLECT_OPEN) return;
  const box=el('reflectnote'); REFLECT_NOTE=box?box.value:'';
  const box2=el('reflectnote2'); REFLECT_NOTE2=box2?box2.value:'';
  REFLECT_OPEN=false;
  el('reflectview').classList.add('hidden');
  releaseClock();
}

/* ---------- global search ----------
   One list over everything the case holds: every action on every tab, whatever the tab's
   own filter is set to, and every line of the chart.

   v0.26b, author instruction (11 October 2026): pressing an action in the results orders
   it, exactly as its own button would after Submit Order, and the box is cleared and keeps
   the focus for the next search. Enter orders the top result. An action on a tab nothing
   can be ordered from (the interview) still navigates to it, as before. */
let SEARCH_OPEN=false, SEARCH_Q='', SEARCH_DONE='';
function searchOpen(){ return SEARCH_OPEN; }
function openSearch(){
  if(!inCase()) return;
  AN.count('search_opens');
  /* Two dropdowns from the same row, so opening one puts the other away. Away, not
     discarded: orders already spoken into the list are still there on the way back. */
  if(VOICE.collapse) VOICE.collapse();
  SEARCH_OPEN=true;
  el('searchpanel').hidden=false;
  el('searchbtn').setAttribute('aria-expanded','true');
  const b=el('searchbox'); b.value=SEARCH_Q; b.focus(); b.select();
  renderSearch();
}
function closeSearch(){
  if(!SEARCH_OPEN) return;
  SEARCH_OPEN=false; SEARCH_DONE='';
  el('searchpanel').hidden=true;
  el('searchbtn').setAttribute('aria-expanded','false');
}
function searchNorm(s){ return String(s==null?'':s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim(); }
/* Every token has to appear somewhere in the row's text, so "chest x" finds the chest
   radiograph and "x chest" finds it too. A row scores higher when a token starts a word in
   the name than when it only appears in the group or the tab. */
/* Words a learner uses for the same order (author instruction, 28 October 2026: a nitro drip
   is found by "nitroglycerin infusion" and the other way round). A token matches if any of its
   forms does. Shared by the global search and every tab filter. */
const SEARCH_SAME={drip:['infusion'],drips:['infusion'],infusion:['drip'],infusions:['drip'],
  nitro:['nitroglycerin'],ntg:['nitroglycerin']};
function searchScore(q,name,extra){
  const hay=' '+searchNorm(name)+' ', side=' '+searchNorm(extra)+' ';
  let score=0;
  for(const t0 of q){
    let best=-1;
    for(const t of [t0].concat(SEARCH_SAME[t0]||[])){
      const s=hay.indexOf(' '+t)>=0?10:hay.indexOf(t)>=0?6:side.indexOf(' '+t)>=0?3:side.indexOf(t)>=0?2:-1;
      if(s>best) best=s;
    }
    if(best<0) return -1;
    score+=best;
  }
  return score;
}
/* One pass over the raw text, escaping each piece. Replacing token by token on the escaped
   string let a later token match inside an earlier <mark> or an entity ("ma", "amp"). */
function searchMark(text,q){
  const ts=q.filter(t=>t.length>=2).map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));
  if(!ts.length) return esc(text);
  return String(text).split(new RegExp('('+ts.join('|')+')','ig'))
    .map((part,i)=>i%2?'<mark>'+esc(part)+'</mark>':esc(part)).join('');
}
function searchHits(){
  const q=searchNorm(SEARCH_Q).split(' ').filter(Boolean);
  if(!q.length) return null;
  const acts=[], lines=[];
  for(const id in ACT){
    const a=ACT[id];
    if(!(PROTO.tabLabel||{})[a.tab]||a.hidden||a.menu_hidden) continue;
    const gl=(a.groups||[a.group]).filter(Boolean);
    const groups=gl.join(' ');
    const sc=searchScore(q,a.name,groups+' '+gl.map(groupLabel).join(' ')+' '+id.replace(/_/g,' ')+' '+(PROTO.tabLabel[a.tab]||''));
    if(sc>=0) acts.push({id,tab:a.tab,name:a.name,group:gl.map(groupLabel).join(', '),score:sc});
  }
  acts.sort((x,y)=>y.score-x.score||x.name.localeCompare(y.name));
  /* Nothing matched by name. The microphone's table knows the brand names, the slang and
     the abbreviations the display names do not carry, so the same words are tried against
     it before giving up: "adrenaline" is not in any name in the catalog and is the first
     word half the room would use. Only exact parses count; a fuzzy one is a guess, and a
     guess belongs in an order the resident confirms, not in a search result. */
  if(!acts.length&&typeof VOICE!=='undefined'){
    const seen=new Set();
    for(const r of VOICE.parse(SEARCH_Q)){
      const ids=r.kind==='ok'?[r.id]:(r.kind==='ambiguous'?r.ids:[]);
      for(const id of ids){
        if(seen.has(id)||!ACT[id]||r.uncertain) continue;
        seen.add(id);
        const a=ACT[id];
        acts.push({id,tab:a.tab,name:a.name,group:(a.groups||[a.group]).filter(Boolean).map(groupLabel).join(', '),
                   score:0,synonym:true});
      }
    }
  }
  for(const it of feedItems()){
    const title=it.name||it.title||'', body=typeof it.body==='string'?it.body:'';
    const sc=searchScore(q,title,body);
    if(sc>=0) lines.push({t:it.t,title,score:sc});
  }
  lines.sort((x,y)=>y.score-x.score||y.t-x.t);
  return {acts:acts.slice(0,40),lines:lines.slice(0,20),q};
}
function renderSearch(){
  const box=el('searchresults'); if(!box) return;
  const hits=searchHits();
  if(!hits){
    box.innerHTML=(SEARCH_DONE?`<div class="srch-done">${esc(SEARCH_DONE)}</div>`:'')
      +'<div class="srch-none">Type to search every tab at once: an examination, a study, '
      +'a drug, a consultation, or anything already in the chart. Pressing an action orders it.</div>';
    return;
  }
  SEARCH_DONE='';
  let html='';
  if(hits.acts.length){
    html+='<div class="srch-sec">'+(hits.acts[0].synonym?'Actions, by another name':'Actions')+'</div>'+hits.acts.map(a=>
      `<button class="srch-hit" data-sgo="${esc(a.id)}"><b>${searchMark(a.name,hits.q)}</b>
        <span class="sh-meta">${esc(PROTO.tabLabel[a.tab]||a.tab)}${a.group?' &middot; '+esc(a.group):''}${
          a.synonym?' &middot; matched as a synonym':''}${
          ST&&ST.taken.has(a.id)?' &middot; already taken':''}</span></button>`).join('');
  }
  if(hits.lines.length){
    html+='<div class="srch-sec">In the chart</div>'+hits.lines.map(l=>
      `<button class="srch-hit" data-schart="1"><b>${searchMark(l.title,hits.q)}</b>
        <span class="sh-meta">${mmss(l.t)}</span></button>`).join('');
  }
  box.innerHTML=html||'<div class="srch-none">Nothing matches that. Try fewer words.</div>';
}
function searchPick(id){
  const a=ACT[id]; if(!a) return;
  if(!(PROTO.voiceTabs||PROTO.orderableTabs).includes(a.tab)){ searchGoTo(id); return; }
  log({actionId:id});
  const verb=a.category==='exam'?'Done':(a.category==='consultant'?'Called':'Ordered');
  SEARCH_DONE=verb+': '+(a.name||id)+'.';
  SEARCH_Q='';
  const b=el('searchbox'); if(b) b.value='';
  render(); renderSearch();
  /* The cursor goes back into the box after the render, and again on the next frame, so
     nothing the press redrew (the record, the nurse) keeps the focus: the next keystroke
     types into the search. */
  const refocus=()=>{ const x=el('searchbox'); if(x&&SEARCH_OPEN){ x.focus(); x.setSelectionRange(x.value.length,x.value.length); } };
  refocus(); requestAnimationFrame(refocus); setTimeout(refocus,60);
}
function searchGoTo(id){
  const a=ACT[id]; if(!a) return;
  closeSearch();
  FILTERS[a.tab]=String(a.name||'').toLowerCase();
  TAB=a.tab;
  setPanels(true,false);
  renderTabs(); renderTab(); scrollTabTop();
}

let LEAVING=false, LEAVE_ACT=null;

function askLeave(action){
  if(!inCase()||LEAVING) return false;
  LEAVE_ACT=action;
  holdClock();
  el('leavemsg').textContent=PROGRESS.kept()
    ? 'Your progress is saved. You can resume this case from the case list.'
    : 'You will lose progress. This case cannot be resumed from where it is.';
  PROGRESS.flush();
  el('leaveview').classList.remove('hidden');
  el('leavecancel').focus();
  return true;
}
function closeLeave(){ el('leaveview').classList.add('hidden'); LEAVE_ACT=null; if(!REFLECT_OPEN) releaseClock(); }
/* The question holds the case clock. It is modal and the deadlines a case authors are claims
   about a patient, so charging a resident the seconds they spent deciding whether to leave
   would make those claims false. It uses the pause fields directly rather than pauseSim(),
   because the pause overlay showing behind a modal reads as two dialogs at once. A case the
   resident had already paused is left alone. */
let CLOCK_HELD=false;
function holdClock(){
  if(PAUSED||CLOCK_HELD||!inCase()) return;
  CLOCK_HELD=true; PAUSED=true; PAUSED_AT=Date.now();
  AUDIO.setScene('idle'); MONITOR.setScene('idle');
}
function releaseClock(){
  if(!CLOCK_HELD) return;
  CLOCK_HELD=false;
  if(!inCase()||!PAUSED) return;      /* the case ended or was paused for another reason */
  const away=Date.now()-PAUSED_AT;
  PAUSED_MS+=away; RAMP_T0+=away; PAUSED=false;
  AUDIO.unlock(); AUDIO.setScene('case'); MONITOR.setScene('case');
  render();
}

el('reflectok').addEventListener('click',closeReflect);
/* Reveal Case Answers asks first, and offers one more try instead. */
function askReplay(){ el('replayview').classList.remove('hidden'); el('replayok').focus(); }
function closeReplay(){ el('replayview').classList.add('hidden'); }
/* The other choice is to read the answers instead (author instruction). */
el('replaycancel').addEventListener('click',e=>{ e.stopPropagation(); closeReplay(); revealAnswers(); });
el('replayok').addEventListener('click',e=>{ e.stopPropagation(); closeReplay(); restart(); });
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&!el('replayview').classList.contains('hidden')){ e.preventDefault(); closeReplay(); }
});
/* A press anywhere outside the search control closes it (author instruction, 23 October 2026).
   Until then only its cross and its own button did, so after ordering from it the panel stayed
   over the monitor and the record for the rest of the case. The press still does what it
   normally does: closing is all this adds. The button and the panel are both inside #search,
   so the button keeps toggling. */
document.addEventListener('pointerdown',e=>{
  if(!SEARCH_OPEN) return;
  const box=el('search');
  if(box&&e.target&&box.contains(e.target)) return;
  closeSearch();
},true);
el('searchbox').addEventListener('input',e=>{ SEARCH_Q=e.target.value; renderSearch(); });
el('searchbox').addEventListener('keydown',e=>{
  if(e.key==='Escape'){ closeSearch(); el('searchbtn').focus(); return; }
  if(e.key==='Enter'){ const f=el('searchresults').querySelector('[data-sgo]'); if(f) f.click(); }
});
el('leavecancel').addEventListener('click',closeLeave);
el('leaveok').addEventListener('click',async ()=>{
  const act=LEAVE_ACT;
  CLOCK_HELD=false;                    /* leaving for good; restart() resets the clock */
  closeLeave();
  LEAVING=true;
  /* The clock is still stopped here (PAUSED stays set), so what is saved is the moment the
     learner asked to leave. A slow network delays leaving by four seconds at most. */
  await PROGRESS.flush(4000);
  if(act==='reload'){ location.reload(); return; }
  /* Back, and the rail's Main menu, which is the same act by another control. The guard
     entry pushed at Begin is popped here. A file opened directly may have
     nothing behind it, in which case the browser does nothing at all and a resident who
     asked to leave would be stuck looking at the case they asked to leave. So if the
     document is still here a moment later, leaving means what it means inside a
     single-page simulator: end the case and go back to the list. */
  const before=location.href;
  history.back();
  setTimeout(()=>{
    if(location.href===before&&document.getElementById('playview')){
      LEAVING=false; restart(); backToPicker();
    }
  },260);
});

/* ---------- the image viewer ----------
   Opened from any thumbnail, anywhere: the chart, the results panel, the debrief. Three
   ways out, because a reader who wants the picture gone should not have to hunt for the
   control. The cross, the backdrop, and Escape.

   It does not pause the case. Every other overlay in this interface either ends the run or
   stops the clock, and this one deliberately does neither: reading a tracing is part of the
   resuscitation rather than a break from it, and a case's deadlines are claims about a
   patient who does not wait while somebody studies an ECG. A resident who wants the clock
   stopped can still switch away from the window, which pauses on visibilitychange as it
   always did. */
let IMG_RETURN=null;
function openImage(id,cap,series){
  if(series&&CTVIEW.has(series)){ CTVIEW.open(series,cap); return; }
  const src=imageSrc(id);
  if(!src) return;
  IMG_RETURN=document.activeElement;
  el('imgfull').src=src;
  el('imgfull').alt=cap||'';
  el('imgview-title').textContent=cap||'Image';
  el('imgview').classList.remove('hidden');
  /* Focus moves to the dialog, which is what a modal should do, EXCEPT when the resident
     is typing. A study that arrives while a question is half-written opens itself under
     the rule below, and taking the caret out of the box mid-sentence would lose the
     question. Escape, the backdrop and the cross all still work without focus. */
  const a=document.activeElement;
  const typing=a&&(a.tagName==='INPUT'||a.tagName==='TEXTAREA'||a.isContentEditable);
  if(!typing) el('imgclose').focus();
}
function closeImage(){
  if(el('imgview').classList.contains('hidden')) return;
  el('imgview').classList.add('hidden');
  /* Drop the source so a 400 KB tracing is not decoded and held for the rest of the run,
     and put focus back where it was rather than at the top of the document. */
  el('imgfull').removeAttribute('src');
  try{ if(IMG_RETURN&&IMG_RETURN.focus) IMG_RETURN.focus(); }catch(err){}
  IMG_RETURN=null;
  /* A second picture waiting behind this one opens after a beat rather than on the same
     frame, so closing one does not read as a dialog that refuses to go away. */
  if(IMG_QUEUE.length) setTimeout(drainImageQueue,450);
}

/* ---------- the CT series viewer (19 October 2026, author instruction) ----------
   A head CT is a stack of images, and the skill is scrolling through it: finding the
   collection, judging its shape against the skull, seeing the fracture on the bone window.
   An image payload that names a `series` keeps its still as the thumbnail in the record, and
   opening it opens this viewer instead of the still. Nothing here names a case: the
   geometry, the windows and the notice come from the series file.

   The voxels are Hounsfield units, gzipped as two byte planes (all the low bytes, then all
   the high bytes, of HU + 1024), so the build can carry them as one base64 string. They are
   decoded once per series per page with the browser's DecompressionStream, which needs no
   network request, and held for reopening. Reading the scan does not pause the clock, for
   the same reason the image viewer never has. Nothing here is logged or scored. */
const CTVIEW=(function(){
  const cache={};                       // series id -> {meta, hu:Int16Array}
  const S={id:null, meta:null, hu:null, i:0, w:80, l:40, win:'Brain', zoom:1, panX:0, panY:0,
           hover:null, token:0, ret:null};
  let off=null, offCtx=null, offImg=null, dpr=1, cw=0, ch=0;
  const lut=new Uint8ClampedArray(4096);
  const stage=()=>el('ctstage'), cvs=()=>el('ctcanvas');
  const isOpen=()=>!el('ctview').classList.contains('hidden');
  const has=id=>!!(id&&PROTO&&PROTO.series&&PROTO.series[id]&&PROTO.series[id].data);

  async function decode(id){
    const key=(PROTO.prefix||'')+'/'+id;
    if(cache[key]) return cache[key];
    if(typeof DecompressionStream==='undefined')
      throw new Error('This browser cannot open the scan. Use a current Chrome, Edge, Firefox or Safari.');
    const m=PROTO.series[id], n=m.n*m.w*m.h;
    const bin=atob(m.data), bytes=new Uint8Array(bin.length);
    for(let k=0;k<bin.length;k++) bytes[k]=bin.charCodeAt(k);
    const buf=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    const u8=new Uint8Array(buf);
    if(u8.length!==2*n) throw new Error('The scan file is damaged (expected '+2*n+' bytes, found '+u8.length+').');
    const hu=new Int16Array(n);
    for(let k=0;k<n;k++) hu[k]=(u8[k]|(u8[n+k]<<8))-1024;
    return (cache[key]={meta:m, hu});
  }

  function buildLut(){
    const lo=S.l-S.w/2, w=Math.max(1,S.w);
    for(let k=0;k<4096;k++) lut[k]=((k-1024-lo)/w)*255;
  }
  function renderSlice(){
    if(!S.hu) return;
    const m=S.meta, n=m.w*m.h, base=S.i*n, d=offImg.data, hu=S.hu;
    for(let p=0,q=0;p<n;p++,q+=4){
      let v=hu[base+p]+1024; v=v<0?0:v>4095?4095:v;
      const g=lut[v]; d[q]=g; d[q+1]=g; d[q+2]=g; d[q+3]=255;
    }
    offCtx.putImageData(offImg,0,0);
    draw();
  }
  function scale(){ return S.meta?Math.min(cw/S.meta.w,ch/S.meta.h)*S.zoom:1; }
  function resize(){
    if(!isOpen()) return;
    dpr=window.devicePixelRatio||1; cw=stage().clientWidth; ch=stage().clientHeight;
    cvs().width=Math.max(1,Math.round(cw*dpr)); cvs().height=Math.max(1,Math.round(ch*dpr));
    draw();
  }
  function toImage(cx,cy){
    const s=scale(), m=S.meta;
    return {x:(cx-cw/2-S.panX)/s+m.w/2, y:(cy-ch/2-S.panY)/s+m.h/2};
  }
  function draw(){
    const c=cvs(), ctx=c.getContext('2d');
    ctx.setTransform(1,0,0,1,0,0); ctx.fillStyle='#000'; ctx.fillRect(0,0,c.width,c.height);
    if(!S.hu) return;
    const m=S.meta, s=scale();
    ctx.setTransform(dpr*s,0,0,dpr*s,dpr*(cw/2+S.panX-(m.w/2)*s),dpr*(ch/2+S.panY-(m.h/2)*s));
    ctx.imageSmoothingEnabled=true; ctx.imageSmoothingQuality='high';
    ctx.drawImage(off,0,0);
    /* A 5 cm bar, so a size can be judged the way it is on a workstation. */
    ctx.setTransform(dpr,0,0,dpr,0,0);
    /* On a narrow stage the window and zoom buttons span the bottom, so the bar and the
       bottom left text sit above them. */
    const tb=el('cttools'), lift=(cw<520&&tb)?tb.offsetHeight+8:0;
    el('ct-bl').style.bottom=(8+lift)+'px';
    const len=(50/m.pixel_mm)*s, x0=12, y0=ch-40-lift;
    ctx.strokeStyle='#e9eef2'; ctx.lineWidth=1.5; ctx.beginPath();
    ctx.moveTo(x0,y0); ctx.lineTo(x0+len,y0);
    for(let t=0;t<=5;t++){ const xx=x0+len*t/5; ctx.moveTo(xx,y0); ctx.lineTo(xx,y0-(t%5===0?7:4)); }
    ctx.stroke();
    ctx.fillStyle='#e9eef2'; ctx.font='11px ui-monospace,Menlo,monospace'; ctx.fillText('5 cm',x0+len+6,y0+4);
    text();
  }
  function text(){
    const m=S.meta; if(!m) return;
    el('ct-tl').innerHTML=esc(m.label||'CT')+'\nIm '+(S.i+1)+' / '+m.n
      +'\n<span class="dim">Z '+Number(m.z_mm[S.i]).toFixed(1)+' mm · '+m.thickness_mm+' mm</span>';
    el('ct-tr').textContent='W '+Math.round(S.w)+'  L '+Math.round(S.l)+'\n'+S.win+(S.zoom!==1?'\nZoom '+S.zoom.toFixed(1)+'x':'');
    el('ct-bl').innerHTML=m.synthetic?'\n<span class="dim">Synthetic image</span>':'';
    el('ct-br').innerHTML=S.hover!=null?'HU '+S.hover:'<span class="dim">HU ·</span>';
    el('ctcount').textContent=(S.i+1)+' / '+m.n;
    el('ctslider').value=S.i+1;
    stage().setAttribute('aria-label','Axial CT image '+(S.i+1)+' of '+m.n+', window '+S.win
      +'. Scroll or use the arrow keys to change image.');
  }
  function setSlice(i){
    if(!S.meta) return;
    i=Math.max(0,Math.min(S.meta.n-1,i)); if(i===S.i) return;
    S.i=i; hoverAt(); renderSlice();
  }
  function setWindow(w,l,name){
    S.w=Math.max(1,Math.min(4000,w)); S.l=Math.max(-1000,Math.min(3000,l)); S.win=name||'Custom';
    el('ctwins').querySelectorAll('.ctbtn').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.win===S.win)));
    buildLut(); renderSlice();
  }
  function setZoom(z,cx,cy){
    const before=(cx!=null)?toImage(cx,cy):null;
    S.zoom=Math.max(1,Math.min(8,z));
    if(S.zoom===1){ S.panX=0; S.panY=0; }
    else if(before){ const s=scale(), m=S.meta; S.panX=cx-cw/2-(before.x-m.w/2)*s; S.panY=cy-ch/2-(before.y-m.h/2)*s; }
    draw();
  }
  let lastPtr=null;
  function hoverAt(cx,cy){
    if(cx!==undefined) lastPtr={cx,cy};
    if(!lastPtr||!S.hu){ S.hover=null; return; }
    const m=S.meta, p=toImage(lastPtr.cx,lastPtr.cy), x=Math.floor(p.x), y=Math.floor(p.y);
    S.hover=(x>=0&&y>=0&&x<m.w&&y<m.h)?S.hu[S.i*m.w*m.h+y*m.w+x]:null;
  }

  async function open(id,cap){
    if(!has(id)) return false;
    const tok=++S.token;
    S.ret=document.activeElement;
    /* The header is "Interactive PACS Viewer: " and the study, from the series' own title,
       else the result's caption (owner, 20 October 2026). */
    const t0=PROTO.series[id].title;
    el('ctview-title').textContent='Interactive PACS Viewer: '+(t0||cap||'CT');
    el('ctview').classList.remove('hidden');
    el('ctmsg').textContent='Loading images'; el('ctmsg').classList.remove('hidden');
    const m=PROTO.series[id];
    /* The footer with the controls line and the image's notice was removed on the owner's
       instruction (20 October 2026). The notice still travels in the pack's series data. */
    el('ctwins').innerHTML=(m.windows||[]).map((w,k)=>
      `<button type="button" class="ctbtn" data-win="${esc(w.name)}" data-w="${w.w}" data-l="${w.l}"`
      +` title="W ${w.w} L ${w.l} (key ${k+1})">${esc(w.name)}</button>`).join('');
    el('ctslider').max=m.n;
    syncHelp();
    /* Focus moves to the stage so the arrow keys scroll at once, except while the resident
       is writing a question to the patient or a note: a scan that opens itself mid-sentence
       must not take the caret. A filter or search box is not writing, and leaving the focus
       there would send the arrow keys to a box behind the dialog. */
    const a=document.activeElement;
    const typing=a&&(a.id==='askbox'||a.tagName==='TEXTAREA'||a.isContentEditable);
    if(!typing) stage().focus({preventScroll:true});
    S.hu=null; resize();
    try{
      const data=await decode(id);
      if(tok!==S.token||!isOpen()) return true;
      S.id=id; S.meta=data.meta; S.hu=data.hu;
      off=document.createElement('canvas'); off.width=m.w; off.height=m.h;
      offCtx=off.getContext('2d'); offImg=offCtx.createImageData(m.w,m.h);
      S.i=Math.max(0,Math.min(m.n-1,(m.start_image||1)-1));
      S.zoom=1; S.panX=0; S.panY=0; S.hover=null; lastPtr=null;
      el('ctmsg').classList.add('hidden');
      const w0=(m.windows||[])[0]||{name:'Brain',w:80,l:40};
      resize(); setWindow(w0.w,w0.l,w0.name);
    }catch(err){
      if(tok===S.token) el('ctmsg').textContent=String(err&&err.message?err.message:err);
    }
    return true;
  }
  function close(){
    if(!isOpen()) return;
    S.token++;
    el('ctview').classList.add('hidden');
    S.hu=null; off=null; offCtx=null; offImg=null;   // the decoded stack stays in the cache
    try{ if(S.ret&&S.ret.focus) S.ret.focus(); }catch(err){}
    S.ret=null;
    if(IMG_QUEUE.length) setTimeout(drainImageQueue,450);
  }

  /* ---- pointer: drag scrolls, right-drag windows, shift-drag or middle-drag pans ---- */
  let drag=null, acc=0, wheelAcc=0;
  el('ctstage').addEventListener('contextmenu',e=>e.preventDefault());
  el('ctstage').addEventListener('pointerdown',e=>{
    if(!S.hu) return;
    stage().focus({preventScroll:true});
    stage().setPointerCapture(e.pointerId);
    const mode=e.button===2?'window':(e.button===1||e.shiftKey)?'pan':'scroll';
    drag={mode, x:e.clientX, y:e.clientY, lastY:e.clientY, w:S.w, l:S.l, panX:S.panX, panY:S.panY};
    acc=0;
  });
  el('ctstage').addEventListener('pointermove',e=>{
    if(!S.hu) return;
    const r=stage().getBoundingClientRect(), cx=e.clientX-r.left, cy=e.clientY-r.top;
    if(drag){
      const dx=e.clientX-drag.x, dy=e.clientY-drag.y;
      if(drag.mode==='scroll'){
        acc+=e.clientY-drag.lastY; drag.lastY=e.clientY;
        while(acc>=8){ acc-=8; setSlice(S.i+1); }
        while(acc<=-8){ acc+=8; setSlice(S.i-1); }
      }else if(drag.mode==='window'){
        const k=Math.max(0.5,drag.w/160);
        setWindow(drag.w+dx*k,drag.l+dy*k*0.5,'Custom');
      }else if(drag.mode==='pan'){
        S.panX=drag.panX+dx; S.panY=drag.panY+dy; draw();
      }
    }
    hoverAt(cx,cy); text();
  });
  const endDrag=e=>{ drag=null; acc=0; try{ stage().releasePointerCapture(e.pointerId); }catch(err){} };
  el('ctstage').addEventListener('pointerup',endDrag);
  el('ctstage').addEventListener('pointercancel',endDrag);
  el('ctstage').addEventListener('pointerleave',()=>{ if(!drag){ lastPtr=null; S.hover=null; text(); } });
  el('ctstage').addEventListener('wheel',e=>{
    if(!S.hu) return;
    e.preventDefault();
    const r=stage().getBoundingClientRect(), cx=e.clientX-r.left, cy=e.clientY-r.top;
    if(e.ctrlKey||e.metaKey){ setZoom(S.zoom*Math.exp(-e.deltaY*0.01),cx,cy); hoverAt(cx,cy); text(); return; }
    wheelAcc+=e.deltaMode===1?e.deltaY*30:e.deltaY;
    /* One image per notch of a mouse wheel (100 to 120 per notch), and smooth on a trackpad,
       whose small deltas add up here. */
    while(wheelAcc>=100){ wheelAcc-=100; setSlice(S.i+1); }
    while(wheelAcc<=-100){ wheelAcc+=100; setSlice(S.i-1); }
    hoverAt(cx,cy); text();
  },{passive:false});

  el('ctslider').addEventListener('input',e=>setSlice(+e.target.value-1));
  el('ctwins').addEventListener('click',e=>{
    const b=e.target.closest('.ctbtn'); if(!b) return;
    setWindow(+b.dataset.w,+b.dataset.l,b.dataset.win);
  });
  el('ctzoomin').addEventListener('click',()=>setZoom(S.zoom*1.25));
  el('ctzoomout').addEventListener('click',()=>setZoom(S.zoom/1.25));
  el('ctreset').addEventListener('click',()=>{ S.zoom=1; S.panX=0; S.panY=0; draw(); });
  el('ctclose').addEventListener('click',close);
  el('ctview').addEventListener('click',e=>{ if(e.target===el('ctview')) close(); });

  /* How to scroll (20 October 2026). Hidden by its cross for the rest of the page's life and
     brought back by the question mark. Nothing is stored: a new session shows it again. A
     press on it is not a drag on the image, but the wheel over it still scrolls. */
  let helpOff=false;
  function syncHelp(){ el('cthelp').classList.toggle('off',helpOff); el('cthelp-show').classList.toggle('off',!helpOff); }
  el('cthelp-x').addEventListener('click',()=>{ helpOff=true; syncHelp(); stage().focus({preventScroll:true}); });
  el('cthelp-show').addEventListener('click',()=>{ helpOff=false; syncHelp(); stage().focus({preventScroll:true}); });
  ['cthelp','cthelp-show','cttools'].forEach(id=>el(id).addEventListener('pointerdown',e=>e.stopPropagation()));
  window.addEventListener('resize',resize);

  /* Keys, in the capture phase so that nothing behind the viewer also acts on them (Escape
     must not also shrink the record). Arrows and the number keys are left alone while the
     resident is typing in a box. */
  document.addEventListener('keydown',e=>{
    if(!isOpen()) return;
    if(e.key==='Escape'){ e.preventDefault(); e.stopImmediatePropagation(); close(); return; }
    const t=e.target, typing=/^(INPUT|TEXTAREA|SELECT)$/.test((t&&t.tagName)||'')&&t.id!=='ctslider';
    if(typing||e.altKey||e.metaKey||e.ctrlKey||!S.hu) return;
    const k=e.key, wins=S.meta.windows||[];
    let done=true;
    if(k==='ArrowUp'||k==='ArrowLeft'||k==='PageUp') setSlice(S.i-1);
    else if(k==='ArrowDown'||k==='ArrowRight'||k==='PageDown') setSlice(S.i+1);
    else if(k==='Home') setSlice(0);
    else if(k==='End') setSlice(S.meta.n-1);
    else if(k>='1'&&k<='9'&&wins[+k-1]) setWindow(wins[+k-1].w,wins[+k-1].l,wins[+k-1].name);
    else if(k==='+'||k==='=') setZoom(S.zoom*1.25);
    else if(k==='-') setZoom(S.zoom/1.25);
    else if(k==='0'){ S.zoom=1; S.panX=0; S.panY=0; draw(); }
    else done=false;
    if(done){ e.preventDefault(); e.stopImmediatePropagation(); }
  },true);

  return {open, close, isOpen, has, state:()=>({id:S.id, i:S.i, w:S.w, l:S.l, win:S.win, zoom:S.zoom, loaded:!!S.hu})};
})();

/* ---------- a picture opens itself ----------
   A result that is a tracing or a film opens full size the moment it comes back, without
   the resident having to find the thumbnail on the chart. Two reasons this is not just a
   convenience. A twelve-lead is the study this case turns on, and a 260-pixel thumbnail on
   a running list is not a tracing anybody can read; and the chart is newest-first but it is
   still a list that the resident may not be looking at when the study lands.

   It does not pause the clock, for the same reason the viewer never did: reading the film
   is part of the resuscitation.

   Each result opens once. The key is the study plus the second it resulted, so a repeat
   twelve-lead is a new picture and the same one is never reopened after it is dismissed.
   Two studies landing together queue rather than race, and nothing opens while the case is
   over, paused, or asking whether to leave. */
let IMG_SEEN=new Set(), IMG_QUEUE=[];
function autoOpenImages(){
  if(!ST||ENDED||PAUSED||LEAVING) return;
  if(!el('leaveview').classList.contains('hidden')) return;
  Object.keys(ST.orders).forEach(id=>ST.orders[id].forEach(rec=>{
    const v=rec.value;
    if(!v||typeof v!=='object'||v.kind!=='image') return;
    const key=id+'@'+rec.dueT;
    if(IMG_SEEN.has(key)) return;
    IMG_SEEN.add(key);
    if(!imageSrc(v.image)) return;              /* degrades to the chart line, as elsewhere */
    IMG_QUEUE.push({img:v.image,cap:v.caption||dispName(id),series:v.series});
  }));
  drainImageQueue();
}
function drainImageQueue(){
  if(!IMG_QUEUE.length||ENDED||PAUSED||LEAVING||imageOpen()) return;
  const n=IMG_QUEUE.shift();
  openImage(n.img,n.cap,n.series);
}
function imageOpen(){ return !el('imgview').classList.contains('hidden')||CTVIEW.isOpen(); }

document.addEventListener('click',e=>{
  const t=e.target.closest?e.target.closest('.imgthumb'):null;
  if(t){ e.preventDefault(); openImage(t.dataset.img,t.dataset.cap,t.dataset.series); return; }
  if(el('imgview').classList.contains('hidden')) return;
  /* The backdrop is the overlay itself; anything inside the card is not it. */
  if(e.target===el('imgview')) closeImage();
});
el('imgclose').addEventListener('click',closeImage);

document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&imageOpen()){ closeImage(); return; }
  if(e.key==='Escape'&&!el('leaveview').classList.contains('hidden')){ closeLeave(); return; }
  /* The pause has no key out. Continue is the only way on, which is the point of it. */
  if(REFLECT_OPEN){ if(e.key==='Escape') e.preventDefault(); return; }
  if(e.key==='Escape'&&searchOpen()){ closeSearch(); el('searchbtn').focus(); return; }
  /* Control or Command and K, which is what a search box is opened with everywhere else and,
     more to the point, is the only thing that works: the History tab puts the cursor in the
     question box the moment it renders, so a bare "/" is a character the resident is typing
     at the patient, not a shortcut. "/" is kept for when nothing has the focus. */
  const typing=/^(INPUT|TEXTAREA|SELECT)$/.test((e.target&&e.target.tagName)||'');
  if((e.key==='k'||e.key==='K')&&(e.ctrlKey||e.metaKey)&&!e.altKey&&inCase()){
    e.preventDefault(); searchOpen()?closeSearch():openSearch(); return;
  }
  if(e.key==='/'&&!typing&&inCase()&&!searchOpen()){ e.preventDefault(); openSearch(); return; }
  const reload=(e.key==='F5')||((e.key==='r'||e.key==='R')&&(e.ctrlKey||e.metaKey)&&!e.altKey);
  if(reload&&inCase()&&!LEAVING){ e.preventDefault(); askLeave('reload'); }
});
window.addEventListener('popstate',()=>{
  if(LEAVING||!inCase()) return;
  /* Put the guard back so the page stays where it is while the resident decides. */
  try{ history.pushState({emsim:1},''); }catch(err){}
  askLeave('back');
});
window.addEventListener('beforeunload',e=>{
  /* A saved run is not lost by a reload: progress.js sends the last moment on pagehide. */
  if(LEAVING||!inCase()||PROGRESS.kept()) return;
  e.preventDefault(); e.returnValue='';
});

/* Escape backs out of the expanded chart, the one state that hides the
   workspace. The leave dialog takes Escape first, above. */
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&RIGHT_WIDE&&!ENDED&&el('leaveview').classList.contains('hidden'))
    minimiseRecord();
});

/* ---------- author notes (temporary, author instruction, 14 October 2026) ----------
   For validating cases, not for learners, and meant to be taken out: SHARED.authorNotes
   false hides it, and the rest is this module, #devnote in shell.html, the .devn styles and
   one line each in debriefHTML and renderTab. The Note button sits beside Search. The case
   clock is held while the box has the focus, so writing does not move the case on. Enter
   saves, Shift and Enter is a new line, Escape closes. Each note keeps a snapshot of the
   case at that moment: time, state, vitals, flags, everything done so far, what is pending
   and the nurse's last line. Notes are kept in this browser, across replays and cases, until
   cleared, and are listed at the bottom of every debrief with one Copy all button. */
const DEVNOTES=(function(){
  const KEY='emsim-author-notes';
  const ON=!(typeof SHARED!=='undefined'&&SHARED.authorNotes===false);
  let notes=[], held=false, clearArm=0;
  const $=id=>document.getElementById(id);
  try{ notes=JSON.parse(localStorage.getItem(KEY)||'[]')||[]; }catch(e){ notes=[]; }
  function persist(){ try{ localStorage.setItem(KEY,JSON.stringify(notes)); }catch(e){} }
  const isOpen=()=>{ const p=$('devnotepanel'); return !!p&&!p.hidden; };
  function vitalsLine(){
    const v=(typeof rampedVitals==='function'&&rampedVitals())||targetVitals()||{};
    const f=(k,u)=>typeof v[k]==='number'?v[k]+(u||''):'?';
    return 'HR '+f('heart_rate')+', BP '+f('systolic_bp')+'/'+f('diastolic_bp')+', SpO2 '+f('oxygen_saturation','%')
      +', RR '+f('respiratory_rate')+', T '+f('temperature_c')+(ST.monitoring?'':' (monitor not attached)');
  }
  function snapshot(text){
    const t=now(), ph=PHASE[ST.phase]||{};
    const done=ST.timeline.filter(x=>x.t<=t+1e-6&&!String(x.id).startsWith('interview:'))
      .map(x=>mmss(x.t)+' '+x.label);
    const asked=ST.timeline.filter(x=>String(x.id).startsWith('interview:')).length;
    const pend=(ST.pending||[]).map(p=>dispName(p.id)+' (due '+mmss(p.dueT)+')');
    const nurse=((ST.nurse||[]).slice(-1)[0]||{}).text||'';
    const title=(CASE.metadata&&CASE.metadata.working_title)||'';
    const mode=((PROTO.difficulty||{}).modes||{})[MODE];
    return [
      PACK.prefix+((PACK.card||{}).number?' case '+PACK.card.number:'')+(title?' ('+title+')':'')+' at '+mmss(t)+(mode?', '+mode.label.toLowerCase()+' mode':''),
      'Note: '+text,
      'State: '+(ph.label||ST.phase)+' ['+ST.phase+']',
      'Vitals: '+vitalsLine(),
      'Flags: '+([...(ST.flags||[])].join(', ')||'none'),
      'Done so far: '+(done.join('; ')||'nothing')+(asked?'. Questions asked: '+asked:''),
      'Pending: '+(pend.join('; ')||'nothing'),
      'Nurse\'s last line: '+(nurse||'none')
    ].join('\n');
  }
  function count(){ const n=$('devnoten'); if(n) n.textContent=notes.length?notes.length+' saved':''; }
  function open(){
    if(!ON||!inCase()) return;
    if(typeof closeSearch==='function') closeSearch();
    if(typeof VOICE!=='undefined'&&VOICE.collapse) VOICE.collapse();
    $('devnotepanel').hidden=false; $('devnotebtn').setAttribute('aria-expanded','true');
    count(); $('devnotemsg').textContent='';
    const b=$('devnotebox'); b.focus(); b.setSelectionRange(b.value.length,b.value.length);
  }
  function close(){
    if(!isOpen()) return;
    $('devnotepanel').hidden=true; $('devnotebtn').setAttribute('aria-expanded','false');
    const b=$('devnotebox'); if(document.activeElement===b) b.blur();
    unhold();
  }
  function hold(){ if(!held&&inCase()&&!PAUSED){ holdClock(); held=CLOCK_HELD; } }
  function unhold(){ if(held){ held=false; releaseClock(); } }
  function saveNote(){
    const b=$('devnotebox'), text=b.value.trim();
    if(!text||!ST) return;
    /* The snapshot is taken from a fresh fold, so it is the case as it stands now. */
    refold();
    notes.push({at:Date.now(), text:snapshot(text)});
    persist();
    b.value=''; count();
    $('devnotemsg').textContent='Saved at '+mmss(now())+'. It is listed at the bottom of the debrief.';
    b.focus();
  }
  function debriefHTML(){
    if(!ON) return '';
    const body=notes.length
      ? notes.map((n,i)=>`<div class="devn-item"><b>Note ${i+1}.</b> ${esc(n.text)}</div>`).join('')
      : '<p class="sub">No notes yet. Use the Note button beside Search during a case.</p>';
    return `<div class="dbsec" id="devnotes"><h2>Author notes</h2>
      <p class="sub">Temporary, for validating cases. Every note saved in this browser, oldest first,
      each with the state of the case when it was written. They stay until cleared.</p>
      <div class="devn-btns">${notes.length?`<button class="btn" id="devnotecopy" type="button">Copy all</button>
        <button class="btn ghost" id="devnoteclear" type="button">Clear all notes</button>`:''}
        <span class="devn-msg" id="devnotecopymsg"></span></div>
      <div class="devn-list">${body}</div></div>`;
  }
  function allText(){ return notes.map((n,i)=>'Note '+(i+1)+'. '+n.text).join('\n\n'); }
  function copyAll(){
    const text=allText(), msg=$('devnotecopymsg');
    const done=ok=>{ if(msg) msg.textContent=ok?'Copied '+notes.length+' note'+(notes.length===1?'':'s')+'.':'Copy failed. Select the notes and copy them by hand.'; };
    const fallback=()=>{
      const ta=document.createElement('textarea'); ta.value=text; ta.setAttribute('readonly','');
      ta.style.cssText='position:fixed;left:-9999px;top:0'; document.body.appendChild(ta); ta.select();
      let ok=false; try{ ok=document.execCommand('copy'); }catch(e){} ta.remove(); done(ok);
    };
    if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(()=>done(true),fallback);
    else fallback();
  }
  function bind(){
    const root=$('devnote'); if(!root) return;
    if(!ON){ root.remove(); return; }
    root.hidden=false;
    $('devnotebtn').addEventListener('click',()=>isOpen()?close():open());
    $('devnoteclose').addEventListener('click',close);
    $('devnotesave').addEventListener('click',saveNote);
    const b=$('devnotebox');
    b.addEventListener('focus',hold);
    b.addEventListener('blur',unhold);
    b.addEventListener('keydown',e=>{
      if(e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); saveNote(); }
      else if(e.key==='Escape'){ e.preventDefault(); e.stopPropagation(); close(); $('devnotebtn').focus(); }
    });
    document.addEventListener('click',e=>{
      const t=e.target;
      if(t&&t.id==='devnotecopy'){ copyAll(); return; }
      if(t&&t.id==='devnoteclear'){
        if(Date.now()-clearArm<4000){ notes=[]; persist(); clearArm=0; const s=$('devnotes'); if(s) s.outerHTML=debriefHTML(); return; }
        clearArm=Date.now(); t.textContent='Click again to clear'; setTimeout(()=>{ if(t.isConnected) t.textContent='Clear all notes'; },4000); return;
      }
      if(isOpen()&&!$('devnote').contains(t)) close();
    });
    /* The button works only inside a case. */
    setInterval(()=>{ const btn=$('devnotebtn'); if(!btn) return; const off=!inCase(); if(btn.disabled!==off) btn.disabled=off; if(off) close(); },400);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',bind); else bind();
  return {debriefHTML, open, close, typing:()=>document.activeElement===$('devnotebox')};
})();
/* Syringe: a bolus, the label on the barrel and the plunger driven in as the drug takes
   effect. Pump: an infusion, the labelled bag above it and the timer on its screen. */
function mvSyringe(label,frac){
  const p=Math.max(0,Math.min(1,frac));               // 0 = just given, 1 = fully pushed
  const tx=3+p*19;                                    // the thumb rest slides toward the flange
  const lx=26+p*58;                                   // the liquid drains toward the needle
  const tl=Math.min(54,label.length*5.1);
  return `<svg width="124" height="33" viewBox="0 0 104 28" aria-hidden="true">
    <path d="M${tx} 14H40" stroke="#6f8798" stroke-width="2"/>
    <rect x="${tx}" y="6.5" width="3" height="15" rx="1.2" fill="#6f8798"/>
    <rect x="25" y="6" width="62" height="16" rx="3" fill="#fff"/>
    <rect x="${lx}" y="7" width="${Math.max(0,86-lx)}" height="14" rx="2" fill="#d6eaf3"/>
    <rect x="25" y="6" width="62" height="16" rx="3" fill="none" stroke="#6f8798" stroke-width="1.2"/>
    <path d="M25 3.5v21" stroke="#6f8798" stroke-width="2" stroke-linecap="round"/>
    <path d="M87 11h4v6h-4z" fill="#6f8798"/><path d="M91 14h12" stroke="#6f8798" stroke-width="1.1" stroke-linecap="round"/>
    <text class="mvlab" x="56" y="17.3" text-anchor="middle" textLength="${tl}" lengthAdjust="spacingAndGlyphs">${label}</text>
  </svg>`;
}
function mvPump(label,timer,fill){
  return `<svg width="86" height="100" viewBox="0 0 74 86" aria-hidden="true">
    <path d="M37 0v4" stroke="#6f8798" stroke-width="1.4"/>
    <path d="M13 5h48a3 3 0 0 1 3 3v22a9 9 0 0 1-9 9H19a9 9 0 0 1-9-9V8a3 3 0 0 1 3-3z" fill="#fff"/>
    <path d="M11 ${8+22*(1-fill)}h52v${Math.max(0,22*fill)}a8 8 0 0 1-8 8H19a8 8 0 0 1-8-8z" fill="#d6eaf3" opacity=".9"/>
    <path d="M13 5h48a3 3 0 0 1 3 3v22a9 9 0 0 1-9 9H19a9 9 0 0 1-9-9V8a3 3 0 0 1 3-3z" fill="none" stroke="#6f8798" stroke-width="1.2"/>
    <text class="mvlab" x="37" y="24" text-anchor="middle" textLength="${Math.min(48,label.length*5.1)}" lengthAdjust="spacingAndGlyphs">${label}</text>
    <path d="M37 39v8" stroke="#6f8798" stroke-width="1.6"/>
    <rect x="9" y="47" width="56" height="37" rx="6" fill="#eef2f5" stroke="#6f8798" stroke-width="1.2"/>
    <rect class="mv-scrbg" x="15" y="53" width="44" height="17" rx="3" fill="#0f1a22"/>
    <text class="mv-scr" x="37" y="65.5" text-anchor="middle">${timer}</text>
    <circle cx="21" cy="77" r="2.2" fill="#38e07b"/><rect x="30" y="75" width="24" height="4" rx="2" fill="#c8d2da"/>
  </svg>`;
}

/* ---------- drugs acting, above the patient's head (author instruction, 14 October 2026) ----------
   A drug or fluid whose authored effect is delayed or timed, or that runs continuously, is
   drawn above the patient while it acts. Drugs and fluids only: positive pressure has timed
   effects too and is not a drug.

   A bolus is a syringe with the drug's name on the barrel and a countdown under it to the
   moment its effect is complete (the latest onset_seconds or duration_seconds among its
   vital effects, or a timed flag's duration); the plunger is driven in as it counts down.
   At zero the timer flashes green three times and the syringe shrinks away. A fluid bolus
   is a labelled bag on a pump with the same countdown on the pump's screen.

   A drip (a catalog entry marked persistent) is a labelled bag on a pump. Its screen counts
   down to the drip's onset in the same way, flashes green three times at zero and then
   reads ON, and the pump stays for as long as the drip runs (author instruction, 14 October
   2026). A drip with no authored onset reads ON from the start. It shrinks away when its
   stop order is given, which is the red cross on the drip's own button (dripStops).

   Display only: it reads the run (ST.timeline, ACT, dripStops) and changes nothing. Timers
   run on the case clock, so they stand still while the case is paused. Switched on by
   SHARED.medOverlayCases, "all" or a list of case prefixes. Every case since 28 October 2026.

   A drug or fluid with no authored timer is drawn too (author instruction, 28 October 2026),
   with a display-only countdown: a syringe for MEDVIS_DEFAULT.syringe seconds, a fluid bag
   for MEDVIS_DEFAULT.bag. It says nothing about when the drug acts. */
const MEDVIS_DEFAULT={syringe:10,bag:60};
const MEDVIS=(function(){
  let host=null, els={}, done=new Set(), run=-1;
  const on=()=>{ const m=SHARED.medOverlayCases; return !!(PACK&&(m==='all'||(Array.isArray(m)&&m.includes(PACK.prefix)))); };
  function label(id){
    let n=String(dispName(id)||id)
      .replace(/^normal saline/i,'NS').replace(/^lactated ringer'?s/i,'LR')
      .replace(/\b(bolus|drip|infusion|IV|IVP|PO|SL|sublingual|push)\b/gi,'')
      .replace(/\s*\/\s*$/,'').replace(/\s+/g,' ').trim();
    return n||String(id);
  }
  const isFluid=a=>a.group==='Fluids'||((a.groups||[]).includes('Fluids'));
  const isDrug=a=>a.category==='medication'||isFluid(a);
  function onsetOf(a){
    let T=0;
    for(const f of (a.vital_effects||[])) T=Math.max(T,+f.onset_seconds||0,+f.duration_seconds||0);
    for(const f of (a.flags_set_timed||[])) T=Math.max(T,+f.duration_seconds||0);
    return T;
  }
  function items(t){
    const out=[], open={}, stops=dripStops(), stopped={};
    for(const d in stops) (stopped[stops[d]]=stopped[stops[d]]||[]).push(d);
    for(const x of ST.timeline){
      if(x.type==='blocked'||x.type==='end'||x.t>t+1e-6) continue;
      const id=x.id, a=ACT[id]; if(!a) continue;
      if(stopped[id]){ for(const d of stopped[id]) if(open[d]){ open[d].end=x.t; open[d]=null; } continue; }
      if(!isDrug(a)) continue;
      const T=onsetOf(a);
      if(a.persistent){
        /* A second order for a running drip is the same drip. */
        if(!open[id]){ const it={key:id+'@'+x.t,id,kind:'pump',drip:true,t0:x.t,onset:T>0?x.t+T:null,end:null}; out.push(it); open[id]=it; }
        continue;
      }
      const D=T>0?T:(isFluid(a)?MEDVIS_DEFAULT.bag:MEDVIS_DEFAULT.syringe);
      out.push({key:id+'@'+x.t,id,kind:isFluid(a)?'pump':'syringe',drip:false,t0:x.t,end:x.t+D,total:D});
    }
    return out;
  }
  function svgFor(it,t){
    const lab=esc(label(it.id));
    if(it.kind==='syringe') return mvSyringe(lab,(t-it.t0)/it.total);
    if(it.drip){
      const counting=it.onset!=null&&t<it.onset;
      return mvPump(lab,counting?mmss(Math.max(0,Math.ceil(it.onset-t))):'ON',0.8);
    }
    return mvPump(lab,mmss(Math.max(0,Math.ceil(it.end-t))),Math.max(0.05,1-(t-it.t0)/it.total));
  }
  function clear(){ if(host) host.innerHTML=''; els={}; }
  function place(){
    const stage=el('patientstage'), fig=el('patientfig'); if(!stage||!fig||!host) return;
    const s=stage.getBoundingClientRect(), f=fig.getBoundingClientRect();
    /* Just above the hair: the drawing has a margin of empty space above the head, so the
       row sits a little way into it. Never above the stage. */
    const bottom=Math.max(0,Math.min(s.height-24,s.bottom-f.top-f.height*0.06));
    host.style.bottom=bottom+'px';
    host.style.maxHeight=Math.max(0,s.height-bottom-6)+'px';
  }
  function retire(n,key,flash){
    n.dataset.finishing='1';
    if(flash) n.classList.add('done');
    setTimeout(()=>{ n.classList.add('gone'); },flash?1100:0);
    setTimeout(()=>{ n.remove(); if(els[key]===n) delete els[key]; done.add(key); },flash?1550:450);
  }
  function update(){
    if(!host){ const st=el('patientstage'); if(!st) return; host=document.createElement('div');
      host.className='medvis'; host.setAttribute('aria-hidden','true'); st.appendChild(host); }
    if(!ST||!inCase()||!on()){ if(Object.keys(els).length) clear(); return; }
    if(run!==RUNID){ run=RUNID; done=new Set(); clear(); }
    place();
    const t=now(), live=new Set();
    for(const it of items(t)){
      if(done.has(it.key)) continue;
      const finished=it.end!=null&&t>=it.end;
      if(finished&&!els[it.key]&&t-it.end>3){ done.add(it.key); continue; }   /* long over, e.g. a skipped clock */
      live.add(it.key);
      let n=els[it.key];
      if(!n){ n=document.createElement('div'); n.className='mv'; n.dataset.key=it.key; host.appendChild(n); els[it.key]=n;
        /* A drip whose onset is already well past when it is first drawn does not flash. */
        if(it.drip&&it.onset!=null&&t-it.onset>3) n.dataset.arrived='1'; }
      if(n.dataset.finishing) continue;
      n.innerHTML=svgFor(it,finished?it.end:t)+(it.kind==='syringe'
        ?`<div class="mv-t">${mmss(finished?0:Math.max(0,Math.ceil(it.end-t)))}</div>`:'');
      if(it.drip){
        if(it.onset!=null&&t>=it.onset&&!n.dataset.arrived){
          n.dataset.arrived='1'; n.classList.add('arrived');
          setTimeout(()=>n.classList.remove('arrived'),1150);
        }
        if(finished) retire(n,it.key,false);       /* stopped: it shrinks away */
      } else if(finished) retire(n,it.key,true);   /* acting: flash green, then go */
    }
    for(const k in els) if(!live.has(k)&&!els[k].dataset.finishing){ els[k].remove(); delete els[k]; }
  }
  setInterval(update,200);
  return {update, items:()=>ST?items(now()):[]};
})();

/* ---------- boot ----------
   Nothing is bound until a case is chosen, and the clock does not start until Begin.
   With a single case the picker is skipped, because choosing from a list of one is a
   step that teaches nothing. */
/* ---------- day and night (author instruction, 28 October 2026) ----------
   The head of the page sets data-theme before anything is drawn. This keeps the switches in
   step with it: on the case board, on the welcome page and on the rail in a case. A choice
   is remembered in this browser only (localStorage, and the page works without it). Until
   one is made, the theme follows the device's setting, live. Nothing about a case changes:
   the monitor, the timings and the scores are the same in both. */
const THEME=(function(){
  const KEY='emsim.theme', root=document.documentElement;
  const mq=window.matchMedia?matchMedia('(prefers-color-scheme: dark)'):null;
  const stored=()=>{ try{ const v=localStorage.getItem(KEY); return (v==='day'||v==='night')?v:null; }catch(e){ return null; } };
  const current=()=>root.getAttribute('data-theme')==='night'?'night':'day';
  const SUN='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M5.5 18.5l1.7-1.7M16.8 7.2l1.7-1.7"/></svg>';
  const MOON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6z"/></svg>';
  function paint(){
    const night=current()==='night';
    document.querySelectorAll('[data-themetoggle]').forEach(b=>{
      const lab=night?'Switch to day':'Switch to night';
      b.setAttribute('aria-label',lab); b.title=lab;
      b.innerHTML=(night?SUN:MOON)+(b.dataset.themetoggle==='label'?'<span class="lb">'+(night?'Day':'Night')+'</span>':'');
    });
    const mc=document.querySelector('meta[name="theme-color"]'); if(mc) mc.setAttribute('content',night?'#0D161C':'#E7EDF1');
  }
  let animT=0;
  function set(t,save){
    root.classList.add('theme-anim'); clearTimeout(animT);
    animT=setTimeout(()=>root.classList.remove('theme-anim'),450);
    root.setAttribute('data-theme',t);
    if(save){ try{ localStorage.setItem(KEY,t); }catch(e){} }
    paint();
  }
  /* The rail's switch sits on top of Main menu, whose height depends on its label. */
  function fitRail(){
    const m=document.getElementById('railmenu');
    if(m&&m.offsetHeight) root.style.setProperty('--railmenu-h',m.offsetHeight+'px');
  }
  function bind(){
    document.querySelectorAll('[data-themetoggle]').forEach(b=>b.addEventListener('click',e=>{
      e.stopPropagation();
      set(current()==='night'?'day':'night',true);
      AN.track('theme_changed',{theme:current()});
    }));
    if(mq){ const f=e=>{ if(!stored()) set(e.matches?'night':'day',false); };
      if(mq.addEventListener) mq.addEventListener('change',f); else if(mq.addListener) mq.addListener(f); }
    window.addEventListener('resize',fitRail);
    paint(); fitRail();
  }
  return {bind, current, set, fitRail};
})();

function boot(){
  THEME.bind();
  ACCESS_UI.init();
  /* The first case that is actually here. In the deployed build every case may be a locked
     stub, and then nothing is bound until one is fetched: begin() renders everything once
     a case is chosen, so the first-render calls below are only for a build that has one. */
  const first=CASES.findIndex(c=>!c.locked);
  if(CASES.length===1&&first===0){
    chooseCase(0);
    el('picker').classList.add('hidden');
    const back=el('backtopicker'); if(back) back.style.display='none';
  } else {
    if(first>=0){ selectCase(first); bindCase(); }   // bind something so the first render has data
    renderPicker();
  }
  setPanels(true,false);
  VOICE.bind();
  if(CASE){ refold(); renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor(); }
}
boot();
