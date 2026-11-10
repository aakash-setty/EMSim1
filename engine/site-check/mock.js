// Mock of the Supabase endpoints the site and the edge function call. Functions are proxied
// to the real edge function running under Deno on :8001.
const http=require('http'), fs=require('fs'), crypto=require('crypto');
const STORE=new Map();
const PACKS=(process.env.PACKS_DIR||'private-packs').replace(/\/?$/,'/');
const S={rpc:'ok', tamper:false, userOk:true, unconfirmed:false, calls:{fn:0,rpc:0,storage:0,user:0,token:0}, log:[]};
const USER={id:'11111111-1111-1111-1111-111111111111',aud:'authenticated',role:'authenticated',email:'res@example.com',email_confirmed_at:new Date().toISOString(),is_anonymous:false,app_metadata:{},user_metadata:{},created_at:new Date().toISOString()};
// v0.18a: the edge function refuses an account whose email is not confirmed. __ctl {unconfirmed:true} serves one.
const userNow=()=>S.unconfirmed?Object.assign({},USER,{email_confirmed_at:null}):USER;
function body(req){return new Promise(r=>{let b=[];req.on('data',c=>b.push(c));req.on('end',()=>r(Buffer.concat(b)))});}
function cors(res,req){res.setHeader('Access-Control-Allow-Origin',req.headers.origin||'*');res.setHeader('Access-Control-Allow-Headers','authorization, apikey, content-type, x-client-info, x-supabase-api-version, prefer, accept, accept-profile, content-profile');res.setHeader('Access-Control-Allow-Methods','GET,POST,PATCH,DELETE,OPTIONS');}
// Saved progress (28 October 2026): public.runs as PostgREST serves it, with the rules of
// supabase/migrations/002_runs.sql that the browser relies on. One signed-in user (the
// 'good-token' bearer); anything else sees and changes nothing. __ctl {runsFail:true} makes
// every write fail; GET /__runs returns the table; POST /__runs {rows} replaces it.
let RUNS=[];
const RUN_COLS=['id','user_id','case_prefix','version_key','mode','status','state','sim_seconds','outcome','ended_by','score_pct','summary','started_at','updated_at','finished_at'];
function runsFilter(u){
  const f=[];
  for(const [k,v] of u.searchParams){ if(['select','order','limit','on_conflict','columns'].includes(k)) continue; const m=v.match(/^eq\.(.*)$/); if(m) f.push([k,m[1]]); }
  return r=>f.every(([k,v])=>String(r[k])===v);
}
function runsPick(rows,u){
  const sel=(u.searchParams.get('select')||'*').split(',');
  return rows.map(r=>sel[0]==='*'?r:Object.fromEntries(sel.map(c=>[c,r[c]])));
}
function runsShape(r){
  if(r.status==='finished'){ r.state=null; r.finished_at=r.finished_at||new Date().toISOString(); }
  else r.finished_at=null;
  r.updated_at=new Date().toISOString();
  return r;
}
async function runsRoute(req,res,u){
  S.calls.runs=(S.calls.runs||0)+1;
  const me=req.headers.authorization==='Bearer good-token'?USER.id:null;
  const send=(code,obj)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(obj===undefined?'':JSON.stringify(obj));};
  const single=/vnd\.pgrst\.object/.test(req.headers.accept||'');
  const ret=(rows)=>{
    const out=runsPick(rows,u);
    if(single){ if(out.length!==1) return send(406,{code:'PGRST116',message:'JSON object requested, multiple (or no) rows returned'}); return send(200,out[0]); }
    return send(200,out);
  };
  const wantRows=/return=representation/.test(req.headers.prefer||'');
  if(!me) return send(401,{code:'42501',message:'permission denied for table runs'});
  const mine=RUNS.filter(r=>r.user_id===me), match=runsFilter(u);
  if(req.method==='GET'){
    let rows=mine.filter(match).sort((a,b)=>b.updated_at.localeCompare(a.updated_at));
    const lim=Number(u.searchParams.get('limit'))||rows.length; return ret(rows.slice(0,lim));
  }
  if(S.runsFail) return send(500,{code:'XX000',message:'mock failure'});
  const b=req.method==='DELETE'?null:JSON.parse((await body(req)).toString()||'{}');
  if(req.method==='POST'){
    const list=Array.isArray(b)?b:[b], made=[];
    for(const x of list){
      if(x.user_id||x.id||x.started_at) return send(403,{code:'42501',message:'permission denied for table runs'});
      if(x.status!=='finished'&&mine.some(r=>r.status==='in_progress'&&r.case_prefix===x.case_prefix))
        return send(409,{code:'23505',message:'duplicate key value violates unique constraint "runs_one_open"'});
      const r=runsShape(Object.assign({id:crypto.randomUUID(),user_id:me,status:'in_progress',sim_seconds:0,outcome:null,ended_by:null,score_pct:null,summary:null,started_at:new Date().toISOString()},x));
      RUNS.push(r); made.push(r);
    }
    S.calls.runsInsert=(S.calls.runsInsert||0)+1;
    return wantRows?ret(made):send(201);
  }
  if(req.method==='PATCH'){
    const hit=mine.filter(match);
    for(const r of hit){
      if(r.status==='finished') return send(400,{code:'P0001',message:'a finished run cannot be changed'});
      for(const k of ['case_prefix','version_key','user_id','id','started_at']) if(k in b) return send(403,{code:'42501',message:'permission denied for table runs'});
    }
    hit.forEach(r=>{ Object.assign(r,b); runsShape(r); });
    S.calls.runsUpdate=(S.calls.runsUpdate||0)+1;
    return wantRows?ret(hit):send(204);
  }
  if(req.method==='DELETE'){
    // 004_programs.sql: a program member can discard a run in progress and nothing else.
    const hit=mine.filter(match).filter(r=>r.status==='in_progress'||!PG.member); RUNS=RUNS.filter(r=>!hit.includes(r));
    S.calls.runsDelete=(S.calls.runsDelete||0)+1;
    return wantRows?ret(hit):send(204);
  }
  send(405,{});
}
// Programs and analytics (10 November 2026): the functions of supabase/migrations/004_programs.sql
// that the browser calls, for the one signed-in user. The real rules are tested against a real
// Postgres by supabase/tests/programs-test.mjs. This is only enough for the pages to be driven.
// POST /__pg {reset:true} starts again; POST /__pg {staff:true} or {member:{...}} sets the account;
// GET /__pg returns the state, with every record_run and staff call that arrived.
const pgFresh=()=>({staff:false, member:null, records:[], calls:[],
  programs:[{id:'aaaaaaaa-0000-0000-0000-000000000001',name:'Mock EM',status:'active',join_code:'MCKCDE23',show_named_results:true,all_cases:true,seats:null,cases:[],created_at:new Date().toISOString()}]});
