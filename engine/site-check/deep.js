const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined});
 const errs=[],csp=[]; const ok=(n,c,x)=>console.log((c?'ok   ':'FAIL ')+n+(c||x===undefined?'':'  -> '+JSON.stringify(x)));
 const hook=p=>{p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{const t=m.text(); if(/Content Security Policy|Refused to/.test(t)) csp.push(t.slice(0,160)); else if(m.type()==='error'&&!/ERR_TUNNEL|status of (400|401|403|429)/.test(t)) errs.push(t.slice(0,160));});};
 // 1. unconfigured site
 let p=await b.newPage({viewport:{width:1440,height:860}}); hook(p);
 await p.goto('http://localhost:8090/'); await p.waitForTimeout(1200);
 await p.click('.wl-case'); await p.waitForTimeout(300); await p.keyboard.press('Enter'); await p.waitForTimeout(300);
 const u=await p.evaluate(()=>({acct:document.getElementById('wl-acct').innerText, dlg:!document.getElementById('signinview').classList.contains('hidden'), picker:!document.getElementById('picker').classList.contains('hidden')}));
 ok('unconfigured site says so and stays on the list', /not configured/.test(u.acct)&&!u.dlg&&u.picker, u);
 await p.close();
 // 2. configured site, a fuller run of one case
 p=await b.newPage({viewport:{width:1440,height:860}}); hook(p);
 await p.goto('http://localhost:8080/'); await p.waitForTimeout(1500);
 const signed=await p.evaluate(()=>ACCESS_UI.signedIn());
 if(!signed){ await p.click('#acct-in'); await p.fill('#signinemail','res@example.com'); await p.fill('#signinpass','right-password'); await p.keyboard.press('Enter'); await p.waitForTimeout(1500); }
 const i=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='MGCA'));
 await p.evaluate(i=>chooseCase(i),i); await p.waitForTimeout(2500);
 ok('MGCA splash', await p.evaluate(()=>PACK.prefix==='MGCA'&&!document.getElementById('splash').classList.contains('hidden')));
 await p.click('#beginbtn'); await p.waitForTimeout(1500);
 // press a real button through the UI
 const ids=await p.evaluate(()=>{ const out=[]; for(const c of ['nasal_cannula_oxygen','insert_iv','attach_monitor']){ const id=(PACK.bindings||{})[c]||c; if(ACT[id]) out.push(id);} return out; });
 for(const id of ids){ await p.evaluate(id=>{searchGoTo(id); const btn=document.querySelector('.ab[data-act="'+id+'"]'); if(btn) btn.click(); const s=document.getElementById('submitorder'); if(s) s.click();},id); await p.waitForTimeout(400); }
 ok('actions taken through the UI', await p.evaluate(ids=>ids.every(id=>ST.taken.has(id)),ids), ids);
 // search and voice panels
 await p.keyboard.press('Control+k'); await p.waitForTimeout(300); await p.keyboard.type('lactate'); await p.waitForTimeout(300); await p.keyboard.press('Escape');
 await p.evaluate(()=>{ const v=document.getElementById('voicebtn'); if(v) v.click(); }); await p.waitForTimeout(400);
 await p.evaluate(()=>{ log({actionId:'early_exit',kind:'early_exit'}); finish(); }); await p.waitForTimeout(1200);
 ok('debrief opens', await p.evaluate(()=>ENDED===true));
 await p.screenshot({path:'/tmp/e2e/debrief.png'});
 ok('no errors in a full run', errs.length===0, errs);
 ok('no CSP violations in a full run', csp.length===0, csp);
 await b.close();
})();
