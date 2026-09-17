/* ============================================================
   VOICE ORDERS. A microphone beside the monitor that takes a spoken string of
   investigations, interventions and stabilization acts, shows what it understood
   as a list the resident edits, and submits the list through the same log path
   as Submit Order.

   Three parts, in order:
     1. normalise()   the pipeline that turns speech, or a table phrase, into the
                      canonical token string both are compared as. It is a mirror of
                      the one in catalog/build_voice_aliases.py, which is what wrote
                      the table; engine-tests.js asserts the two agree on every phrase.
     2. parse()       greedy longest-phrase matching over the bound action table.
                      Pure: no DOM, no state beyond the index built at bind.
     3. the recorder and the dropdown, which exist only in a browser.

   WHAT THE PARSER IS AND IS NOT. It recognises what a phrase MEANS in the catalog's
   vocabulary. It does not decide whether an order is right, and it does not turn a
   diagnosis into its workup: "sepsis labs" is answered with "name the labs", because
   a parser that expanded it would be taking the case for the resident. The two
   author-stated exceptions, "calcium" as the level and "CMP" as Chem 7 plus the
   hepatic panel, live in the table with that note beside them. A phrase that could
   mean two entries is returned as a choice rather than resolved by frequency, since
   the cost of a silently wrong order in a teaching tool is the lesson itself.

   The recogniser is the browser's (Web Speech API). Chrome, Edge and Safari have it;
   Firefox does not, and on a network that blocks the vendor's speech service it fails
   the same way. Either way the button still opens the list with a text box, so an
   order can be typed in the same words and parsed by the same code.
   ============================================================ */
