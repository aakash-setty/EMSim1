/* ============================================================
   UI. Everything below renders derived state; nothing stores it.
   ============================================================ */
let LOG=[], SEQ=0, T0=Date.now(), ST=null, TAB='history', ENDED=false;
/* v0.9: `diagnoses` is an ordered list and its first entry is the primary. The
   singular is filled in at submit for readers written before the list existed. */
let PENDING_HANDOFF={disposition:null,diagnoses:[]};
let LASTNURSE=-1, LASTPHASE=null, ASKTEXT='', DXTEXT='';
/* Filter text and the pending order basket are per tab, so switching tabs and
   coming back leaves both exactly as they were. */
const FILTERS={}, BASKET={};
/* Expanded state for collapsible groups, per tab, so leaving and returning to a tab
   leaves the accordion exactly as it was. */
const EXPANDED={};
/* Seeded once per tab from SHARED.defaultExpanded, then left alone. A learner who
   collapses a group that opened by default keeps it collapsed for the rest of the run,
   because the set exists from the first call and is never re-seeded. */
const expandedOf = t => (EXPANDED[t]=EXPANDED[t]
  || new Set(((PROTO&&PROTO.defaultExpanded)||{})[t]||[]));
let MODE='easy', STARTED=false;
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
    const lbl=RIGHT_WIDE?'Minimise the chart':'Expand the chart';
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
const filterOf = t => FILTERS[t]||'';
const basketOf = t => (BASKET[t]=BASKET[t]||new Set());

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
function log(e){ e.seq=SEQ++; e.t=now(); LOG.push(e); refold(); }
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
  /* The header carries the full monitor at every panel state, so vitals are
     never occluded. The expanded record panel additionally carries a compact
     copy in its own header, because a resident reading two columns of chart at
     70% width should not have to look back up to the top of the window. */
  const mini=el('rp-mini');
  if(mini) mini.innerHTML = RIGHT_WIDE
    ? cells.map(c=>`<span class="m"><span class="k">${c[0]}</span><b class="v-${c[3]}">${c[1]}</b></span>`).join('')
      + `<span class="m"><span class="k">elapsed</span><b>${mmss(ST.now)}</b></span>`
    : '';
  el('monitor').innerHTML = cells.map(c=>
    `<div class="vit"><div class="vitlab">${c[0]}</div>
     <div class="vitval v-${c[3]}">${c[1]}</div><div class="vitunit">${c[2]}</div></div>`).join('')
    + `<div class="clockbox"><div class="vitlab">elapsed</div>
       <div class="clock">${mmss(ST.now)}</div>
       <div class="phasechip">${esc(PROTO.phaseShort[ST.phase]||ST.phase)}</div>
       <div class="phasechip">${esc(PROTO.difficulty.modes[MODE].label)}</div></div>`;
  if(LASTPHASE!==null && LASTPHASE!==ST.phase) el('monitor').animate?.([{opacity:.35},{opacity:1}],{duration:420});
  LASTPHASE=ST.phase;
  /* The trace is decorative: its path does not encode rate, and the argument is
     only a cache key. Feed it the phase's authored rate rather than the ramping
     one so it redraws on a phase change instead of on every frame for five
     seconds. */
  renderTrace(on&&p&&p.vitals?p.vitals.heart_rate:undefined, p?p.rhythm:undefined);
  renderSound();
  AUDIO.sync();
}
/* Deterministic pseudo-random, so a redraw of the same phase produces the same
   picture. Math.random() here would make the trace shimmer on every render, which
   would read as a fault rather than as a rhythm. */
function traceRand(seed){
  let x=seed>>>0||1;
  return ()=>{ x^=x<<13; x>>>=0; x^=x>>17; x^=x<<5; x>>>=0; return x/4294967296; };
}
function renderTrace(hr, rhythm){
  const svg=el('trace');
  if(typeof hr!=='number'){ svg.innerHTML=''; svg.dataset.hr=''; return; }
  const key=String(hr)+'|'+(rhythm||'regular');
  if(svg.dataset.hr===key) return;
  svg.dataset.hr=key;
  const beats=6, w=420; let d='';
  if(rhythm==='irregularly_irregular'){
    /* Two things separate this from the regular trace and both are the finding rather
       than decoration: the complexes are unevenly spaced, and there is no P wave. The
       spacing is drawn from the same shifted-exponential shape the audio uses and then
       normalised to the width, so the picture and the sound tell the same story without
       either importing the other's code. The complex itself keeps a fixed width and the
       baseline between complexes absorbs the difference, because a long R-R interval
       lengthens diastole and does not widen the QRS. Still decorative: the six beats on
       screen are not the six beats you are hearing. */
    const rnd=traceRand(Math.round(hr)*2654435761);
    const raw=[]; for(let b=0;b<beats;b++) raw.push(0.62+0.38*(-Math.log(1-rnd())));
    const tot=raw.reduce((a,c)=>a+c,0);
    const cw=32;                       /* complex width in pixels, fixed */
    let x=0;
    for(let b=0;b<beats;b++){
      const seg=w*raw[b]/tot, flat=Math.max(4,seg-cw), c=x+flat;
      d+=`M${x} 14 L${c} 14 `
       + `L${c+cw*0.10} 17 L${c+cw*0.22} 2 L${c+cw*0.34} 20 L${c+cw*0.46} 14 `
       + `L${c+cw*0.62} 14 L${c+cw*0.78} 9 L${c+cw*0.94} 14 L${x+seg} 14 `;
      x+=seg;
    }
  } else {
    /* Unchanged, so the two cases written before a rhythm existed draw exactly what
       they drew before. The complex scales with the segment here, which a fixed-width
       one would not, and there is no reason to redraw a picture nobody complained
       about. */
    const seg=w/beats;
    for(let b=0;b<beats;b++){
      const x=b*seg;
      d+=`M${x} 14 L${x+seg*0.30} 14 L${x+seg*0.36} 11 L${x+seg*0.42} 14 `
       + `L${x+seg*0.47} 17 L${x+seg*0.52} 2 L${x+seg*0.57} 20 L${x+seg*0.62} 14 `
       + `L${x+seg*0.78} 14 L${x+seg*0.84} 9 L${x+seg*0.90} 14 L${x+seg} 14 `;
    }
  }
  svg.innerHTML=`<path d="${d}" fill="none" stroke="var(--hr)" stroke-width="1.3"/>`;
}
function renderSound(){
  const b=el('soundbtn'); if(!b) return;
  /* Four states, not three. Sound can be on and the room still be silent, because the
     heartbeat is the monitor's and there is no monitor yet. Saying "Sound on" over
     silence reads as a fault, so the button says which of the two is missing. */
  b.textContent = AUDIO.running
    ? (ST&&ST.monitoring ? 'Sound on' : 'Sound on, no monitor')
    : (AUDIO.enabled ? 'Enable sound' : 'Sound off');
  b.setAttribute('aria-pressed', AUDIO.running?'true':'false');

}