let PG=pgFresh();
function pgAnalytics(a){
  const prog=a.p_program?PG.programs.find(p=>p.id===a.p_program):null;
  const named=PG.staff||!prog||prog.show_named_results;
  const rec=PG.records.filter(r=>!a.p_program||r.program_id===a.p_program);
  const sel=rec.filter(r=>!a.p_first||r.attempt_no===1);
  const mixOf=l=>({n:l.length,met:l.filter(r=>r.result==='met').length,met_prompted:l.filter(r=>r.result==='met_prompted').length,not_met:l.filter(r=>r.result==='not_met').length,
    harmful:l.filter(r=>r.why.includes('harmful_action')).length,lost:l.filter(r=>r.why.includes('case_lost')).length});
  const by=(l,f)=>{ const m=new Map(); l.forEach(x=>{ const k=f(x); if(!m.has(k)) m.set(k,[]); m.get(k).push(x); }); return [...m.values()]; };
  const its=sel.flatMap(r=>r.items.map(i=>Object.assign({case_prefix:r.case_prefix},i)));
  const me=PG.member;
  return {generated_at:new Date().toISOString(), first_only:!!a.p_first, days:a.p_days, named, staff:PG.staff,
    program:prog?Object.assign({},prog):null,
    totals:{people:me?1:0,residents:me&&me.role!=='admin'?1:0,active_30d:rec.length?1:0,with_a_finished_run:rec.length?1:0,runs:rec.length,first_attempts:rec.filter(r=>r.attempt_no===1).length,open_runs:RUNS.filter(r=>r.status==='in_progress').length},
    members:me?[{user_id:USER.id,name:me.display_name,pgy:me.pgy,role:me.role,joined_at:new Date().toISOString(),cases_finished:new Set(rec.map(r=>r.case_prefix)).size,runs:rec.length,
      open:RUNS.filter(r=>r.status==='in_progress').length,case_minutes:0,last_finished:rec.length?new Date().toISOString():null,cases:[...new Set(rec.map(r=>r.case_prefix))],results:named?mixOf(sel):null}]:[],
    cases:by(sel,r=>r.case_prefix).map(l=>Object.assign({case_prefix:l[0].case_prefix,learners:1,median_seconds:60,open:0},mixOf(l))),
    items:by(its.filter(i=>i.k==='critical'||i.k==='recommended'),i=>i.case_prefix+'|'+i.k+'|'+i.id).map(l=>({case_prefix:l[0].case_prefix,kind:l[0].k,item_id:l[0].id,tab:l[0].tab,cat:l[0].cat,grp:l[0].grp,
      n:l.length,done:l.filter(i=>i.r==='done').length,prompted:l.filter(i=>i.r==='done'&&i.p).length,learners_missed:l.some(i=>i.r==='missed')?1:0,median_delay:null})),
    safety:by(its.filter(i=>i.k==='discouraged'||i.k==='harmful'),i=>i.case_prefix+'|'+i.k+'|'+i.id).map(l=>({case_prefix:l[0].case_prefix,kind:l[0].k,item_id:l[0].id,tab:l[0].tab,cat:l[0].cat,grp:l[0].grp,runs:l.length,learners:1})),
    handoff:by(its.filter(i=>i.k==='diagnosis'||i.k==='disposition'),i=>i.case_prefix+'|'+i.k+'|'+i.id+'|'+i.r).map(l=>({case_prefix:l[0].case_prefix,kind:l[0].k,item_id:l[0].id,result:l[0].r,n:l.length})),
    months:sel.length?[Object.assign({month:new Date().toISOString().slice(0,7)},mixOf(sel))]:[],
    years:by(sel,r=>String(r.pgy)).map(l=>Object.assign({pgy:l[0].pgy,learners:1},mixOf(l)))};
}
const pgDenied={code:'42501',message:'not allowed'};
const PG_FNS={
  my_program:()=>({staff:PG.staff,enforce:false,free_cases:[],member:PG.member}),
  join_program:a=>{
    if(PG.member) return 'already_member';
    const g=PG.programs.find(p=>p.join_code===String(a.p_code||'').replace(/[^A-Za-z0-9]/g,'').toUpperCase());
    if(!g) return 'bad_code';
    PG.member={program_id:g.id,program:g.name,status:g.status,role:'resident',display_name:String(a.p_name||'').trim(),pgy:a.p_pgy,show_named_results:g.show_named_results,all_cases:g.all_cases,cases:[],join_code:null};
    return 'ok'; },
  record_run:a=>{
    const run=RUNS.find(r=>r.id===a.p_run&&r.user_id===USER.id&&r.status==='finished');
    if(!run) return 'no_run';
    if(PG.records.some(r=>r.run_id===a.p_run)) return 'exists';
    const rec=a.p_record;
    if(!rec||!Array.isArray(rec.items)||!['met','met_prompted','not_met'].includes(rec.result)) return 'bad_record';
    if(rec.result!=='not_met'&&run.outcome!=='all') return 'mismatch';
    PG.records.push({run_id:a.p_run,case_prefix:run.case_prefix,program_id:PG.member?PG.member.program_id:null,pgy:PG.member?PG.member.pgy:null,
      attempt_no:1+PG.records.filter(r=>r.case_prefix===run.case_prefix).length,result:rec.result,why:rec.why||[],items:rec.items,phases:rec.phases,trail:a.p_trail});
    return 'ok'; },
  program_analytics:a=>{
    const admin=PG.member&&PG.member.role==='admin'&&a.p_program===PG.member.program_id;
    if(!PG.staff&&!admin) return {__error:pgDenied};
    return pgAnalytics(a); },
  staff_overview:()=>PG.staff?{settings:{enforce_entitlements:false,free_cases:[]},accounts:1,individuals:PG.member?0:1,records:PG.records.length,
    programs:PG.programs.map(p=>Object.assign({residents:PG.member&&PG.member.role==='resident'?1:0,admins:PG.member&&PG.member.role==='admin'?1:0,runs:PG.records.filter(r=>r.program_id===p.id).length,last_finished:null},p))}:{__error:pgDenied},
  staff_save_program:a=>{
    if(!PG.staff) return {__error:pgDenied};
    let g=PG.programs.find(p=>p.id===a.p_id);
    if(!g){ g={id:crypto.randomUUID(),name:a.p_name,status:'active',join_code:'NEWCDE'+String(PG.programs.length+22).slice(-2),show_named_results:true,all_cases:true,seats:a.p_seats||null,cases:[],created_at:new Date().toISOString()}; PG.programs.push(g); }
    if(typeof a.p_named==='boolean') g.show_named_results=a.p_named;
    if(typeof a.p_all_cases==='boolean') g.all_cases=a.p_all_cases;
    if(Array.isArray(a.p_cases)) g.cases=a.p_cases;
    if(a.p_status) g.status=a.p_status;
    return g.id; },
  staff_new_code:()=>PG.staff?'FRESHCD2':{__error:pgDenied},
  program_set_member:a=>{ if(a.p_role==='remove') PG.member=null; else if(PG.member) PG.member.role=a.p_role; return 'ok'; },
  staff_set_settings:()=>PG.staff?null:{__error:pgDenied},
};
async function pgRoute(req,res,fn){
  const send=(code,obj)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(obj===undefined?null:obj));};
  if(req.headers.authorization!=='Bearer good-token') return send(401,{code:'42501',message:'sign in first'});
  const a=JSON.parse((await body(req)).toString()||'{}');
  if(fn!=='my_program'&&fn!=='program_analytics'&&fn!=='staff_overview') PG.calls.push({fn,args:fn==='record_run'?{p_run:a.p_run}:a});
  if(PG.fail) return send(500,{code:'XX000',message:'mock failure'});
  const out=PG_FNS[fn](a);
  if(out&&out.__error) return send(403,out.__error);
  send(200,out);
}
http.createServer(async (req,res)=>{
  const u=new URL(req.url,'http://x'); S.log.push(req.method+' '+u.pathname);
  if(u.pathname==='/__ctl'){ const b=JSON.parse((await body(req)).toString()||'{}'); Object.assign(S,b); res.end(JSON.stringify(S)); return; }
  if(u.pathname==='/__runs'){ if(req.method==='POST'){ const b=JSON.parse((await body(req)).toString()||'{}'); RUNS=b.rows||[]; } res.end(JSON.stringify(RUNS)); return; }
  if(u.pathname.startsWith('/functions/v1/')){
    if(req.method==='POST') S.calls.fn++;
    const b=await body(req);
    const h={...req.headers}; delete h.host; delete h['content-length'];
    const r=await fetch('http://127.0.0.1:8000'+u.pathname.replace('/functions/v1',''),{method:req.method,headers:h,body:req.method==='POST'?b:undefined});
    const out=Buffer.from(await r.arrayBuffer());
    const hh={}; r.headers.forEach((v,k)=>{ if(k!=='content-length'&&k!=='content-encoding'&&k!=='transfer-encoding') hh[k]=v; });
    res.writeHead(r.status,hh); res.end(out); return;
  }
  cors(res,req);
  if(req.method==='OPTIONS'){res.writeHead(204);res.end();return;}
  if(u.pathname==='/auth/v1/token'){
    S.calls.token++;
    const b=JSON.parse((await body(req)).toString()||'{}');
    if(u.searchParams.get('grant_type')==='password'){
      if(b.email!=='res@example.com'||b.password!=='right-password'){res.writeHead(400,{'Content-Type':'application/json'});res.end(JSON.stringify({code:400,error_code:'invalid_credentials',msg:'Invalid login credentials'}));return;}
    }
    const now=Math.floor(Date.now()/1000);
    res.writeHead(200,{'Content-Type':'application/json'});
    res.end(JSON.stringify({access_token:'good-token',token_type:'bearer',expires_in:3600,expires_at:now+3600,refresh_token:'r1',user:USER}));return;
  }
  // v0.18h. Google sign-in: the authorize endpoint sends the browser straight back with a
  // code (or, with __ctl {oauthDenied:true}, with the error Supabase gives an uninvited account).
  if(u.pathname==='/auth/v1/authorize'){
    S.calls.authorize=(S.calls.authorize||0)+1; S.lastAuthorize=Object.fromEntries(u.searchParams);
    const back=new URL(u.searchParams.get('redirect_to'));
    if(S.oauthDenied){ back.searchParams.set('error','access_denied'); back.searchParams.set('error_code','signup_disabled'); back.searchParams.set('error_description','Signups not allowed for this instance'); }
    else back.searchParams.set('code','test-auth-code');
    res.writeHead(302,{Location:back.toString()}); res.end(); return;
  }
  if(u.pathname==='/auth/v1/logout'){res.writeHead(204);res.end();return;}
  if(u.pathname==='/auth/v1/user'){
    S.calls.user++;
    const ok=S.userOk&&req.headers.authorization==='Bearer good-token'&&req.headers.apikey==='svc';
    res.writeHead(ok?200:401,{'Content-Type':'application/json'}); res.end(JSON.stringify(ok?userNow():{code:401,msg:'invalid JWT'})); return;
  }
  if(u.pathname==='/rest/v1/rpc/claim_case_load'){
    S.calls.rpc++; const b=JSON.parse((await body(req)).toString());
    S.lastRpc={body:b,auth:req.headers.authorization,apikey:req.headers.apikey};
    res.writeHead(200,{'Content-Type':'application/json'}); res.end(JSON.stringify(S.rpc)); return;
  }
  if(u.pathname==='/__pg'){ if(req.method==='POST'){ const b=JSON.parse((await body(req)).toString()||'{}'); if(b.reset) PG=pgFresh(); else Object.assign(PG,b); } res.end(JSON.stringify(PG)); return; }
  if(u.pathname.startsWith('/rest/v1/rpc/')&&PG_FNS[u.pathname.slice(13)]) return pgRoute(req,res,u.pathname.slice(13));
  if(u.pathname==='/rest/v1/runs') return runsRoute(req,res,u);
  if(u.pathname.startsWith('/storage/v1/object/')){
    // Packs live at case-packs/<PREFIX>/<sha256>.json. Uploads (from publish_packs.js) go to an
    // in-memory store and record the auth headers. Downloads read the store, then, unless
    // __ctl {storeOnly:true}, fall back to private-packs/<PREFIX>.json when its hash matches.
    S.calls.storage++; S.lastStorage=u.pathname;
    const key=decodeURIComponent(u.pathname.replace(/^\/storage\/v1\/object\/(authenticated\/)?/,''));
    if(req.method==='POST'||req.method==='PUT'){
      const b=await body(req); S.uploads=(S.uploads||[]);
      S.uploads.push({key,bytes:b.length,apikey:req.headers.apikey||null,auth:req.headers.authorization||null,upsert:req.headers['x-upsert']||null,type:req.headers['content-type']||null});
      if(!(req.headers.apikey==='sb_secret_test')){res.writeHead(403,{'Content-Type':'application/json'});res.end(JSON.stringify({statusCode:'403',error:'Unauthorized',message:'bad key'}));return;}
      STORE.set(key,b); res.writeHead(200,{'Content-Type':'application/json'}); res.end(JSON.stringify({Key:key})); return;
    }
    const nf=()=>{res.writeHead(400,{'Content-Type':'application/json'});res.end(JSON.stringify({statusCode:'404',error:'not_found',message:'Object not found'}));};
    let data=STORE.get(key);
    if(!data&&!S.storeOnly){
      const m=key.match(/^case-packs\/([A-Z0-9]+)\/([0-9a-f]{64})\.json$/);
      const f=m&&PACKS+m[1]+'.json';
      if(f&&fs.existsSync(f)){ const d=fs.readFileSync(f); if(crypto.createHash('sha256').update(d).digest('hex')===m[2]) data=d; }
    }
    if(!data) return nf();
    if(S.tamper) data=Buffer.concat([data,Buffer.from(' ')]);
    res.writeHead(200,{'Content-Type':'application/json'}); res.end(data); return;
  }
  res.writeHead(404); res.end('no mock for '+u.pathname);
}).listen(54321,()=>console.log('mock on 54321'));
