// Serves a site directory with the headers from vercel.json, plus one extra connect-src for the mock.
const http=require('http'),fs=require('fs'),path=require('path');
const [dir,port,conf,extra]=process.argv.slice(2);
const hdrs=JSON.parse(fs.readFileSync(conf)).headers[0].headers;
http.createServer((req,res)=>{
  let p=decodeURIComponent(new URL(req.url,'http://x').pathname); if(p==='/') p='/index.html';
  const f=path.join(dir,p); if(!f.startsWith(dir)||!fs.existsSync(f)){res.writeHead(404);res.end();return;}
  for(const h of hdrs){ let v=h.value; if(h.key==='Content-Security-Policy'&&extra) v=v.replace("connect-src 'self'","connect-src 'self' "+extra); if(h.key!=='Strict-Transport-Security') res.setHeader(h.key,v); }
  res.setHeader('Content-Type',f.endsWith('.html')?'text/html; charset=utf-8':'application/octet-stream');
  fs.createReadStream(f).pipe(res);
}).listen(Number(port),()=>console.log('site on',port));
