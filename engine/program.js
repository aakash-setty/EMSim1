/* ---------- programs and analytics (10 November 2026) ----------
   A residency program buys seats. Its residents join it with a code, and its admins see how
   the group is doing. WeSim staff see every program and every account. The rules live in the
   database (supabase/migrations/004_programs.sql): this file only asks and draws. Every
   number on these screens comes back from one function, program_analytics, which checks who
   is asking, so nothing here can show an account more than the database allows it.

   Owner decisions (10 November 2026):
     - a program admin always sees who finished what, by name. Results by name are one
       switch per program, set by staff. It is on for now.
     - individual accounts continue beside programs.
     - a member of a program cannot delete a finished run.

   The local build has no backend and this module does nothing there.

   Nothing here names a case, a drug or a diagnosis. Labels come from the case list and the
   shared catalog at run time. The styles are added by this file so that shell.html stays
   as it is. */
const PROGRAM = (function(){
  const CFG = (typeof ACCESS==='object' && ACCESS) || {mode:'local'};
  const SITE = CFG.mode==='site';
  const A = (typeof ANALYTICS==='object' && ANALYTICS) || {track(){}};
  const $ = id => document.getElementById(id);
  const esc = t => String(t==null?'':t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const JOIN_KEY = 'emsim-join-code';
  const YEARS = [['','Prefer not to say'],['0','Medical student'],['1','PGY-1'],['2','PGY-2'],['3','PGY-3'],['4','PGY-4'],['5','PGY-5 or later']];
  const TABS = [['overview','Overview'],['people','Residents'],['cases','Cases'],['missed','Missed and unsafe'],['map','Gap map'],['programs','Programs']];
  const AREAS = [['stabilization','Stabilization'],['interventions','Actions'],['investigations','Labs and imaging'],['consultations','Consults'],['exam','Examination']];
  const MIN_N = 5;                 /* below this, a rate is not shown as a rate */

  let client=null, uid=null, info=null, infoState='idle';   /* idle | loading | ready | error */
  let view={open:false, tab:'overview', scope:null, first:true, days:null, data:null, state:'idle', err:'',
            overview:null, openCase:null, confirm:null, note:''};
  let join={open:false, busy:false, err:''};

  const on = () => SITE && !!client && !!uid;
  const member = () => (info&&info.member)||null;
  const isStaff = () => !!(info&&info.staff);
  const canSee = () => isStaff() || (member()&&member().role==='admin');

  /* ---- labels ---- */
  const caseOf = prefix => (typeof CASES==='object'&&CASES ? CASES.find(c=>c.prefix===prefix) : null)||null;
  const caseName = prefix => { const c=caseOf(prefix), k=(c&&c.card)||{}; return k.complaint||k.title||prefix; };
  const caseCat = prefix => { const c=caseOf(prefix), k=(c&&c.card)||{}; return k.category||'Other'; };
  const allPrefixes = () => (typeof CASES==='object'&&CASES ? CASES.map(c=>c.prefix) : []);
  const words = id => String(id||'').replace(/^hidden_/,'').replace(/_/g,' ');
  function actName(id){
    const base=(typeof SHARED==='object'&&SHARED&&SHARED.actionsBase)||{};
    return (base[id]&&base[id].name)||words(id);
  }
  function dxName(id){
    if(!id) return 'None given';
    const list=(typeof SHARED==='object'&&SHARED&&SHARED.diagnoses)||[];
    const d=list.find(x=>x.id===id);
    return (d&&d.label)||words(id);
  }
  const yearName = p => p===null||p===undefined ? 'Not said' : (p===0?'Student':'PGY-'+p);
  const mmss = s => { s=Math.max(0,Math.round(Number(s)||0)); return Math.floor(s/60)+':'+String(s%60).padStart(2,'0'); };
  const day = t => { if(!t) return 'Never'; const d=new Date(t); return isNaN(d)?'':d.toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'}); };
  const pct = (a,b) => b>0 ? Math.round(100*a/b) : null;
  /* A rate with the count it rests on. Under MIN_N the count is all that is shown. */
  const rate = (a,b) => b>=MIN_N ? `<b>${pct(a,b)}%</b> <span class="pg-n">${a} of ${b}</span>` : `<span class="pg-n">${a} of ${b}</span>`;

  /* ---- session ---- */
  function init(cl){
    if(!SITE) return;
    client=cl;
    try{
      const m=location.search.match(/[?&]join=([A-Za-z0-9-]{4,16})/);
      if(m){ sessionStorage.setItem(JOIN_KEY, m[1].toUpperCase()); history.replaceState(null,'',location.pathname+location.hash); }
    }catch(e){}
    build();
  }
  function onSession(s){
    if(!SITE) return;
    const id=(s&&s.user&&s.user.id)||null;
    if(id===uid) return;
    uid=id; info=null; infoState='idle';
    if(view.open) close();
    if(join.open) closeJoin();
    if(uid) load(); else paintAccount();
  }
  async function load(){
    if(!on()) return;
    infoState='loading';
    try{
      const {data,error}=await client.rpc('my_program');
      if(error) throw error;
      info=data||{}; infoState='ready';
    }catch(e){ info=null; infoState='error'; }
    paintAccount();
    let code=''; try{ code=sessionStorage.getItem(JOIN_KEY)||''; }catch(e){}
    if(code && infoState==='ready'){
      if(member()){ try{ sessionStorage.removeItem(JOIN_KEY); }catch(e){} }
      else openJoin(code);
    }
  }

  /* ---- the account line: what access.js leaves a slot for ---- */
  function paintAccount(){
    const slot=$('acct-prog'); if(!slot) return;
    if(!on()||infoState!=='ready'){ slot.innerHTML=''; return; }
    const m=member();
    slot.innerHTML=
      (m ? `<span class="pg-chip" title="You are registered under this program">${esc(m.program)}</span>`
         : `<button type="button" id="pg-join">Join a program</button>`)+
      (canSee() ? `<button type="button" id="pg-open">Analytics</button>` : '');
    const j=$('pg-join'); if(j) j.onclick=()=>openJoin('');
    const o=$('pg-open'); if(o) o.onclick=open;
  }

  /* ---- joining ---- */
  function openJoin(code){
    join={open:true,busy:false,err:''};
    const v=$('pgjoin'); if(!v) return;
    v.classList.remove('hidden');
    $('pgj-code').value=code||''; $('pgj-err').textContent='';
    (code?$('pgj-name'):$('pgj-code')).focus();
  }
  function closeJoin(){
    join.open=false; const v=$('pgjoin'); if(v) v.classList.add('hidden');
    try{ sessionStorage.removeItem(JOIN_KEY); }catch(e){}
  }
  const JOIN_SAYS={bad_code:'That code is not one we know. Check it with your program.',
    closed:'That program is closed to new members.', full:'That program has no seats left. Tell your program.',
    already_member:'This account already belongs to a program.', bad_name:'Enter your name, up to 80 characters.'};
  async function submitJoin(){
    if(join.busy) return;
    const code=$('pgj-code').value.trim(), name=$('pgj-name').value.trim(), y=$('pgj-year').value;
    const err=$('pgj-err');
    if(code.replace(/[^A-Za-z0-9]/g,'').length<8){ err.textContent='Enter the eight-character code from your program.'; return; }
    if(!name){ err.textContent='Enter your name as your program knows you.'; return; }
    join.busy=true; $('pgj-ok').disabled=true; err.textContent='';
    try{
      const {data,error}=await client.rpc('join_program',{p_code:code,p_name:name,p_pgy:y===''?null:Number(y)});
      if(error) throw error;
      if(data==='ok'){ A.track('program_joined',{}); closeJoin(); await load(); if(typeof PROGRESS==='object'&&PROGRESS.refresh) PROGRESS.refresh(); }
      else err.textContent=JOIN_SAYS[data]||'That did not work. Try again.';
    }catch(e){ err.textContent='That did not work. Check your connection and try again.'; }
    finally{ join.busy=false; const b=$('pgj-ok'); if(b) b.disabled=false; }
  }

  /* ---- the analytics view ---- */
  function open(){
    if(!canSee()) return;
    const m=member();
    view.open=true; view.note=''; view.confirm=null; view.openCase=null;
    if(view.scope===null) view.scope = isStaff() ? 'all' : m.program_id;
    if(!isStaff()) view.scope=m.program_id;
    if(view.tab==='programs'&&!isStaff()) view.tab='overview';
    $('pgview').classList.remove('hidden');
    A.track('analytics_opened',{staff:isStaff()});
    paint(); fetchAll();
  }
  function close(){ view.open=false; view.data=null; const v=$('pgview'); if(v) v.classList.add('hidden'); }
  async function fetchAll(){
    view.state='loading'; view.err=''; paint();
    try{
      if(isStaff()){
        const o=await client.rpc('staff_overview'); if(o.error) throw o.error;
        view.overview=o.data;
      }
      const r=await client.rpc('program_analytics',
        {p_program: view.scope==='all'?null:view.scope, p_first:view.first, p_days:view.days});
      if(r.error) throw r.error;
      view.data=r.data; view.state='ready';
    }catch(e){
      view.state='error';
      view.err=(e&&e.code==='42501')?'This account cannot see these numbers.':'The numbers could not be loaded. Check your connection and try again.';
    }
    paint();
  }

  function mix(o){
    const n=(o.met||0)+(o.met_prompted||0)+(o.not_met||0);
    if(!n) return '<span class="pg-n">No runs</span>';
    const w=x=>(100*x/n).toFixed(1);
    return `<span class="pg-mix" role="img" aria-label="${o.met||0} met, ${o.met_prompted||0} met with prompts, ${o.not_met||0} not met">
      <i class="a" style="width:${w(o.met||0)}%"></i><i class="b" style="width:${w(o.met_prompted||0)}%"></i><i class="c" style="width:${w(o.not_met||0)}%"></i></span>
      <span class="pg-n">${o.met||0} / ${o.met_prompted||0} / ${o.not_met||0}</span>`;
  }
  const KEY=`<p class="pg-key"><span class="pg-mix k"><i class="a" style="width:100%"></i></span> Met
    <span class="pg-mix k"><i class="b" style="width:100%"></i></span> Met with prompts
    <span class="pg-mix k"><i class="c" style="width:100%"></i></span> Not met.
    Counts are shown in that order.</p>`;
  const table=(head,rows,empty)=> rows.length
    ? `<div class="pg-tw"><table class="pg-t"><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`
    : `<p class="pg-empty">${empty}</p>`;

  function tOverview(d){
    const t=d.totals||{}, sum={met:0,met_prompted:0,not_met:0};
    (d.cases||[]).forEach(c=>{ sum.met+=c.met; sum.met_prompted+=c.met_prompted; sum.not_met+=c.not_met; });
    const tile=(n,l)=>`<div class="pg-tile"><b>${esc(n)}</b><span>${esc(l)}</span></div>`;
    return `<div class="pg-tiles">
        ${tile(t.residents||0, d.program?'Residents registered':'Accounts with a record')}
        ${tile(t.with_a_finished_run||0,'Have finished a case')}
        ${tile(t.active_30d||0,'Active in the last 30 days')}
        ${tile(t.runs||0,'Finished runs')}
        ${tile(t.first_attempts||0,'First attempts')}
        ${tile(t.open_runs||0,'Runs in progress')}
      </div>
      <h3>Results, ${d.first_only?'first attempts':'all attempts'}</h3>
      <p class="pg-big">${mix(sum)}</p>${KEY}
      <h3>By year of training</h3>
      ${table(['Year','Learners','Runs','Results'],(d.years||[]).map(y=>
        `<tr><td>${esc(yearName(y.pgy))}</td><td>${y.learners}</td><td>${y.n}</td><td>${mix(y)}</td></tr>`),'No finished runs yet.')}
      <h3>By month</h3>
      ${table(['Month','Runs','Results'],(d.months||[]).map(m=>
        `<tr><td>${esc(m.month)}</td><td>${m.n}</td><td>${mix(m)}</td></tr>`),'No finished runs yet.')}`;
  }
  function tPeople(d){
    const total=allPrefixes().length;
    const head=['Name','Year','Cases finished','Runs','In progress','Case minutes','Last finished'];
    if(d.named) head.push('Results','Harmful action','Case lost');
    head.push('');
    const rows=(d.members||[]).map(m=>{
      const r=m.results||{}, who=m.name||('Account '+String(m.user_id).slice(0,8));
      const tools= (m.role==='individual') ? '' :
        (view.confirm===m.user_id
          ? `<span class="pg-sure">Remove ${esc(who)}? <button type="button" data-pgrm="${esc(m.user_id)}">Remove</button> <button type="button" data-pgno="1">Keep</button></span>`
          : ((m.role==='resident'?`<button type="button" class="pg-link" data-pgask="${esc(m.user_id)}">Remove</button>`:'')+
             (isStaff()?` <button type="button" class="pg-link" data-pgrole="${esc(m.user_id)}" data-to="${m.role==='admin'?'resident':'admin'}">${m.role==='admin'?'Make resident':'Make admin'}</button>`:'')));
      return `<tr><td>${esc(who)}${m.role==='admin'?' <span class="pg-tag">Admin</span>':''}${m.role==='individual'?' <span class="pg-tag">Individual</span>':''}</td>
        <td>${esc(yearName(m.pgy))}</td><td>${m.cases_finished}${total?` <span class="pg-n">of ${total}</span>`:''}</td>
        <td>${m.runs}</td><td>${m.open}</td><td>${m.case_minutes}</td><td>${esc(day(m.last_finished))}</td>
        ${d.named?`<td>${mix(r)}</td><td>${r.harmful||0}</td><td>${r.lost||0}</td>`:''}<td class="pg-tools">${tools}</td></tr>`;
    });
    return (d.named?KEY:`<p class="pg-note">Results by name are off for this program. This list shows who has finished what. Results are shown for the group on the other tabs.</p>`)+
      table(head,rows,'Nobody has joined yet. Residents join with the program code.')+
      (d.program&&d.program.join_code?`<p class="pg-note">Program code: <b class="pg-code">${esc(d.program.join_code)}</b>. Residents sign up, choose Join a program and enter it. A link that fills it in: <span class="pg-code">${esc(location.origin+location.pathname+'?join='+d.program.join_code)}</span></p>`:'');
  }
  function caseDetail(d,prefix){
    const its=(d.items||[]).filter(i=>i.case_prefix===prefix).sort((a,b)=>(a.kind<b.kind?-1:a.kind>b.kind?1:0)||(a.done/a.n-b.done/b.n));
    const sf=(d.safety||[]).filter(i=>i.case_prefix===prefix).sort((a,b)=>b.learners-a.learners);
    const ho=k=>(d.handoff||[]).filter(i=>i.case_prefix===prefix&&i.kind===k).sort((a,b)=>b.n-a.n);
    return `<div class="pg-detail">
      <h4>Expected actions</h4>
      ${table(['Action','Kind','Done','Only after a prompt','Median time to act'],its.map(i=>
        `<tr><td>${esc(actName(i.item_id))}</td><td>${esc(i.kind)}</td><td>${rate(i.done,i.n)}</td><td>${rate(i.prompted,i.done)}</td>
         <td>${i.median_delay===null||i.median_delay===undefined?'':mmss(i.median_delay)}</td></tr>`),'Nothing recorded.')}
      <h4>Discouraged and harmful actions taken</h4>
      ${table(['Action','Kind','Learners','Runs'],sf.map(i=>
        `<tr><td>${esc(actName(i.item_id))}</td><td>${esc(i.kind)}</td><td>${i.learners}</td><td>${i.runs}</td></tr>`),'None taken.')}
      <h4>Primary diagnosis given</h4>
      ${table(['Diagnosis','Verdict','Runs'],ho('diagnosis').map(i=>
        `<tr><td>${esc(dxName(i.item_id))}</td><td>${esc(i.result)}</td><td>${i.n}</td></tr>`),'Nothing recorded.')}
      <h4>Disposition chosen</h4>
      ${table(['Disposition','Verdict','Runs'],ho('disposition').map(i=>
        `<tr><td>${esc(i.item_id?words(i.item_id):'None given')}</td><td>${esc(i.result)}</td><td>${i.n}</td></tr>`),'Nothing recorded.')}
    </div>`;
  }
  function tCases(d){
    const rows=[];
    (d.cases||[]).forEach(c=>{
      const openRow=view.openCase===c.case_prefix;
      rows.push(`<tr class="pg-row${openRow?' on':''}"><td><button type="button" class="pg-link" data-pgcase="${esc(c.case_prefix)}" aria-expanded="${openRow}">${esc(caseName(c.case_prefix))}</button>
          <span class="pg-n">${esc(caseCat(c.case_prefix))}</span></td>
        <td>${c.learners}</td><td>${c.n}</td><td>${mix(c)}</td><td>${c.harmful}</td><td>${c.lost}</td>
        <td>${mmss(c.median_seconds)}</td><td>${c.open}</td></tr>`);
      if(openRow) rows.push(`<tr class="pg-sub"><td colspan="8">${caseDetail(d,c.case_prefix)}</td></tr>`);
    });
    return KEY+table(['Case','Learners','Runs','Results','Harmful action','Case lost','Median case time','In progress'],rows,'No finished runs yet.')+
      `<p class="pg-note">Choose a case to see its actions, diagnoses and dispositions.</p>`;
  }
  function tMissed(d){
    const crit=(d.items||[]).filter(i=>i.kind==='critical'&&i.n>0)
      .map(i=>Object.assign({miss:i.n-i.done, unp:i.done-i.prompted},i))
      .sort((a,b)=>(b.miss/b.n-a.miss/a.n)||(b.n-a.n));
    const missed=crit.filter(i=>i.miss>0), prompted=crit.filter(i=>i.prompted>0).sort((a,b)=>b.prompted/b.n-a.prompted/a.n);
    const sf=(d.safety||[]).slice().sort((a,b)=>b.learners-a.learners||b.runs-a.runs);
    const wrong=(d.handoff||[]).filter(i=>i.result==='incorrect'||i.result==='none').sort((a,b)=>b.n-a.n);
    return `<h3>Critical actions missed</h3>
      ${table(['Action','Case','Missed','Learners'],missed.map(i=>
        `<tr><td>${esc(actName(i.item_id))}</td><td>${esc(caseName(i.case_prefix))}</td><td>${rate(i.miss,i.n)}</td><td>${i.learners_missed}</td></tr>`),'No critical action was missed.')}
      <h3>Critical actions done only after a prompt</h3>
      ${table(['Action','Case','Prompted first','Median time to act'],prompted.map(i=>
        `<tr><td>${esc(actName(i.item_id))}</td><td>${esc(caseName(i.case_prefix))}</td><td>${rate(i.prompted,i.n)}</td><td>${i.median_delay===null||i.median_delay===undefined?'':mmss(i.median_delay)}</td></tr>`),'No critical action needed a prompt.')}
      <h3>Discouraged and harmful actions taken</h3>
      ${table(['Action','Group','Case','Kind','Learners','Runs'],sf.map(i=>
        `<tr><td>${esc(actName(i.item_id))}</td><td>${esc(i.grp||'')}</td><td>${esc(caseName(i.case_prefix))}</td><td>${esc(i.kind)}</td><td>${i.learners}</td><td>${i.runs}</td></tr>`),'None taken.')}
      <h3>Handoffs that were wrong or missing</h3>
      ${table(['Given','Part','Case','Runs'],wrong.map(i=>
        `<tr><td>${esc(i.kind==='diagnosis'?dxName(i.item_id):(i.item_id?words(i.item_id):'None given'))}</td><td>${esc(i.kind)}</td><td>${esc(caseName(i.case_prefix))}</td><td>${i.n}</td></tr>`),'Every handoff was correct or defensible.')}`;
  }
  function tMap(d){
    const cells={}, cats=[];
    (d.items||[]).filter(i=>i.kind==='critical').forEach(i=>{
      const cat=caseCat(i.case_prefix), tab=AREAS.some(a=>a[0]===i.tab)?i.tab:null;
      if(!tab) return;
      if(!cats.includes(cat)) cats.push(cat);
      const k=cat+'|'+tab, c=cells[k]=cells[k]||{n:0,unp:0};
      c.n+=i.n; c.unp+=i.done-i.prompted;
    });
    cats.sort();
    if(!cats.length) return '<p class="pg-empty">No finished runs yet.</p>';
    const cell=(cat,tab)=>{
      const c=cells[cat+'|'+tab];
      if(!c) return '<td class="pg-cell none"></td>';
      if(c.n<MIN_N) return `<td class="pg-cell few"><span class="pg-n">${c.unp} of ${c.n}</span></td>`;
      const p=pct(c.unp,c.n), band=p>=85?'hi':(p>=60?'mid':'lo');
      return `<td class="pg-cell ${band}"><b>${p}%</b><span class="pg-n">${c.unp} of ${c.n}</span></td>`;
    };
    return `<p class="pg-note">Each cell is the share of expected critical actions done with no prompt, across the cases in that topic. A topic rests on the cases the library has in it, which may be one. A cell with fewer than ${MIN_N} shows the count only.</p>
      <div class="pg-tw"><table class="pg-t pg-map"><thead><tr><th>Topic</th>${AREAS.map(a=>`<th>${a[1]}</th>`).join('')}</tr></thead>
      <tbody>${cats.map(cat=>`<tr><th scope="row">${esc(cat)}</th>${AREAS.map(a=>cell(cat,a[0])).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function tPrograms(){
    const o=view.overview||{}, ps=o.programs||[], st=o.settings||{}, all=allPrefixes();
    const rows=ps.map(p=>`<tr><td><button type="button" class="pg-link" data-pgscope="${esc(p.id)}">${esc(p.name)}</button>${p.status==='closed'?' <span class="pg-tag">Closed</span>':''}</td>
        <td class="pg-code">${esc(p.join_code)} <button type="button" class="pg-link" data-pgcode="${esc(p.id)}">New code</button></td>
        <td>${p.residents}${p.seats?` <span class="pg-n">of ${p.seats}</span>`:''}</td><td>${p.admins}</td><td>${p.runs}</td><td>${esc(day(p.last_finished))}</td>
        <td><label class="pg-sw"><input type="checkbox" data-pgnamed="${esc(p.id)}" ${p.show_named_results?'checked':''}> Results by name</label></td>
        <td><label class="pg-sw"><input type="checkbox" data-pgall="${esc(p.id)}" ${p.all_cases?'checked':''}> Every case</label>
          ${p.all_cases?'':`<div class="pg-pick">${all.map(x=>`<label><input type="checkbox" data-pgpick="${esc(p.id)}" value="${esc(x)}" ${p.cases.includes(x)?'checked':''}> ${esc(x)}</label>`).join('')}</div>`}</td>
        <td><button type="button" class="pg-link" data-pgstatus="${esc(p.id)}" data-to="${p.status==='closed'?'active':'closed'}">${p.status==='closed'?'Reopen':'Close'}</button></td></tr>`);
    return `<div class="pg-tiles"><div class="pg-tile"><b>${o.accounts||0}</b><span>Accounts</span></div>
        <div class="pg-tile"><b>${o.individuals||0}</b><span>Not in a program</span></div>
        <div class="pg-tile"><b>${ps.length}</b><span>Programs</span></div>
        <div class="pg-tile"><b>${o.records||0}</b><span>Run records</span></div></div>
      <h3>Programs</h3>
      ${table(['Program','Join code','Residents','Admins','Runs','Last finished','Visibility','Cases',''],rows,'No programs yet.')}
      <form class="pg-new" id="pg-new"><label for="pg-newname">New program</label>
        <input id="pg-newname" class="signinbox" maxlength="120" placeholder="Program name" autocomplete="off">
        <input id="pg-newseats" class="signinbox" inputmode="numeric" maxlength="5" placeholder="Seats (blank for no limit)" autocomplete="off">
        <button class="btn" type="submit">Create</button></form>
      <p class="pg-note">A resident who joins becomes a resident. To make someone an admin, open the program, find them under Residents and choose Make admin.</p>
      <h3>Who can open which case</h3>
      <p class="pg-note">Off: every signed-in account can open every case, as now. On: an account opens a case only if its program includes it, the account is paid, or the case is ticked as free below.</p>
      <label class="pg-sw"><input type="checkbox" id="pg-enforce" ${st.enforce_entitlements?'checked':''}> Limit cases to what each account is entitled to</label>
      <div class="pg-pick">${all.map(x=>`<label><input type="checkbox" data-pgfree="1" value="${esc(x)}" ${(st.free_cases||[]).includes(x)?'checked':''}> ${esc(x)} free</label>`).join('')}</div>`;
  }

  function paint(){
    const v=$('pgview'); if(!v||!view.open) return;
    const d=view.data, o=view.overview||{};
    const tabs=TABS.filter(t=>t[0]!=='programs'||isStaff());
    const scope = isStaff()
      ? `<select id="pg-scope" aria-label="Whose data"><option value="all"${view.scope==='all'?' selected':''}>Every account</option>
          ${(o.programs||[]).map(p=>`<option value="${esc(p.id)}"${view.scope===p.id?' selected':''}>${esc(p.name)}</option>`).join('')}</select>`
      : `<span class="pg-scope">${esc((member()||{}).program||'')}</span>`;
    let body;
    if(view.state==='error') body=`<p class="pg-empty">${esc(view.err)}</p>`;
    else if(!d) body='<p class="pg-empty">Loading.</p>';
    else body=({overview:tOverview,people:tPeople,cases:tCases,missed:tMissed,map:tMap,programs:tPrograms})[view.tab](d);
    $('pg-body').innerHTML=
      `<div class="pg-bar">${scope}
        <label class="pg-sw"><input type="checkbox" id="pg-first" ${view.first?'checked':''}> First attempts only</label>
        <select id="pg-days" aria-label="Period"><option value="">All time</option><option value="30"${view.days===30?' selected':''}>Last 30 days</option>
          <option value="90"${view.days===90?' selected':''}>Last 90 days</option><option value="365"${view.days===365?' selected':''}>Last year</option></select>
        <span class="pg-msg" role="status">${esc(view.note)}</span></div>
      <div class="pg-tabs" role="tablist">${tabs.map(t=>`<button type="button" role="tab" aria-selected="${view.tab===t[0]}" data-pgtab="${t[0]}"${view.tab===t[0]?' class="on"':''}>${t[1]}</button>`).join('')}</div>
      <div class="pg-pane${view.state==='loading'?' busy':''}">${body}</div>
      <p class="pg-foot">These numbers describe performance in simulated cases, for teaching and feedback. Each record is worked out in the learner's own browser and is not checked by the server. Nothing clinical in the cases has been reviewed by a physician unless that case says so. Do not use these numbers alone to decide promotion, remediation or dismissal.</p>`;
  }

  async function call(fn,args,note){
    try{
      const r=await client.rpc(fn,args); if(r.error) throw r.error;
      view.note=note||''; return r.data;
    }catch(e){ view.note='That change was not saved. Try again.'; return undefined; }
  }
  const prog = id => ((view.overview||{}).programs||[]).find(p=>p.id===id);
  const savePrg = (p,over,note) => call('staff_save_program',Object.assign({p_id:p.id,p_name:null,p_named:null,p_all_cases:null,p_cases:null,p_seats:p.seats||null,p_status:null},over),note);

  function bind(){
    const v=$('pgview');
    v.addEventListener('click', async e=>{
      const t=e.target.closest('button'); if(!t) return;
      if(t.id==='pg-close'){ close(); return; }
      const ds=t.dataset;
      if(ds.pgtab){ view.tab=ds.pgtab; view.note=''; paint(); return; }
      if(ds.pgcase){ view.openCase=view.openCase===ds.pgcase?null:ds.pgcase; paint(); return; }
      if(ds.pgask){ view.confirm=ds.pgask; paint(); return; }
      if(ds.pgno){ view.confirm=null; paint(); return; }
      if(ds.pgrm){ view.confirm=null; await call('program_set_member',{p_user:ds.pgrm,p_role:'remove'},'Removed. Their finished runs stay in the program.'); fetchAll(); return; }
      if(ds.pgrole){ await call('program_set_member',{p_user:ds.pgrole,p_role:ds.to},'Saved.'); fetchAll(); return; }
      if(ds.pgscope){ view.scope=ds.pgscope; view.tab='overview'; fetchAll(); return; }
      if(ds.pgcode){ await call('staff_new_code',{p_id:ds.pgcode},'New code issued. The old code no longer works.'); fetchAll(); return; }
      if(ds.pgstatus){ const p=prog(ds.pgstatus); if(p){ await savePrg(p,{p_status:ds.to},'Saved.'); fetchAll(); } return; }
    });
    v.addEventListener('change', async e=>{
      const t=e.target, ds=t.dataset||{};
      if(t.id==='pg-scope'){ view.scope=t.value; fetchAll(); return; }
      if(t.id==='pg-first'){ view.first=t.checked; fetchAll(); return; }
      if(t.id==='pg-days'){ view.days=t.value?Number(t.value):null; fetchAll(); return; }
      if(t.id==='pg-enforce'){ await call('staff_set_settings',{p_enforce:t.checked,p_free:null},t.checked?'Cases are now limited by entitlement.':'Every account can open every case.'); fetchAll(); return; }
      if(ds.pgfree){ const list=[...v.querySelectorAll('[data-pgfree]:checked')].map(x=>x.value);
        await call('staff_set_settings',{p_enforce:null,p_free:list},'Saved.'); fetchAll(); return; }
      if(ds.pgnamed){ const p=prog(ds.pgnamed); if(p){ await savePrg(p,{p_named:t.checked},t.checked?'This program now sees results by name.':'This program now sees results for the group only.'); fetchAll(); } return; }
      if(ds.pgall){ const p=prog(ds.pgall); if(p){ await savePrg(p,{p_all_cases:t.checked},'Saved.'); fetchAll(); } return; }
      if(ds.pgpick){ const p=prog(ds.pgpick); if(p){ const list=[...v.querySelectorAll('[data-pgpick="'+ds.pgpick+'"]:checked')].map(x=>x.value);
        await savePrg(p,{p_cases:list},'Saved.'); fetchAll(); } return; }
    });
    v.addEventListener('submit', async e=>{
      if(e.target.id!=='pg-new') return;
      e.preventDefault();
      const name=$('pg-newname').value.trim(), seats=parseInt($('pg-newseats').value,10);
      if(name.length<2){ view.note='Enter a program name.'; paint(); return; }
      await call('staff_save_program',{p_id:null,p_name:name,p_named:true,p_all_cases:true,p_cases:null,p_seats:seats>0?seats:null,p_status:null},'Program created.');
      fetchAll();
    });
    v.addEventListener('keydown', e=>{ if(e.key==='Escape'){ e.stopPropagation(); close(); } });
    $('pgj-form').addEventListener('submit', e=>{ e.preventDefault(); submitJoin(); });
    $('pgj-no').onclick=closeJoin;
    $('pgjoin').addEventListener('keydown', e=>{ if(e.key==='Escape'){ e.stopPropagation(); closeJoin(); } });
  }

  function build(){
    if($('pgview')) return;
    const css=document.createElement('style');
    css.textContent=`
.pg-chip{font-size:12px;padding:4px 10px;border-radius:999px;background:var(--okl);color:var(--ok);white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis}
#acct-prog{display:inline-flex;align-items:center;gap:8px}
#pgview{position:fixed;inset:0;z-index:290;background:var(--dash-bg,var(--paper));color:var(--ink);overflow:auto;font-family:var(--sans)}
#pgview.hidden{display:none}
.pg-wrap{max-width:1180px;margin:0 auto;padding:22px 24px 60px}
.pg-head{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.pg-head h1{font-size:22px;font-weight:650;letter-spacing:-.01em;margin:0;flex:1}
.pg-bar{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin-bottom:12px;font-size:13.5px}
.pg-bar select{font:inherit;font-size:13.5px;color:var(--ink);background:var(--solid);border:1px solid var(--rule);border-radius:6px;padding:6px 8px}
.pg-scope{font-weight:600}
.pg-msg{color:var(--ok);font-size:13px}
.pg-sw{display:inline-flex;align-items:center;gap:6px;font-size:13.5px;cursor:pointer}
.pg-tabs{display:flex;flex-wrap:wrap;gap:4px;border-bottom:1px solid var(--rule);margin-bottom:16px}
.pg-tabs button{font:inherit;font-size:13.5px;color:var(--ink2);background:none;border:0;border-bottom:2px solid transparent;padding:9px 12px;cursor:pointer}
.pg-tabs button.on{color:var(--act);border-bottom-color:var(--act);font-weight:600}
.pg-pane{background:var(--solid);border:1px solid var(--rule2);border-radius:10px;padding:18px 20px;min-height:200px}
.pg-pane.busy{opacity:.55}
.pg-pane h3{font-size:15px;font-weight:650;margin:22px 0 8px}
.pg-pane h3:first-child{margin-top:0}
.pg-pane h4{font-size:13px;font-weight:650;margin:14px 0 6px;color:var(--ink2)}
.pg-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:6px}
.pg-tile{border:1px solid var(--rule2);border-radius:8px;padding:12px 14px;background:var(--sunk)}
.pg-tile b{display:block;font-size:26px;font-weight:650;font-family:var(--mono)}
.pg-tile span{font-size:12.5px;color:var(--ink2)}
.pg-tw{overflow-x:auto}
.pg-t{width:100%;border-collapse:collapse;font-size:13.5px}
.pg-t th{text-align:left;font-weight:600;font-size:12px;color:var(--ink2);padding:7px 10px;border-bottom:1px solid var(--rule);white-space:nowrap}
.pg-t td{padding:8px 10px;border-bottom:1px solid var(--rule2);vertical-align:top}
.pg-t tbody tr:nth-child(even) td{background:var(--stripe)}
.pg-t tr.pg-sub td{background:var(--sunk)}
.pg-n{color:var(--ink3);font-size:12px;font-family:var(--mono);white-space:nowrap}
.pg-tag{font-size:11px;padding:1px 7px;border-radius:999px;background:var(--actl);color:var(--act)}
.pg-mix{display:inline-flex;width:120px;height:10px;border-radius:5px;overflow:hidden;background:var(--sunk);vertical-align:middle;margin-right:6px}
.pg-mix.k{width:14px;margin:0 3px 0 10px}
.pg-mix i{display:block;height:100%}
.pg-mix .a{background:var(--ok)} .pg-mix .b{background:var(--warn)} .pg-mix .c{background:var(--harm)}
.pg-big .pg-mix{width:min(520px,70%);height:16px;border-radius:8px}
.pg-key,.pg-note,.pg-foot{font-size:12.5px;color:var(--ink2);line-height:1.5;margin:8px 0}
.pg-foot{margin-top:18px;max-width:900px}
.pg-empty{color:var(--ink2);font-size:14px;padding:18px 0}
.pg-link{font:inherit;font-size:13px;color:var(--act);background:none;border:0;padding:0;cursor:pointer;text-align:left}
.pg-link:hover{text-decoration:underline}
.pg-tools{white-space:nowrap;text-align:right}
.pg-sure button{font:inherit;font-size:12.5px;margin-left:4px}
.pg-code{font-family:var(--mono);letter-spacing:.04em;overflow-wrap:anywhere}
.pg-map th[scope=row]{font-size:13px;color:var(--ink);white-space:normal}
.pg-cell{text-align:center;min-width:104px}
.pg-cell b{display:block;font-size:16px}
.pg-cell.hi{background:var(--okl)!important} .pg-cell.mid{background:var(--warnl)!important} .pg-cell.lo{background:var(--harml)!important}
.pg-cell.few{background:var(--sunk)!important}
.pg-pick{display:flex;flex-wrap:wrap;gap:4px 12px;margin-top:6px;font-size:12.5px}
.pg-new{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:14px 0 4px}
.pg-new label{font-size:13px;font-weight:600}
.pg-new .signinbox{width:auto;flex:1 1 200px;margin:0}
.pgj-says{font-size:13px;color:var(--ink2);line-height:1.5;margin:0 0 12px}
#pgjoin label{display:block;font-size:12.5px;color:var(--ink2);margin:0 0 4px}
@media (max-width:640px){.pg-wrap{padding:14px 12px 50px}.pg-pane{padding:14px 12px}}`;
    document.head.appendChild(css);
    const box=document.createElement('div');
    box.innerHTML=`
<div id="pgview" class="hidden" role="dialog" aria-modal="true" aria-labelledby="pg-title">
  <div class="pg-wrap">
    <div class="pg-head"><h1 id="pg-title">Analytics</h1><button class="btn ghost" type="button" id="pg-close">Close</button></div>
    <div id="pg-body"></div>
  </div>
</div>
<div id="pgjoin" class="leaveview hidden" role="dialog" aria-modal="true" aria-labelledby="pgj-title">
  <form class="leavecard signincard" id="pgj-form" novalidate>
    <h2 id="pgj-title">Join a program</h2>
    <p class="pgj-says">Your program's admins will see which cases you finish and your results in them, under the name you give here. They do not see anything you type in a case. You cannot delete a finished case while you are in a program.</p>
    <label for="pgj-code">Program code</label>
    <input class="signinbox" id="pgj-code" maxlength="16" autocomplete="off" autocapitalize="characters" spellcheck="false">
    <label for="pgj-name">Your name</label>
    <input class="signinbox" id="pgj-name" maxlength="80" autocomplete="name">
    <label for="pgj-year">Year of training</label>
    <select class="signinbox" id="pgj-year">${YEARS.map(y=>`<option value="${y[0]}">${y[1]}</option>`).join('')}</select>
    <div class="signinerr" id="pgj-err" role="alert"></div>
    <div class="leavebtns"><button class="btn ghost" type="button" id="pgj-no">Not now</button><button class="btn" type="submit" id="pgj-ok">Join</button></div>
  </form>
</div>`;
    while(box.firstElementChild) document.body.appendChild(box.firstElementChild);
    bind();
  }

  return {init, onSession, paintAccount, isMember:()=>!!member(), enabled:on,
          /* for the site check */ _state:()=>({uid, infoState, info, view:{open:view.open,tab:view.tab,scope:view.scope,state:view.state,first:view.first}})};
})();
