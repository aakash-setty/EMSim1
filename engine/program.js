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
  const TABS = [['overview','Overview'],['people','Residents'],['cases','Cases'],['missed','Missed and unsafe'],['prio','Teaching priorities'],['programs','Programs']];
  const CLOSED = 85;               /* a skill area done unprompted this often is called closed */
  const GAIN = 15;                 /* points gained from the first year to the last to call it closing */
  const MIN_N = 5;                 /* below this, a rate is not shown as a rate */

  let client=null, uid=null, info=null, infoState='idle';   /* idle | loading | ready | error */
  let view={open:false, tab:'overview', scope:null, first:true, days:null, data:null, state:'idle', err:'',
            overview:null, openCase:null, confirm:null, note:'', prev:null, testNamed:true, prioSort:'count', openSkill:null};
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

  /* ---- test data (10 November 2026, owner's request) ----
     A made-up program with made-up residents and made-up runs, so the screens can be tried
     and developed before real data exists. It is built in this browser, from a fixed seed,
     so it is the same every time. Nothing is read from or written to the database, and no
     real account appears in it. Staff only.

     What is real in it: the case list and the catalog's action and diagnosis names. What is
     not: everything else. The actions each case "expects" are drawn at random from the
     catalog, so they do not fit the case. The screens say so.

     How the numbers are made, so that the screens have shapes to show. The rates are
     invented and are not an estimate of how real residents do: each resident has
     a skill that rises with the year of training and an appetite for doing cases. Each
     expected action has its own difficulty. A weaker resident misses more, needs more
     prompts, acts later, and takes more discouraged actions. A second attempt is better
     than a first. aggregate() then gathers the runs exactly as program_analytics does in
     the database, so First attempts only, the period and results by name all work. */
  const TEST_ID='test';
  let TEST=null;
  function seeded(seed){
    let a=seed>>>0;
    return ()=>{ a=(a+0x6D2B79F5)|0; let t=Math.imul(a^(a>>>15),1|a); t=(t+Math.imul(t^(t>>>7),61|t))^t; return ((t^(t>>>14))>>>0)/4294967296; };
  }
  function testStore(){
    if(TEST) return TEST;
    const R=seeded(20261110);
    const clamp=(x,lo,hi)=>Math.max(lo,Math.min(hi,x));
    const bell=()=>(R()+R()+R())/3;                       /* 0 to 1, bunched in the middle */
    const take=(list,n)=>{ const l=list.slice(), out=[]; while(l.length&&out.length<n) out.push(l.splice(Math.floor(R()*l.length),1)[0]); return out; };
    const GIVEN=['Avery','Blake','Casey','Devon','Emery','Finley','Harper','Jordan','Kendall','Logan','Morgan','Parker','Quinn','Reese','Riley','Rowan','Sage','Skyler','Taylor','Tatum'];
    const FAMILY=['Abara','Bianchi','Castillo','Dubois','Eriksen','Farouk','Greene','Haddad','Ito','Jensen','Kowalski','Lindqvist','Mensah','Nakamura','Okafor','Petrov','Quintero','Rahman','Silva','Tanaka','Ueda','Vargas','Whitfield','Yilmaz'];
    const base=(typeof SHARED==='object'&&SHARED&&SHARED.actionsBase)||{};
    const byTab={}; Object.keys(base).forEach(id=>{ const a=base[id]; if(a.hidden||/^stop_|^hidden_/.test(id)) return; (byTab[a.tab]=byTab[a.tab]||[]).push(id); });
    const dxAll=((typeof SHARED==='object'&&SHARED&&SHARED.diagnoses)||[]).map(d=>d.id);
    const DISP=['icu','step_down','ward','discharge_home'];
    const now=Date.now(), DAY=86400000;

    const people=[];
    const names=take(GIVEN.flatMap(g=>FAMILY.map(f=>g+' '+f)),38);
    for(let y=1;y<=3;y++) for(let k=0;k<12;k++){
      people.push({user_id:'test-'+y+'-'+k, name:names[people.length], pgy:y, role:'resident',
        joined_at:new Date(now-(250-Math.floor(R()*20))*DAY).toISOString(),
        skill:clamp(0.36+0.13*y+(bell()-0.5)*0.5,0.08,0.97), keen:clamp(0.25+bell()*0.9,0.1,1)});
    }
    people.push({user_id:'test-a-0',name:names[36],pgy:null,role:'admin',joined_at:new Date(now-260*DAY).toISOString(),skill:0,keen:0});
    people.push({user_id:'test-a-1',name:names[37],pgy:null,role:'admin',joined_at:new Date(now-260*DAY).toISOString(),skill:0,keen:0});

    const cases=allPrefixes().map(prefix=>{
      const item=(k,id,late)=>({k,id,tab:(base[id]||{}).tab||null,cat:(base[id]||{}).category||null,grp:(base[id]||{}).group||null,
                                hard:(R()<0.2?0.45+R()*0.35:0.03+R()*0.2), et:late?take([120,240,360],1)[0]:0});
      const crit=[].concat(take(byTab.stabilization||[],2),take(byTab.investigations||[],3),take(byTab.interventions||[],3),take(byTab.consultations||[],1));
      const rest=id=>!crit.includes(id);
      return {prefix, tough:(R()-0.5)*0.24,
        critical:crit.map((id,i)=>item('critical',id,i%3===2)),
        recommended:[].concat(take((byTab.investigations||[]).filter(rest),2),take((byTab.exam||[]).filter(rest),2)).map(id=>item('recommended',id,false)),
        discouraged:take((byTab.interventions||[]).filter(rest),3).map(id=>item('discouraged',id,false)),
        harmful:item('harmful',take((byTab.interventions||[]).filter(rest),1)[0],false),
        dx:take(dxAll,4), disp:take(DISP,4)};
    });

    const records=[], open=[];
    people.filter(p=>p.role==='resident').forEach(p=>{
      cases.forEach(c=>{
        if(R()>p.keen*0.9){ if(R()<0.06) open.push({user_id:p.user_id,case_prefix:c.prefix}); return; }
        let when=now-Math.floor((0.02+R()*0.96)*235)*DAY - Math.floor(R()*DAY);
        const tries=1+(R()<0.34?1:0)+(R()<0.09?1:0);
        for(let n=1;n<=tries;n++){
          const skill=clamp(p.skill-c.tough+(n-1)*0.17,0.03,0.99), items=[], why=[];
          let missed=0, prompted=0;
          c.critical.forEach(i=>{
            const pOwn=clamp(skill+0.45-i.hard*0.9,0.03,0.995), own=R()<pOwn, done=own||R()<0.93;
            if(!done) missed++; else if(!own) prompted++;
            items.push({k:'critical',id:i.id,tab:i.tab,cat:i.cat,grp:i.grp,r:done?'done':'missed',p:!own,et:i.et,
              dt:done?Math.round((i.et+(own?12+R()*(1.15-skill)*260*(0.5+i.hard):170+R()*150))*10)/10:null});
          });
          c.recommended.forEach(i=>{
            const done=R()<clamp(skill+0.05-i.hard,0.03,0.97);
            items.push({k:'recommended',id:i.id,tab:i.tab,cat:i.cat,grp:i.grp,r:done?'done':'missed',p:false,et:0,dt:done?Math.round((20+R()*400)*10)/10:null});
          });
          c.discouraged.forEach(i=>{ if(R()<(1-skill)*(0.1+i.hard*0.5))
            items.push({k:'discouraged',id:i.id,tab:i.tab,cat:i.cat,grp:i.grp,r:'taken',p:false,et:null,dt:Math.round((30+R()*500)*10)/10}); });
          const harm=R()<(1-skill)*0.07, lost=!harm&&missed>=2&&R()<(1-skill)*0.3;
          if(harm) items.push({k:'harmful',id:c.harmful.id,tab:c.harmful.tab,cat:c.harmful.cat,grp:c.harmful.grp,r:'taken',p:false,et:null,dt:Math.round((40+R()*400)*10)/10});
          let dxR='none', dxId=null, dR='none', dId=null;
          if(!harm&&!lost){
            const a=R(), b=R(), pd=0.6+skill*0.38, pp=0.75+skill*0.24;
            if(a<pd){ dxR='correct'; dxId=c.dx[0]; } else if(a<pd+(1-pd)*0.5){ dxR='defensible'; dxId=c.dx[1]; } else { dxR='incorrect'; dxId=c.dx[2+Math.floor(R()*2)]; }
            if(b<pp){ dR='correct'; dId=c.disp[0]; } else if(b<pp+(1-pp)*0.4){ dR='defensible'; dId=c.disp[1]; } else { dR='incorrect'; dId=c.disp[2+Math.floor(R()*2)]; }
          }
          items.push({k:'diagnosis',id:dxId,tab:null,cat:null,grp:null,r:dxR,p:false,et:null,dt:null});
          items.push({k:'disposition',id:dId,tab:null,cat:null,grp:null,r:dR,p:false,et:null,dt:null});
          if(lost) why.push('case_lost'); if(harm) why.push('harmful_action'); if(missed) why.push('critical_missed');
          if(!harm&&!lost){ if(dxR==='incorrect') why.push('diagnosis'); if(dR==='incorrect') why.push('disposition'); }
          records.push({user_id:p.user_id,pgy:p.pgy,case_prefix:c.prefix,attempt_no:n,
            result:why.length?'not_met':(prompted?'met_prompted':'met'),why,items,
            sim_seconds:Math.round(harm||lost?120+R()*420:420+R()*(1.3-skill)*700),finished_at:Math.min(when,now-3600000)});
          when+=Math.floor((1+R()*24)*DAY);
        }
      });
    });
    TEST={people,records,open};
    return TEST;
  }
  /* The same gathering program_analytics does in the database, over a list of run records. */
  function aggregate(store,opt){
    const now=Date.now();
    const rec=store.records.filter(r=>opt.days===null||opt.days===undefined||r.finished_at>now-opt.days*86400000);
    const sel=rec.filter(r=>!opt.first||r.attempt_no===1);
    const count=(l,f)=>l.reduce((n,x)=>n+(f(x)?1:0),0);
    const mixOf=l=>({n:l.length,met:count(l,r=>r.result==='met'),met_prompted:count(l,r=>r.result==='met_prompted'),not_met:count(l,r=>r.result==='not_met'),
                     harmful:count(l,r=>r.why.includes('harmful_action')),lost:count(l,r=>r.why.includes('case_lost'))});
    const groups=(l,key)=>{ const m=new Map(); l.forEach(x=>{ const k=key(x); if(!m.has(k)) m.set(k,[]); m.get(k).push(x); }); return [...m.values()]; };
    const median=l=>{ if(!l.length) return null; const a=l.slice().sort((x,y)=>x-y), h=a.length>>1; return a.length%2?a[h]:(a[h-1]+a[h])/2; };
    const uniq=l=>new Set(l).size;
    const its=[]; sel.forEach(r=>r.items.forEach(i=>its.push({run:r,i})));
    const key=x=>x.run.case_prefix+'|'+x.i.k+'|'+x.i.id;
    const crit=its.filter(x=>x.i.k==='critical'), area=x=>x.i.grp||'Other';
    const skillOf=l=>({n:l.length,done:count(l,x=>x.i.r==='done'),prompted:count(l,x=>x.i.r==='done'&&x.i.p),learners:uniq(l.map(x=>x.run.user_id))});
    return {generated_at:new Date().toISOString(), first_only:!!opt.first, days:opt.days===undefined?null:opt.days, named:!!opt.named, staff:true, test:true,
      program:{id:TEST_ID,name:'Test program',status:'active',join_code:null,show_named_results:!!opt.named,all_cases:true,seats:null,cases:[]},
      totals:{people:store.people.length,residents:count(store.people,p=>p.role!=='admin'),
        active_30d:uniq(rec.filter(r=>r.finished_at>now-30*86400000).map(r=>r.user_id)),with_a_finished_run:uniq(rec.map(r=>r.user_id)),
        runs:rec.length,first_attempts:count(rec,r=>r.attempt_no===1),open_runs:store.open.length},
      members:store.people.slice().sort((a,b)=>a.name<b.name?-1:1).map(p=>{
        const mine=rec.filter(r=>r.user_id===p.user_id), cs=[...new Set(mine.map(r=>r.case_prefix))];
        return {user_id:p.user_id,name:p.name,pgy:p.pgy,role:p.role,joined_at:p.joined_at,cases_finished:cs.length,runs:mine.length,
          open:count(store.open,o=>o.user_id===p.user_id),case_minutes:Math.round(mine.reduce((n,r)=>n+r.sim_seconds,0)/60),
          last_finished:mine.length?new Date(Math.max.apply(null,mine.map(r=>r.finished_at))).toISOString():null,cases:cs,
          results:opt.named?mixOf(sel.filter(r=>r.user_id===p.user_id)):null}; }),
      cases:groups(sel,r=>r.case_prefix).map(l=>Object.assign({case_prefix:l[0].case_prefix,learners:uniq(l.map(r=>r.user_id)),
        median_seconds:median(l.map(r=>r.sim_seconds)),open:count(store.open,o=>o.case_prefix===l[0].case_prefix)},mixOf(l)))
        .sort((a,b)=>a.case_prefix<b.case_prefix?-1:1),
      items:groups(its.filter(x=>x.i.k==='critical'||x.i.k==='recommended'),key).map(l=>({case_prefix:l[0].run.case_prefix,kind:l[0].i.k,item_id:l[0].i.id,
        tab:l[0].i.tab,cat:l[0].i.cat,grp:l[0].i.grp,n:l.length,done:count(l,x=>x.i.r==='done'),prompted:count(l,x=>x.i.r==='done'&&x.i.p),
        learners_missed:uniq(l.filter(x=>x.i.r==='missed').map(x=>x.run.user_id)),
        median_delay:median(l.filter(x=>x.i.r==='done'&&x.i.dt!==null&&x.i.et!==null).map(x=>x.i.dt-x.i.et))})),
      safety:groups(its.filter(x=>x.i.k==='discouraged'||x.i.k==='harmful'),key).map(l=>({case_prefix:l[0].run.case_prefix,kind:l[0].i.k,item_id:l[0].i.id,
        tab:l[0].i.tab,cat:l[0].i.cat,grp:l[0].i.grp,runs:l.length,learners:uniq(l.map(x=>x.run.user_id))})),
      skills:groups(crit,area).map(l=>Object.assign({grp:area(l[0]),learners_lost:uniq(l.filter(x=>x.i.r!=='done'||x.i.p).map(x=>x.run.user_id)),
        cases:uniq(l.map(x=>x.run.case_prefix))},skillOf(l))),
      skill_years:groups(crit,x=>area(x)+'|'+x.run.pgy).map(l=>Object.assign({grp:area(l[0]),pgy:l[0].run.pgy},skillOf(l))),
      handoff:groups(its.filter(x=>x.i.k==='diagnosis'||x.i.k==='disposition'),x=>key(x)+'|'+x.i.r).map(l=>({case_prefix:l[0].run.case_prefix,kind:l[0].i.k,
        item_id:l[0].i.id,result:l[0].i.r,n:l.length})),
      months:groups(sel,r=>new Date(r.finished_at).toISOString().slice(0,7)).map(l=>Object.assign({month:new Date(l[0].finished_at).toISOString().slice(0,7)},mixOf(l)))
        .sort((a,b)=>a.month<b.month?-1:1),
      years:groups(sel,r=>String(r.pgy)).map(l=>Object.assign({pgy:l[0].pgy,learners:uniq(l.map(r=>r.user_id))},mixOf(l))).sort((a,b)=>(a.pgy||99)-(b.pgy||99))};
  }
  const inTest = () => view.scope===TEST_ID;
  function toggleTest(){
    if(!isStaff()) return;
    if(inTest()) view.scope=view.prev||'all';
    else { view.prev=view.scope; view.scope=TEST_ID; if(view.tab==='programs') view.tab='overview'; A.track('analytics_test_data',{}); }
    view.openCase=null; view.confirm=null; view.note='';
    fetchAll();
  }

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
    $('pg-close').focus();
    A.track('analytics_opened',{staff:isStaff()});
    paint(); fetchAll();
  }
  function close(){
    view.open=false; view.data=null; const v=$('pgview'); if(v) v.classList.add('hidden');
    const o=$('pg-open'); if(o) o.focus();
  }
  async function fetchAll(){
    view.state='loading'; view.err=''; paint();
    try{
      if(isStaff()){
        const o=await client.rpc('staff_overview'); if(o.error) throw o.error;
        view.overview=o.data;
      }
      if(inTest()){ view.data=aggregate(testStore(),{first:view.first,days:view.days,named:view.testNamed}); view.state='ready'; paint(); return; }
      const r=await client.rpc('program_analytics',
        {p_program: view.scope==='all'?null:view.scope, p_first:view.first, p_days:view.days});
      if(r.error) throw r.error;
      const d=r.data;
      /* Teaching priorities reads program_skills (005). If that is not there yet, the skill
         areas are gathered here from the items, without learners and without the years. */
      try{
        const k=await client.rpc('program_skills',
          {p_program: view.scope==='all'?null:view.scope, p_first:view.first, p_days:view.days});
        if(k.error) throw k.error;
        d.skills=(k.data&&k.data.skills)||[]; d.skill_years=(k.data&&k.data.skill_years)||[];
      }catch(e){
        const m=new Map();
        (d.items||[]).filter(i=>i.kind==='critical').forEach(i=>{ const g=i.grp||'Other';
          const o=m.get(g)||{grp:g,n:0,done:0,prompted:0,learners:null,learners_lost:null,set:new Set()};
          o.n+=i.n; o.done+=i.done; o.prompted+=i.prompted; o.set.add(i.case_prefix); m.set(g,o); });
        d.skills=[...m.values()].map(o=>{ o.cases=o.set.size; delete o.set; return o; }); d.skill_years=null;
      }
      view.data=d; view.state='ready';
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

  /* The two overview charts. Each bar is one group's runs split into the three results, as
     shares, with the number of runs beside it so a tall share of a small group is not
     mistaken for much. A segment says what it is when the pointer rests on it. */
  const PARTS=[['met','Met','a'],['met_prompted','Met with prompts','b'],['not_met','Not met','c']];
  const seg=(o,horizontal)=>{ const n=(o.met||0)+(o.met_prompted||0)+(o.not_met||0);
    return PARTS.map(p=>{ const v=o[p[0]]||0, sh=n?100*v/n:0; if(!v) return '';
      return `<i class="${p[2]}" style="flex:${v} 0 0" title="${p[1]}: ${v} of ${n} (${Math.round(sh)}%)">${sh>=(horizontal?11:16)?`<em>${Math.round(sh)}%</em>`:''}</i>`; }).join(''); };
  function yearChart(years){
    if(!years.length) return '<p class="pg-empty">No finished runs yet.</p>';
    return `<div class="pg-ych" role="img" aria-label="Results by year of training, as shares of each year's runs">${years.map(y=>
      `<div class="pg-yrow"><span class="pg-yl">${esc(yearName(y.pgy))}<small>${y.n} ${y.n===1?'run':'runs'}, ${y.learners} ${y.learners===1?'learner':'learners'}</small></span>
        <span class="pg-stack h">${seg(y,true)}</span></div>`).join('')}</div>`;
  }
  function monthChart(months){
    if(!months.length) return '<p class="pg-empty">No finished runs yet.</p>';
    const name=m=>{ const d=new Date(m+'-15T00:00:00Z'); return isNaN(d)?m:d.toLocaleDateString(undefined,{month:'short',timeZone:'UTC'}); };
    return `<div class="pg-mch" role="img" aria-label="Results by month, as shares of each month's runs">${months.map((m,i)=>
      `<div class="pg-mcol"><span class="pg-stack v">${seg(m,false)}</span>
        <span class="pg-ml">${esc(name(m.month))}${(i===0||/-01$/.test(m.month))?`<small>${esc(m.month.slice(0,4))}</small>`:''}</span><span class="pg-n">${m.n}</span></div>`).join('')}</div>
      <p class="pg-key">The number under each month is its runs.</p>`;
  }
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
      <div class="pg-two">
        <section><h3>By year of training</h3>${yearChart(d.years||[])}
          <details class="pg-ast"><summary>Show as a table</summary>${table(['Year','Learners','Runs','Results'],(d.years||[]).map(y=>
            `<tr><td>${esc(yearName(y.pgy))}</td><td>${y.learners}</td><td>${y.n}</td><td>${mix(y)}</td></tr>`),'No finished runs yet.')}</details></section>
        <section><h3>By month</h3>${monthChart(d.months||[])}
          <details class="pg-ast"><summary>Show as a table</summary>${table(['Month','Runs','Results'],(d.months||[]).map(m=>
            `<tr><td>${esc(m.month)}</td><td>${m.n}</td><td>${mix(m)}</td></tr>`),'No finished runs yet.')}</details></section>
      </div>`;
  }
  function tPeople(d){
    const total=allPrefixes().length;
    const head=['Name','Year','Cases finished','Runs','In progress','Case minutes','Last finished'];
    if(d.named) head.push('Results','Harmful action','Case lost');
    head.push('');
    const rows=(d.members||[]).map(m=>{
      const r=m.results||{}, who=m.name||('Account '+String(m.user_id).slice(0,8));
      const tools= (m.role==='individual'||d.test) ? '' :
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
  /* Teaching priorities (10 November 2026). The gap map it replaces crossed the case's topic
     with the ordering tab, and neither is something a program teaches to. This asks the two
     questions a program can act on, by skill area (the group the catalog files an action
     under):
       1. Where are critical actions lost most? A chance is one critical action expected in
          one run. It is lost when the action was missed or was done only after the nurse
          prompted for it. The list opens ordered by the number of chances lost, not the
          share, because the highest shares tend to sit on the fewest chances: one case and
          a dozen runs can top a list by rate and mean very little.
       2. Does the gap close with training? The same rate for each year. A gap that is still
          open in the last year is the program's to teach. One that closes is being learned.
     A skill area opens to the actions in it. CLOSED and GAIN are this file's own
     thresholds, chosen to sort the list, not taken from any standard. */
  function tPriorities(d){
    const sk=(d.skills||[]).map(x=>Object.assign({},x,{unp:x.done-x.prompted,missed:x.n-x.done,lost:x.n-(x.done-x.prompted)}));
    if(!sk.length) return '<p class="pg-empty">No finished runs yet.</p>';
    const byRate=(a,b)=>(b.lost/b.n-a.lost/a.n)||(b.lost-a.lost), byCount=(a,b)=>(b.lost-a.lost)||(b.lost/b.n-a.lost/a.n);
    const rated=sk.filter(x=>x.n>=MIN_N).sort(view.prioSort==='count'?byCount:byRate);
    const few=sk.filter(x=>x.n<MIN_N).sort((a,b)=>b.lost-a.lost);
    const hasYears=Array.isArray(d.skill_years);
    const yearsOf=g=>(d.skill_years||[]).filter(y=>y.grp===g&&y.pgy!==null&&y.pgy!==undefined&&y.n>=MIN_N)
      .map(y=>({pgy:y.pgy,n:y.n,rate:100*(y.done-y.prompted)/y.n})).sort((a,b)=>a.pgy-b.pgy);
    const verdict=ys=>{
      if(ys.length<2) return {k:'none',t:'Too few runs in two years to compare'};
      const first=ys[0], last=ys[ys.length-1], gain=Math.round(last.rate-first.rate), at=`${Math.round(last.rate)}% unprompted in ${yearName(last.pgy)}`;
      if(last.rate>=CLOSED) return {k:'ok',t:`Closed by ${yearName(last.pgy)}. ${at}`};
      if(gain>=GAIN) return {k:'warn',t:`Closing, not closed. Up ${gain} points, ${at}`};
      return {k:'harm',t:`Persists. ${gain>=0?'Up '+gain:'Down '+(-gain)} points, ${at}`};
    };
    const detail=g=>{
      const its=(d.items||[]).filter(i=>i.kind==='critical'&&(i.grp||'Other')===g).sort((a,b)=>((b.n-b.done+b.prompted)/b.n)-((a.n-a.done+a.prompted)/a.n));
      return `<div class="pg-detail">${table(['Action','Case','Missed','Only after a prompt','Median time to act'],its.map(i=>
        `<tr><td>${esc(actName(i.item_id))}</td><td>${esc(caseName(i.case_prefix))}</td><td>${rate(i.n-i.done,i.n)}</td><td>${rate(i.prompted,i.n)}</td>
         <td>${i.median_delay===null||i.median_delay===undefined?'':mmss(i.median_delay)}</td></tr>`),'Nothing recorded.')}</div>`;
    };
    const who=x=>(x.learners?`${x.learners_lost} of ${x.learners} ${x.learners===1?'learner':'learners'}, `:'')+`${x.cases} ${x.cases===1?'case':'cases'}`;
    const row=x=>{
      const on=view.openSkill===x.grp, pm=100*x.missed/x.n, pp=100*x.prompted/x.n;
      return `<div class="pg-pr${on?' on':''}">
        <button type="button" class="pg-link pg-prn" data-pgskill="${esc(x.grp)}" aria-expanded="${on}">${esc(x.grp)}</button>
        <span class="pg-prbar" role="img" aria-label="${Math.round(pm+pp)} percent of chances lost">${x.missed?`<i class="c" style="width:${pm.toFixed(1)}%" title="Missed: ${x.missed} of ${x.n}"></i>`:''}${x.prompted?`<i class="b" style="width:${pp.toFixed(1)}%" title="Done only after a prompt: ${x.prompted} of ${x.n}"></i>`:''}</span>
        <span class="pg-prv"><b>${Math.round(pm+pp)}%</b> <span class="pg-n">${x.lost} of ${x.n} chances</span></span>
        <span class="pg-prw pg-n">${esc(who(x))}</span></div>${on?detail(x.grp):''}`;
    };
    const top=rated[0];
    const lead= top&&top.lost ? (()=>{ const v=verdict(yearsOf(top.grp));
        return `<p class="pg-lead"><b>${esc(top.grp)}</b> ${view.prioSort==='count'?'is where the most chances are lost':'has the highest share lost'}: ${top.lost} of ${top.n} chances (${Math.round(100*top.lost/top.n)}%), across ${esc(who(top))}.${hasYears&&v.k!=='none'?' '+esc(v.t)+'.':''}</p>`; })()
      : '<p class="pg-lead">No critical action was lost in any skill area with enough runs to rate.</p>';
    const order=rated.map(x=>({x,ys:yearsOf(x.grp)})).map(o=>Object.assign(o,{v:verdict(o.ys)}))
      .sort((a,b)=>(a.ys.length<2)-(b.ys.length<2)||((a.ys[a.ys.length-1]||{rate:101}).rate-(b.ys[b.ys.length-1]||{rate:101}).rate));
    const dots=o=>{
      const lo=Math.min.apply(null,o.ys.map(y=>y.rate)), hi=Math.max.apply(null,o.ys.map(y=>y.rate));
      return `<div class="pg-dr"><span class="pg-prn">${esc(o.x.grp)}</span>
        <span class="pg-track" role="img" aria-label="${esc(o.ys.map(y=>yearName(y.pgy)+' '+Math.round(y.rate)+' percent').join(', '))}">
          <i class="goal" style="left:${CLOSED}%"></i>${o.ys.length>1?`<i class="span" style="left:${lo.toFixed(1)}%;width:${(hi-lo).toFixed(1)}%"></i>`:''}
          ${o.ys.map((y,i)=>`<i class="dot y${Math.max(0,Math.min((y.pgy||1)-1,3))}" style="left:${y.rate.toFixed(1)}%" title="${esc(yearName(y.pgy))}: ${Math.round(y.rate)}% unprompted, ${y.n} chances">${y.pgy}</i>`).join('')}</span>
        <span class="pg-verdict ${o.v.k}">${esc(o.v.t)}</span></div>`;
    };
    return `${lead}
      <h3>Where critical actions are lost</h3>
      <p class="pg-note">A chance is one critical action expected in one run. It is lost when the action was missed, or done only after the nurse prompted for it. Skill areas are the groups the order menus use. Choose one to see its actions.</p>
      <div class="pg-sort" role="group" aria-label="Order"><span>Order by</span>
        <button type="button" data-pgsort="count"${view.prioSort==='count'?' class="on"':''} aria-pressed="${view.prioSort==='count'}">Chances lost</button>
        <button type="button" data-pgsort="rate"${view.prioSort==='rate'?' class="on"':''} aria-pressed="${view.prioSort==='rate'}">Share lost</button></div>
      <p class="pg-key"><span class="pg-mix k"><i class="c" style="width:100%"></i></span> Missed
        <span class="pg-mix k"><i class="b" style="width:100%"></i></span> Done only after a prompt</p>
      <div class="pg-prs">${rated.map(row).join('')}</div>
      ${few.length?`<p class="pg-note">Too few chances to rate (under ${MIN_N}): ${few.map(x=>`${esc(x.grp)} (${x.lost} of ${x.n})`).join(', ')}.</p>`:''}
      <h3>Does it close with training?</h3>
      ${hasYears?`<p class="pg-note">Each dot is one year of training: the share of chances done with no prompt. The line marks ${CLOSED}%. A skill area still left of it in the last year is one the program has not closed. A year with fewer than ${MIN_N} chances is left out. The ${CLOSED}% line and the ${GAIN}-point rule are choices made to sort this list, not a standard.</p>
        <div class="pg-axis"><span></span><span class="pg-ticks"><i style="left:0">0%</i><i style="left:50%">50%</i><i style="left:100%">100%</i></span><span></span></div>
        <div class="pg-drs">${order.map(dots).join('')}</div>`
      :`<p class="pg-note">The comparison by year needs the database function program_skills, which is not answering. The list above was gathered without it.</p>`}`;
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
    const tabs=TABS.filter(t=>t[0]!=='programs'||(isStaff()&&!inTest()));
    const scope = isStaff()
      ? `<select id="pg-scope" aria-label="Whose data"><option value="all"${view.scope==='all'?' selected':''}>Every account</option>
          ${(o.programs||[]).map(p=>`<option value="${esc(p.id)}"${view.scope===p.id?' selected':''}>${esc(p.name)}</option>`).join('')}
          <option value="${TEST_ID}"${inTest()?' selected':''}>Test data (made up)</option></select>`
      : `<span class="pg-scope">${esc((member()||{}).program||'')}</span>`;
    let body;
    if(view.state==='error') body=`<p class="pg-empty">${esc(view.err)}</p>`;
    else if(!d) body='<p class="pg-empty">Loading.</p>';
    else body=({overview:tOverview,people:tPeople,cases:tCases,missed:tMissed,prio:tPriorities,programs:tPrograms})[view.tab](d);
    $('pg-body').innerHTML=
      `<div class="pg-bar">${scope}
        <label class="pg-sw"><input type="checkbox" id="pg-first" ${view.first?'checked':''}> First attempts only</label>
        <select id="pg-days" aria-label="Period"><option value="">All time</option><option value="30"${view.days===30?' selected':''}>Last 30 days</option>
          <option value="90"${view.days===90?' selected':''}>Last 90 days</option><option value="365"${view.days===365?' selected':''}>Last year</option></select>
        <span class="pg-msg" role="status">${esc(view.note)}</span></div>
      <div class="pg-tabs" role="tablist">${tabs.map(t=>`<button type="button" role="tab" aria-selected="${view.tab===t[0]}" data-pgtab="${t[0]}"${view.tab===t[0]?' class="on"':''}>${t[1]}</button>`).join('')}
        ${isStaff()?`<button type="button" class="pg-testtab${inTest()?' on':''}" data-pgtest="1" aria-pressed="${inTest()}">Test data</button>`:''}</div>
      ${inTest()?`<div class="pg-testbar" role="note"><b>Test data.</b> Every resident, run and result on these tabs is made up in this browser. Nothing is real and nothing is saved.
          The actions each case expects are drawn at random from the catalog, so they do not fit the case.
          <span class="pg-testtools"><label class="pg-sw"><input type="checkbox" id="pg-testnamed" ${view.testNamed?'checked':''}> Results by name</label>
          <button type="button" class="pg-link" data-pgtest="1">Back to real data</button></span></div>`:''}
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
      if(ds.pgtest){ toggleTest(); return; }
      if(ds.pgtab){ view.tab=ds.pgtab; view.note=''; paint(); return; }
      if(ds.pgcase){ view.openCase=view.openCase===ds.pgcase?null:ds.pgcase; paint(); return; }
      if(ds.pgskill){ view.openSkill=view.openSkill===ds.pgskill?null:ds.pgskill; paint(); return; }
      if(ds.pgsort){ view.prioSort=ds.pgsort; paint(); return; }
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
      if(t.id==='pg-scope'){ if(t.value===TEST_ID&&!inTest()){ toggleTest(); return; }
        view.scope=t.value; view.openCase=null; fetchAll(); return; }
      if(t.id==='pg-testnamed'){ view.testNamed=t.checked; fetchAll(); return; }
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
    /* Escape closes whichever of the two is open. The listener is on the document because a
       repaint replaces the element that had the focus, and the key then goes to the body. */
    document.addEventListener('keydown', e=>{
      if(e.key!=='Escape') return;
      if(join.open){ e.stopPropagation(); closeJoin(); }
      else if(view.open){ e.stopPropagation(); close(); }
    }, true);
    $('pgj-form').addEventListener('submit', e=>{ e.preventDefault(); submitJoin(); });
    $('pgj-no').onclick=closeJoin;
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
.pg-bar select{width:auto;flex:0 0 auto;font:inherit;font-size:13.5px;color:var(--ink);background:var(--solid);border:1px solid var(--rule);border-radius:6px;padding:6px 8px}
.pg-scope{font-weight:600}
.pg-msg{color:var(--ok);font-size:13px}
.pg-sw{display:inline-flex;align-items:center;gap:6px;font-size:13.5px;cursor:pointer}
.pg-tabs{display:flex;flex-wrap:wrap;gap:4px;border-bottom:1px solid var(--rule);margin-bottom:16px}
.pg-tabs button{font:inherit;font-size:13.5px;color:var(--ink2);background:none;border:0;border-bottom:2px solid transparent;padding:9px 12px;cursor:pointer}
.pg-tabs button.on{color:var(--act);border-bottom-color:var(--act);font-weight:600}
.pg-testtab{margin-left:auto;border:1px solid var(--rule)!important;border-radius:999px;padding:5px 14px!important;align-self:center;margin-bottom:5px}
.pg-tabs button.pg-testtab.on{background:var(--warnl);color:var(--warn);border-color:var(--warn)!important}
.pg-testbar{background:var(--warnl);border:1px solid var(--warn);border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:13px;line-height:1.5}
.pg-testtools{display:inline-flex;align-items:center;gap:14px;margin-left:10px;white-space:nowrap}
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
.pg-two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px;margin-top:22px}
.pg-two h3{margin-top:0}
.pg-stack{display:flex;gap:2px;border-radius:4px;overflow:hidden}
.pg-stack i{display:flex;align-items:center;justify-content:center;min-width:0;font-style:normal}
.pg-stack i.a{background:var(--ok)} .pg-stack i.b{background:var(--warn)} .pg-stack i.c{background:var(--harm)}
.pg-stack em{font-style:normal;font-size:11.5px;font-weight:600;color:#fff;font-family:var(--mono)}
.pg-stack.h{flex:1;height:26px}
.pg-stack.v{flex-direction:column-reverse;height:150px;width:100%;max-width:44px}
.pg-yrow{display:flex;align-items:center;gap:12px;margin:10px 0}
.pg-yl{flex:0 0 132px;font-size:13.5px;font-weight:600}
.pg-yl small,.pg-ml small{display:block;font-weight:400;font-size:11.5px;color:var(--ink3)}
.pg-mch{display:flex;align-items:flex-end;gap:8px;margin-top:10px}
.pg-mcol{flex:1 1 0;display:flex;flex-direction:column;align-items:center;gap:4px;min-width:0}
.pg-ml{font-size:12px;text-align:center;min-height:34px}
.pg-ast{margin-top:10px;font-size:12.5px;color:var(--ink2)}
.pg-ast summary{cursor:pointer}
.pg-lead{font-size:15.5px;line-height:1.5;margin:0 0 18px;max-width:820px}
.pg-sort{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink2);margin:6px 0}
.pg-sort button{font:inherit;font-size:12.5px;color:var(--ink2);background:var(--solid);border:1px solid var(--rule);border-radius:999px;padding:3px 11px;cursor:pointer}
.pg-sort button.on{color:var(--act);border-color:var(--act);background:var(--actl)}
.pg-pr,.pg-dr,.pg-axis{display:grid;grid-template-columns:minmax(150px,230px) minmax(120px,1fr) minmax(150px,190px) minmax(0,200px);gap:14px;align-items:center;padding:7px 0;border-bottom:1px solid var(--rule2)}
.pg-dr,.pg-axis{grid-template-columns:minmax(150px,230px) minmax(160px,1fr) minmax(0,330px)}
.pg-axis{border:0;padding:0 0 2px}
.pg-prn{font-size:13.5px;overflow-wrap:anywhere}
.pg-prbar{display:flex;gap:2px;height:14px;background:var(--sunk);border-radius:3px;overflow:hidden}
.pg-prbar i{display:block;height:100%} .pg-prbar .c{background:var(--harm)} .pg-prbar .b{background:var(--warn)}
.pg-prv b{font-size:14px;font-family:var(--mono)}
.pg-pr.on{border-bottom:0}
.pg-track,.pg-ticks{position:relative;display:block;height:24px}
.pg-track{background:linear-gradient(var(--rule),var(--rule)) center/100% 1px no-repeat}
.pg-track i{position:absolute;top:50%;font-style:normal}
.pg-track .goal{width:0;height:24px;margin-top:-12px;border-left:1px dashed var(--ink3)}
.pg-track .span{height:3px;margin-top:-1.5px;background:var(--ink3);border-radius:2px}
.pg-track .dot{width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;border:2px solid var(--solid);display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;font-family:var(--mono);color:#fff;background:var(--act)}
.pg-track .dot.y0{background:#7FB2DC;color:#0F3554} .pg-track .dot.y1{background:#3F86C4} .pg-track .dot.y2{background:#155A94} .pg-track .dot.y3{background:#0C3C66}
.pg-ticks{height:16px}
.pg-ticks i{position:absolute;top:0;transform:translateX(-50%);font-style:normal;font-size:11px;color:var(--ink3);font-family:var(--mono)}
.pg-verdict{font-size:12.5px;line-height:1.35;padding-left:10px;border-left:3px solid var(--rule)}
.pg-verdict.ok{border-color:var(--ok)} .pg-verdict.warn{border-color:var(--warn)} .pg-verdict.harm{border-color:var(--harm)}
@media (max-width:860px){.pg-two{grid-template-columns:1fr}.pg-pr,.pg-dr,.pg-axis{grid-template-columns:1fr;gap:4px}.pg-axis{display:none}}
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
          /* for the site check */ _state:()=>({uid, infoState, info, view:{open:view.open,tab:view.tab,scope:view.scope,state:view.state,first:view.first,test:inTest()}}),
          _test:()=>{ const t=testStore(); return {people:t.people.length, records:t.records.length, open:t.open.length}; }};
})();
