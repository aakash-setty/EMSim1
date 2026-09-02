/* ============================================================
   UI. Everything below renders derived state; nothing stores it.
   ============================================================ */
let LOG=[], SEQ=0, T0=Date.now(), ST=null, TAB='patient', ENDED=false;
let PENDING_HANDOFF={disposition:null,diagnosis:null};
let LASTNURSE=-1, LASTPHASE=null, ASKTEXT='', DXTEXT='';
/* Filter text and the pending order basket are per tab, so switching tabs and
   coming back leaves both exactly as they were. */
const FILTERS={}, BASKET={};
/* Expanded state for collapsible groups, per tab, so leaving and returning to a tab
   leaves the accordion exactly as it was. */
const EXPANDED={};
const expandedOf = t => (EXPANDED[t]=EXPANDED[t]||new Set());
let MODE='easy', STARTED=false;
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

/* ---------- monitor (section 6, 8.4) ---------- */
function jitter(v,amp){ return v + Math.round((Math.sin(Date.now()/1300+v)+Math.sin(Date.now()/770+v*2))/2*amp); }
function renderMonitor(){
  const p=PHASE[ST.phase], v=p.vitals;
  const halted = ST.halted||ST.complete||ST.earlyExit;
  const j = halted ? (x=>x) : jitter;
  /* A case still being authored has null vitals. Show a dash rather than crashing:
     the picker offers skeletons on purpose, and a skeleton that white-screens is
     worse than one that reads as obviously unfinished. */
  const num=(x,amp)=>typeof x==='number'?j(x,amp||0):'\u2013';
  const cells=[
    ['HR',   num(v.heart_rate,2),                            'min\u207B\u00B9','hr'],
    ['BP',   (typeof v.systolic_bp==='number'&&typeof v.diastolic_bp==='number')
               ? v.systolic_bp+'/'+v.diastolic_bp : '\u2013',  'mmHg','bp'],
    ['SpO\u2082', num(v.oxygen_saturation,1),                 '%','spo2'],
    ['RR',   num(v.respiratory_rate,1),                      'min\u207B\u00B9','rr'],
    ['T',    typeof v.temperature_c==='number'?v.temperature_c.toFixed(1):'\u2013','\u00B0C','temp']
  ];
  el('monitor').innerHTML = cells.map(c=>
    `<div class="vit"><div class="vitlab">${c[0]}</div>
     <div class="vitval v-${c[3]}">${c[1]}</div><div class="vitunit">${c[2]}</div></div>`).join('')
    + `<div class="clockbox"><div class="vitlab">elapsed</div>
       <div class="clock">${mmss(ST.now)}</div>
       <div class="phasechip">${esc(PROTO.phaseShort[ST.phase]||ST.phase)}</div>
       <div class="phasechip">${esc(PROTO.difficulty.modes[MODE].label)}</div></div>`;
  if(LASTPHASE!==null && LASTPHASE!==ST.phase) el('monitor').animate?.([{opacity:.35},{opacity:1}],{duration:420});
  LASTPHASE=ST.phase;
  renderTrace(v.heart_rate);
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
  b.textContent = AUDIO.running ? 'Sound on' : (AUDIO.enabled ? 'Enable sound' : 'Sound off');
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
  }).join('') : '<div style="font-size:12.5px;color:var(--ink3)">Nothing pending.</div>';
  renderFeed();
}

/* ---------- running chart ----------
   Everything the case has produced, in the order it arrived: results as they come back,
   exam findings, consultant replies, what the patient said, and every action performed
   or blocked. It is always on screen, because a finding read on one tab is gone the
   moment the resident moves to another and the whole point of a chart is that it is not.

   Results enter the feed at the moment they RESULT, not when they were ordered, so the
   order here is the order the resident actually learned things. */
