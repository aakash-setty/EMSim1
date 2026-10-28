/* ---------- saved progress (28 October 2026) ----------
   The deployed build keeps each signed-in learner's runs in Supabase (public.runs,
   supabase/migrations/002_runs.sql). The local build has no backend and this module does
   nothing there: every call below returns at once and the simulator behaves as before.

   What is saved. A run is its action log, the case clock, the mode and a few screen
   settings. fold() rebuilds everything else from those, so a resumed run is the same run.
   ui.js makes the snapshot (runSnapshot) and puts one back (resumeRun); this file only
   moves it to and from the database. When the case ends, the row keeps the score summary
   and the database empties the saved state, so the log and anything typed into the case
   are not kept after the debrief.

   Owner decisions (28 October 2026):
     - a run saved against an older version of the case is not resumed. The splash says the
       case has been improved and the run is deleted. versionKey (build time) is a hash of
       the pack, the engine and the shared catalog, which is everything fold() reads.
     - history is score summaries only.
     - abandoned runs are discarded: Start over deletes the run in progress.
     - learners may delete their history.

   Nothing here names a case, a drug or a diagnosis. Analytics get counts and the case
   prefix only, as everywhere else. */
const PROGRESS = (function(){
  const CFG = (typeof ACCESS==='object' && ACCESS) || {mode:'local'};
  const SITE = CFG.mode==='site';
  const A = (typeof ANALYTICS==='object' && ANALYTICS) || {track(){}};
  const $ = id => document.getElementById(id);
  const escP = t => String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const SAVE_EVERY_MS = 5000;     // an action is saved within five seconds
  const CLOCK_EVERY_S = 15;       // and the clock alone, every fifteen seconds of case time
  const LIST_COLS = 'id,case_prefix,version_key,mode,status,sim_seconds,outcome,ended_by,score_pct,summary,started_at,updated_at,finished_at';

  const KEYS = {};                // prefix -> versionKey, read from the stubs before any pack replaces them
  let client=null, uid=null, token='';
  let runs=[], listState='idle';  // idle | loading | ready | error
  let cur=null;                   // the run being played: {id, prefix, key, mode, gone, closing}
  let dirty=false, saving=null, again=false, savedAtT=-1, saveFailed=false;
  let want=null;                  // a prefix the home panel asked to resume once its case opens
  let confirmDel=null, openRow=null, splashBusy=false;

  const on = () => SITE && !!client && !!uid;
  const inRun = () => typeof inCase==='function' && inCase();
  const mmssP = s => { s=Math.max(0,Math.floor(s||0)); return Math.floor(s/60)+':'+String(s%60).padStart(2,'0'); };
  const caseIndex = prefix => CASES.findIndex(c=>c.prefix===prefix);
  const caseTitle = prefix => { const c=CASES[caseIndex(prefix)]; const k=(c&&c.card)||{}; return k.complaint||k.title||prefix; };
  /* "Case N" before a title, from the case's card. Escaped, and empty for a case with none. */
  const caseNo = prefix => { const c=CASES[caseIndex(prefix)]; const n=c&&c.card&&c.card.number;
    return n?`<span class="hm-no">Case ${escP(n)}</span>`:''; };
  const openRun = prefix => runs.find(r=>r.status==='in_progress'&&r.case_prefix===prefix)||null;

  /* ---- session ---- */
  function init(cl){
    if(!SITE) return;
    CASES.forEach(c=>{ if(c.versionKey) KEYS[c.prefix]=c.versionKey; });
    client=cl;
    setInterval(tick, SAVE_EVERY_MS);
    /* A tab being closed or reloaded: send what there is, without waiting for an answer. */
    window.addEventListener('pagehide', beacon);
    bindHome();
  }
  function onSession(s){
    if(!SITE) return;
    token=(s&&s.access_token)||'';
    const id=(s&&s.user&&s.user.id)||null;
    if(id===uid) return;
    uid=id; runs=[]; cur=null; dirty=false; listState='idle';
    if(uid) refresh(); else paintHome();
  }
  async function refresh(){
    if(!on()) return;
    listState= runs.length?'ready':'loading'; paintHome();
    try{
      const {data,error}=await client.from('runs').select(LIST_COLS)
        .order('updated_at',{ascending:false}).limit(300);
      if(error) throw error;
      runs=data||[]; listState='ready';
    }catch(e){ listState='error'; }
    paintHome();
    if(typeof wlVisible==='function' && wlVisible() && typeof renderPicker==='function') renderPicker();
  }

  /* ---- saving ---- */
  function touch(){ if(cur) dirty=true; }
  function tick(){
    if(!on()||!cur||cur.gone||cur.closing||!inRun()) return;
    const t=(typeof ST==='object'&&ST)?ST.now:0;
    if(dirty || t-savedAtT>=CLOCK_EVERY_S) save();
  }
  function rowFrom(snap){
    return {mode:snap.mode, state:snap, sim_seconds:Math.min(86400,Math.max(0,Math.floor(snap.t||0)))};
  }
  async function insertRun(row){
    const body=Object.assign({case_prefix:cur.prefix, version_key:cur.key, status:'in_progress'}, row);
    let r=await client.from('runs').insert(body).select('id').single();
    if(r.error && r.error.code==='23505'){
      /* Another run of this case is in progress, from another tab or device. The newest
         start wins: the owner's rule is that an abandoned run is discarded. */
      await client.from('runs').delete().eq('case_prefix',cur.prefix).eq('status','in_progress');
      r=await client.from('runs').insert(body).select('id').single();
    }
    if(r.error) throw r.error;
    return r.data.id;
  }
  function save(){
    if(!on()||!cur||cur.gone) return Promise.resolve();
    if(saving){ again=true; return saving; }
    const run=cur, snap=runSnapshot();
    dirty=false;
    saving=(async()=>{
      try{
        const row=rowFrom(snap);
        if(!run.id){ run.id=await insertRun(row); A.track('run_saved',{case:run.prefix}); }
        else{
          const {data,error}=await client.from('runs').update(row)
            .eq('id',run.id).eq('status','in_progress').select('id');
          if(error) throw error;
          /* Nothing matched: the run was deleted or started again somewhere else. Stop
             saving this one rather than fighting over it. */
          if(!data||!data.length) run.gone=true;
        }
        savedAtT=snap.t; saveFailed=false;
      }catch(e){ if(run===cur) dirty=true; saveFailed=true; }
      finally{
        saving=null;
        if(again){ again=false; if(cur&&!cur.closing) save(); }
      }
    })();
    return saving;
  }
  /* Save now and wait for it, but never for long: leaving must not hang on the network. */
  function flush(ms){
    if(!on()||!cur||cur.gone) return Promise.resolve();
    return Promise.race([save(), new Promise(r=>setTimeout(r, ms||4000))]);
  }
  function beacon(){
    if(!on()||!cur||!cur.id||cur.gone||cur.closing||!inRun()||!token) return;
    try{
      const body=JSON.stringify(rowFrom(runSnapshot()));
      if(body.length>60000) return;                 /* keepalive requests are capped at 64 KB */
      fetch(CFG.supabaseUrl.replace(/\/+$/,'')+'/rest/v1/runs?id=eq.'+encodeURIComponent(cur.id)+'&status=eq.in_progress',
        {method:'PATCH', keepalive:true, body,
         headers:{'apikey':CFG.supabaseKey,'Authorization':'Bearer '+token,
                  'Content-Type':'application/json','Prefer':'return=minimal'}}).catch(()=>{});
    }catch(e){}
  }
  /* True when leaving keeps the run: there is a saved row and the last save worked. */
  const kept = () => on() && !!cur && !!cur.id && !cur.gone && !saveFailed;

  /* ---- the run's life ---- */
  function start(prefix, mode){
    if(!on()) return;
    const old=openRun(prefix);
    if(old){ discard(old,'start_over'); }
    cur={id:null, prefix, key:KEYS[prefix]||'', mode, gone:!KEYS[prefix], closing:false};
    dirty=true; savedAtT=-1; saveFailed=false;
  }
  /* The learner left for the list, or replayed from the debrief: stop saving into this run.
     A run still in progress stays in the database to be resumed. */
  function detach(){
    const had=!!cur;
    const p=(cur&&!cur.closing&&!cur.gone&&inRun())?flush(2000):Promise.resolve();
    cur=null; dirty=false;
    if(had) p.then(refresh);
  }
  async function discard(r, reason){
    runs=runs.filter(x=>x.id!==r.id);
    A.track('run_discarded',{case:r.case_prefix, reason});
    try{ await client.from('runs').delete().eq('id',r.id); }catch(e){}
    paintHome();
  }
  async function finish(res){
    if(!on()||!cur||cur.gone) { cur=null; return; }
    const run=cur; run.closing=true; cur=null; dirty=false;
    /* The dashboard before this run, to say afterwards what it changed. */
    const before=listState==='ready'?derive():null;
    if(saving) try{ await saving; }catch(e){}
    /* Off the local list at once, so a Replay straight from the debrief is not offered a
       Resume of the run that just ended. refresh() below brings back the finished row. */
    runs=runs.filter(x=>x.id!==run.id);
    const row={status:'finished', state:null, mode:res.mode,
               sim_seconds:Math.min(86400,Math.max(0,Math.round(res.sim_seconds||0))),
               outcome:res.outcome, ended_by:res.ended_by,
               score_pct:(typeof res.score_pct==='number')?Math.max(0,Math.min(100,Math.round(res.score_pct))):null,
               summary:res.summary};
    try{
      let error;
      if(run.id&&!run.gone){
        ({error}=await client.from('runs').update(row).eq('id',run.id).eq('status','in_progress'));
      } else {
        ({error}=await client.from('runs').insert(Object.assign({case_prefix:run.prefix, version_key:run.key}, row)));
      }
      if(error) throw error;
    }catch(e){ A.track('run_save_failed',{case:run.prefix, at:'finish'}); }
    await refresh();
    if(before&&listState==='ready'){
      feedback=diff(before,derive(),run.prefix); paintHome();
      const sc=$('db-scroll'); if(sc) sc.scrollTop=0;
    }
  }

  /* ---- the splash: resume, start over, or the case has changed ---- */
  function onSplash(prefix, retried){
    const box=$('sp-run'); if(!box) return;
    const begin=$('beginbtn');
    /* The list has not arrived yet (a case opened straight after the page loaded). Begin
       waits for it, or Start over could discard a run the learner was never offered. */
    if(on()&&listState!=='ready'&&!retried){
      if(begin) begin.disabled=true;
      refresh().finally(()=>{ if(begin) begin.disabled=false; if(!inRun()&&typeof PACK==='object'&&PACK&&PACK.prefix===prefix) onSplash(prefix,true); });
      return;
    }
    const r=on()?openRun(prefix):null;
    if(!r){
      box.hidden=true; box.innerHTML='';
      if(begin){ begin.textContent='Begin'; begin.classList.remove('ghost'); }
      want=null; return;
    }
    if(r.version_key!==KEYS[prefix]){
      want=null;
      box.hidden=true; box.innerHTML='';
      if(begin){ begin.textContent='Begin'; begin.classList.remove('ghost'); }
      showImproved(r);
      return;
    }
    box.hidden=false;
    box.innerHTML=`<button class="btn begin" type="button" id="sp-resume">Resume at ${escP(mmssP(r.sim_seconds))}</button>
      <span class="sp-runnote" id="sp-runnote">You have this case in progress. Start over deletes it.</span>`;
    if(begin){ begin.textContent='Start over'; begin.classList.add('ghost'); }
    $('sp-resume').onclick=()=>resume(r);
    if(want===prefix){ want=null; resume(r); }
  }
  function showImproved(r){
    const v=$('improvedview'); if(!v) return;
    v.classList.remove('hidden');
    const ok=$('improvedok'); ok.focus();
    ok.onclick=()=>{ v.classList.add('hidden'); };
    discard(r,'version');
  }
  async function resume(r){
    if(splashBusy) return;
    splashBusy=true;
    const note=$('sp-runnote'), btn=$('sp-resume');
    if(btn) btn.disabled=true;
    try{
      const {data,error}=await client.from('runs').select('state,version_key,status').eq('id',r.id).single();
      if(error) throw error;
      if(!data||data.status!=='in_progress') throw new Error('gone');
      const s=data.state;
      if(!s||s.v!==1||!Array.isArray(s.log)) throw new Error('bad state');
      cur={id:r.id, prefix:r.case_prefix, key:r.version_key, mode:s.mode, gone:false, closing:false};
      dirty=false; savedAtT=+s.t||0; saveFailed=false;
      A.track('run_resumed',{case:r.case_prefix, sim_seconds:Math.round(+s.t||0)});
      resumeRun(s);
    }catch(e){
      if(note) note.textContent= (e&&e.message==='gone')
        ? 'This run is no longer saved. Start the case again.'
        : 'Your saved run could not be loaded. Check your connection and try again.';
      if(e&&e.message==='gone') refresh();
    }finally{
      splashBusy=false; if(btn) btn.disabled=false;
    }
  }

  /* ==========================================================================
     The dashboard (author instruction, 28 October 2026): progress you can see, mastery per
     case, a practice streak, milestones, and a word after each case about what changed.

     Everything here is worked out in this browser from the learner's own rows. Nothing is
     stored for it and nothing is shared, so it cannot drift from the history it describes.
     Programs never see it (owner decision, 28 September 2026).

     The thresholds are teaching choices made with the author, not physician reviewed:
       Attempted  a finished run of the case.
       Passed     a run that completed every critical action (the debrief's own "All Critical
                  Actions Achieved").
       Mastered   that, with an overall score of MASTER_SCORE or more, in the default mode
                  (the harder one, where the nurse prompts late).
     ========================================================================== */
  const MASTER_SCORE = 90;
  const MASTER_MODE = ((typeof SHARED==='object'&&SHARED.difficulty)||{}).default||'normal';
  const TIERS = {
    new:      {rank:0, label:'Not started'},
    tried:    {rank:1, label:'Attempted'},
    passed:   {rank:2, label:'Passed'},
    mastered: {rank:3, label:'Mastered'}};
  const OUTCOME={all:['All critical actions','ok'], missed:['Critical actions missed','warn'], failed:['Case failed','harm']};
  const ENDED_BY={completed:'Handed over', clock:'Ran out of time', action:'Ended by an action',
                  harmful_action:'Stopped by a harmful action', early_exit:'Ended early'};
  let tab='cases', feedback=null;

  const caseNum = prefix => { const c=CASES[caseIndex(prefix)]; return (c&&c.card&&c.card.number)||null; };
  const caseCat = prefix => { const c=CASES[caseIndex(prefix)]; return (c&&c.card&&c.card.category)||'Cases'; };
  const caseName = prefix => { const n=caseNum(prefix); return (n?'Case '+n+', ':'')+caseTitle(prefix); };
  const dayKey = d => { const x=new Date(d); return x.getFullYear()+'-'+(x.getMonth()+1)+'-'+x.getDate(); };
  const plural = (n,w) => n+' '+w+(n===1?'':'s');

  /* Everything the dashboard shows, from the runs. */
  function derive(){
    const fin=runs.filter(r=>r.status==='finished')
      .sort((a,b)=>String(a.finished_at||'').localeCompare(String(b.finished_at||'')));
    const per={};
    CASES.forEach(c=>{ per[c.prefix]={tier:'new', best:null, first:null, attempts:0, crit:null, open:openRun(c.prefix)}; });
    for(const r of fin){
      const p=per[r.case_prefix]; if(!p) continue;
      p.attempts++;
      const s=r.summary||{};
      const scored=s.scored!==false&&typeof r.score_pct==='number'&&r.outcome!=='failed';
      if(scored){ if(p.first===null) p.first=r.score_pct; if(p.best===null||r.score_pct>p.best) p.best=r.score_pct; }
      if(s.critical&&s.critical.total&&(!p.crit||s.critical.done>p.crit.done)) p.crit={done:s.critical.done, total:s.critical.total};
      let t='tried';
      if(r.outcome==='all'){ t='passed'; if(scored&&r.score_pct>=MASTER_SCORE&&r.mode===MASTER_MODE) t='mastered'; }
      if(TIERS[t].rank>TIERS[p.tier].rank) p.tier=t;
    }
    const list=Object.values(per), N=CASES.length;
    const passed=list.filter(p=>TIERS[p.tier].rank>=2).length;
    const mastered=list.filter(p=>p.tier==='mastered').length;
    const critDone=list.reduce((s,p)=>s+(p.crit?p.crit.done:0),0);
    const critTotal=list.reduce((s,p)=>s+(p.crit?p.crit.total:0),0);
    /* The streak: calendar days, in the learner's own time zone, with a finished case. It
       survives until the end of today, so a learner who practised yesterday has not lost it
       yet. They are told so, once, without a countdown. */
    const days=new Set(fin.map(r=>dayKey(r.finished_at)));
    const d=new Date(); d.setHours(0,0,0,0);
    const today=days.has(dayKey(d));
    if(!today) d.setDate(d.getDate()-1);
    let current=0; while(days.has(dayKey(d))){ current++; d.setDate(d.getDate()-1); }
    const sorted=[...days].map(k=>{ const [y,m,dd]=k.split('-').map(Number); return new Date(y,m-1,dd).getTime(); }).sort((a,b)=>a-b);
    let longest=0, run=0;
    sorted.forEach((t,i)=>{ run=(i&&Math.round((t-sorted[i-1])/864e5)===1)?run+1:1; longest=Math.max(longest,run); });
    const cats=[...new Set(CASES.map(c=>(c.card&&c.card.category)||'Cases'))];
    const catsTried=new Set(fin.filter(r=>per[r.case_prefix]).map(r=>caseCat(r.case_prefix))).size;
    const cleanRuns=fin.filter(r=>r.outcome==='all').length;
    const comeback=list.some(p=>p.best!==null&&p.first!==null&&p.best-p.first>=20);
    const milestones=[
      {id:'first',   icon:'flag',   title:'First case',        desc:'Finish any case.',                                have:fin.length,  need:1},
      {id:'clean',   icon:'check',  title:'Clean run',         desc:'Complete every critical action in one case.',     have:cleanRuns?1:0, need:1},
      {id:'master',  icon:'star',   title:'Mastery',           desc:'Master a case: every critical action and '+MASTER_SCORE+'% or more in '+modeLabel(MASTER_MODE)+' mode.', have:mastered?1:0, need:1},
      {id:'systems', icon:'grid',   title:'Every system',      desc:'Finish a case in every category.',                have:catsTried,   need:cats.length},
      {id:'half',    icon:'half',   title:'Half the board',    desc:'Pass half of the cases.',                         have:passed,      need:Math.max(1,Math.ceil(N/2))},
      {id:'full',    icon:'full',   title:'Full board',        desc:'Pass every case.',                                have:passed,      need:Math.max(1,N)},
      {id:'streak',  icon:'flame',  title:'Three days running',desc:'Finish a case on three days in a row.',           have:longest,     need:3},
      {id:'ten',     icon:'stack',  title:'Ten cases',         desc:'Finish ten cases.',                               have:fin.length,  need:10},
      {id:'comeback',icon:'up',     title:'Comeback',          desc:'Raise your best score on a case by 20 points.',   have:comeback?1:0, need:1}
    ].map(m=>Object.assign(m,{earned:m.have>=m.need}));
    /* Next up: a case to open now. A run in progress comes first (Continue shows it), then
       the lowest-numbered case not yet passed, then the passed case furthest from mastery. */
    const byNum=CASES.map(c=>c.prefix).sort((a,b)=>(caseNum(a)||1e9)-(caseNum(b)||1e9));
    let next=byNum.find(p=>TIERS[per[p].tier].rank<2&&!per[p].open)||null, nextWhy='';
    if(next) nextWhy=per[next].attempts?'Not passed yet':'Not started';
    else {
      const cand=byNum.filter(p=>per[p].tier==='passed'&&!per[p].open).sort((a,b)=>(per[a].best||0)-(per[b].best||0));
      if(cand.length){ next=cand[0]; nextWhy='Passed. Mastery needs every critical action and '+MASTER_SCORE+'% in '+modeLabel(MASTER_MODE)+' mode'; }
    }
    return {per, N, passed, mastered, critDone, critTotal, finished:fin.length,
            streak:{current, today, atRisk:!today&&current>0, longest}, milestones, next, nextWhy, fin};
  }

  /* What changed with the case just finished. Said plainly, and said even when nothing
     improved, so the learner always hears back. */
  function diff(before, after, prefix){
    const b=before.per[prefix]||{}, a=after.per[prefix]||{}, items=[];
    const name=caseName(prefix);
    if(a.best!==null&&(b.best===null||a.best>b.best))
      items.push({kind:'best', text: b.best===null?`First score on ${name}: ${a.best}%.`:`New best on ${name}: ${b.best}% to ${a.best}%.`});
    if(TIERS[a.tier]&&TIERS[b.tier]&&TIERS[a.tier].rank>TIERS[b.tier].rank&&a.tier!=='tried')
      items.push({kind:'tier', text:`${name} is now ${TIERS[a.tier].label}.`});
    after.milestones.forEach(m=>{ const o=before.milestones.find(x=>x.id===m.id); if(m.earned&&o&&!o.earned) items.push({kind:'milestone', id:m.id, text:`Milestone earned: ${m.title}.`}); });
    if(after.streak.current>before.streak.current&&after.streak.current>1)
      items.push({kind:'streak', text:`${plural(after.streak.current,'day')} in a row.`});
    if(!items.length){
      const last=after.fin.filter(r=>r.case_prefix===prefix).slice(-1)[0];
      items.push({kind:'done', text:`Finished ${name}.`+(a.best!==null?` Your best stays at ${a.best}%.`:'')+
        (last&&last.outcome!=='all'?' Every critical action is what passes it.':'')});
    }
    return {prefix, items};
  }

  /* ---- small drawings ---- */
  const ICON={
    flag:'<path d="M6 21V4M6 4h11l-2 4 2 4H6"/>',
    check:'<path d="M5 12.5l4.2 4.3L19 7"/>',
    star:'<path d="M12 3.6l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/>',
    grid:'<rect x="4" y="4" width="6.5" height="6.5" rx="1.4"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.4"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.4"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.4"/>',
    half:'<circle cx="12" cy="12" r="8"/><path d="M12 4v16" /><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>',
    full:'<circle cx="12" cy="12" r="8" fill="currentColor"/>',
    flame:'<path d="M12 3c1 3.2 5 5.4 5 10a5 5 0 0 1-10 0c0-2.4 1.3-3.8 2.4-5 .2 1.6 1 2.6 2.1 3 .3-2.7-.6-5.2.5-8z"/>',
    stack:'<path d="M4 8l8-4 8 4-8 4z"/><path d="M4 12l8 4 8-4"/><path d="M4 16l8 4 8-4"/>',
    up:'<path d="M5 17l5-5 3 3 6-6"/><path d="M14 9h5v5"/>',
    play:'<path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/>',
    x:'<path d="M6 6l12 12M18 6L6 18"/>'
  };
  const icon = (k,cls) => `<svg class="${cls||'ic'}" viewBox="0 0 24 24" aria-hidden="true">${ICON[k]||''}</svg>`;
  function ringSvg(f,r,w,cls){
    f=Math.max(0,Math.min(1,f||0)); const s=2*(r+w), c=2*Math.PI*r;
    return `<svg class="${cls}" viewBox="0 0 ${s} ${s}" aria-hidden="true"><circle class="t" cx="${s/2}" cy="${s/2}" r="${r}" stroke-width="${w}"/>`+
      (f>0?`<circle class="f" cx="${s/2}" cy="${s/2}" r="${r}" stroke-width="${w}" stroke-dasharray="${(f*c).toFixed(2)} ${c.toFixed(2)}" transform="rotate(-90 ${s/2} ${s/2})"/>`:'')+`</svg>`;
  }

  /* ---- the case cards (ui.js renderPicker asks for each one) ---- */
  function cardInfo(prefix){
    if(!on()||listState!=='ready') return {cls:'', html:'', aria:''};
    const D=derive(), p=D.per[prefix]; if(!p) return {cls:'', html:'', aria:''};
    const T=TIERS[p.tier];
    const sub=[p.best!==null?'Best '+p.best+'%':'', p.attempts?plural(p.attempts,'attempt'):''].filter(Boolean).join(' · ');
    const html=`<span class="dc-foot">
        <span class="dc-ring">${ringSvg(p.best!==null?p.best/100:0,14,3.5,'dc-svg')}${p.tier==='mastered'?icon('star','dc-star'):''}</span>
        <span class="dc-st"><b>${T.label}</b>${sub?`<span>${escP(sub)}</span>`:''}</span>
        ${p.open?`<span class="dc-go">${icon('play','ic')}In progress · ${escP(mmssP(p.open.sim_seconds))}</span>`:''}
      </span>`;
    const aria=[T.label+'.', p.best!==null?'Best score '+p.best+' percent.':'', p.attempts?plural(p.attempts,'attempt')+'.':'',
                p.open?'In progress at '+mmssP(p.open.sim_seconds)+'.':''].filter(Boolean).join(' ');
    return {cls:' t-'+p.tier+(p.open?' t-open':''), html, aria};
  }
  /* Kept for anything that still asks for the old one-line badge. */
  function rowBadge(prefix){ const c=cardInfo(prefix); return {html:c.html, aria:c.aria}; }

  /* ---- the panels ---- */
  function when(iso){
    const d=new Date(iso); if(isNaN(d)) return '';
    return d.toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'})+', '+
           d.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
  }
  function modeLabel(m){
    const D=(typeof SHARED==='object'&&SHARED.difficulty)||{};
    return ((D.modes||{})[m]||{}).label||m||'';
  }
  function statsHTML(D){
    const s=D.streak;
    const tile=(n,label,cls,note)=>`<div class="ds-tile${cls?' '+cls:''}"><b>${n}</b><span>${escP(label)}</span>${note?`<em>${escP(note)}</em>`:''}</div>`;
    return `<div class="ds-main" role="img" aria-label="${D.passed} of ${D.N} cases passed">
        ${ringSvg(D.N?D.passed/D.N:0,40,8,'ds-svg')}
        <div class="ds-num"><b>${D.passed}</b><small>/${D.N}</small></div>
        <div class="ds-lab">Cases passed</div>
      </div>
      <div class="ds-tiles">
        ${tile(D.mastered,'Mastered','t-m')}
        ${tile(D.critTotal?`${D.critDone}<small>/${D.critTotal}</small>`:'–','Critical actions found','t-c')}
        ${tile(s.current,'Day streak','t-s'+(s.atRisk?' risk':''), s.atRisk?'Finish a case today to keep it':(s.longest>s.current?'Longest '+s.longest:''))}
        ${tile(D.finished,'Cases finished','t-f')}
      </div>`;
  }
  function feedbackHTML(){
    if(!feedback||!feedback.items.length) return '';
    const glyph={best:'up', tier:'star', milestone:'check', streak:'flame', done:'flag'};
    return `<div class="db-fb" role="status">
      <ul>${feedback.items.map(i=>`<li class="fb-${i.kind}">${icon(glyph[i.kind]||'check','ic')}<span>${escP(i.text)}</span></li>`).join('')}</ul>
      <button class="db-x" type="button" data-fbclose="1" aria-label="Dismiss">${icon('x','ic')}</button></div>`;
  }
  /* The patient on a card: the same silhouette the case list uses. */
  function faceHTML(prefix){
    const c=CASES[caseIndex(prefix)]||{}, p=(c.case&&c.case.patient)||c.patient||{};
    const s=String(p.sex||'').toLowerCase();
    return `<span class="wl-face cx-face">${(s==='male'||s==='female')?`<i class="${s}"></i>`:''}</span>`;
  }
  function whoLine(prefix){
    const c=CASES[caseIndex(prefix)]||{}, p=(c.case&&c.case.patient)||c.patient||{};
    return [p.age!=null?p.age:'', ({male:'M',female:'F'})[String(p.sex||'').toLowerCase()]||''].filter(x=>x!=='').join(' ');
  }
  const runMins = prefix => { const c=CASES[caseIndex(prefix)]; const s=c&&c.card&&c.card.runtime_seconds; return s?Math.round(s/60):null; };
  /* Continue and Next up, as the two things to do now (author instruction, 28 October 2026:
     "more prominently and artfully displayed"). A run in progress is the lead card, with its
     case time as a ring round the patient and as a bar. Next up stands beside it. */
  function continueHTML(D){
    const open=runs.filter(r=>r.status==='in_progress');
    const cards=open.map(r=>{
      const pre=r.case_prefix, stale=r.version_key!==KEYS[pre], gone=caseIndex(pre)<0;
      const mins=runMins(pre), frac=mins?Math.min(1,(r.sim_seconds||0)/(mins*60)):0;
      return `<article class="cx cx-go">
        <div class="cx-art"><span class="cx-ringwrap">${ringSvg(frac,44,5,'cx-svg')}${faceHTML(pre)}</span></div>
        <div class="cx-body">
          <div class="cx-kind">${icon('play','ic')}Continue where you left off</div>
          <h3 class="cx-title">${caseNo(pre)}${escP(caseTitle(pre))}</h3>
          <div class="cx-meta">${escP([whoLine(pre),modeLabel(r.mode),'saved '+when(r.updated_at)].filter(Boolean).join(' · '))}</div>
          <div class="cx-time"><span class="cx-bar"><i style="width:${Math.round(frac*100)}%"></i></span>
            <span class="hm-mono">${escP(mmssP(r.sim_seconds))}${mins?' of about '+mins+' min':' of case time'}</span></div>
          ${stale?'<div class="hm-cw">This case has been improved since. It will start from the beginning.</div>':''}
          <div class="hm-ca">
            ${gone?'':`<button class="btn cx-btn" type="button" data-hmresume="${escP(pre)}">${icon('play','ic')}${stale?'Open':'Resume'}</button>`}
            <button class="hm-link" type="button" data-hmdel="${escP(r.id)}">Discard</button>
          </div>
          ${confirmDel===r.id?confirmHTML(r.id,'Discard this run? It cannot be resumed afterwards.'):''}
        </div>
      </article>`;
    });
    if(D.next){
      const pre=D.next, p=D.per[pre], mins=runMins(pre);
      cards.push(`<article class="cx cx-next t-${p.tier}">
        <div class="cx-art"><span class="cx-ringwrap">${ringSvg(p.best!==null?p.best/100:0,44,5,'cx-svg')}${faceHTML(pre)}</span></div>
        <div class="cx-body">
          <div class="cx-kind">${icon('flag','ic')}Next up</div>
          <h3 class="cx-title">${caseNo(pre)}${escP(caseTitle(pre))}</h3>
          <div class="cx-meta">${escP([whoLine(pre),caseCat(pre),mins?'about '+mins+' min':''].filter(Boolean).join(' · '))}</div>
          <div class="cx-why">${escP(D.nextWhy)}${p.best!==null?' · best '+p.best+'%':''}</div>
          <div class="hm-ca"><button class="btn cx-btn ${open.length?'ghost':''}" type="button" data-hmopencase="${escP(pre)}">${p.attempts?'Try again':'Start'}<span class="cx-arr" aria-hidden="true">→</span></button></div>
        </div>
      </article>`);
    }
    if(!cards.length) return '<p class="hm-empty">Every case is mastered. Nothing is waiting for you.</p>';
    return `<div class="cx-grid${cards.length===1?' one':''}">${cards.join('')}</div>`+
      (open.length?'':'<p class="hm-empty sm">No case in progress. A case you leave before the end is saved and waits here.</p>');
  }
  /* The milestones as a shelf of medals (author instruction, 28 October 2026). An earned one
     is gold. One not yet earned is a dim disc with its progress as a ring round it, and the
     nearest is lit, as the thing to aim at. One earned with the case just played says New. */
  function milestonesHTML(D){
    const got=D.milestones.filter(m=>m.earned).length;
    const near=D.milestones.filter(m=>!m.earned).sort((a,b)=>(b.have/b.need)-(a.have/a.need))[0];
    const isNew=id=>!!(feedback&&feedback.items.some(i=>i.id===id));
    return `<div class="tr-head">
        <h2 id="hm-h3">Milestones</h2>
        <span class="tr-count"><b>${got}</b> of ${D.milestones.length} earned</span>
        ${near?`<span class="tr-next">Next: <b>${escP(near.title)}</b>${near.need>1?', '+escP(Math.min(near.have,near.need)+' of '+near.need):''}. ${escP(near.desc)}</span>`:'<span class="tr-next">Every milestone earned.</span>'}
      </div>
      <ul class="tr-row">${D.milestones.map(m=>{
        const cls=['tr', m.earned?'on':'', near&&near.id===m.id?'next':'', isNew(m.id)?'new':''].filter(Boolean).join(' ');
        const state=m.earned?'Earned':(m.need>1?Math.min(m.have,m.need)+' of '+m.need:'Not yet');
        return `<li class="${cls}" title="${escP(m.desc)}">
          <span class="tr-medal">${m.earned?'':ringSvg(m.have/m.need,33,3,'tr-svg')}<span class="tr-disc">${icon(m.icon,'ic')}</span>${isNew(m.id)?'<span class="tr-newtag">New</span>':''}</span>
          <b class="tr-t">${escP(m.title)}</b>
          <span class="tr-s">${escP(state)}</span>
        </li>`; }).join('')}</ul>`;
  }
  function confirmHTML(id,q){
    return `<div class="hm-confirm" role="group" aria-label="Confirm">
      <span>${escP(q)}</span>
      <button class="btn harm" type="button" data-hmdelok="${escP(id)}">Delete</button>
      <button class="hm-link" type="button" data-hmdelno="1">Cancel</button></div>`;
  }
  /* The debrief's two dials, small: critical actions (green) and the overall score (blue). */
  function ring(f,big,cap,cls,aria){
    f=Math.max(0,Math.min(1,f||0)); const r=23, c=2*Math.PI*r;
    return `<span class="hm-dial ${cls}" role="img" aria-label="${escP(aria)}">
      <span class="hm-ring"><svg viewBox="0 0 56 56" aria-hidden="true">
        <circle class="t" cx="28" cy="28" r="${r}"/>
        ${f>0?`<circle class="f" cx="28" cy="28" r="${r}" stroke-dasharray="${(f*c).toFixed(2)} ${c.toFixed(2)}" transform="rotate(-90 28 28)"/>`:''}
      </svg><span class="hm-dn">${big}</span></span>
      <span class="hm-dc" aria-hidden="true">${escP(cap)}</span></span>`;
  }
  function dialsHTML(crit, scored, pct){
    const a=(crit&&crit.total)
      ? ring(crit.done/crit.total, escP(crit.done)+'/'+escP(crit.total), 'Critical', 'crit',
             crit.done+' of '+crit.total+' critical actions completed')
      : '<span class="hm-dial none" aria-hidden="true"></span>';
    const b=scored
      ? ring(pct/100, escP(pct)+'<small>%</small>', 'Overall', 'ovr', 'Overall score '+pct+' percent')
      : ring(0, 'n/a', 'Overall', 'ovr muted', 'Overall score: not scored');
    return `<span class="hm-dials">${a}${b}</span>`;
  }
  /* The trend: the overall score of the last twenty finished runs, oldest on the left. A run
     the debrief does not score is a short grey stub, so a failure still shows as a run. */
  function trendHTML(D){
    const last=D.fin.slice(-20);
    if(last.length<2) return '';
    const SLOTS=20, W=100/SLOTS, off=SLOTS-last.length;
    const bars=last.map((r,j)=>{ const i=j+off;
      const s=r.summary||{}, scored=s.scored!==false&&typeof r.score_pct==='number'&&r.outcome!=='failed';
      const h=scored?Math.max(3,r.score_pct):3, o=OUTCOME[r.outcome]||['','tried'];
      return `<rect class="tb ${scored?o[1]:'ns'}" x="${(i*W+W*0.18).toFixed(2)}" y="${100-h}" width="${(W*0.64).toFixed(2)}" height="${h}" rx="1"><title>${escP(caseName(r.case_prefix)+': '+(scored?r.score_pct+'%':'not scored')+', '+when(r.finished_at))}</title></rect>`;
    }).join('');
    return `<figure class="db-trend"><figcaption><b>Overall score</b><span>Your last ${last.length} finished runs, oldest first. Green: every critical action. Amber: some missed. Grey: not scored.</span></figcaption>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Bar chart of your last ${last.length} overall scores">
        <line class="tg" x1="0" x2="100" y1="${100-MASTER_SCORE}" y2="${100-MASTER_SCORE}"/>${bars}</svg>
      <div class="db-trend-k"><span>${MASTER_SCORE}% line: the mastery score</span></div></figure>`;
  }
  function attemptsHTML(){
    const done=runs.filter(r=>r.status==='finished');
    if(!done.length) return '<p class="hm-empty">Finished cases appear here with their scores.</p>';
    return '<div class="hm-list">'+done.map(r=>{
      const o=OUTCOME[r.outcome]||['',''], s=r.summary||{}, crit=s.critical||null;
      const scored=s.scored!==false&&typeof r.score_pct==='number';
      const open=openRow===r.id;
      const rows=Array.isArray(s.rows)?s.rows:[];
      return `<div class="hm-row${open?' open':''}">
        <button class="hm-rh" type="button" data-hmopen="${escP(r.id)}" aria-expanded="${open}">
          ${dialsHTML(crit, scored, r.score_pct)}
          <span class="hm-rb">
            <span class="hm-rt">${caseNo(r.case_prefix)}${escP(caseTitle(r.case_prefix))}</span>
            <span class="hm-rm"><span class="hm-tag ${o[1]}">${escP(o[0])}</span>
              <span>${escP(modeLabel(r.mode))}</span><span class="hm-mono">${escP(mmssP(r.sim_seconds))}</span></span>
          </span>
          <span class="hm-rd">${escP(when(r.finished_at||r.updated_at))}</span>
        </button>
        ${open?`<div class="hm-rx">
          <div class="hm-why">${escP(ENDED_BY[r.ended_by]||'')}${scored?'':'. Not scored, as in the debrief'}</div>
          ${rows.map(x=>`<div class="hm-part"><span class="l">${escP(x.label)}</span>
            <span class="bar"><i style="width:${typeof x.pct==='number'?x.pct:0}%"></i></span>
            <span class="p hm-mono">${typeof x.pct==='number'?escP(x.pct)+'%':'–'}</span>
            <span class="d">${escP(x.detail||'')}</span></div>`).join('')}
          <div class="hm-ra"><button class="hm-link" type="button" data-hmdel="${escP(r.id)}">Delete this attempt</button></div>
          ${confirmDel===r.id?confirmHTML(r.id,'Delete this attempt from your history?'):''}
        </div>`:''}
      </div>`;
    }).join('')+'</div>';
  }
  function greeting(){
    const h=new Date().getHours();
    return h<5?'Working late.':h<12?'Good morning.':h<18?'Good afternoon.':'Good evening.';
  }
  function paintTabs(){
    const tabs=$('db-tabs'); if(!tabs) return;
    const signed=on();
    if(!signed) tab='cases';
    tabs.querySelectorAll('[data-dbtab]').forEach(b=>{
      const t=b.dataset.dbtab, sel=t===tab;
      b.setAttribute('aria-selected',String(sel)); b.tabIndex=sel?0:-1;
      if(t==='history') b.hidden=!signed;
    });
    const hc=$('db-hcount'); if(hc) hc.textContent=String(runs.filter(r=>r.status==='finished').length);
    const pc=$('db-cases'), ph=$('db-history');
    if(pc) pc.hidden=tab!=='cases';
    if(ph) ph.hidden=tab!=='history';
  }
  function paintHome(){
    const box=$('wl-home'), pk=$('picker'), st=$('db-stats'), gr=$('db-greet'), hist=$('db-history');
    if(!box||!pk) return;
    const show=on();
    pk.classList.toggle('home-on',show);
    box.hidden=!show; if(st) st.hidden=!show; if(gr) gr.hidden=!show;
    paintTabs();
    if(!show){ box.innerHTML=''; if(st) st.innerHTML=''; if(hist) hist.innerHTML=''; return; }
    if(gr) gr.textContent=greeting();
    if(listState==='loading'||listState==='idle'){
      if(st) st.innerHTML='<div class="ds-skel"></div><div class="ds-skel"></div><div class="ds-skel"></div>';
      box.innerHTML='<p class="hm-empty">Loading your progress…</p>';
      if(hist) hist.innerHTML='';
      return;
    }
    if(listState==='error'){
      if(st) st.innerHTML='';
      box.innerHTML='<p class="hm-empty">Your progress could not be loaded. <button class="hm-link" type="button" data-hmretry="1">Try again</button></p>';
      return;
    }
    const D=derive();
    if(st) st.innerHTML=statsHTML(D);
    box.innerHTML=`${feedbackHTML()}
      <section class="db-play" aria-label="Continue">${continueHTML(D)}</section>
      <section class="db-trophy" aria-labelledby="hm-h3">${milestonesHTML(D)}</section>`;
    if(hist) hist.innerHTML=`${trendHTML(D)}
      <section class="hm-sec" aria-labelledby="hm-h2"><h2 id="hm-h2">Your attempts</h2>${attemptsHTML()}</section>
      <p class="hm-note">While a case is in progress, your account keeps what you did and asked in it, so that
        you can resume. When the case ends only the score summary is kept. You can delete any of it here.
        Nothing here is shared with anyone.</p>`;
  }
  function bindHome(){
    const handle=e=>{
      const t=e.target.closest('button'); if(!t) return;
      if(t.dataset.dbtab){ e.stopPropagation(); tab=t.dataset.dbtab; paintTabs(); return; }
      if(!t.closest('#wl-home,#db-history')) return;
      e.stopPropagation();
      if(t.dataset.fbclose){ feedback=null; paintHome(); return; }
      if(t.dataset.hmretry){ refresh(); return; }
      if(t.dataset.hmopen){ openRow=openRow===t.dataset.hmopen?null:t.dataset.hmopen; confirmDel=null; paintHome(); return; }
      if(t.dataset.hmdel){ confirmDel=t.dataset.hmdel; paintHome(); return; }
      if(t.dataset.hmdelno){ confirmDel=null; paintHome(); return; }
      if(t.dataset.hmdelok){ del(t.dataset.hmdelok); return; }
      if(t.dataset.hmopencase){ const i=caseIndex(t.dataset.hmopencase); if(i>=0) chooseCase(i); return; }
      if(t.dataset.hmresume){
        const i=caseIndex(t.dataset.hmresume); if(i<0) return;
        want=t.dataset.hmresume;
        chooseCase(i);
      }
    };
    ['wl-home','db-history','db-tabs'].forEach(id=>{ const n=$(id); if(n) n.addEventListener('click',handle); });
    /* Arrow keys move between the two tabs, as a tab list should. */
    const tabs=$('db-tabs');
    if(tabs) tabs.addEventListener('keydown',e=>{
      if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight') return;
      const vis=[...tabs.querySelectorAll('[data-dbtab]')].filter(b=>!b.hidden);
      const i=vis.findIndex(b=>b.dataset.dbtab===tab);
      const n=vis[(i+(e.key==='ArrowRight'?1:vis.length-1))%vis.length]; if(!n) return;
      e.preventDefault(); e.stopPropagation(); tab=n.dataset.dbtab; paintTabs(); n.focus();
    });
  }
  async function del(id){
    const r=runs.find(x=>x.id===id); confirmDel=null;
    if(!r){ paintHome(); return; }
    runs=runs.filter(x=>x.id!==id); paintHome();
    if(typeof renderPicker==='function') renderPicker();
    A.track(r.status==='finished'?'attempt_deleted':'run_discarded',{case:r.case_prefix, reason:'deleted'});
    try{
      const {error}=await client.from('runs').delete().eq('id',id);
      if(error) throw error;
    }catch(e){ refresh(); }
  }

  return {init, onSession, refresh, touch, start, detach, finish, flush, kept, onSplash, rowBadge, cardInfo,
          active:()=>on()&&!!cur&&!cur.gone, enabled:on,
          /* for the site check */ _state:()=>({uid, listState, runs:runs.length, cur:cur&&{...cur}, dirty, saveFailed, tab, feedback}),
          _derive:()=>derive()};
})();