/* ---------- nurse ---------- */
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
    const isStudy=catOf(x.id)==='investigation';
    add({t:x.t,kind:x.tag==='harmful'?'harm':(isStudy?'order':'action'),
         name:isStudy?('Ordered: '+x.label):x.label});
  }
  for(const r of ST.readouts){
    if(r.kind==='exam')    add({t:r.t,kind:'exam',name:r.title,payload:r.body});
    if(r.kind==='consult') add({t:r.t,kind:'consult',name:r.title,body:r.body});
    /* An unmatched question is answered by the case's out_of_scope_fallback: the
       patient says they do not understand. That is feedback on the phrasing, not a
       finding, and a chart is a record of what was learned about the patient. It stays
       on the History tab, where the resident can see which of their questions did not
       land, and it does not go in the chart. r.matched is the topic the matcher chose,
       and is null exactly when the fallback answered. */
    if(r.kind==='speech'&&r.matched) add({t:r.t,kind:'speech',name:r.title,body:r.body});
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
  Object.keys(ST.orders).forEach(id=>ST.orders[id].forEach(o=>{
    if(o.value===null) return;                      /* still pending, lives in the rail above */
    add({t:o.dueT,kind:catOf(id)==='investigation'?'lab':'imaging',
         name:dispName(id),payload:o.value});
  }));
  out.sort((a,b)=>b.t-a.t||b.seq-a.seq);
  return out;
}

/* ---------- results that are a picture ----------
   A twelve-lead tracing is not prose and a case may author it as the image itself, with no
   report text at all: the reading is the skill, and a payload that hands the resident "QRS
   132 ms" beside the tracing has done the reading for them. DIPH authors three that way.

   The media map is per case and lives on PROTO, keyed by the file stem, so a case that
   ships no images costs nothing here and a payload naming a missing one degrades to a line
   of text rather than to a broken image icon. The validator catches that case before it
   ever ships; this is the runtime half of the same guarantee. */
function imageSrc(id){ return (PROTO.media||{})[id]||null; }

function imageThumb(v){
  const src=imageSrc(v.image);
  const cap=v.caption||'Image';
  if(!src) return `<div class="fb">${esc(cap)} (image ${esc(v.image||'?')} is not in this build)</div>`;
  /* A button rather than a div, so it is reachable by keyboard and announces itself. The
     data attributes are read by the delegated click handler; the src is inlined because
     every image in the build is already a data URI. */
  return `<button type="button" class="imgthumb" data-img="${esc(v.image)}"
            data-cap="${esc(cap)}" title="${esc(cap)} - click to open">
            <img src="${src}" alt="${esc(cap)}" loading="lazy">
          </button><p class="imgcap">${esc(cap)}. Click to open.</p>`;
}

function feedPayload(v){
  if(!v||typeof v!=='object') return v?`<div class="fb">${esc(v)}</div>`:'';
  if(v.kind==='image') return imageThumb(v);
  if(v.components&&v.components.length)
    return '<table>'+v.components.map(c=>
      `<tr><td class="lb">${esc(c.label)}</td>
           <td class="vl${c.abnormal?' abn':''}">${esc(c.value)}${c.unit?' '+esc(c.unit):''}</td></tr>`
    ).join('')+'</table>';
  const txt=v.report||v.findings||v.value||'';
  return txt?`<div class="fb${v.abnormal?' abn':''}">${esc(txt)}</div>`:'';
}