const VOICE=(function(){
  'use strict';
  /* ---------- 1. normalisation ---------- */
  let TAB=null;                 // the normalisation tables from the voice block
  let CANON=[];                 // [RegExp, replacement] pairs, compiled once
  let FILL=new Set(), UNIT=new Set(), NUM={};
  function setTables(t){
    TAB=t; NUM=t.numberWords||{}; FILL=new Set(t.fillers||[]); UNIT=new Set(t.units||[]);
    /* The Python side matches `(?<= )pat(?= )` and leaves the leading space in place.
       Lookbehind is not universal in Safari, so the JS pattern consumes the leading
       space and the replacement puts it back. Same result on the same string. */
    CANON=(t.canon||[]).map(([p,r])=>[new RegExp(' '+p+'(?= )','g'),' '+r.replace(/\\(\d)/g,'$$$1')]);
  }
  function normalise(text){
    if(!TAB) return '';
    let t=String(text||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
    if(!t) return '';
    t=t.split(' ').map(w=>NUM[w]!==undefined?NUM[w]:w).join(' ');
    /* To a fixed point, as the Python side does: one rule's output can be the next
       rule's input, and dropping a filler can bring two words a rule names together.
       Four rounds is the same bound. */
    for(let pass=0;pass<4;pass++){
      const before=t;
      t=' '+t+' ';
      for(const [rx,rep] of CANON){ t=t.replace(rx,rep); t=t.replace(/ {2,}/g,' '); }
      t=t.split(' ').filter(w=>w&&!FILL.has(w)&&!UNIT.has(w)).join(' ');
      if(t===before) break;
    }
    /* Bare numbers go last, so a volume a rule names ("500 of normal saline") is still
       there when the fluid name has been reduced to the word the rule expects. */
    return t.split(' ').filter(w=>w&&!/^[0-9]+$/.test(w)).join(' ');
  }


  /* ---------- 2. the index and the parser ---------- */
  /* phrase -> {kind:'act'|'expand'|'ambig'|'unavail', ids:[actId...], hint} */
  let INDEX=new Map(), MAXLEN=1, SINGLES=[];
  let RESOLVE=null;             // catalog id -> bound action id, or null if not orderable
  function orderable(id){
    const a=(typeof ACT!=='undefined'&&ACT)?ACT[id]:null;
    return !!(a&&PROTO&&PROTO.orderableTabs.indexOf(a.tab)>=0);
  }
  function resolveCatalog(cid){
    const eff=((typeof PACK!=='undefined'&&PACK&&PACK.bindings)||{})[cid]||cid;
    return orderable(eff)?eff:null;
  }
  function put(phrase,entry,authored){
    if(!phrase) return;
    const have=INDEX.get(phrase);
    if(have){
      if(have.authored) return;           // the table wins over a name-derived phrase
      if(authored){ INDEX.set(phrase,Object.assign({authored:true},entry)); return; }
      /* Two derived names collide: offer both rather than pick. */
      if(have.kind==='act'&&entry.kind==='act'&&have.ids[0]!==entry.ids[0])
        INDEX.set(phrase,{kind:'ambig',ids:have.ids.concat(entry.ids)});
      return;
    }
    INDEX.set(phrase,Object.assign({authored:!!authored},entry));
  }
  /* Phrases a display name gives for free: the name itself, each half of an "A - B"
     name in both orders, the text inside and outside a parenthesis, and the id. */
  function derived(id){
    const a=ACT[id]; const out=new Set();
    const name=a.name||'';
    out.add(name);
    const dash=name.split(/\s+-\s+/);
    if(dash.length===2){ out.add(dash[0]+' '+dash[1]); out.add(dash[1]+' '+dash[0]); }
    const par=name.match(/^(.*?)\s*\((.*?)\)\s*$/);
    if(par){ out.add(par[1]); out.add(par[2]); }
    out.add(id.replace(/_/g,' '));
    return [...out];
  }
  function build(data){
    INDEX=new Map(); MAXLEN=1; SINGLES=[];
    if(!data||!data.normalisation) return;
    setTables(data.normalisation);
    const A=data.aliases||{}, E=data.expansions||{}, M=data.ambiguous||{}, U=data.unavailable||{}, H=data.hints||[];
    for(const cid in A){
      const id=resolveCatalog(cid); if(!id) continue;
      for(const p of A[cid]) put(normalise(p),{kind:'act',ids:[id]},true);
    }
    for(const p in E){
      const ids=E[p].map(resolveCatalog).filter(Boolean);
      if(ids.length) put(normalise(p),{kind:ids.length>1?'expand':'act',ids},true);
    }
    for(const p in M){
      const ids=[...new Set(M[p].map(resolveCatalog).filter(Boolean))];
      if(ids.length>1) put(normalise(p),{kind:'ambig',ids},true);
      else if(ids.length===1) put(normalise(p),{kind:'act',ids},true);
    }
    for(const p in U) put(normalise(p),{kind:'unavail',ids:[],hint:typeof U[p]==='number'?(H[U[p]]||''):String(U[p]||'')},true);
    for(const id in ACT){
      if(!orderable(id)) continue;
      for(const p of derived(id)) put(normalise(p),{kind:'act',ids:[id]},false);
    }
    for(const k of INDEX.keys()){
      const n=k.split(' ').length; if(n>MAXLEN) MAXLEN=n;
      if(n===1&&k.length>=5) SINGLES.push(k);
    }
  }
  /* Optimal string alignment distance, capped. The same measure the interview matcher
     uses for spelling repair, kept local so this file evaluates without ui.js. */
  function osa(a,b,max){
    if(Math.abs(a.length-b.length)>max) return max+1;
    const d=[]; for(let i=0;i<=a.length;i++){ d[i]=[i]; }
    for(let j=1;j<=b.length;j++) d[0][j]=j;
    for(let i=1;i<=a.length;i++){
      let row=max+1;
      for(let j=1;j<=b.length;j++){
        const c=a[i-1]===b[j-1]?0:1;
        let v=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+c);
        if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1]) v=Math.min(v,d[i-2][j-2]+1);
        d[i][j]=v; if(v<row) row=v;
      }
      if(row>max) return max+1;
    }
    return d[a.length][b.length];
  }
  /* One misheard word. Tolerance grows with length, and a candidate is accepted only
     when it is the ONLY phrase at that distance: two drugs one letter apart are not a
     guess the parser is allowed to make. */
  function fuzzy(w){
    if(w.length<6) return null;
    const max=w.length>=10?2:1;
    let best=null, n=0, bd=max+1;
    for(const k of SINGLES){
      const d=osa(w,k,max);
      if(d<bd){ bd=d; best=k; n=1; } else if(d===bd) n++;
    }
    return (best&&bd<=max&&n===1)?best:null;
  }
  const RATIONALE=new Set(['for','because','since','as','so','if','when','while','until','after','before','given','due','secondary','cause','considering']);
  /* Canonical tokens that are qualifiers rather than orders. Left over on their own
     they are a dose or a route that nothing needed, not a thing the parser missed. */
  const NOISE=new Set(['rate','drip','bolus','transfuse','im','oral','rectal','sublingual','intranasal','noncontrast','contrast',
                       'second','stop','maintenance','kvo','wideopen','liter','twoliters','halfliter','quarterliter','fifteenliters',
                       'someliters','thirtyperkilo','precautions','percent','headup','crossmatch','mri','xr','ct','cta']);
  function flush(res,rows){
    if(!res.length) return;
    const kept=res.filter(w=>!NOISE.has(w));
    if(kept.length&&!RATIONALE.has(res[0])) rows.push({kind:'unknown',heard:kept.join(' ')});
    res.length=0;
  }
  function rowsFor(e,heard,extra){
    const base=Object.assign({heard},extra||{});
    if(e.kind==='act') return [Object.assign({kind:'ok',id:e.ids[0]},base)];
    if(e.kind==='expand') return e.ids.map(id=>Object.assign({kind:'ok',id,via:heard},base));
    if(e.kind==='ambig') return [Object.assign({kind:'ambiguous',ids:e.ids.slice()},base)];
    return [Object.assign({kind:'unavailable',hint:e.hint||''},base)];
  }
  /* The parser. Returns rows in the order they were said, one per order, with the
     same entry never twice. */
  function parse(text){
    const toks=normalise(text).split(' ').filter(Boolean);
    const rows=[], res=[];
    let i=0;
    while(i<toks.length){
      let hit=null, len=0;
      for(let L=Math.min(MAXLEN,toks.length-i);L>=1;L--){
        const e=INDEX.get(toks.slice(i,i+L).join(' '));
        if(e){ hit=e; len=L; break; }
      }
      let extra=null;
      if(!hit){
        const f=fuzzy(toks[i]);
        if(f){ hit=INDEX.get(f); len=1; extra={uncertain:true,heardAs:f}; }
      }
      if(hit){ flush(res,rows); rows.push(...rowsFor(hit,toks.slice(i,i+len).join(' '),extra)); i+=len; }
      else { res.push(toks[i]); i++; }
    }
    flush(res,rows);
    const seen=new Set(), out=[];
    for(const r of rows){
      const key=r.kind==='ok'?'ok:'+r.id:(r.kind==='ambiguous'?'am:'+r.ids.join(','):r.kind+':'+r.heard);
      if(seen.has(key)) continue;
      seen.add(key); out.push(r);
    }
    return out;
  }

  /* ---------- 3. recorder and dropdown ---------- */
  /* Two states, two icons. The microphone means "nothing is being recorded, press to
     start"; the pause bars mean "something is, press to stop". A red button alone did
     not say which of the two it was, and the one thing a live microphone must never be
     is ambiguous. The bars and the dot are filled rather than stroked, because the
     stroke weight the rest of the interface uses reads as an outline of a shape rather
     than as the shape, and a transport control is read at a glance. */
  const ICON_MIC='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/>'
                +'<path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/></svg>';
  const ICON_PAUSE='<svg viewBox="0 0 24 24" aria-hidden="true">'
                  +'<rect x="8.5" y="5" width="3" height="14" rx="1" fill="currentColor" stroke="none"/>'
                  +'<rect x="12.5" y="5" width="3" height="14" rx="1" fill="currentColor" stroke="none"/></svg>';
  /* The panel's button draws at 12 pixels, where the 24-unit icons above collapse: two
     3-unit bars become a pair of 1.5-pixel lines with half a pixel between them, which
     reads as one bar. These are the same two shapes on a 12-unit grid, so the gap
     survives the size. */
  const ICON_PAUSE_SM='<svg viewBox="0 0 12 12" aria-hidden="true">'
                     +'<rect x="1.8" y="1.5" width="3" height="9" rx="0.8" fill="currentColor" stroke="none"/>'
                     +'<rect x="7.2" y="1.5" width="3" height="9" rx="0.8" fill="currentColor" stroke="none"/></svg>';
  const ICON_DOT_SM='<svg viewBox="0 0 12 12" aria-hidden="true">'
                   +'<circle cx="6" cy="6" r="3.6" fill="currentColor" stroke="none"/></svg>';
  const inBrowser=typeof document!=='undefined'&&typeof document.getElementById==='function';
  const SR=inBrowser?(window.SpeechRecognition||window.webkitSpeechRecognition||null):null;
  const MAX_MS=120000;          // a single recording; the button says so when it ends
  let rec=null, LISTENING=false, ARMED=false, WANT_STOP=false, T0=0;
  let FINAL='', INTERIM='', ERROR='', NOTE='';
  let ROWS=[], OPEN=false, LIVE=false;
  const $=id=>document.getElementById(id);
  const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

  function supported(){ return !!SR; }
  function listening(){ return LISTENING; }
  /* True from the click until the microphone is live. The pause-on-blur guard reads it,
     because the permission prompt can take the window's focus and a case that pauses
     itself the moment someone tries to speak to it is not a feature. */
  function arming(){ return ARMED; }

  function start(){
    if(!SR||LISTENING) return;
    FINAL=''; INTERIM=''; ERROR=''; NOTE=''; WANT_STOP=false; T0=Date.now();
    LISTENING=true; ARMED=true; LIVE=false;
    rec=new SR();
    rec.continuous=true; rec.interimResults=true; rec.maxAlternatives=1;
    rec.lang=(navigator.language&&/^en/i.test(navigator.language))?navigator.language:'en-US';
    rec.onaudiostart=()=>{ ARMED=false; LIVE=true; paint(); };
    rec.onresult=e=>{
      let interim='';
      for(let i=e.resultIndex;i<e.results.length;i++){
        const r=e.results[i];
        if(r.isFinal) FINAL+=r[0].transcript+' '; else interim+=r[0].transcript+' ';
      }
      INTERIM=interim; paint();
    };
    rec.onerror=e=>{
      const k=e&&e.error;
      if(k==='not-allowed'||k==='service-not-allowed'){
        ERROR='The browser blocked the microphone. Allow it for this page, or type the order below.';
        WANT_STOP=true;
      } else if(k==='network'){
        ERROR='The browser could not reach its speech service. Type the order below.';
        WANT_STOP=true;
      } else if(k==='audio-capture'){
        ERROR='No microphone was found. Type the order below.';
        WANT_STOP=true;
      }
      /* 'no-speech' and 'aborted' are not errors here: the first is silence, which
         onend restarts through, and the second is our own stop. */
    };
    /* The browser ends a session after a few seconds of silence even with continuous
       set. While the resident has not clicked stop, that is a pause for thought rather
       than the end of the order, so the session is restarted and the finals kept. */
    rec.onend=()=>{
      if(LISTENING&&!WANT_STOP&&(Date.now()-T0)<MAX_MS){
        try{ rec.start(); return; }catch(err){}
      }
      if(LISTENING&&!WANT_STOP) NOTE='Stopped after two minutes.';
      finishRecording();
    };
    try{ rec.start(); }
    catch(err){ ERROR='The microphone could not be started. Type the order below.'; finishRecording(); }
    OPEN=true; paint();
  }
  function stop(){ if(!LISTENING) return; WANT_STOP=true; try{ rec.stop(); }catch(err){ finishRecording(); } }
  function abort(){ if(!LISTENING) return; WANT_STOP=true; try{ rec.abort(); }catch(err){} }
  function finishRecording(){
    LISTENING=false; ARMED=false; LIVE=false; rec=null;
    const heard=(FINAL+' '+INTERIM).trim();
    FINAL=''; INTERIM='';
    if(heard) addRows(parse(heard));
    paint();
  }
  function addRows(rows){
    for(const r of rows){
      const key=r.kind==='ok'?'ok:'+r.id:(r.kind==='ambiguous'?'am:'+r.ids.join(','):r.kind+':'+r.heard);
      if(ROWS.some(x=>x._key===key)) continue;
      r._key=key; ROWS.push(r);
    }
  }
  function typed(text){
    const t=String(text||'').trim(); if(!t) return;
    const rows=parse(t);
    if(!rows.length) rows.push({kind:'unknown',heard:normalise(t)||t});
    addRows(rows); paint();
  }
  function remove(i){ ROWS.splice(i,1); paint(); }
  function choose(i,id){
    const r=ROWS[i]; if(!r||r.kind!=='ambiguous') return;
    const key='ok:'+id;
    if(ROWS.some(x=>x._key===key)){ ROWS.splice(i,1); }
    else ROWS[i]={kind:'ok',id,heard:r.heard,_key:key};
    paint();
  }
  function clear(){ ROWS=[]; ERROR=''; NOTE=''; }
  function close(){ abort(); clear(); OPEN=false; paint(); }
  /* The reset the case calls on restart, on finish and when it pauses: nothing
     spoken into a case survives the case, and a paused case is not listening. */
  function reset(){ abort(); clear(); OPEN=false; if(inBrowser) paint(); }
  function pause(){ if(LISTENING){ WANT_STOP=true; try{ rec.stop(); }catch(err){ finishRecording(); } } }
  function confirm(){
    const ok=ROWS.filter(r=>r.kind==='ok');
    if(!ok.length) return;
    /* One log entry per order at the same instant, exactly as Submit Order does, so
       the fold applies them in sequence and every prerequisite evaluates as it would
       one at a time. */
    for(const r of ok) log({actionId:r.id});
    clear(); OPEN=false;
    render(); paint();
  }
  function toggle(){
    if(!inCase()) return;
    if(LISTENING){ stop(); return; }
    if(SR){ start(); }
    else { OPEN=true; NOTE='Speech recognition is not available in this browser. Type the order instead.'; paint(); focusBox(); }
  }
  function focusBox(){ const b=$('voicebox'); if(b) b.focus(); }
  function tabOf(id){ const a=ACT[id]; return a?(PROTO.tabLabel[a.tab]||a.tab):''; }
  function statusOf(id){
    if(!ST) return '';
    const orders=ST.orders[id]||[], last=orders[orders.length-1];
    if(IS_STUDY(id)){ if(last&&last.value===null) return 'pending'; if(last) return 'resulted'; return ''; }
    if(ST.taken.has(id)) return (ACT[id].repeatable===false)?'already done':'given before';
    return '';
  }
  function rowHTML(r,i){
    const x=`<button class="vx" data-vrm="${i}" title="Remove" aria-label="Remove this order">&#215;</button>`;
    if(r.kind==='ok'){
      const st=statusOf(r.id);
      return `<li class="vrow ok${r.uncertain?' unsure':''}">
        <span class="vmain"><span class="vname">${esc(dispName(r.id))}</span>
          <span class="vtab">${esc(tabOf(r.id))}</span>${st?`<span class="vst">${esc(st)}</span>`:''}
          <span class="vheard">${r.uncertain?'heard "'+esc(r.heard)+'", taken as "'+esc(r.heardAs)+'"':(r.via?'from "'+esc(r.via)+'"':'')}</span></span>${x}</li>`;
    }
    if(r.kind==='ambiguous'){
      return `<li class="vrow amb"><span class="vmain"><span class="vname">Which one? <span class="vq">"${esc(r.heard)}"</span></span>
        <span class="vchoices">${r.ids.map(id=>`<button class="vch" data-vpick="${i}" data-vid="${esc(id)}">${esc(dispName(id))}</button>`).join('')}</span></span>${x}</li>`;
    }
    if(r.kind==='unavailable'){
      return `<li class="vrow na"><span class="vmain"><span class="vname">Not available: <span class="vq">"${esc(r.heard)}"</span></span>
        ${r.hint?`<span class="vheard">${esc(r.hint)}</span>`:''}</span>${x}</li>`;
    }
    return `<li class="vrow na"><span class="vmain"><span class="vname">Not understood: <span class="vq">"${esc(r.heard)}"</span></span>
      <span class="vheard">Say the study or drug by name, or type it below.</span></span>${x}</li>`;
  }
  function paint(){
    if(!inBrowser) return;
    const btn=$('voicebtn'), panel=$('voicepanel'); if(!btn||!panel) return;
    const active=inCase();
    btn.disabled=!active;
    btn.classList.toggle('live',LISTENING);
    btn.setAttribute('aria-pressed',LISTENING?'true':'false');
    /* Only touched when the state actually changes: paint runs on every speech result
       and rewriting the button's markup forty times a minute is churn for nothing. */
    const wantIcon=LISTENING?'pause':'mic';
    if(btn.dataset.icon!==wantIcon){ btn.dataset.icon=wantIcon; btn.innerHTML=LISTENING?ICON_PAUSE:ICON_MIC; }
    const blab=LISTENING?'Pause recording':(SR?'Record an order':'Type an order');
    btn.title=blab; btn.setAttribute('aria-label',blab);
    const lab=$('voicelab'); if(lab) lab.textContent=LISTENING?'Recording':'Voice order';
    panel.hidden=!OPEN||!active;
    if(panel.hidden) return;
    const okN=ROWS.filter(r=>r.kind==='ok').length;
    const live=(FINAL+' '+INTERIM).trim();
    let status;
    if(LISTENING) status=ARMED?'Waiting for the microphone…':(live?'':'Listening. Say the orders, then press Pause Recording.');
    else status=ROWS.length?'':'Nothing heard yet.';
    $('voicestatus').innerHTML=
      (ERROR?`<div class="verr">${esc(ERROR)}</div>`:'')+
      (NOTE?`<div class="vnote">${esc(NOTE)}</div>`:'')+
      (LISTENING&&live?`<div class="vlive">${esc(live)}</div>`:'')+
      (status?`<div class="vnote">${esc(status)}</div>`:'');
    /* The same toggle as the microphone, in words, because the control that starts and
       stops a recording should be reachable without aiming at a 46-pixel circle behind
       the panel. Hidden rather than disabled where the browser has no recogniser: there
       is nothing to record, and the status line already says so. */
    const rec=$('voicerec');
    if(rec){
      rec.hidden=!SR;
      rec.classList.toggle('live',LISTENING);
      rec.setAttribute('aria-pressed',LISTENING?'true':'false');
      const ri=$('voicerecicon'), wantRec=LISTENING?'pause':'dot';
      if(ri&&ri.dataset.icon!==wantRec){ ri.dataset.icon=wantRec; ri.innerHTML=LISTENING?ICON_PAUSE_SM:ICON_DOT_SM; }
      const rl=$('voicereclab'); if(rl) rl.textContent=LISTENING?'Pause Recording':'Record';
    }
    $('voicelist').innerHTML=ROWS.map(rowHTML).join('');
    const c=$('voiceok'); c.disabled=!okN; c.textContent='Confirm'+(okN?' ('+okN+')':'');
    const cl=$('voicecancel'); cl.textContent=ROWS.length?'Discard':'Close';
  }
  function bind(){
    if(!inBrowser) return;
    const root=$('voice'); if(!root) return;
    root.addEventListener('click',e=>{
      const t=e.target.closest('#voicebtn,#voicerec,#voiceok,#voicecancel,[data-vrm],[data-vpick]');
      if(!t) return;
      e.stopPropagation();
      if(t.id==='voicebtn'||t.id==='voicerec'){ toggle(); return; }
      if(t.id==='voiceok'){ confirm(); return; }
      if(t.id==='voicecancel'){ close(); return; }
      if(t.dataset.vrm!==undefined){ remove(Number(t.dataset.vrm)); return; }
      if(t.dataset.vpick!==undefined){ choose(Number(t.dataset.vpick),t.dataset.vid); return; }
    });
    root.addEventListener('keydown',e=>{
      if(e.target.id==='voicebox'&&e.key==='Enter'){ typed(e.target.value); e.target.value=''; e.preventDefault(); return; }
      if(e.key==='Escape'){ close(); $('voicebtn').focus(); }
    });
    /* Clicks in the dropdown must not reach the page's handler, which treats a click
       on the header as a click on the room when the record panel is wide. */
    root.addEventListener('mousedown',e=>e.stopPropagation());
    paint();
  }
  return {normalise,build,parse,index:()=>INDEX,supported,listening,arming,bind,paint,reset,pause,typed,
          rows:()=>ROWS.slice()};
})();
