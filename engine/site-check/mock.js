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
    const hit=mine.filter(match); RUNS=RUNS.filter(r=>!hit.includes(r));
    S.calls.runsDelete=(S.calls.runsDelete||0)+1;
    return wantRows?ret(hit):send(204);
  }
  send(405,{});
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
