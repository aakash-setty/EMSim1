/* ============================================================
   UI. Everything below renders derived state; nothing stores it.
   ============================================================ */
let LOG=[], SEQ=0, T0=Date.now(), ST=null, TAB='history', ENDED=false;
let PENDING_HANDOFF={disposition:null,diagnosis:null};
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

const now = ()=> ENDED ? ST.now : (STARTED ? (Date.now()-T0)/1000 : 0);
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
function jitter(v,amp){ return v + Math.round((Math.sin(Date.now()/1300+v)+Math.sin(Date.now()/770+v*2))/2*amp); }
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
    ['HR',   num(v.heart_rate,2),                            'min\u207B\u00B9','hr'],
    ['BP',   (on&&typeof v.systolic_bp==='number'&&typeof v.diastolic_bp==='number')
               ? v.systolic_bp+'/'+v.diastolic_bp : '\u2013',  'mmHg','bp'],
    ['SpO\u2082', num(v.oxygen_saturation,1),                 '%','spo2'],
    ['RR',   num(v.respiratory_rate,1),                      'min\u207B\u00B9','rr'],
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
  renderTrace(on&&p&&p.vitals?p.vitals.heart_rate:undefined);
  renderSound();
  AUDIO.sync();
}
function renderTrace(hr){
  const svg=el('trace');
  if(typeof hr!=='number'){ svg.innerHTML=''; svg.dataset.hr=''; return; }
  if(svg.dataset.hr===String(hr)) return;
  svg.dataset.hr=String(hr);
  const beats=6, w=420, seg=w/beats; let d='';
  for(let b=0;b<beats;b++){
    const x=b*seg;
    d+=`M${x} 14 L${x+seg*0.30} 14 L${x+seg*0.36} 11 L${x+seg*0.42} 14 `
     + `L${x+seg*0.47} 17 L${x+seg*0.52} 2 L${x+seg*0.57} 20 L${x+seg*0.62} 14 `
     + `L${x+seg*0.78} 14 L${x+seg*0.84} 9 L${x+seg*0.90} 14 L${x+seg} 14 `;
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
    if(LASTNURSE>=0 && n.kind==='prompt') AUDIO.trill();
    LASTNURSE=ST.nurse.length;
  }
  line.textContent=n.text;
  const lab={prompt:'prompt',blocked:'blocked action',result:'result',halt:'halt',narration:''}[n.kind]||'';
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
                      narrates a change the resident may not have been watching for */
  const NURSE_IN_CHART={prompt:1,deterioration:1};
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

function feedPayload(v){
  if(!v||typeof v!=='object') return v?`<div class="fb">${esc(v)}</div>`:'';
  if(v.components&&v.components.length)
    return '<table>'+v.components.map(c=>
      `<tr><td class="lb">${esc(c.label)}</td>
           <td class="vl${c.abnormal?' abn':''}">${esc(c.value)}${c.unit?' '+esc(c.unit):''}</td></tr>`
    ).join('')+'</table>'+(v.comment?`<div class="fb">${esc(v.comment)}</div>`:'');
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

/* ---------- result payload rendering: abnormal components in red ---------- */
function renderPayload(v){
  if(v===null||v===undefined) return '<div class="body">No result is defined for this study.</div>';
  if(typeof v==='string') return `<div class="body">${esc(v)}</div>`;
  if(v.kind==='report'){
    return `<div class="body${v.abnormal?' abn-report':''}">${esc(v.report)}</div>`;
  }
  const rows=(v.components||[]).map(c=>
    `<tr class="${c.abnormal?'abn':''}">
       <td class="lab">${esc(c.label)}</td>
       <td class="val">${esc(c.value)}${c.unit?' '+esc(c.unit):''}</td>
       <td class="ref">${esc(c.reference_range||'')}</td>
     </tr>`).join('');
  return `<table class="labtbl">${rows}</table>`
       + (v.comment?`<div class="body" style="margin-top:6px">${esc(v.comment)}</div>`:'')
       + (v.verify?`<div class="verify">Needs verification: ${esc(v.verify)}</div>`:'');
}

/* ---------- action buttons ---------- */
function actionsFor(tab){
  const f=filterOf(tab), out={};
  for(const id in ACT){
    const a=ACT[id];
    if(a.tab!==tab) continue;
    if(f && !(a.name.toLowerCase().includes(f)||id.includes(f))) continue;
    (out[a.group]=out[a.group]||[]).push(id);
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
    <h3>Ask the patient</h3>
    <p class="sub">Type a question in your own words.</p>
    <div style="display:flex;gap:8px">
      <input type="text" id="askbox" placeholder="Ask the patient something" autocomplete="off" value="${esc(ASKTEXT)}">
      <button class="btn" id="askbtn">Ask</button>
    </div>
    ${semChip()}
</div>
    ${outs?`<div class="panel"><h3>What he told you</h3>${outs}</div>`:''}`;
}

function tabHandoff(){
  const h=CASE.handoff;
  const disp=[{id:h.correct_disposition.id,label:h.correct_disposition.label}]
    .concat(h.alternative_dispositions.map(d=>({id:d.id,label:d.label})))
    .sort((a,b)=>PROTO.dispOrder.indexOf(a.id)-PROTO.dispOrder.indexOf(b.id));
  const dx=PENDING_HANDOFF.diagnosis;
  const pend=ST.pending.length;
  /* Results are on the chart the moment they return, so there is no unread state to
     warn about. What can still be missed is a study that never came back. */
  return `<div class="panel"><h2>Handoff</h2>
    <p class="sub">Submitting and confirming ends the case and generates the debrief.
    The diagnosis list is the full catalog, ${PROTO.diagnoses.length} entries.</p>
    <h3>Level of care</h3>
    ${disp.map(d=>`<button class="opt" data-disp="${d.id}" aria-pressed="${PENDING_HANDOFF.disposition===d.id}">${esc(d.label)}</button>`).join('')}
    <h3>Working diagnosis</h3>
    <input type="text" id="dxbox" placeholder="Search ${PROTO.diagnoses.length} diagnoses" autocomplete="off"
      value="${esc(dx?dxLabel(dx):DXTEXT)}">
    <div id="dxhits"></div>
    ${dx?`<div class="note">Selected: <b>${esc(dxLabel(dx))}</b></div>`:''}
    <h3>Confirm</h3>
    ${pend?`<div class="note"><b>Before you confirm.</b> ${pend} study still pending.</div>`:''}
    <button class="btn" id="submitho" ${(!PENDING_HANDOFF.disposition||!dx)?'disabled':''}>Hand over and end the case</button>
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
function buildMatcher(){
  DF={}; RARE={}; NTOP=CASE.interview.topics.length;
  VOCAB=new Set(); REPAIR_CACHE=new Map();
  for(const t of CASE.interview.topics){
    const seen=new Set();
    for(const c of [t.canonical].concat(t.variants||[])) norm(c).forEach(w=>seen.add(w));
    seen.forEach(w=>DF[w]=(DF[w]||0)+1);
  }
  for(const t of CASE.interview.topics){
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
function matchTopic(q){
  const qt=normQuery(q), scores={};
  for(const t of CASE.interview.topics){
    let b=0;
    for(const c of [t.canonical].concat(t.variants||[])){ const s=wdice(qt,norm(c)); if(s>b) b=s; }
    scores[t.topic]=b;
  }
  let best=null,bs=0;
  for(const k in scores) if(scores[k]>bs){ bs=scores[k]; best=k; }
  for(const w of qt){
    if(RARE[w]&&!RARE[w].has(best)){
      let alt=null,as=0; RARE[w].forEach(t=>{ if(scores[t]>as){ as=scores[t]; alt=t; } });
      if(alt&&as>=PROTO.matchThreshold*0.6){ best=alt; bs=Math.max(bs,as); break; }
    }
  }
  return bs>=PROTO.matchThreshold ? {topic:best,score:bs} : {topic:null,score:bs};
}

/* ---------- fusion of the lexical and semantic matchers ----------
   The lexical matcher above is unchanged and remains authoritative until the
   embedding model has loaded, and permanently if it never does.

   The rule is arranged so that where the semantic layer is not confident, the
   lexical answer stands exactly as it does today. Three of the four branches
   can only add or withhold a match, not silently substitute a different one:

     semantic >= ACCEPT                    the semantic topic wins outright
     AGREE <= semantic < ACCEPT and both   the same topic, so nothing changed
       matchers picked the same topic      except the recorded confidence
     semantic < VETO                       nothing in the bank is close, so the
                                           patient answers out of scope even
                                           where the lexical matcher found a
                                           token overlap
     otherwise                             today's lexical result, unchanged

   The VETO branch is the only one that can remove a match the current build
   would have made. It exists because section 10.6 names out-of-scope handling
   as the weakest part of the system, and because a confident wrong answer is
   invisible to the learner where a fallthrough is not. It is also the branch
   most in need of measurement: see engine/matcher_eval.mjs.

   Every result records which matcher produced it. Because the model may finish
   loading part way through a case, two identical questions in one session can
   be routed by different matchers, and a debrief that claims to report what the
   learner did should be able to say which. Nothing already in the log is ever
   re-matched: the topic is frozen at the moment the question was asked. */
async function matchOne(q){
  const lex=matchTopic(q);
  const out=(topic,score,matcher)=>({topic,score,matcher,lexTopic:lex.topic});
  if(!SEM.ready()) return out(lex.topic,lex.score,'lexical');
  let sem=null;
  try{ sem=await SEM.best(q); }catch(e){ sem=null; }
  if(!sem||sem.topic===null) return out(lex.topic,lex.score,'lexical');
  if(sem.score>=SEM.ACCEPT)                              return out(sem.topic,sem.score,'semantic');
  if(sem.score>=SEM.AGREE && sem.topic===lex.topic)      return out(sem.topic,sem.score,'both');
  if(SEM.VETO>0 && sem.score<SEM.VETO)                   return out(null,sem.score,'semantic-veto');
  return out(lex.topic,lex.score,'lexical');
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
  const parts=splitClauses(q);
  if(!parts.length){
    const only=await matchOne(q);
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
  try{ SEM.init(CASE.case_id, CASE.interview.topics); }catch(e){}
}
/* Repaint the History tab when the matcher changes state, so the line under the
   question box stops saying "improving" once it has. Nothing else depends on it. */
SEM.onChange(()=>{ if(!ENDED && TAB==='history') renderTab(); });

/* ---------- events ---------- */
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-tab],[data-act],[data-ask],[data-disp],[data-dx],'
    +'#askbtn,#submitho,#earlyexit,#restart,#soundbtn,#submitorder,#clearorder,#clearfilter,'
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
    render(); return;
  }
  if(t.dataset.ask){ ask(t.dataset.ask); return; }
  if(t.id==='askbtn'){ const b=el('askbox'); if(b&&b.value.trim()) ask(b.value.trim()); return; }
  if(t.dataset.disp){ PENDING_HANDOFF.disposition=t.dataset.disp; render(); return; }
  if(t.dataset.dx){ PENDING_HANDOFF.diagnosis=t.dataset.dx; DXTEXT=''; render(); return; }
  if(t.id==='submitho'){ log({actionId:'handoff_submit',payload:{...PENDING_HANDOFF}}); finish(); return; }
  if(t.id==='earlyexit'){ log({actionId:'early_exit',kind:'early_exit'}); finish(); return; }
  if(t.id==='restart'){ restart(); return; }
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
      d.label.toLowerCase().includes(q)||d.syn.some(s=>s.toLowerCase().includes(q))).slice(0,10);
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
    log({actionId:null,kind:'interview',topic:m.topic,q:m.q,score:m.score,matcher:m.matcher});
  render();
}

/* ---------- loop ---------- */
let lastFold=0;
function tick(){
  if(!ENDED){
    const t=Date.now();
    if(t-lastFold>100){ lastFold=t; refold(); } else { ST.now=now(); }
    if(ST.halted){ finish(); return; }
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
},300);

/* ---------- ending ---------- */
function finish(){
  refold(); ENDED=true; AUDIO.stop();
  el('playview').classList.add('hidden');
  const v=el('endview'); v.classList.remove('hidden');
  v.innerHTML='<div class="endwrap">'+(ST.halted?haltCard():'')+debriefHTML()+'</div>';
  v.scrollTop=0;
}
function restart(){
  LOG=[];SEQ=0;ENDED=false;STARTED=false;TAB='history';LASTNURSE=-1;LASTPHASE=null;
  resetRamp();
  Object.keys(FILTERS).forEach(k=>delete FILTERS[k]);
  Object.keys(BASKET).forEach(k=>delete BASKET[k]);
  Object.keys(EXPANDED).forEach(k=>delete EXPANDED[k]);
  PENDING_HANDOFF={disposition:null,diagnosis:null};
  AUDIO.stop();
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
  ST.expected.forEach(id=>{ (ST.taken.has(id)?done:omit).push(id); });
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

  const domRows=CASE.debrief_configuration.clinical_domains.map(d=>{
    const exp=d.actions.filter(a=>ST.expected.has(a));
    const got=exp.filter(a=>ST.taken.has(a));
    const bad=d.actions.filter(a=>ST.halted&&ST.halted.id===a);
    return `<tr><td>${esc(d.label)}</td><td class="n">${got.length}/${exp.length}</td>
      <td class="n">${bad.length?'<span class="pill p-harm">halted here</span>'
        :(exp.length&&got.length===exp.length?'<span class="pill p-ok">complete</span>'
        :(exp.length?'<span class="pill p-warn">review</span>':'<span class="pill p-neu">n/a</span>'))}</td></tr>`;
  }).join('');

  let ho='';
  if(ST.handoff){
    const h=CASE.handoff, dId=ST.handoff.disposition, xId=ST.handoff.diagnosis;
    const dOK=dId===h.correct_disposition.id;
    const dAlt=h.alternative_dispositions.find(a=>a.id===dId);
    const dExp=dOK?h.correct_disposition.explanation:(dAlt?dAlt.explanation:'');
    const dV=dOK?['correct','p-ok']:(dAlt&&dAlt.verdict==='acceptable_with_qualification'?['defensible','p-warn']:['incorrect','p-harm']);
    const xOK=xId===PROTO.correctDxId;
    const xDef=!xOK&&(PROTO.altDxDefensible||[]).includes(xId);
    const xExp=xOK?PROTO.correctDxExplanation:(PROTO.altDx[xId]||PROTO.unlistedDxNote);
    const xV=xOK?['correct','p-ok']:(xDef?['defensible','p-warn']:['incorrect','p-harm']);
    ho=`<div class="dbsec"><h2>Handoff</h2>
      <div class="item"><div class="hd"><span class="nm">Level of care: ${esc(dispLabel(dId))}</span>
        <span class="pill ${dV[1]}">${dV[0]}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(dExp)}</div></div>
      <div class="item"><div class="hd"><span class="nm">Diagnosis: ${esc(dxLabel(xId))}</span>
        <span class="pill ${xV[1]}">${xV[0]}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(xExp)}</div></div></div>`;
  } else if(ST.earlyExit){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>You ended the case early, so this debrief is marked incomplete.</p></div>`;
  } else if(ST.halted){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>The case halted before a handoff.</p></div>`;
  }

  const defaults=[...ST.defaultsServed];

  /* What ran out. Timed mechanics are the one thing in the debrief a resident cannot
     reconstruct from the chart: an effect that lapsed and a flag that expired leave no
     entry anywhere, because nothing was done at the moment they happened, which is the
     point of them. Without this block a case whose lesson is "you had thirty seconds and
     used them on the wrong thing" ends with the resident none the wiser.

     One row per administration, not per effect, so a repeated drug reads as the repeated
     act it was. Rendered only when the case uses the mechanics, so a case that authors
     none is unchanged. */
  const wore=(function(){
    const rows=[];
    for(const fx of ST.vitalFx){
      const from=fx.t+(fx.onset||0), to=fx.duration===null?null:fx.t+fx.duration;
      rows.push({t:fx.t,
        what:dispName(fx.id),
        detail:(fx.delta>0?'+':'')+fx.delta+' '+fx.vital.replace(/_/g,' ')
              +', '+(to===null
                     ? (fx.guard?'while its condition held':'for the rest of the case')
                     : 'from '+mmss(from)+' to '+mmss(to))});
    }
    for(const ex of ST.flagExpiries)
      rows.push({t:ex.t,what:ex.flag.replace(/_/g,' '),detail:'stopped acting at '+mmss(ex.t)});
    return rows.sort((a,b)=>a.t-b.t);
  })();

  /* Critical actions lead. They are what the case is about, and a resident reading top
     to bottom should meet the medicine before the scoreboard. */
  return `<div class="dbf">
    ${ST.halted?`<div class="dbsec"><h2>Harmful action</h2>${item(ST.halted.id,'harmful','p-harm')}</div>`:''}

    <div class="dbsec"><h2>Critical actions</h2>
      ${done.length?done.map(id=>item(id,'critical','p-crit',dispExp(id))).join(''):'<p>No critical action was completed.</p>'}
      ${omit.length?'<h3>Missed</h3>'+omit.map(id=>item(id,'not done','p-harm',dispExp(id))).join(''):''}
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
      <p class="sub">${ST.halted?'Halted':(ST.earlyExit?'Ended early, incomplete':'Completed')} at ${mmss(ST.now)},
      in ${esc(PROTO.difficulty.modes[MODE].label.toLowerCase())}${DM()!==1?`, so nurse prompts were ${DM()} times later than the authored deadlines`:''}.
      Points direct review; they do not rank you.</p>
      <table class="dom"><tr><th>Domain</th><th class="n">Done</th><th class="n"></th></tr>${domRows}</table>
      <div style="margin-top:16px"><button class="btn" id="restart">Replay this case</button>
      ${CASES.length>1?'<button class="btn ghost" id="pickanother" style="margin-left:8px">Choose a different case</button>':''}</div></div>

    ${wore.length?`<div class="dbsec"><h2>What was acting, and for how long</h2>
      <p class="sub">Some of what you gave worked for a fixed time and then stopped. Nothing
      appears in the chart at the moment it wears off, because nothing was done then.</p>
      ${wore.map(r=>`<div class="item"><div class="hd">
        <span class="nm">${esc(r.what)}</span>
        <span class="pill p-warn">${mmss(r.t)}</span>
        <span class="pill p-neu">${esc(r.detail)}</span></div></div>`).join('')}</div>`:''}

    ${traps.length?`<div class="dbsec"><h2>Things that looked reasonable and were not</h2>
      ${traps.map(x=>item(x.id,'no benefit here','p-neu')).join('')}
      </div>`:''}

    ${ST.blocked.length?`<div class="dbsec"><h2>Blocked attempts</h2>
      <p class="sub">Sequence teaching, not penalised. The system already corrected you at the time.</p>
      ${ST.blocked.map(b=>`<div class="item"><div class="hd"><span class="nm">${esc(dispName(b.id))}</span>
        <span class="pill p-warn">${mmss(b.t)}</span>
        <span class="pill p-neu">${b.source==='catalog_default'?'catalog prerequisite':'case prerequisite'}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(b.message)}</div></div>`).join('')}</div>`:''}

    ${ho}

    ${defaults.length?`<div class="dbsec"><h2>Answered by a default, not by the case</h2>
      <p class="sub">These returned the catalog's normal result or the global response because this case
      authors nothing for them. A normal default is not a neutral default: if an author forgets a study
      that matters, the learner is shown normal and taught the wrong thing.</p>
      <p>${defaults.map(d=>esc(dispName(d))).join(', ')}.</p></div>`:''}

    ${stillPending.length?`<div class="dbsec"><h2>Results you did not read</h2>
      ${stillPending.length?`<p>Still pending when the case ended: ${stillPending.map(i=>esc(dispName(i))).join(', ')}.</p>`:''}
      <p class="sub">Handing over with a result you never looked at is a real handover failure.</p></div>`:''}

    <div class="dbsec"><h2>Independent and prompted</h2>
      <table class="dom"><tr><th>Critical action</th><th>How it happened</th></tr>
      ${[...ST.expected].map(id=>{
        const s2=ST.taken.has(id)?(ST.prompted.has(id)?['after a prompt','p-warn']:['on your own','p-ok']):['omitted','p-harm'];
        return `<tr><td>${esc(dispExp(id))}</td><td><span class="pill ${s2[1]}">${s2[0]}</span></td></tr>`;
      }).join('')}</table>
      <div class="note">A prompted action counts as done. This is here so you know where you needed help,
      not as a penalty.</div></div>

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
    ['HR', num(v.heart_rate)?String(v.heart_rate):'\u2013', 'min\u207B\u00B9'],
    ['BP', (num(v.systolic_bp)&&num(v.diastolic_bp))?v.systolic_bp+'/'+v.diastolic_bp:'\u2013','mmHg'],
    ['SpO\u2082', num(v.oxygen_saturation)?String(v.oxygen_saturation):'\u2013','%'],
    ['RR', num(v.respiratory_rate)?String(v.respiratory_rate):'\u2013','min\u207B\u00B9'],
    ['T',  num(v.temperature_c)?v.temperature_c.toFixed(1):'\u2013','\u00B0C']
  ];
  box.innerHTML=cells.map(c=>`<div class="spvitcell"><div class="spvitlab">${c[0]}</div>
    <div class="spvitval">${esc(c[1])}</div>
    <div class="spvitunit">${c[2]}</div></div>`).join('');
}

function begin(){
  STARTED=true; T0=Date.now();
  el('splash').classList.add('hidden');
  AUDIO.unlock();
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

/* Escape backs out of the expanded chart, the one state that hides the
   workspace. Nothing else is modal, so nothing else needs a key. */
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&RIGHT_WIDE&&!ENDED) minimiseRecord();
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
