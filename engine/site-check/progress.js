// Saved progress (28 October 2026), end to end against the mock's public.runs: autosave, leave
// and resume, the resumed run matching the one left, finishing into a score summary, the
// home panel, delete, Start over, the case-has-changed notice, a reload, and the local build.
const {chromium}=require('playwright');
const M='http://localhost:54321';
const ctl=b=>fetch(M+'/__ctl',{method:'POST',body:JSON.stringify(b)}).then(r=>r.json());
const table=()=>fetch(M+'/__runs').then(r=>r.json());
const setTable=rows=>fetch(M+'/__runs',{method:'POST',body:JSON.stringify({rows})}).then(r=>r.json());
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROME||undefined});
 const ctx=await b.newContext({viewport:{width:1440,height:860}});
 const p=await ctx.newPage(); const errs=[], csp=[], dialogs=[];
 p.on('pageerror',e=>errs.push('pageerror: '+e.message));
 p.on('dialog',d=>{ dialogs.push(d.type()); d.accept().catch(()=>{}); });
 p.on('console',m=>{ const t=m.text(); if(/Content Security Policy|Refused to/.test(t)) csp.push(t.slice(0,200)); else if(m.type()==='error' && !/ERR_TUNNEL|status of (400|401|403|406|409|429|500)/.test(t)) errs.push('console: '+t.slice(0,200)); });
 const ok=(n,c,x)=>console.log((c?'ok   ':'FAIL ')+'progress: '+n+(c||x===undefined?'':'  -> '+JSON.stringify(x).slice(0,400)));
 const wait=ms=>p.waitForTimeout(ms);
 // A downloaded case waits behind the charging defibrillator until its button is pressed.
 const shock=async()=>{ for(let k=0;k<20;k++){ if(await p.evaluate(()=>{ const d=document.getElementById('chargedeliver'); return !!d&&!d.disabled&&!document.getElementById('chargeview').classList.contains('hidden'); })){ await p.click('#chargedeliver'); await wait(500); return; } await wait(150); } };
 await ctl({rpc:'ok',tamper:false,userOk:true,unconfirmed:false,storeOnly:false,runsFail:false}); await setTable([]);

 await p.goto('http://localhost:8080/'); await wait(1200);
 // Case numbers (28 October 2026): on the list, the welcome tiles, and found by "case N".
 const nums=await p.evaluate(()=>{
   const q=document.getElementById('wl-q'); q.value='case 4'; renderPicker();
   const hit=[...document.querySelectorAll('.wl-case')].map(b=>CASES[+b.dataset.case].prefix);
   q.value=''; renderPicker();
   return {n:CASES.length, cards:CASES.map(c=>c.card.number), rows:document.querySelectorAll('.wl-case .wl-no').length,
     tiles:document.querySelectorAll('.ld-case .n').length, hit}; });
 ok('every case has its own number, shown on every row and tile', new Set(nums.cards).size===nums.n&&nums.cards.every(n=>Number.isInteger(n)&&n>0)&&nums.rows===nums.n&&nums.tiles===nums.n, nums);
 ok('"case 4" finds exactly that case', nums.hit.length===1, nums.hit);
 ok('signed out: no home panel', await p.evaluate(()=>document.getElementById('wl-home').hidden&&!document.getElementById('picker').classList.contains('home-on')));
 const idx=await p.evaluate(()=>CASES.findIndex(c=>c.prefix==='CHFE'));
 const KEYS=await p.evaluate(()=>Object.fromEntries(CASES.map(c=>[c.prefix,c.versionKey])));
 ok('every case stub carries a version key', Object.values(KEYS).every(k=>/^[0-9a-f]{32}$/.test(k||'')), KEYS);
 await p.evaluate(i=>ACCESS_UI.open(i),idx); await wait(300);
 await p.fill('#signinemail','res@example.com'); await p.fill('#signinpass','right-password'); await p.keyboard.press('Enter'); await wait(2500);
 await shock();
 ok('signed in, the case splash is open', await p.evaluate(()=>PACK&&PACK.prefix==='CHFE'&&!document.getElementById('splash').classList.contains('hidden')));
 ok('the splash shows the case number', await p.evaluate(()=>document.getElementById('sp-no').textContent==='Case '+PACK.card.number&&!document.getElementById('sp-no').hidden));
 ok('a case with nothing saved offers Begin only', await p.evaluate(()=>document.getElementById('sp-run').hidden&&document.getElementById('beginbtn').textContent==='Begin'));

 // A run in a non-default mode, with a few acts, a tab change and a handoff being drafted.
 const alt=await p.evaluate(()=>{ const D=SHARED.difficulty; return Object.keys(D.modes).find(k=>k!==D.default); });
 await p.evaluate(m=>{ MODE=m; begin(); },alt); await wait(4200);           // past the nurse card
 const acts=await p.evaluate(()=>{
   const ids=Object.keys(ACT).filter(id=>ACT[id].tab==='stabilization'&&!(ACT[id].performs&&ACT[id].performs.length)).slice(0,3);
   ids.forEach(id=>log({actionId:id})); render();
   TAB='investigations'; renderTabs(); renderTab();
   PENDING_HANDOFF={disposition:'x_test_disposition',diagnoses:['x_test_dx']};
   return ids; });
 ok('the run took three acts', acts.length===3, acts);
 await wait(6000);
 let T=await table();
 ok('autosave: one run in progress, with the log', T.length===1&&T[0].status==='in_progress'&&T[0].case_prefix==='CHFE'&&T[0].state&&T[0].state.log.length>=3&&T[0].mode===alt, T.map(r=>[r.status,r.case_prefix,r.mode,r.state&&r.state.log.length]));
 ok('the run is saved under this build\'s version key', T[0]&&T[0].version_key===KEYS.CHFE, [T[0]&&T[0].version_key,KEYS.CHFE]);

 // Leave through the rail's Main menu.
 await p.evaluate(()=>askLeave('menu')); await wait(400);
 const leave=await p.evaluate(()=>({txt:document.getElementById('leavemsg').textContent, t:now(), log:JSON.stringify(LOG)}));
 ok('the leave dialog says the progress is saved', /progress is saved/.test(leave.txt), leave.txt);
 await p.click('#leaveok'); await wait(1500);
 ok('left to the case list', await p.evaluate(()=>!document.getElementById('picker').classList.contains('hidden')));
 T=await table();
 ok('the saved moment is the moment of leaving', T.length===1&&Math.abs(T[0].state.t-leave.t)<0.05&&JSON.stringify(T[0].state.log)===leave.log, T[0]&&[T[0].state.t,leave.t]);
 ok('the home panel replaces most of the picture', await p.evaluate(()=>document.getElementById('picker').classList.contains('home-on')&&!document.getElementById('wl-home').hidden));
 const home=await p.evaluate(()=>document.getElementById('wl-home').innerText);
 ok('Continue lists the run with its case time', /Continue/i.test(home)&&/Resume/.test(home), home.slice(0,300));
 ok('the run carries its case number', /Case \d+/.test(home), home.slice(0,200));
 ok('the case row says in progress', await p.evaluate(()=>/In progress/.test((document.querySelector('.wl-case[data-case="'+CASES.findIndex(c=>c.prefix==='CHFE')+'"]')||{}).innerText||'')));
 await p.screenshot({path:'/tmp/e2e/progress-home.png'});

 // Resume from the home panel: the same run, paused at the same moment.
 const fnBefore=(await ctl({})).calls.fn;
 await p.click('[data-hmresume="CHFE"]'); await wait(1500);
 const r1=await p.evaluate(pre=>{
   const fp=st=>JSON.stringify({phase:st.phase,seq:st.phaseSeq,flags:[...st.flags].sort(),taken:[...st.taken].sort(),
     sat:[...st.satisfied].sort(),nurse:st.nurse.map(n=>n.t+n.kind+n.text),vitals:st.vitals,pending:st.pending.length});
   return {paused:PAUSED&&!document.getElementById('pauseview').classList.contains('hidden'),
     msg:document.getElementById('pausemsg').innerText, t:now(), mode:MODE, tab:TAB, ho:PENDING_HANDOFF,
     sameLog:JSON.stringify(LOG)===pre, sameState:fp(ST)===fp(fold(JSON.parse(pre),now(),DM())),
     nintro:typeof NINTRO==='object'&&NINTRO.active(), splash:!document.getElementById('splash').classList.contains('hidden')};
 },leave.log);
 ok('resumed paused, with a resume message, no nurse card, splash closed', r1.paused&&/Resumed at/.test(r1.msg)&&!r1.nintro&&!r1.splash, r1);
 ok('resumed at the saved case time', Math.abs(r1.t-leave.t)<0.05, [r1.t,leave.t]);
 ok('the same log and the same state as when it was left', r1.sameLog&&r1.sameState, r1);
 ok('mode, tab and the drafted handoff come back', r1.mode===alt&&r1.tab==='investigations'&&r1.ho.disposition==='x_test_disposition'&&r1.ho.diagnoses[0]==='x_test_dx', r1);
 ok('resuming a case already loaded does not download it again', (await ctl({})).calls.fn===fnBefore);
 await wait(1500);
 ok('the clock does not move until play is pressed', Math.abs(await p.evaluate(()=>now())-leave.t)<0.05);
 await p.click('#resumebtn'); await wait(1500);
 ok('after play the clock runs on from there', await p.evaluate(t=>now()>t+1&&now()<t+3,leave.t));

 // Finish: the row becomes a score summary and its log is emptied.
 await p.evaluate(()=>{ log({actionId:'early_exit',kind:'early_exit'}); finish(); }); await wait(1500);
 T=await table();
 const f=T.find(r=>r.status==='finished');
 ok('finishing turns the run into a score summary', T.length===1&&f&&f.state===null&&f.outcome&&f.ended_by==='early_exit'&&f.summary&&Array.isArray(f.summary.rows)&&f.summary.rows.length>=5, T);
 ok('the summary is labels, percentages and counts only', f&&f.summary.rows.every(r=>Object.keys(r).sort().join()==='detail,id,label,pct'), f&&f.summary.rows[0]);
 const pct=await p.evaluate(()=>{ const o=overallScore(ST); return o.scored?o.pct:null; });
 ok('the stored score is the debrief\'s', f&&f.score_pct===pct, [f&&f.score_pct,pct]);
 await p.evaluate(()=>toPickerFromDebrief()); await wait(1200);
 const h2=await p.evaluate(()=>document.getElementById('wl-home').innerText);
 ok('Your attempts lists it; nothing in progress', /No case in progress/.test(h2)&&/Ended early|Critical|critical|failed/i.test(h2), h2.slice(0,400));
 ok('the case row shows the attempt', await p.evaluate(()=>/attempt/.test(document.querySelector('.wl-case[data-case="'+CASES.findIndex(c=>c.prefix==='CHFE')+'"]').innerText)));
 await p.click('[data-hmopen]'); await wait(200);
 ok('an attempt opens to its summary rows', await p.evaluate(()=>document.querySelectorAll('.hm-part').length>=5));
 await p.screenshot({path:'/tmp/e2e/progress-attempt.png'});
 await p.click('.hm-rx [data-hmdel]'); await wait(150);
 await p.click('[data-hmdelok]'); await wait(800);
 ok('delete removes the attempt', (await table()).length===0&&await p.evaluate(()=>!document.querySelector('.hm-row')));

 // Start over: a saved run is discarded and a new one takes its place.
 await p.evaluate(i=>chooseCase(i),idx); await wait(400);
 await p.evaluate(()=>begin()); await wait(4000); await p.evaluate(()=>{ log({actionId:Object.keys(ACT).find(id=>ACT[id].tab==='stabilization')}); }); await wait(6000);
 const firstId=(await table())[0]&&(await table())[0].id;
 await p.evaluate(()=>askLeave('menu')); await wait(300); await p.click('#leaveok'); await wait(1500);
 await p.evaluate(i=>chooseCase(i),idx); await wait(500);
 const sp=await p.evaluate(()=>({run:!document.getElementById('sp-run').hidden, resume:(document.getElementById('sp-resume')||{}).textContent||'', begin:document.getElementById('beginbtn').textContent}));
 ok('the splash offers Resume and Start over', sp.run&&/Resume at \d+:\d\d/.test(sp.resume)&&sp.begin==='Start over', sp);
 await p.click('#beginbtn'); await wait(4000); await wait(6000);
 T=await table();
 ok('Start over discards the old run and saves the new one', T.length===1&&T[0].status==='in_progress'&&T[0].id!==firstId, T.map(r=>[r.id===firstId,r.status]));

 // A reload keeps the run, with no browser prompt.
 await p.evaluate(()=>{ log({actionId:Object.keys(ACT).filter(id=>ACT[id].tab==='stabilization')[1]}); }); await wait(300);
 const beforeReload=await p.evaluate(()=>({t:now(),n:LOG.length}));
 await p.reload(); await wait(2500);
 T=await table();
 ok('a reload asks nothing', dialogs.length===0, dialogs);
 ok('the run survives the reload, saved up to the moment of leaving', T.length===1&&T[0].status==='in_progress'&&T[0].state.log.length===beforeReload.n&&T[0].state.t>=beforeReload.t-0.5, T[0]&&[T[0].state.log.length,beforeReload.n,T[0].state.t,beforeReload.t]);
 ok('after the reload the home panel shows it', /Resume/.test(await p.evaluate(()=>document.getElementById('wl-home').innerText)));

 // The case has changed since: the notice, and the run is deleted.
 const stale=Object.assign({},T[0],{version_key:'f'.repeat(32)});
 await setTable([stale]); await p.evaluate(()=>PROGRESS.refresh()); await wait(600);
 ok('Continue warns that the case has changed', /improved since/.test(await p.evaluate(()=>document.getElementById('wl-home').innerText)));
 await p.click('[data-hmresume="CHFE"]'); await wait(3000); await shock();
 const imp=await p.evaluate(()=>({shown:!document.getElementById('improvedview').classList.contains('hidden'), title:document.getElementById('improvedtitle').innerText,
   splash:!document.getElementById('splash').classList.contains('hidden'), started:STARTED}));
 ok('the case-has-been-improved notice opens over the splash, nothing resumed', imp.shown&&/improved/.test(imp.title)&&imp.splash&&!imp.started, imp);
 await wait(500);
 ok('and the old run is deleted', (await table()).length===0);
 await p.click('#improvedok'); await wait(200);
 ok('OK closes it and the splash offers Begin', await p.evaluate(()=>document.getElementById('improvedview').classList.contains('hidden')&&document.getElementById('beginbtn').textContent==='Begin'&&document.getElementById('sp-run').hidden));

 // A save that fails does not stop the case, and the leave dialog does not promise anything.
 await p.evaluate(()=>begin()); await wait(4000);
 await ctl({runsFail:true}); await p.evaluate(()=>log({actionId:Object.keys(ACT).find(id=>ACT[id].tab==='stabilization')})); await wait(6000);
 await p.evaluate(()=>askLeave('menu')); await wait(400);
 const lt=await p.evaluate(()=>document.getElementById('leavemsg').textContent);
 ok('with saving failing, the leave dialog says progress will be lost', /lose progress/.test(lt), lt);
 await p.click('#leavecancel'); await ctl({runsFail:false}); await wait(6000);
 ok('saving recovers when the server does', (await table()).length===1);
 await p.evaluate(()=>askLeave('menu')); await wait(300); await p.click('#leaveok'); await wait(1500);

 // Phone width: the home panel and the list both fit, no sideways scroll.
 await p.setViewportSize({width:390,height:844}); await wait(400);
 const narrow=await p.evaluate(()=>({sw:document.documentElement.scrollWidth, home:document.getElementById('wl-home').getBoundingClientRect().height}));
 ok('phone width: no sideways scroll, the panel has room', narrow.sw<=390&&narrow.home>120, narrow);
 await p.screenshot({path:'/tmp/e2e/progress-phone.png'});
 await p.setViewportSize({width:1440,height:860});

 // Day and night (28 October 2026): the board's switch flips the theme and is remembered.
 const th0=await p.evaluate(()=>document.documentElement.dataset.theme);
 await p.click('.wl-head [data-themetoggle]'); await wait(300);
 const th1=await p.evaluate(()=>({t:document.documentElement.dataset.theme, s:localStorage.getItem('emsim.theme')}));
 ok('the day and night switch flips the theme and remembers it', th1.t!==th0&&th1.s===th1.t&&['day','night'].includes(th1.t), [th0,th1]);
 await p.click('.wl-head [data-themetoggle]'); await wait(300);
 ok('no page errors', errs.length===0, errs);
 ok('no CSP violations', csp.length===0, csp);

 // The site with no Supabase settings: nothing of this appears.
 const q=await ctx.newPage(); const errs0=[]; q.on('pageerror',e=>errs0.push(e.message));
 await q.goto('http://localhost:8090/'); await q.waitForTimeout(1000);
 ok('unconfigured site: no home panel, no progress calls', await q.evaluate(()=>document.getElementById('wl-home').hidden&&!PROGRESS.enabled())&&errs0.length===0, errs0);
 await b.close();
})();
