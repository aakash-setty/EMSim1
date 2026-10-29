const {chromium}=require('playwright');
const ctl=b=>fetch('http://localhost:54321/__ctl',{method:'POST',body:JSON.stringify(b)}).then(r=>r.json());
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined});
 const ctx=await b.newContext({viewport:{width:1440,height:860}});
 const p=await ctx.newPage(); const errs=[], csp=[];
 p.on('pageerror',e=>errs.push('pageerror: '+e.message));
 p.on('console',m=>{ const t=m.text(); if(/Content Security Policy|Refused to/.test(t)) csp.push(t.slice(0,200)); else if(m.type()==='error' && !/ERR_TUNNEL|status of (400|401|403|429)/.test(t)) errs.push('console: '+t.slice(0,200)); });
 const ok=(n,c,x)=>console.log((c?'ok   ':'FAIL ')+n+(c||x===undefined?'':'  -> '+JSON.stringify(x)));
 // Since 11 October 2026 a downloaded case waits behind the charging defibrillator (CHARGE in
 // ui.js) until the learner presses its button. This presses it once it is armed.
 const shock=async()=>{ for(let k=0;k<20;k++){ if(await p.evaluate(()=>{ const d=document.getElementById('chargedeliver'); return !!d&&!d.disabled&&!document.getElementById('chargeview').classList.contains('hidden'); })){ await p.click('#chargedeliver'); await p.waitForTimeout(500); return; } await p.waitForTimeout(150); } };
 const FN_BEFORE=(await ctl({})).calls.fn; await p.goto('http://localhost:8080/'); await p.waitForTimeout(1500);
 const s0=await p.evaluate(()=>({rows:document.querySelectorAll('.wl-case').length, locks:document.querySelectorAll('.wl-case .wl-lock').length,
   acct:document.getElementById('wl-acct').innerText, legal:document.getElementById('pk-legal').innerText, h1:document.querySelector('.wl-text h1').innerText,
   title:document.title, CASE:typeof CASE!=='undefined'&&CASE!==null, locked:CASES.filter(c=>c.locked).length, n:CASES.length}));
 console.log(JSON.stringify(s0));
 const N=s0.n; ok('one row and one lock per case, nothing bound', N>0&&s0.rows===N&&s0.locks===N&&!s0.CASE&&s0.locked===N, s0);
 ok('sign-in line and button on the list', /Sign in to open a case/.test(s0.acct)&&/Sign in/.test(s0.acct));
 const L0=await p.evaluate(()=>({shown:LANDING.visible(), tiles:document.querySelectorAll('.ld-case').length,
   top:(document.elementFromPoint(720,400)||{}).closest?!!document.elementFromPoint(720,400).closest('#landing'):false,
   imgs:[...document.querySelectorAll('#landing .ld-shot img')].map(i=>i.naturalWidth)}));
 ok('signed out: the welcome page covers the list', L0.shown&&L0.top&&L0.tiles===N, L0);
 ok('welcome page screenshots load', L0.imgs.length===3&&L0.imgs.every(w=>w>0), L0.imgs);
 // Credits and licenses (29 October 2026), from the welcome page's footer.
 await p.click('.ld-foot [data-credits]'); await p.waitForTimeout(300);
 const cr=await p.evaluate(()=>{ const v=document.getElementById('creditsview');
   return {open:!v.hidden, items:v.querySelectorAll('.crd-item').length, texts:[...v.querySelectorAll('.crd-full pre')].map(x=>x.textContent.length),
     ofl:/SIL OPEN FONT LICENSE/i.test(v.textContent), mit:/Pablo Stanley/.test(v.textContent), focus:document.activeElement&&document.activeElement.classList.contains('crd-x')}; });
 ok('the welcome page opens the credits, every licence with its text', cr.open&&cr.items>=8&&cr.texts.length>=6&&cr.texts.every(n=>n>200)&&cr.ofl&&cr.mit&&cr.focus, cr);
 await p.keyboard.press('Escape'); await p.waitForTimeout(150);
 ok('Escape closes the credits', await p.evaluate(()=>document.getElementById('creditsview').hidden));
 await p.click('[data-ldact="sit"]'); await p.waitForTimeout(1300);
 ok('the demo takes an action', await p.evaluate(()=>document.querySelector('[data-ldact="sit"]').classList.contains('done')));
 // The demo's twelve-lead (28 October 2026): Get an ECG prints it over about half the screen and
 // asks where the STEMI is. A wrong answer says why, Escape closes it, it opens again, and
 // High-lateral ends the demo on its Good call card.
 await p.waitForTimeout(2400); await p.click('[data-ldact="ecg"]'); await p.waitForTimeout(3400);
 const e0=await p.evaluate(()=>{ const w=document.getElementById('ld-ecgwrap'), s=w.querySelector('.ld-ecgsheet').getBoundingClientRect();
   return {on:!w.hidden&&w.classList.contains('on'), traces:w.querySelectorAll('svg .trace').length, frac:+(s.height/innerHeight).toFixed(2),
     opts:[...w.querySelectorAll('[data-ldecg]')].map(b=>b.textContent.trim()), monitor:document.querySelector('.ld-lead span').textContent}; });
 ok('Get an ECG opens the 12-lead over about half the screen, three answers, lead I on the monitor',
   e0.on&&e0.traces===13&&e0.frac>0.4&&e0.frac<0.75&&e0.opts.join()==='Anterior,Inferior,High-lateral'&&e0.monitor==='I', e0);
 await p.click('[data-ldecg="anterior"]'); await p.waitForTimeout(300);
 ok('a wrong answer says why and the sheet stays open', await p.evaluate(()=>{ const w=document.getElementById('ld-ecgwrap');
   return w.classList.contains('on')&&/Not anterior/.test(document.getElementById('ld-ecgfb').textContent)&&w.querySelector('[data-ldecg="anterior"]').disabled; }));
 await p.keyboard.press('Escape'); await p.waitForTimeout(700);
 ok('Escape closes the sheet and the demo offers it again', await p.evaluate(()=>document.getElementById('ld-ecgwrap').hidden&&!!document.querySelector('#ld-actions [data-ldact="ecgopen"]')));
 await p.click('[data-ldact="ecgopen"]'); await p.waitForTimeout(2900);
 await p.click('[data-ldecg="highlat"]'); await p.waitForTimeout(3700);
 const e1=await p.evaluate(()=>({closed:document.getElementById('ld-ecgwrap').hidden, over:!document.getElementById('ld-over').hidden,
   title:document.getElementById('ld-overtitle').textContent, scroll:getComputedStyle(document.getElementById('landing')).overflowY}));
 ok('High-lateral is right: the sheet closes, the page scrolls again, the demo ends on Good call', e1.closed&&e1.over&&/High-lateral/.test(e1.title)&&e1.scroll==='auto', e1);
 ok('no review tools (speed control) in the site', await p.evaluate(()=>typeof REVIEW_SPEED==='undefined'&&!document.getElementById('reviewspeed')));
 ok('legal line and product name', /2026 Aakash Setty/.test(s0.legal)&&/EMSim/.test(s0.h1)&&s0.title==='EMSim');
 // the page must sit on the list without errors (setInterval guard)
 await p.waitForTimeout(1200);
 ok('no errors idling on the list', errs.length===0, errs);
 // keyboard on the list with nothing bound
 await p.keyboard.press('/'); await p.keyboard.type('chest'); await p.keyboard.press('Escape'); await p.keyboard.press('ArrowDown'); await p.waitForTimeout(200);
 ok('list keys stay off under the welcome page', errs.length===0&&await p.evaluate(()=>document.activeElement.id!=='wl-q'&&document.getElementById('wl-q').value===''), errs);
 // click a locked case: dialog
 const idx=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='CHFE'));
 await p.click('.ld-case[data-ldcase="'+idx+'"]'); await p.waitForTimeout(300);
 const d0=await p.evaluate(()=>({open:!document.getElementById('signinview').classList.contains('hidden'), title:document.getElementById('signintitle').innerText,
   google:!document.getElementById('signingoogle').hidden, pw:!document.getElementById('signinpass').hidden}));
 ok('a case tile on the welcome page opens sign-up, Google only', d0.open&&/Create your free account/.test(d0.title)&&d0.google&&!d0.pw, d0);
 await p.click('#signinswitch [data-signmode="signin"]'); await p.waitForTimeout(200);
 const dlg=await p.evaluate(()=>!document.getElementById('signinview').classList.contains('hidden')&&/Log in/.test(document.getElementById('signintitle').innerText)&&!document.getElementById('signinpass').hidden);
 ok('switching to log in shows the password form', dlg);
 // typing "/" and Enter inside the dialog must not reach the list
 await p.fill('#signinemail',''); await p.click('#signinemail'); await p.keyboard.type('res@example.com');
 await p.click('#signinpass'); await p.keyboard.type('wrong/pass'); 
 ok('slash typed into the password, not the search', await p.evaluate(()=>document.getElementById('signinpass').value==='wrong/pass' && document.activeElement.id==='signinpass'));
 await p.keyboard.press('Enter'); await p.waitForTimeout(800);
 const err1=await p.evaluate(()=>document.getElementById('signinerr').innerText);
 ok('wrong password is refused with a message', /do not match/.test(err1), err1);
 ok('still on the list, dialog open', await p.evaluate(()=>!document.getElementById('picker').classList.contains('hidden')&&!document.getElementById('signinview').classList.contains('hidden')));
 await p.fill('#signinpass','right-password'); await p.keyboard.press('Enter'); await p.waitForTimeout(2500);
 const s1=await p.evaluate(()=>({dlg:!document.getElementById('signinview').classList.contains('hidden'), splash:!document.getElementById('splash').classList.contains('hidden'),
   prefix:PACK&&PACK.prefix, locked:CASES.filter(c=>c.locked).length}));
 console.log(JSON.stringify(s1));
 ok('after sign-in the pending case loads and its splash opens', !s1.dlg&&s1.splash&&s1.prefix==='CHFE'&&s1.locked===N-1);
 ok('signed in: the welcome page is gone', await p.evaluate(()=>!LANDING.visible()));
 await shock();
 let c=await ctl({}); const fn1=c.calls.fn;
 ok('one function call for one case', fn1===FN_BEFORE+1, c.calls);
 // The nurse's opening card holds the clock for about 4.4 s (13 October 2026).
 await p.evaluate(()=>begin()); await p.waitForTimeout(6000);
 ok('the case runs', await p.evaluate(()=>STARTED&&ST&&ST.now>0.5));
 await p.screenshot({path:'/tmp/e2e/running.png'});
 // leave to the list and reopen: no second download
 await p.evaluate(()=>{ ENDED=true; }); await p.evaluate(()=>backToPicker()); await p.waitForTimeout(400);
 const s2=await p.evaluate(()=>({locks:document.querySelectorAll('.wl-case .wl-lock').length, acct:document.getElementById('wl-acct').innerText}));
 ok('signed in: no locks on the list, account shown', s2.locks===0&&/res@example.com/.test(s2.acct), s2);
 await p.evaluate(i=>{ ENDED=false; chooseCase(i); },idx); await p.waitForTimeout(600);
 c=await ctl({}); ok('reopening a loaded case does not download it again', c.calls.fn===fn1, c.calls);
 await p.evaluate(()=>backToPicker()); await p.waitForTimeout(300);
 // tampered pack
 await ctl({tamper:true});
 const di=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='DIPH'));
 await p.evaluate(i=>chooseCase(i),di); await p.waitForTimeout(2500);
 let m=await p.evaluate(()=>document.querySelector('#wl-acct .msg').innerText);
 ok('a pack that fails the hash check is refused', /being updated/.test(m)&&await p.evaluate(()=>CASES.find(c=>c.prefix==='DIPH').locked), m);
 ok('still on the list', await p.evaluate(()=>!document.getElementById('picker').classList.contains('hidden')));
 await ctl({tamper:false, rpc:'rate_limited'});
 await p.evaluate(i=>chooseCase(i),di); await p.waitForTimeout(1500);
 m=await p.evaluate(()=>document.querySelector('#wl-acct .msg').innerText);
 ok('rate limit message', /short time/.test(m), m);
 await ctl({rpc:'suspended'});
 await p.evaluate(i=>chooseCase(i),di); await p.waitForTimeout(1500);
 m=await p.evaluate(()=>document.querySelector('#wl-acct .msg').innerText);
 ok('suspended message', /does not have access/.test(m), m);
 await ctl({rpc:'ok', unconfirmed:true});
 await p.evaluate(i=>chooseCase(i),di); await p.waitForTimeout(1500);
 m=await p.evaluate(()=>document.querySelector('#wl-acct .msg').innerText);
 ok('an account whose email is not confirmed is refused', /does not have access/.test(m), m);
 await ctl({unconfirmed:false, userOk:false});
 await p.evaluate(i=>chooseCase(i),di); await p.waitForTimeout(1500);
 ok('a token the server rejects asks to sign in again', await p.evaluate(()=>!document.getElementById('signinview').classList.contains('hidden')));
 await p.keyboard.press('Escape'); await p.waitForTimeout(200);
 ok('Escape closes the dialog', await p.evaluate(()=>document.getElementById('signinview').classList.contains('hidden')));
 await ctl({userOk:true});
 // session survives a reload (persisted by supabase-js)
 await p.reload(); await p.waitForTimeout(1500);
 const s3=await p.evaluate(()=>({acct:document.getElementById('wl-acct').innerText, locked:CASES.filter(c=>c.locked).length}));
 ok('reload: session kept, packs dropped', /res@example/.test(s3.acct)&&s3.locked===N, s3);
 await p.evaluate(i=>chooseCase(i),di); await p.waitForTimeout(3000);
 ok('a large pack with images (DIPH) loads and opens', await p.evaluate(()=>PACK&&PACK.prefix==='DIPH'&&Object.keys(PACK.media||{}).length>0&&!document.getElementById('splash').classList.contains('hidden')));
 await shock();
 await p.evaluate(()=>backToPicker()); await p.waitForTimeout(300);
 await p.click('#acct-out'); await p.waitForTimeout(2000);
 const s4=await p.evaluate(()=>({acct:document.getElementById('wl-acct').innerText, locked:CASES.filter(c=>c.locked).length, ls:Object.keys(localStorage).filter(k=>/sb-|supabase/.test(k)).map(k=>k+':'+String(localStorage.getItem(k)).length)}));
 ok('sign out: reloaded, locked, session gone', /Sign in to open a case/.test(s4.acct)&&s4.locked===N, s4);
 ok('signed out again: the welcome page is back', await p.evaluate(()=>LANDING.visible()));
 await p.screenshot({path:'/tmp/e2e/list.png'});
 ok('no page errors anywhere', errs.length===0, errs);
 ok('no CSP violations', csp.length===0, csp);
 await b.close();
})();