function feedItems(){
  const out=[];
  for(const x of ST.timeline){
    if(x.type==='blocked'){ out.push({t:x.t,kind:'blocked',name:x.label}); continue; }
    /* Observational entries are already represented by the readout they produced, and
       the interview and review entries would just duplicate it. */
    if(x.type==='observational') continue;
    if(x.type==='end') continue;
    /* A study appears twice: once when it is sent, once when it results. Same name on
       both reads as a duplicate, so the order is labelled as an order. */
    const isStudy=catOf(x.id)==='investigation';
    out.push({t:x.t,kind:x.tag==='harmful'?'harm':(isStudy?'order':'action'),
              name:isStudy?('Ordered: '+x.label):x.label});
  }
  for(const r of ST.readouts){
    if(r.kind==='exam')    out.push({t:r.t,kind:'exam',name:r.title,payload:r.body});
    if(r.kind==='consult') out.push({t:r.t,kind:'consult',name:r.title,body:r.body});
    if(r.kind==='speech')  out.push({t:r.t,kind:'speech',name:r.title,body:r.body});
  }
  Object.keys(ST.orders).forEach(id=>ST.orders[id].forEach(o=>{
    if(o.value===null) return;                      /* still pending, lives in the rail above */
    out.push({t:o.dueT,kind:catOf(id)==='investigation'?'lab':'imaging',
              name:dispName(id),payload:o.value});
  }));
  out.sort((a,b)=>a.t-b.t);
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
    : '<div style="font-size:12.5px;color:var(--ink3)">Nothing yet.</div>';
  /* Follow the newest entry only when something has actually been added, so a reader
     scrolled back through earlier results is not yanked to the bottom every tick. */
  if(items.length!==FEED_N){
    FEED_N=items.length;
    const f=el('feed'); f.scrollTop=f.scrollHeight;
  }
}

