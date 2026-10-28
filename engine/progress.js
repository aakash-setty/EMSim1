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
    refresh();
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

  /* ---- the case board ---- */
  function bestOf(prefix){
    let b=null;
    for(const r of runs) if(r.status==='finished'&&r.case_prefix===prefix&&typeof r.score_pct==='number'&&r.outcome!=='failed')
      if(b===null||r.score_pct>b) b=r.score_pct;
    return b;
  }
  /* The small line under a case row: a run in progress, or the best scored attempt. */
  function rowBadge(prefix){
    if(!on()||listState!=='ready') return {html:'',aria:''};
    const r=openRun(prefix);
    if(r) return {html:`<span class="wl-prog go">In progress · ${escP(mmssP(r.sim_seconds))}</span>`,
                  aria:'In progress at '+mmssP(r.sim_seconds)+'.'};
    const b=bestOf(prefix), n=runs.filter(x=>x.status==='finished'&&x.case_prefix===prefix).length;
    if(n) return {html:`<span class="wl-prog">${b===null?'':'Best '+b+'% · '}${n} attempt${n===1?'':'s'}</span>`,
                  aria:(b===null?'':'Best score '+b+' percent. ')+n+' attempt'+(n===1?'':'s')+'.'};
    return {html:'',aria:''};
  }

  /* ---- the home panel (the left side of the case board, signed in) ---- */
  const OUTCOME={all:['All critical actions','ok'], missed:['Critical actions missed','warn'], failed:['Case failed','harm']};
  const ENDED_BY={completed:'Handed over', clock:'Ran out of time', action:'Ended by an action',
                  harmful_action:'Stopped by a harmful action', early_exit:'Ended early'};
  function when(iso){
    const d=new Date(iso); if(isNaN(d)) return '';
    return d.toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'})+', '+
           d.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'});
  }
  function modeLabel(m){
    const D=(typeof SHARED==='object'&&SHARED.difficulty)||{};
    return ((D.modes||{})[m]||{}).label||m||'';
  }
  function continueHTML(){
    const open=runs.filter(r=>r.status==='in_progress');
    if(!open.length) return '<p class="hm-empty">No case in progress. A case you leave before the end is saved here.</p>';
    return '<div class="hm-cont">'+open.map(r=>{
      const stale=r.version_key!==KEYS[r.case_prefix], gone=caseIndex(r.case_prefix)<0;
      return `<div class="hm-card">
        <div class="hm-ct">${escP(caseTitle(r.case_prefix))}</div>
        <div class="hm-cm"><span class="hm-mono">${escP(mmssP(r.sim_seconds))}</span> of case time · ${escP(modeLabel(r.mode))} · saved ${escP(when(r.updated_at))}</div>
        ${stale?'<div class="hm-cw">This case has been improved since. It will start from the beginning.</div>':''}
        <div class="hm-ca">
          ${gone?'':`<button class="btn" type="button" data-hmresume="${escP(r.case_prefix)}">${stale?'Open':'Resume'}</button>`}
          <button class="hm-link" type="button" data-hmdel="${escP(r.id)}">Discard</button>
        </div>
        ${confirmDel===r.id?confirmHTML(r.id,'Discard this run? It cannot be resumed afterwards.'):''}
      </div>`;
    }).join('')+'</div>';
  }
  function confirmHTML(id,q){
    return `<div class="hm-confirm" role="group" aria-label="Confirm">
      <span>${escP(q)}</span>
      <button class="btn harm" type="button" data-hmdelok="${escP(id)}">Delete</button>
      <button class="hm-link" type="button" data-hmdelno="1">Cancel</button></div>`;
  }
  /* The debrief's two dials, small (author instruction, 28 October 2026): critical actions
     (green ring, the count in the centre) and the overall score (blue ring). A case with no
     critical actions has no first dial, as in the debrief, and keeps its slot empty so the
     rows line up. A run the debrief does not score shows an empty ring and "n/a". */
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
            <span class="hm-rt">${escP(caseTitle(r.case_prefix))}</span>
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
  function paintHome(){
    const box=$('wl-home'), pk=$('picker');
    if(!box||!pk) return;
    const show=on();
    pk.classList.toggle('home-on',show);
    box.hidden=!show;
    if(!show){ box.innerHTML=''; return; }
    let inner;
    if(listState==='loading'||listState==='idle') inner='<p class="hm-empty">Loading your progress…</p>';
    else if(listState==='error') inner='<p class="hm-empty">Your progress could not be loaded. <button class="hm-link" type="button" data-hmretry="1">Try again</button></p>';
    else inner=`<section class="hm-sec" aria-labelledby="hm-h1"><h2 id="hm-h1">Continue</h2>${continueHTML()}</section>
      <section class="hm-sec" aria-labelledby="hm-h2"><h2 id="hm-h2">Your attempts</h2>${attemptsHTML()}</section>
      <p class="hm-note">While a case is in progress, your account keeps what you did and asked in it, so that
        you can resume. When the case ends only the score summary is kept. You can delete any of it here.</p>`;
    box.innerHTML=inner;
  }
  function bindHome(){
    const box=$('wl-home'); if(!box) return;
    box.addEventListener('click',e=>{
      const t=e.target.closest('button'); if(!t) return;
      e.stopPropagation();
      if(t.dataset.hmretry){ refresh(); return; }
      if(t.dataset.hmopen){ openRow=openRow===t.dataset.hmopen?null:t.dataset.hmopen; confirmDel=null; paintHome(); return; }
      if(t.dataset.hmdel){ confirmDel=t.dataset.hmdel; paintHome(); return; }
      if(t.dataset.hmdelno){ confirmDel=null; paintHome(); return; }
      if(t.dataset.hmdelok){ del(t.dataset.hmdelok); return; }
      if(t.dataset.hmresume){
        const i=caseIndex(t.dataset.hmresume); if(i<0) return;
        want=t.dataset.hmresume;
        chooseCase(i);
      }
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

  return {init, onSession, refresh, touch, start, detach, finish, flush, kept, onSplash, rowBadge,
          active:()=>on()&&!!cur&&!cur.gone, enabled:on,
          /* for the site check */ _state:()=>({uid, listState, runs:runs.length, cur:cur&&{...cur}, dirty, saveFailed})};
})();
