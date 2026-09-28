// v0.18h. Google sign-in against the mock: the round trip, the pending case, and the refusal
// of an account that was not invited.
const {chromium}=require('playwright');
const ctl=b=>fetch('http://localhost:54321/__ctl',{method:'POST',body:JSON.stringify(b)}).then(r=>r.json());
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined});
 const ok=(n,c,x)=>console.log((c?'ok   ':'FAIL ')+n+(c||x===undefined?'':'  -> '+JSON.stringify(x)));
 const errs=[]; const hook=p=>{p.on('pageerror',e=>errs.push(e.message)); p.on('console',m=>{ if(/Content Security Policy|Refused to/.test(m.text())) errs.push(m.text().slice(0,160)); });};
 // 1. an invited account: back from Google, signed in, and the case that was clicked opens
 await ctl({oauthDenied:false});
 let ctx=await b.newContext({viewport:{width:1440,height:860}}); let p=await ctx.newPage(); hook(p);
 await p.goto('http://localhost:8080/'); await p.waitForTimeout(1200);
 const i=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='MGCA'));
 await p.evaluate(i=>ACCESS_UI.open(i),i); await p.waitForTimeout(400);
 ok('dialog offers Google', await p.evaluate(()=>!document.getElementById('signingoogle').hidden));
 await Promise.all([p.waitForURL(/localhost:8080\/(\?|$)/,{timeout:8000}).catch(()=>{}), p.click('#signingoogle')]);
 await p.waitForTimeout(2500);
 const s1=await p.evaluate(()=>({url:location.href, signed:ACCESS_UI.signedIn(), prefix:(typeof PACK==='object'&&PACK)?PACK.prefix:null, splash:!document.getElementById('splash').classList.contains('hidden')}));
 const st=await ctl({});
 ok('the request asks Google with PKCE and comes back here', st.lastAuthorize&&st.lastAuthorize.provider==='google'&&!!st.lastAuthorize.code_challenge&&/localhost:8080/.test(st.lastAuthorize.redirect_to||''), st.lastAuthorize);
 ok('signed in after the round trip', s1.signed, s1);
 ok('the code is removed from the address bar', !/code=/.test(s1.url), s1.url);
 ok('the case clicked before leaving opens on return', s1.prefix==='MGCA'&&s1.splash, s1);
 await ctx.close();
 // 2. an account that was not invited
 await ctl({oauthDenied:true});
 ctx=await b.newContext({viewport:{width:1440,height:860}}); p=await ctx.newPage(); hook(p);
 await p.goto('http://localhost:8080/'); await p.waitForTimeout(1200);
 await p.click('#acct-in'); await p.waitForTimeout(300);
 await Promise.all([p.waitForURL(/error=/,{timeout:8000}).catch(()=>{}), p.click('#signingoogle')]);
 await p.waitForTimeout(2000);
 const s2=await p.evaluate(()=>({url:location.href, signed:ACCESS_UI.signedIn(), acct:document.getElementById('wl-acct').innerText}));
 ok('an uninvited Google account is refused with a clear message', !s2.signed&&/not on the invite list/.test(s2.acct), s2);
 ok('the error is removed from the address bar', !/error=/.test(s2.url), s2.url);
 await ctl({oauthDenied:false});
 ok('no page errors or CSP reports in the Google flow', errs.length===0, errs);
 await b.close();
})();