/* ---------- tabs ---------- */
function renderTabs(){
  el('tabbar').innerHTML=PROTO.tabOrder.map(id=>{
    let badge='';
    if(id==='investigations'&&ST.pending.length) badge=`<span class="badge">${ST.pending.length}</span>`;
    return `<button class="tab" role="tab" aria-selected="${id===TAB}" data-tab="${id}">${esc(PROTO.tabLabel[id])}${badge}</button>`;
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
  let html='';
  for(const g of names){
    const picked=groups[g].filter(id=>basketOf(tab).has(id)).length;
    if(collapsible){
      const isOpen=open.has(g);
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
  if(collapsible&&filterOf(tab)) names.forEach(g=>open.add(g));
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
    patient:tabPatient, history:tabHistory, handoff:tabHandoff,
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
  box.innerHTML=(R[TAB]||tabPatient)();
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

/* appearance renderer (section 6): computed globally from authored values */
function appearanceProse(){
  const p=PHASE[ST.phase], a=p.appearance, v=p.vitals;
  const D=['comfortable','mildly uncomfortable','visibly distressed','in severe distress'][a.distress_level]
          ||'of unrecorded distress';
  const A=['awake and alert','drowsy but rousable','obtunded','unresponsive'][a.alertness_level]
          ||'of unrecorded alertness';
  const bits=[`He is ${A} and ${D}.`];
  if(v.oxygen_saturation<90) bits.push('There is dusky discolouration of the lips and nail beds.');
  else if(v.oxygen_saturation<94) bits.push('Colour is dull but not frankly cyanosed.');
  if(a.distress_level>=3) bits.push('He is sweating, sitting bolt upright, and using his neck and shoulder muscles to breathe.');
  else if(a.distress_level===2) bits.push('He is breathing faster than normal and prefers to sit up.');
  if(v.systolic_bp<90) bits.push('He is pale and his skin is cool to touch.');
  if(a.alertness_level>=2) bits.push('He does not respond to voice.');
  bits.push(`Pupils are ${a.pupil_size} and ${a.pupil_reactivity}.`);
  return bits.join(' ');
}

function tabPatient(){
  const p=CASE.patient, m=CASE.metadata;
  return `<div class="panel">
    <h2>${esc(m.working_title)}</h2>
    <p class="sub">${p.age} year old ${p.sex}, ${p.weight_kg} kg. Written for
      ${esc(String(m.target_level).split(',').map(x=>x.trim().replace(/_/g,' ')).join(', '))}.</p>
    <h3>Handover from the paramedics</h3>
    <p>${esc(p.ems_handover_text)}</p>
    <h3>What you see</h3>
    <p>${esc(appearanceProse())}</p>
    <h3>Background</h3>
    <p>${esc(Array.isArray(p.background)?p.background.join(' '):p.background)}</p>
  </div>`;
}

function tabHistory(){
  const outs=ST.readouts.filter(r=>r.kind==='speech').slice(-10).reverse().map(r=>
    `<div class="speech"><div class="who">You asked: ${esc(r.title)}</div>${esc(r.body)}
     </div>`).join('');
  return `<div class="panel"><h2>History</h2>
    <p class="sub">Type a question in your own words.</p>
    <div style="display:flex;gap:8px">
      <input type="text" id="askbox" placeholder="Ask the patient something" autocomplete="off" value="${esc(ASKTEXT)}">
      <button class="btn" id="askbtn">Ask</button>
    </div>
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
let DF={}, NTOP=0, RARE={};
/* Rebuilt whenever a case is selected: the weights describe one case's variant bank. */
function buildMatcher(){
  DF={}; RARE={}; NTOP=CASE.interview.topics.length;
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
}
const idf=w=>Math.log((NTOP+1)/((DF[w]||0)+0.5));
function wdice(a,b){
  const A=new Set(a),B=new Set(b); if(!A.size||!B.size) return 0;
  let inter=0,tot=0;
  new Set([...A,...B]).forEach(w=>{ const g=idf(w); tot+=g; if(A.has(w)&&B.has(w)) inter+=g; });
  return tot ? (2*inter)/(tot+inter) : 0;
}
function matchTopic(q){
  const qt=norm(q), scores={};
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

/* ---------- events ---------- */
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-tab],[data-act],[data-ask],[data-disp],[data-dx],'
    +'#askbtn,#submitho,#earlyexit,#restart,#soundbtn,#submitorder,#clearorder,#clearfilter,'
    +'[data-group],[data-mode],[data-case],#beginbtn,#backtopicker,#pickanother');
  if(t&&t.id==='soundbtn'){ AUDIO.toggle(); renderSound(); return; }
  AUDIO.unlock();
  if(!t) return;
  if(t.dataset.tab){ TAB=t.dataset.tab; render(); return; }
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
function ask(q){
  const m=matchTopic(q);
  log({actionId:null,kind:'interview',topic:m.topic,q,score:m.score});
  ASKTEXT=''; const b=el('askbox'); if(b) b.value='';
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
  v.innerHTML=(ST.halted?haltCard():'')+debriefHTML();
  window.scrollTo(0,0);
}
function restart(){
  LOG=[];SEQ=0;ENDED=false;STARTED=false;TAB='patient';LASTNURSE=-1;LASTPHASE=null;
  Object.keys(FILTERS).forEach(k=>delete FILTERS[k]);
  Object.keys(BASKET).forEach(k=>delete BASKET[k]);
  Object.keys(EXPANDED).forEach(k=>delete EXPANDED[k]);
  PENDING_HANDOFF={disposition:null,diagnosis:null};
  AUDIO.stop();
  el('endview').classList.add('hidden'); el('playview').classList.remove('hidden');
  el('splash').classList.remove('hidden');
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
  const item=(id,pill,pillcls)=>{
    const note=noteOf(id), refs=refsOf(id);
    const head=`<span class="nm">${esc(dispName(id))}</span><span class="pill ${pillcls}">${pill}</span>
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
    const xExp=xOK?PROTO.correctDxExplanation:(PROTO.altDx[xId]||PROTO.unlistedDxNote);
    ho=`<div class="dbsec"><h2>Handoff</h2>
      <div class="item"><div class="hd"><span class="nm">Level of care: ${esc(dispLabel(dId))}</span>
        <span class="pill ${dV[1]}">${dV[0]}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(dExp)}</div></div>
      <div class="item"><div class="hd"><span class="nm">Diagnosis: ${esc(dxLabel(xId))}</span>
        <span class="pill ${xOK?'p-ok':'p-harm'}">${xOK?'correct':'incorrect'}</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(xExp)}</div></div></div>`;
  } else if(ST.earlyExit){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>You ended the case early, so this debrief is marked incomplete.</p></div>`;
  } else if(ST.halted){
    ho=`<div class="dbsec"><h2>Handoff</h2><p>The case halted before a handoff.</p></div>`;
  }

  const defaults=[...ST.defaultsServed];

  /* Critical actions lead. They are what the case is about, and a resident reading top
     to bottom should meet the medicine before the scoreboard. */
  return `<div class="dbf">
    ${ST.halted?`<div class="dbsec"><h2>Harmful action</h2>${item(ST.halted.id,'harmful','p-harm')}</div>`:''}

    <div class="dbsec"><h2>Critical actions</h2>
      ${done.length?done.map(id=>item(id,'critical','p-crit')).join(''):'<p>No critical action was completed.</p>'}
      ${omit.length?'<h3>Missed</h3>'+omit.map(id=>item(id,'not done','p-harm')).join(''):''}
      ${[...ST.fuOutstanding].length?'<h3>Follow-up obligations left open</h3>'+[...ST.fuOutstanding].map(fid=>
        `<div class="item"><div class="hd"><span class="nm">${esc(fid.replace(/_/g,' '))}</span>
        <span class="pill p-harm">not done</span></div>
        <div class="note" style="background:none;border:0;padding:0;margin:4px 0 0">${esc(FU[fid].debrief_note)}</div></div>`).join(''):''}</div>

    ${rec.length?`<div class="dbsec"><h2>Also worth doing</h2>
      ${rec.map(id=>item(id,'recommended','p-ok')).join('')}</div>`:''}

    <div class="dbsec"><h2>Summary</h2>
      <p class="sub">${ST.halted?'Halted':(ST.earlyExit?'Ended early, incomplete':'Completed')} at ${mmss(ST.now)},
      in ${esc(PROTO.difficulty.modes[MODE].label.toLowerCase())}${DM()!==1?`, so nurse prompts were ${DM()} times later than the authored deadlines`:''}.
      Points direct review; they do not rank you.</p>
      <table class="dom"><tr><th>Domain</th><th class="n">Done</th><th class="n"></th></tr>${domRows}</table>
      <div style="margin-top:16px"><button class="btn" id="restart">Replay this case</button>
      ${CASES.length>1?'<button class="btn ghost" id="pickanother" style="margin-left:8px">Choose a different case</button>':''}</div></div>

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
        return `<tr><td>${esc(dispName(id))}</td><td><span class="pill ${s2[1]}">${s2[0]}</span></td></tr>`;
      }).join('')}</table>
      <div class="note">A prompted action counts as done. This is here so you know where you needed help,
      not as a penalty.</div></div>

    <div class="dbsec"><h2>Points to carry out of this case</h2>
      ${(CASE.debrief_configuration.cross_cutting_teaching_points||[]).map(p=>
        `<div class="item"><div class="note" style="background:none;border:0;padding:0;margin:0">${esc(typeof p==='string'?p:p.point||'')}</div></div>`).join('')}</div>

  </div>`;
}

/* ---------- case picker ---------- */
function renderPicker(){
  el('pk-list').innerHTML=CASES.map((c,i)=>{
    const k=c.card, lv=Array.isArray(k.target_level)
      ? k.target_level.map(x=>String(x).replace(/_/g,' ')).join(', ')
      : String(k.target_level||'').replace(/_/g,' ');
    const mins=k.runtime_seconds?Math.round(k.runtime_seconds/60)+' min':'';
    return `<button class="casecard" data-case="${i}">
      <span class="pk">${esc(c.prefix)}</span>
      <span class="ti">${esc(k.title)}</span>
      ${k.chief_complaint?`<span class="cc">\u201C${esc(k.chief_complaint)}\u201D</span>`:''}
      <span class="mt">${[esc(k.setting),esc(lv),mins].filter(Boolean).join('  \u00B7  ')}</span>
      ${(c.buildNotes||[]).length?`<span class="mt flagred">incomplete: ${c.buildNotes.length} build problem${c.buildNotes.length>1?'s':''}, this case will not run correctly</span>`:''}
    </button>`;
  }).join('');
  el('pk-warn').textContent = CASES.length===1
    ? ''
    : 'Each case is independent. Nothing carries over between them.';
}
function chooseCase(i){
  selectCase(i);
  buildMatcher();
  MODE=SHARED.difficulty.default;
  el('picker').classList.add('hidden');
  el('splash').classList.remove('hidden');
  renderSplash();
}
function backToPicker(){
  el('splash').classList.add('hidden');
  el('picker').classList.remove('hidden');
  renderPicker();
}

/* ---------- splash ---------- */
function renderSplash(){
  const m=CASE.metadata, p=CASE.patient, cs=m.care_setting||{}, ar=m.arrival||{};
  el('sp-setting').textContent=cs.label||'';
  el('sp-title').textContent=m.working_title||'';
  el('sp-cc').textContent=m.chief_complaint_patient_voice
    ? '\u201C'+m.chief_complaint_patient_voice+'\u201D' : '';
  el('sp-arrival').textContent=[ar.line,p.ems_handover_text].filter(Boolean).join(' ');
  const D=PROTO.difficulty;
  el('sp-modes').innerHTML=Object.keys(D.modes).map(k=>{
    const md=D.modes[k];
    return `<button class="mode" role="radio" data-mode="${k}" aria-checked="${MODE===k}">
      <b>${esc(md.label)}</b><span>${esc(md.description)}</span></button>`;
  }).join('');

}
function begin(){
  STARTED=true; T0=Date.now();
  el('splash').classList.add('hidden');
  AUDIO.unlock();
  render();
  requestAnimationFrame(tick);
}

/* keep the sticky rail clear of the header, whose height varies */
const hdr=document.querySelector('.stick');
const setHdr=()=>document.documentElement.style.setProperty('--hdr',hdr.offsetHeight+'px');
if(window.ResizeObserver) new ResizeObserver(setHdr).observe(hdr);
window.addEventListener('resize',setHdr); setHdr();

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
    selectCase(0); buildMatcher();     // bind something so the first render has data
    renderPicker();
  }
  refold(); renderTabs(); renderTab(); renderRail(); renderNurse(); renderMonitor();
}
boot();
