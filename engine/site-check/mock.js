// Mock of the Supabase endpoints the site and the edge function call. Functions are proxied
// to the real edge function running under Deno on :8001.
const http=require('http'), fs=require('fs');
const PACKS=(process.env.PACKS_DIR||'private-packs').replace(/\/?$/,'/');
const S={rpc:'ok', tamper:false, userOk:true, unconfirmed:false, calls:{fn:0,rpc:0,storage:0,user:0,token:0}, log:[]};
const USER={id:'11111111-1111-1111-1111-111111111111',aud:'authenticated',role:'authenticated',email:'res@example.com',email_confirmed_at:new Date().toISOString(),is_anonymous:false,app_metadata:{},user_metadata:{},created_at:new Date().toISOString()};
// v0.18a: the edge function refuses an account whose email is not confirmed. __ctl {unconfirmed:true} serves one.
const userNow=()=>S.unconfirmed?Object.assign({},USER,{email_confirmed_at:null}):USER;
function body(req){return new Promise(r=>{let b=[];req.on('data',c=>b.push(c));req.on('end',()=>r(Buffer.concat(b)))});}
function cors(res,req){res.setHeader('Access-Control-Allow-Origin',req.headers.origin||'*');res.setHeader('Access-Control-Allow-Headers','authorization, apikey, content-type, x-client-info, x-supabase-api-version');res.setHeader('Access-Control-Allow-Methods','GET,POST,OPTIONS');}
http.createServer(async (req,res)=>{
  const u=new URL(req.url,'http://x'); S.log.push(req.method+' '+u.pathname);
  if(u.pathname==='/__ctl'){ const b=JSON.parse((await body(req)).toString()||'{}'); Object.assign(S,b); res.end(JSON.stringify(S)); return; }
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
  if(u.pathname.startsWith('/storage/v1/object/')){
    S.calls.storage++; S.lastStorage=u.pathname;
    const name=u.pathname.split('/').pop();
    const f=PACKS+name;
    if(!/^[A-Z0-9]+\.json$/.test(name)||!fs.existsSync(f)){res.writeHead(400,{'Content-Type':'application/json'});res.end(JSON.stringify({statusCode:'404',error:'not_found',message:'Object not found'}));return;}
    let data=fs.readFileSync(f); if(S.tamper) data=Buffer.concat([data,Buffer.from(' ')]);
    res.writeHead(200,{'Content-Type':'application/json'}); res.end(data); return;
  }
  res.writeHead(404); res.end('no mock for '+u.pathname);
}).listen(54321,()=>console.log('mock on 54321'));