let FEED_N=-1;
function renderFeed(){
  const items=feedItems();
  el('feedcount').textContent = items.length ? items.length : '';
  el('feed').innerHTML = items.length ? items.map(i=>
    `<div class="fitem k-${i.kind}${(i.payload&&i.payload.abnormal)?' abnormal':''}">
       <div class="fh"><span class="ft">${mmss(i.t)}</span><span class="fn">${esc(i.name)}</span></div>
       ${i.payload!==undefined?feedPayload(i.payload):(i.body?`<div class="fb">${esc(i.body)}</div>`:'')}
     </div>`).join('')
    : '<div class="emptyline">Nothing yet.</div>';
  /* Follow the newest entry only when something has actually been added, so a reader
     scrolled down through earlier results is not yanked back every tick. The newest
     entry is now at the TOP, so following it means scrolling to zero rather than to the
     full height. */
  if(items.length!==FEED_N){
    FEED_N=items.length;
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
    return `<button class="tabbtn" role="tab" aria-selected="${id===TAB&&LEFT_OPEN}" data-tab="${id}"
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
  for(const id in ACT){
    const a=ACT[id];
    if(a.tab!==tab) continue;
    if(f && !(a.name.toLowerCase().includes(f)||id.includes(f))) continue;
    for(const g of (a.groups||[a.group])) (out[g]=out[g]||[]).push(id);
  }
  Object.keys(out).forEach(g=>out[g].sort((x,y)=>ACT[x].name.localeCompare(ACT[y].name)));
  return out;
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
function actionButton(id,tab){
  const a=ACT[id];
  const orders=ST.orders[id]||[];
  const last=orders[orders.length-1];
  let cls='ab';
  if(IS_STUDY(id)){
    if(last&&last.value===null) cls+=' pend';
    else if(last) cls+=' hasres';
  } else if(ST.taken.has(id)) cls+=' done';
  if(a.orphan) cls+=' orphan';
  if(tab&&basketOf(tab).has(id)) cls+=' picked';
  return `<button class="${cls}" data-act="${id}" data-tabof="${tab||''}">${esc(a.name)}</button>`;
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
    const picked=groups[g].filter(id=>basketOf(tab).has(id)).length;
    if(collapsible){
      const isOpen=forced||open.has(g);
      html+=`<button class="grouphdr" data-group="${esc(g)}" data-tabof="${tab}"
        aria-expanded="${isOpen}"><span class="chev">${isOpen?'\u25BC':'\u25B6'}</span>
        <span>${esc(g)}</span>
        ${picked?`<span class="picks">${picked} selected</span>`:''}
        <span class="n">${groups[g].length}</span></button>`;
      if(!isOpen) continue;
      html+='<div class="groupbody">';
    } else {
      html+=`<h3>${esc(g)}</h3>`;
    }
    if(g==='Not in the catalog')
      html+=`<div class="note" style="border-left-color:var(--harm)">${esc(PROTO.orphanNote)}</div>`;
    html+=`<div class="grid">${groups[g].map(id=>actionButton(id,tab)).join('')}</div>`;
    if(collapsible) html+='</div>';
  }
  if(!names.length) html='<p class="sub">Nothing matches that filter.</p>';
  const orderable=PROTO.orderableTabs.includes(tab);
  const basket=[...basketOf(tab)];
  return `<div class="panel"><h2>${esc(PROTO.tabLabel[tab])}</h2>
    <p class="sub">${intro}</p>
    <div class="toolbar">
      <span class="searchwrap">
        <input type="text" id="filterbox" class="filter" placeholder="Filter this tab"
          value="${esc(filterOf(tab))}" data-tabof="${tab}">
        ${filterOf(tab)?`<button class="clearfilter" id="clearfilter" data-tabof="${tab}"
          title="Clear the filter" aria-label="Clear the filter">\u00D7</button>`:''}
      </span>
      ${orderable?`<button class="btn" id="submitorder" data-tabof="${tab}" ${basket.length?'':'disabled'}>
          Submit Order${basket.length?' ('+basket.length+')':''}</button>
        <button class="btn ghost" id="clearorder" data-tabof="${tab}" ${basket.length?'':'disabled'}>Clear</button>`:''}
    </div>
    ${orderable?`<div class="basket${basket.length?'':' empty'}">${basket.length
        ? 'Selected, not yet sent: '+basket.map(id=>esc(dispName(id))).join(', ')+'.'
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
             +renderActionTab('exam','Repeat any manoeuvre; it returns the current state.')
             +readoutPanel('exam','Findings'),
    investigations:()=>renderActionTab('investigations',
      'A result reflects the patient at the moment it was ordered, not when it arrives.')+resultsPanel(),
    stabilization:()=>renderActionTab('stabilization','Access, airway, oxygen and monitoring.')+blockPanel(),
    interventions:()=>renderActionTab('interventions','')+blockPanel(),
    consultations:()=>renderActionTab('consultations','')
             +readoutPanel('consult','Conversations')
  };
  const active=document.activeElement, keepId=active&&active.id, keepPos=active&&active.selectionStart;
  box.innerHTML=(R[TAB]||tabHistory)();
  if(keepId==='filterbox'||keepId==='dxbox'||keepId==='askbox'){
    const back=el(keepId);
    if(back){ back.focus(); try{ back.setSelectionRange(keepPos,keepPos); }catch(e){} }
  } else if(TAB==='history'){
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
      ? `<div class="speech"><div class="who">${esc(r.title)}, ${mmss(r.t)}${r.source!=='case'?'  (catalog default)':''}</div>${esc(r.body)}</div>`
      : `<div class="read"><h4>${esc(r.title)}</h4>
         <div class="body${(r.body&&r.body.abnormal)?' abn-report':''}">${esc(
            r.body&&r.body.findings!==undefined?r.body.findings:r.body)}</div>
         <div class="meta">${mmss(r.t)}</div></div>`
  ).join('');
  return outs?`<div class="panel"><h3>${title}</h3>${outs}</div>`:'';
}
function blockPanel(){
  const blk=ST.blocked.slice(-3).reverse().map(b=>
    `<div class="blockmsg"><b>${esc(dispName(b.id))} did not happen.</b><br>${esc(b.message)}
     <div class="meta">${b.source==='catalog_default'?'catalog default prerequisite':'case prerequisite'}</div></div>`).join('');
  return blk?`<div class="panel"><h3>Recent blocks</h3>${blk}</div>`:'';
}
function resultsPanel(){
  const res=[];
  Object.keys(ST.orders).forEach(id=>ST.orders[id].forEach(o=>{ if(o.value!==null) res.push({id,o}); }));
  res.sort((a,b)=>b.o.dueT-a.o.dueT);
  if(!res.length) return '';
  return `<div class="panel"><h3>Results</h3>`+res.map(r=>`<div class="read">
      <h4>${esc(dispName(r.id))}</h4>
      ${renderPayload(r.o.value)}
      <div class="meta">ordered ${mmss(r.o.orderT)}, resulted ${mmss(r.o.dueT)},
      ${r.o.source==='case'?'authored by the case':'catalog default (normal)'}
</div>
    </div>`).join('')+'</div>';
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

function tabHistory(){
  const outs=ST.readouts.filter(r=>r.kind==='speech').slice(-10).reverse().map(r=>
    `<div class="speech"><div class="who">You asked: ${esc(r.title)}</div>${esc(r.body)}
     </div>`).join('');
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
    <p class="sub">Type a question in your own words.</p>
    <div style="display:flex;gap:8px">
      <input type="text" id="askbox" placeholder="Ask the patient something" autocomplete="off" value="${esc(ASKTEXT)}">
      <button class="btn" id="askbtn">Ask</button>
    </div>
    ${semChip()}
</div>
    ${outs?`<div class="panel"><h3>What you were told</h3>${outs}</div>`:''}`;
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
    <h3>Level of care</h3>
    ${disp.map(d=>`<button class="opt" data-disp="${d.id}" aria-pressed="${PENDING_HANDOFF.disposition===d.id}">${esc(d.label)}</button>`).join('')}
    <h3>Diagnoses</h3>
    <p class="sub">Name everything you are handing over. The first entry is your primary
    diagnosis; add as many others as apply to this patient.</p>
    ${dxs.length?`<ol class="dxlist">${dxs.map((id,i)=>`<li class="dxrow${i?'':' primary'}">
        <span class="dxrank">${i?i+1:'Primary'}</span>
        <span class="dxname">${esc(dxLabel(id))}</span>
        ${i?`<button class="dxbtn" data-dxup="${id}" title="Make this the primary diagnosis" aria-label="Make ${esc(dxLabel(id))} the primary diagnosis">Make primary</button>`:''}
        <button class="dxbtn" data-dxrm="${id}" title="Remove" aria-label="Remove ${esc(dxLabel(id))}">\u00D7</button>
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

/* ---------- interview matching (section 10.6) ---------- */
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
   which section 10.6 names as the failure mode invisible to the learner. Two
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
   runs it, per section 10.6, so that region has to stay free of anything the
   lexical matcher does not need. */
function bindCase(){
  buildMatcher();
  /* Not awaited. The case must be playable the instant it is chosen, and a
     first model load can take tens of seconds. */
  try{ SEM.init(CASE.case_id, semanticRows()); }catch(e){}
}
/* Repaint the History tab when the matcher changes state, so the line under the
   question box stops saying "improving" once it has. Nothing else depends on it. */
SEM.onChange(()=>{ if(!ENDED && TAB==='history') renderTab(); });

/* ---------- events ---------- */
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-tab],[data-act],[data-ask],[data-disp],[data-dx],[data-dxrm],[data-dxup],'
    +'#askbtn,#submitho,#earlyexit,#restart,#revealanswers,#soundbtn,#submitorder,#clearorder,#clearfilter,'
    +'[data-group],[data-mode],[data-case],#beginbtn,#backtopicker,#pickanother,'
    +'#rp-toggle,#lp-collapse');
  if(t&&t.id==='soundbtn'){ AUDIO.toggle(); renderSound(); return; }
  AUDIO.unlock();
  /* Panel controls run before the ENDED guard and before the null check: the
     record panel is a click target in its own right, and the toggle sits
     inside it, so the toggle has to be tested first or every expand would be
     followed immediately by the panel's own handler. */
  if(t&&t.id==='rp-toggle'){ RIGHT_WIDE?minimiseRecord():expandRecord(); return; }
  if(t&&t.id==='lp-collapse'){ setPanels(false,RIGHT_WIDE); renderTabs(); return; }
  if(!RIGHT_WIDE && !ENDED && e.target.closest('#rightpanel')){
    expandRecord(); renderTabs(); return;
  }
  /* The expanded record leaves the room showing to its left. A click on that
     background is the same gesture as the minimise button in the record's corner:
     the reader is done with the chart. Anything that is itself a control (the rail,
     the header, an overlay, the record) keeps its own behaviour. */
  if(RIGHT_WIDE && !ENDED && !e.target.closest(
       '#rightpanel,#tabbar,#leftpanel,header,#endview,#pauseview,#leaveview,#picker,#splash,button,a,input')){
    minimiseRecord(); return;
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
  if(t.dataset.act){
    const id=t.dataset.act, tabof=t.dataset.tabof;
    if(id.indexOf('interview_topic_')===0){
      const tid=id.slice(16);
      const tp=CASE.interview.topics.find(x=>x.topic===tid);
      ask(tp?tp.canonical:tid.replace(/_/g,' ')); return;
    }
    /* On an orderable tab a click selects; nothing is sent until Submit Order. */
    if(tabof&&PROTO.orderableTabs.includes(tabof)){
      const bag=basketOf(tabof);
      bag.has(id)?bag.delete(id):bag.add(id);
      renderTab(); return;
    }
    log({actionId:id}); render(); return;
  }
  if(t.dataset.case){ chooseCase(Number(t.dataset.case)); return; }
  if(t.id==='backtopicker'){ backToPicker(); return; }
  if(t.dataset.mode){ MODE=t.dataset.mode; renderSplash(); return; }
  if(t.id==='beginbtn'){ begin(); return; }
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
  if(t.id==='clearorder'){ basketOf(t.dataset.tabof).clear(); renderTab(); return; }
  if(t.id==='submitorder'){
    const tabof=t.dataset.tabof, bag=basketOf(tabof);
    /* Submit in the order they were picked. Each is a separate log entry at the same
       instant, so the fold applies them in sequence and prerequisites, transitions and
       harmful tags all evaluate exactly as they would one at a time. */
    for(const id of [...bag]) log({actionId:id});
    bag.clear();
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
    const list=PENDING_HANDOFF.diagnoses.slice();
    log({actionId:'handoff_submit',payload:{disposition:PENDING_HANDOFF.disposition,
         diagnosis:list[0]||null,diagnoses:list}});
    finish(); return;
  }
  if(t.id==='earlyexit'){ log({actionId:'early_exit',kind:'early_exit'}); finish(); return; }
  if(t.id==='restart'){ restart(); return; }
  if(t.id==='revealanswers'){ revealAnswers(); return; }
  if(t.id==='pickanother'){ toPickerFromDebrief(); return; }
});
document.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&e.target.id==='askbox'&&e.target.value.trim()) ask(e.target.value.trim());
});
document.addEventListener('input',e=>{
  if(e.target.id==='askbox'){ ASKTEXT=e.target.value; return; }
  if(e.target.id==='filterbox'){
    FILTERS[e.target.dataset.tabof||TAB]=e.target.value.toLowerCase().trim();
    renderTab(); return;
  }
  if(e.target.id==='dxbox'){
    DXTEXT=e.target.value;
    const q=e.target.value.toLowerCase().trim();
    const hits=q.length<2?[]:PROTO.diagnoses.filter(d=>
      !PENDING_HANDOFF.diagnoses.includes(d.id)&&
      (d.label.toLowerCase().includes(q)||d.syn.some(s=>s.toLowerCase().includes(q)))).slice(0,10);
    el('dxhits').innerHTML=hits.length?`<div class="hits">${hits.map(d=>
      `<button class="hit" data-dx="${d.id}">${esc(d.label)}${d.syn.length?`<span class="syn">${esc(d.syn.join(', '))}</span>`:''}</button>`).join('')}</div>`:'';
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
  ASKTEXT=''; const b=el('askbox'); if(b) b.value='';
  let ms;
  try{ ms=await matchQuestion(q); }
  catch(e){ const l=matchTopic(q); ms=[{topic:l.topic,score:l.score,matcher:'lexical',q}]; }
  finally{ ASKING=false; }
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
  }
  renderMonitor(); renderNurse(); renderRail();
  requestAnimationFrame(tick);
}
function render(){
  refold();
  if(ST.halted&&!ENDED){ finish(); return; }
  renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor();
}
/* Rebuild the tab only when something the tab shows has actually changed. A nurse
   line or a prompt does not change the action grid, and rebuilding it can swallow a
   click the user has already started. */
const tabFingerprint=()=>ST?ST.resulted.size+':'+ST.pending.length+':'+ST.blocked.length
                            +':'+ST.readouts.length+':'+ST.phase:'';
setInterval(()=>{
  if(ENDED) return;
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

function gateHTML(){
  const kind=endingKind();
  const done=[...ST.expected].filter(id=>ST.satisfied.has(id));
  const dispExp=id=>((ACT[id]||{}).expectation_label)||dispName(id);
  /* Names only. No pill, no expander, no teaching note: a note attached to a completed
     action is still an answer, and this screen is deliberately not the answer key. */
  return `<div class="dbf">
    <div class="dbsec gate">
      <h2 class="gatetitle ${kind==='all'?'g-ok':'g-bad'}">${esc(GATE_TITLE[kind])}</h2>
      ${ST.failed&&ST.failed.reason?`<p class="sub">${esc(ST.failed.reason)}</p>`:''}
      ${ST.halted&&ST.halted.reason?`<p class="sub">${esc(ST.halted.reason)}</p>`:''}
      <h3 class="gatesub">Critical actions you completed</h3>
      ${done.length
        ? `<div class="gatelist">${done.map(id=>
            `<div class="gitem">${esc(dispExp(id))}</div>`).join('')}</div>`
        : `<p class="sub">None of this case's critical actions were completed.</p>`}
      <div class="gatebtns">
        <button class="btn" id="restart">Replay this case</button>
        <button class="btn ghost" id="revealanswers">Reveal Case Answers</button>
        ${CASES.length>1?'<button class="btn ghost" id="pickanother">Choose a different case</button>':''}
      </div>
    </div>
  </div>`;
}

function revealAnswers(){
  REVEALED=true;
  const v=el('endview');
  v.innerHTML='<div class="endwrap">'
    +(ST.halted?haltCard():'')+(ST.failed?failCard():'')+debriefHTML()+'</div>';
  v.scrollTop=0;
}

/* The clock's equivalent of haltCard. A harmful action names itself; a terminal phase
   reached by the clock has no action to name, so the phase's own timeout_reason is the
   whole explanation and it is authored for exactly this. A terminal phase reached by an
   instantaneous transition does have an action to name, and the action's own debrief note
   names it; the phase's timeout_reason then has to be true of both routes, which is a
   constraint on the case rather than on this card. */
function failCard(){
  return `<div class="halt"><h2>The case ended here</h2>
    <p><b>${esc(PHASE[ST.failed.phase].label||ST.failed.phase)}</b> at ${mmss(ST.failed.t)}.</p>
    ${ST.failed.reason?`<p>${esc(ST.failed.reason)}</p>`:''}
    <p style="color:var(--ink2);font-size:13.5px">Nothing you did before this is lost.
    It is all below.</p></div>`;
}

function finish(){
  /* The room goes quiet with the case. A debrief is reading rather than resuscitating,
     and ambience still humming under it is the interface not noticing the case is over.
     setScene('idle') stops the heartbeat and the room together. */
  refold(); ENDED=true; AUDIO.setScene('idle');
  /* Neither overlay belongs over a debrief. The case is over, so there is nothing to
     resume and nothing left to lose by leaving. */
  el('pauseview').classList.add('hidden'); closeLeave(); PAUSED=false;
  el('playview').classList.add('hidden');
  const v=el('endview'); v.classList.remove('hidden');
  REVEALED=false;
  v.innerHTML='<div class="endwrap">'+gateHTML()+'</div>';
  v.scrollTop=0;
}
function restart(){
  LOG=[];SEQ=0;ENDED=false;STARTED=false;TAB='history';LASTNURSE=-1;LASTPHASE=null;
  closeImage(); IMG_SEEN=new Set(); IMG_QUEUE=[];
  resetRamp();
  Object.keys(FILTERS).forEach(k=>delete FILTERS[k]);
  Object.keys(BASKET).forEach(k=>delete BASKET[k]);
  Object.keys(EXPANDED).forEach(k=>delete EXPANDED[k]);
  PENDING_HANDOFF={disposition:null,diagnoses:[]};
  PAUSED=false; PAUSED_MS=0; PAUSED_AT=0;
  el('pauseview').classList.add('hidden'); closeLeave();
  AUDIO.setScene('idle');
  el('endview').classList.add('hidden'); el('playview').classList.remove('hidden');
  el('splash').classList.remove('hidden');
  setPanels(true,false);
  renderSplash(); refold(); renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor();
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
function debriefHTML(){
  const done=[],omit=[];
  /* `satisfied`, so a critical action performed through a coverage group is not
     reported as missed. The action grid still reads `taken`, so only the button that
     was actually pressed is drawn as used. */
  ST.expected.forEach(id=>{ (ST.satisfied.has(id)?done:omit).push(id); });
  const rec=[...ST.recommendedTaken];
  const dis=[...ST.discouragedTaken];
  const traps=ST.timeline.filter(x=>x.tag==='neutral'&&PROTO.traps.includes(x.id));
  const stillPending=ST.pending.map(p=>p.id);
  const noteOf=id=>(ACT[id]||{}).debrief_note;
  /* References carry a verification marker in the case file, for example
     "[PubMed record checked]" or "[UNVERIFIED, confirm before release]". That is a note
     to the reviewing physician, not to the learner, and it stays in the case file and the
     review packet rather than being printed in the debrief. */
  const refsOf=id=>((ACT[id]||{}).references||[])
    .map(r=>r.replace(/\s*\[[^\]]*\]\s*$/,'').trim());
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
    return `<div class="item"><details class="teach">
      <summary class="hd">${head}<span class="expand">Why</span></summary>
      ${note?`<div class="note" style="background:none;border:0;padding:0;margin:8px 0 0">${esc(note)}</div>`:''}
      ${refs.length?`<div class="refs">${refs.map(esc).join('<br>')}</div>`:''}
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
                appropriate:['appropriate','p-ok'],defensible:['defensible','p-warn'],unsupported:['not supported','p-harm']};
    const dxItem=(label,pill,why)=>`<div class="item"><div class="hd"><span class="nm">${esc(label)}</span>
        <span class="pill ${pill[1]}">${esc(pill[0])}</span></div>
        ${why?`<div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(why)}</div>`:''}</div>`;
    const named=dx.rows.some(r=>r.verdict==='primary_correct'||r.verdict==='main_not_primary');
    ho=`<div class="dbsec"><h2>Handoff</h2>
      <div class="item"><div class="hd"><span class="nm">Level of care: ${esc(dispLabel(dId))}</span>
        <span class="pill ${dV[1]}">${dV[0]}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(dExp)}</div></div>
      <h3>Diagnoses you handed over</h3>
      ${dx.rows.map((r,i)=>dxItem((i?'':'Primary: ')+dxLabel(r.id),PILL[r.verdict]||['','p-neu'],r.why)).join('')}
      ${dx.missed.length?'<h3>Also true of this patient, and not named</h3>'
        +dx.missed.map(m=>dxItem(dxLabel(m.id),['not named','p-warn'],m.why)).join(''):''}
      ${named?'':dxItem('The case\'s diagnosis: '+dxLabel(PROTO.correctDxId),['answer','p-neu'],PROTO.correctDxExplanation)}
      </div>`;
  } else if(ST.earlyExit){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>You ended the case early, so this debrief is marked incomplete.</p></div>`;
  } else if(ST.halted){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>The case halted before a handoff.</p></div>`;
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

  /* Critical actions lead. They are what the case is about, and a resident reading top
     to bottom should meet the medicine before the scoreboard. */
  return `<div class="dbf">
    ${ST.halted?`<div class="dbsec"><h2>Harmful action</h2>${item(ST.halted.id,'harmful','p-harm')}</div>`:''}

    <div class="dbsec"><h2 class="crith">Critical actions</h2>
      ${done.length?done.map(id=>item(id,'critical','p-crit',dispExp(id))).join(''):'<p>No critical action was completed.</p>'}
      ${omit.length?'<h3 class="misshd">Non-Critical Missed Actions</h3>'+omit.map(id=>item(id,'not done','p-harm',dispExp(id))).join(''):''}
      ${[...ST.fuOutstanding].length?'<h3>Follow-up obligations left open</h3>'+[...ST.fuOutstanding].map(fid=>
        `<div class="item"><div class="hd"><span class="nm">${esc(fid.replace(/_/g,' '))}</span>
        <span class="pill p-harm">not done</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(FU[fid].debrief_note)}</div></div>`).join(''):''}</div>

    ${rec.length?`<div class="dbsec"><h2>Also worth doing</h2>
      ${rec.map(id=>item(id,'recommended','p-ok')).join('')}</div>`:''}

    ${dis.length?`<div class="dbsec"><h2>Wrong here, and worth understanding why</h2>
      <p class="sub">These did not stop the case and some of them will have moved a number
      in the direction you wanted. Being wrong is not the same as being dangerous, and a
      drug that produces the effect you asked for can still be the wrong drug for the
      disease underneath it.</p>
      ${dis.map(id=>item(id,'discouraged','p-warn')).join('')}</div>`:''}

    <div class="dbsec"><h2>Summary</h2>
      <p class="sub">${ST.halted?'Halted':(ST.failed?(ST.failed.byClock?'Ended by the clock':'Ended by an action'):(ST.earlyExit?'Ended early, incomplete':'Completed'))} at ${mmss(ST.now)},
      in ${esc(PROTO.difficulty.modes[MODE].label.toLowerCase())}${DM()!==1?`, so nurse prompts were ${DM()} times later than the authored deadlines`:''}.
      Points direct review; they do not rank you. Critical actions count two, recommended
      actions one, a discouraged action costs one, and a harmful action zeroes its tab.</p>
      <table class="score"><tr><th>Category</th><th class="n">Score</th><th class="n">Points</th><th>Detail</th></tr>${scoreRows}</table>
      <div style="margin-top:16px"><button class="btn" id="restart">Replay this case</button>
      ${CASES.length>1?'<button class="btn ghost" id="pickanother" style="margin-left:8px">Choose a different case</button>':''}</div></div>

    ${traps.length?`<div class="dbsec"><h2>Things that looked reasonable and were not</h2>
      ${traps.map(x=>item(x.id,'no benefit here','p-neu')).join('')}
      </div>`:''}

    ${ho}

    ${read.length?`<div class="dbsec"><h2>Your results, read</h2>
      <p class="sub">While the case ran you saw the numbers and nothing else. This is the
      case's own reading of each panel you ordered, in the order they came back.</p>
      ${read.map(r=>`<div class="item"><div class="hd"><span class="nm">${esc(dispName(r.id))}</span>
        <span class="pill p-neu">${mmss(r.o.dueT)}</span></div>
        ${renderPayload(r.o.value)}
        <div class="note" style="background:none;border:0;padding:0;margin:6px 0 0">${esc(r.o.value.comment)}</div></div>`).join('')}</div>`:''}

    ${defaults.length?`<div class="dbsec"><h2>Answered by a default, not by the case</h2>
      <p class="sub">These returned the catalog's normal result or the global response because this case
      authors nothing for them. A normal default is not a neutral default: if an author forgets a study
      that matters, the learner is shown normal and taught the wrong thing.</p>
      <p>${defaults.map(d=>esc(dispName(d))).join(', ')}.</p></div>`:''}

    ${stillPending.length?`<div class="dbsec"><h2>Results you did not read</h2>
      ${stillPending.length?`<p>Still pending when the case ended: ${stillPending.map(i=>esc(dispName(i))).join(', ')}.</p>`:''}
      <p class="sub">Handing over with a result you never looked at is a real handover failure.</p></div>`:''}

    <div class="dbsec"><h2>Points to carry out of this case</h2>
      ${(CASE.debrief_configuration.cross_cutting_teaching_points||[]).map(p=>
        `<div class="item"><div class="note" style="background:none;border:0;padding:0;margin:0">${esc(typeof p==='string'?p:p.point||'')}</div></div>`).join('')}</div>

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
    const k=c.card||{}, p=(c.case&&c.case.patient)||{};
    /* "medical student, intern, junior resident" is a range and reads better as one */
    const lvs=(Array.isArray(k.target_level)?k.target_level:[k.target_level||''])
      .filter(Boolean).map(x=>String(x).replace(/_/g,' '));
    const lv=lvs.length>2 ? lvs[0]+' to '+lvs[lvs.length-1] : lvs.join(' and ');
    return {i, prefix:c.prefix,
      complaint:k.complaint||k.title||c.prefix,
      age:p.age, sex:(p.sex||'').toLowerCase(),
      category:k.category||'Cases',
      level:lv.charAt(0).toUpperCase()+lv.slice(1),
      mins:k.runtime_seconds?Math.round(k.runtime_seconds/60):null,
      unreviewed:k.unreviewed!==false,
      broken:(c.buildNotes||[]).length};
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
  const hits=m.filter(c=>{
    if(WL_FILTER!=='all'&&c.category!==WL_FILTER) return false;
    if(!q) return true;
    const hay=[c.complaint,c.category,c.level,String(c.age),WL_SHORT[c.sex]||'',c.sex,c.prefix]
      .join(' ').toLowerCase();
    return q.split(/\s+/).every(t=>hay.includes(t));
  });
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
      const aria=[c.complaint,
                  (WL_LABEL[c.sex]||'Patient')+', '+(c.age!==undefined?c.age+' years old':'age not recorded'),
                  c.category,c.level,c.mins?'about '+c.mins+' minutes':'',
                  c.unreviewed?'Unsigned draft.':'Reviewed.',
                  c.broken?'Incomplete: '+c.broken+' build problems, this case will not run correctly.':''
                 ].filter(Boolean).join('. ');
      html+=`<button class="wl-case" type="button" role="option" data-case="${c.i}"
        data-row="${WL_ROWS.indexOf(c)}" aria-label="${esc(aria)}">
        <span class="wl-face">${face}</span>
        <span class="wl-body">
          <span class="wl-ttl">${esc(c.complaint)}</span>
          <span class="wl-meta">
            <span class="ag">${c.age!==undefined?esc(String(c.age)):'\u2013'} ${esc(WL_SHORT[c.sex]||'\u2013')}</span>
            <span class="lv">${c.broken?'<span style="color:var(--harm)">will not run correctly</span>':esc(c.level)}</span>
            <span class="rt">${c.mins?c.mins+' min':''}</span>
          </span>
        </span>
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
function wlVisible(){ return !el('picker').classList.contains('hidden'); }
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
function chooseCase(i){
  selectCase(i);
  bindCase();
  MODE=SHARED.difficulty.default;
  el('picker').classList.add('hidden');
  el('splash').classList.remove('hidden');
  renderSplash();
}
function backToPicker(){
  AUDIO.setScene('idle');
  el('splash').classList.add('hidden');
  el('picker').classList.remove('hidden');
  WL_SEL=-1;                          // returning must not land on a stale highlight
  renderPicker();
  const q=el('wl-q'); if(q) q.blur();
}

/* ---------- splash ---------- */
function renderSplash(){
  const m=CASE.metadata, p=CASE.patient, cs=m.care_setting||{}, ar=m.arrival||{};
  el('sp-setting').textContent=cs.label||'';
  el('sp-title').textContent=m.working_title||'';
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
  const D=PROTO.difficulty;
  el('sp-modes').innerHTML=Object.keys(D.modes).map(k=>{
    const md=D.modes[k];
    return `<button class="mode" role="radio" data-mode="${k}" aria-checked="${MODE===k}">
      <b>${esc(md.label)}</b><span>${esc(md.description)}</span></button>`;
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
function renderSplashVitals(){
  const sec=el('sp-vitalsec'), box=el('sp-vitals');
  if(!sec||!box) return;
  const v=(CASE&&CASE.phases&&CASE.phases[0])?CASE.phases[0].vitals:null;
  const num=x=>typeof x==='number';
  if(!v||!num(v.heart_rate)){ sec.classList.add('hidden'); box.innerHTML=''; return; }
  sec.classList.remove('hidden');
  const cells=[
    ['HR', num(v.heart_rate)?String(v.heart_rate):'\u2013', '/minute'],
    ['BP', (num(v.systolic_bp)&&num(v.diastolic_bp))?v.systolic_bp+'/'+v.diastolic_bp:'\u2013','mmHg'],
    ['SpO\u2082', num(v.oxygen_saturation)?String(v.oxygen_saturation):'\u2013','%'],
    ['RR', num(v.respiratory_rate)?String(v.respiratory_rate):'\u2013','/minute'],
    ['T',  num(v.temperature_c)?v.temperature_c.toFixed(1):'\u2013','\u00B0C']
  ];
  box.innerHTML=cells.map(c=>`<div class="spvitcell"><div class="spvitlab">${c[0]}</div>
    <div class="spvitval">${esc(c[1])}</div>
    <div class="spvitunit">${c[2]}</div></div>`).join('');
}

function begin(){
  STARTED=true; T0=Date.now(); PAUSED=false; PAUSED_MS=0; PAUSED_AT=0;
  /* A history entry to pop, so the back button has something to catch. It can throw on a
     file:// URL in some browsers, and a simulator that will not start because the history
     API refused would be a poor trade for a guard. */
  try{ history.pushState({emsim:1},''); }catch(err){}
  el('splash').classList.add('hidden');
  AUDIO.unlock();
  /* The room starts here rather than on the splash. A case that has been chosen and not
     started is not a case anybody is in. */
  AUDIO.setScene('case');
  render();
  requestAnimationFrame(tick);
}

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
  PAUSED=true; PAUSED_AT=Date.now();
  AUDIO.setScene('idle');
  el('pauseview').classList.remove('hidden');
}
function resumeSim(){
  if(!PAUSED) return;
  const away=Date.now()-PAUSED_AT;
  PAUSED_MS+=away;
  /* A vitals ramp in flight resumes where it was rather than arriving while nobody was
     watching. It is measured from the wall clock, so it needs the same offset. */
  RAMP_T0+=away;
  PAUSED=false;
  el('pauseview').classList.add('hidden');
  AUDIO.unlock(); AUDIO.setScene('case');
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
let LEAVING=false, LEAVE_ACT=null;

function askLeave(action){
  if(!inCase()||LEAVING) return false;
  LEAVE_ACT=action;
  el('leaveview').classList.remove('hidden');
  el('leavecancel').focus();
  return true;
}
function closeLeave(){ el('leaveview').classList.add('hidden'); LEAVE_ACT=null; }

el('leavecancel').addEventListener('click',closeLeave);
el('leaveok').addEventListener('click',()=>{
  const act=LEAVE_ACT;
  closeLeave();
  LEAVING=true;
  if(act==='reload'){ location.reload(); return; }
  /* Back. The guard entry pushed at Begin is popped here. A file opened directly may have
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
function openImage(id,cap){
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
    IMG_QUEUE.push({img:v.image,cap:v.caption||dispName(id)});
  }));
  drainImageQueue();
}
function drainImageQueue(){
  if(!IMG_QUEUE.length||ENDED||PAUSED||LEAVING||imageOpen()) return;
  const n=IMG_QUEUE.shift();
  openImage(n.img,n.cap);
}
function imageOpen(){ return !el('imgview').classList.contains('hidden'); }

document.addEventListener('click',e=>{
  const t=e.target.closest?e.target.closest('.imgthumb'):null;
  if(t){ e.preventDefault(); openImage(t.dataset.img,t.dataset.cap); return; }
  if(!imageOpen()) return;
  /* The backdrop is the overlay itself; anything inside the card is not it. */
  if(e.target===el('imgview')) closeImage();
});
el('imgclose').addEventListener('click',closeImage);

document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&imageOpen()){ closeImage(); return; }
  if(e.key==='Escape'&&!el('leaveview').classList.contains('hidden')){ closeLeave(); return; }
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
  if(LEAVING||!inCase()) return;
  e.preventDefault(); e.returnValue='';
});

/* Escape backs out of the expanded chart, the one state that hides the
   workspace. The leave dialog takes Escape first, above. */
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&RIGHT_WIDE&&!ENDED&&el('leaveview').classList.contains('hidden'))
    minimiseRecord();
});

/* ---------- boot ----------
   Nothing is bound until a case is chosen, and the clock does not start until Begin.
   With a single case the picker is skipped, because choosing from a list of one is a
   step that teaches nothing. */
function boot(){
  if(CASES.length===1){
    chooseCase(0);
    el('picker').classList.add('hidden');
    const back=el('backtopicker'); if(back) back.style.display='none';
  } else {
    selectCase(0); bindCase();         // bind something so the first render has data
    renderPicker();
  }
  setPanels(true,false);
  refold(); renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor();
}
boot();
